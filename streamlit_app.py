import base64

import requests
import streamlit as st
from openai import OpenAI

from theme import apply_theme

API_DOCS_URL = "https://github.com/tjboise/lab_llm_api#readme"

MODEL = "llama-4-scout"

st.set_page_config(page_title="WangLab", page_icon="✻", layout="centered")

apply_theme("WangLab", "Rutgers University · Self-hosted LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

with st.sidebar:
    st.markdown("## Settings")
    uploaded_images = st.file_uploader(
        "Attach image(s)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key=f"uploader_{st.session_state.uploader_key}",
    )

    st.divider()
    st.link_button("🔌 Use the API", API_DOCS_URL, use_container_width=True)
    st.caption("Docs on calling this model from your own code.")

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

BASE_URL = st.secrets["VLLM_BASE_URL"]  # e.g. "https://xxxx.ngrok-free.dev/v1"
API_KEY = st.secrets["VLLM_API_KEY_CHAT"]  # dedicated key so usage is tracked as "chat"


@st.cache_data(ttl=15)
def fetch_usage():
    usage_url = BASE_URL.removesuffix("/v1") + "/usage"
    resp = requests.get(usage_url, timeout=10)
    resp.raise_for_status()
    return resp.json()  # {"chat": {...}, "api": {...}} — persisted on the server


with st.sidebar:
    st.divider()
    st.markdown("## 💰 Usage")
    try:
        usage = fetch_usage()
        chat_tokens = usage["chat"]["prompt_tokens"] + usage["chat"]["completion_tokens"]
        api_tokens = usage["api"]["prompt_tokens"] + usage["api"]["completion_tokens"]

        st.metric("Total tokens", f"{chat_tokens + api_tokens:,.0f}")
        stat_col1, stat_col2 = st.columns(2)
        stat_col1.metric("Chat", f"{chat_tokens:,.0f}")
        stat_col2.metric("API", f"{api_tokens:,.0f}")
        st.page_link("pages/1_📊_Usage_Stats.py", label="Full stats & who's using it", icon="📊")
    except Exception as e:
        st.caption(f"Usage stats unavailable: {e}")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def render_content(content):
    if isinstance(content, str):
        st.markdown(content)
        return
    for part in content:
        if part["type"] == "text":
            st.markdown(part["text"])
        elif part["type"] == "image_url":
            header, b64data = part["image_url"]["url"].split(",", 1)
            st.image(base64.b64decode(b64data))


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_content(message["content"])

if user_input := st.chat_input("Say something..."):
    if uploaded_images:
        content = [{"type": "text", "text": user_input}]
        for img in uploaded_images:
            b64data = base64.b64encode(img.getvalue()).decode()
            content.append({"type": "image_url", "image_url": {"url": f"data:{img.type};base64,{b64data}"}})
        st.session_state.uploader_key += 1  # reset the file_uploader widget
    else:
        content = user_input

    st.session_state.messages.append({"role": "user", "content": content})
    with st.chat_message("user"):
        render_content(content)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                max_tokens=2048,
                stream=True,
            )
            reply = st.write_stream(
                chunk.choices[0].delta.content
                for chunk in stream
                if chunk.choices and chunk.choices[0].delta.content
            )
        except Exception as e:
            reply = f"Error reaching the model API: {e}"
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
