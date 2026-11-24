import base64
import io

import requests
import streamlit as st
from docx import Document
from openai import OpenAI
from pypdf import PdfReader

from theme import apply_theme

API_DOCS_URL = "https://github.com/tjboise/lab_llm_api#readme"

MODEL = "llama-4-scout"
# The model's context window is 16K tokens; leave room for the question and the answer.
MAX_DOC_CHARS = 24_000

st.set_page_config(page_title="WangLab", page_icon="✻", layout="centered")

apply_theme("WangLab", "Rutgers University · Self-hosted LLM Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.markdown("## Settings")
    st.caption("Use the **+** button in the message box to attach images, PDF or Word files.")

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


def extract_text(file) -> str:
    if file.name.lower().endswith(".pdf"):
        return "\n\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(file.getvalue())).pages)
    doc = Document(io.BytesIO(file.getvalue()))
    parts = [p.text for p in doc.paragraphs]
    for table in doc.tables:
        parts += [" | ".join(cell.text for cell in row.cells) for row in table.rows]
    return "\n".join(parts)


def to_api_messages(messages):
    """Turn stored messages (which may hold "doc" parts) into OpenAI-format messages."""
    api_messages = []
    for m in messages:
        if isinstance(m["content"], str):
            api_messages.append(m)
            continue
        parts = []
        for part in m["content"]:
            if part["type"] == "doc":
                parts.append({"type": "text", "text": f'[Attached document: {part["name"]}]\n{part["text"]}'})
            else:
                parts.append(part)
        api_messages.append({"role": m["role"], "content": parts})
    return api_messages


def render_content(content):
    if isinstance(content, str):
        st.markdown(content)
        return
    for part in content:
        if part["type"] == "text":
            st.markdown(part["text"])
        elif part["type"] == "doc":
            st.caption(f'📄 {part["name"]}')
        elif part["type"] == "image_url":
            header, b64data = part["image_url"]["url"].split(",", 1)
            st.image(base64.b64decode(b64data))


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        render_content(message["content"])

if prompt := st.chat_input(
    "Say something...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "webp", "pdf", "docx"],
):
    user_input = prompt.text or "Please analyze the attached file(s)."
    uploaded_files = prompt.files
    if uploaded_files:
        content = [{"type": "text", "text": user_input}]
        budget = MAX_DOC_CHARS
        for f in uploaded_files:
            if f.name.lower().endswith((".pdf", ".docx")):
                try:
                    text = extract_text(f)
                except Exception as e:
                    st.error(f"Couldn't read {f.name}: {e}")
                    continue
                if not text.strip():
                    st.warning(f"{f.name} has no extractable text (scanned PDF?). Upload its pages as images instead.")
                    continue
                if len(text) > budget:
                    st.warning(f"{f.name} is too long for the model's context window; only the first part is used.")
                text = text[:budget]
                budget -= len(text)
                content.append({"type": "doc", "name": f.name, "text": text})
            else:
                b64data = base64.b64encode(f.getvalue()).decode()
                content.append({"type": "image_url", "image_url": {"url": f"data:{f.type};base64,{b64data}"}})
    else:
        content = user_input

    st.session_state.messages.append({"role": "user", "content": content})
    with st.chat_message("user"):
        render_content(content)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=to_api_messages(st.session_state.messages),
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
