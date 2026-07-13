import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="Chat with Qwen3-32B", page_icon="💬")
st.title("💬 Chat with Qwen3-32B")

BASE_URL = st.secrets["VLLM_BASE_URL"]  # e.g. "https://xxxx.trycloudflare.com/v1"
API_KEY = st.secrets["VLLM_API_KEY"]
MODEL = "qwen3-32b"

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=MODEL,
                messages=st.session_state.messages,
                max_tokens=2048,
                stream=True,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            reply = st.write_stream(
                chunk.choices[0].delta.content
                for chunk in stream
                if chunk.choices[0].delta.content
            )
        except Exception as e:
            reply = f"Error reaching the model API: {e}"
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
