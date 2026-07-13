import streamlit as st
from openai import OpenAI

RUTGERS_SCARLET = "#CC0033"
API_DOCS_URL = "https://github.com/tjboise/lab_llm_api#readme"

MODEL_OPTIONS = {
    "Qwen3-32B": "qwen3-32b",
}

st.set_page_config(page_title="WangLab", page_icon="🧪", layout="centered")

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 2rem; }}

    .wanglab-banner {{
        background: linear-gradient(90deg, {RUTGERS_SCARLET} 0%, #8a0026 100%);
        padding: 1.25rem 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
    }}
    .wanglab-banner h1 {{
        margin: 0;
        font-size: 1.8rem;
        color: white;
    }}
    .wanglab-banner p {{
        margin: 0.25rem 0 0 0;
        opacity: 0.9;
        font-size: 0.95rem;
    }}

    section[data-testid="stSidebar"] {{
        border-right: 3px solid {RUTGERS_SCARLET};
    }}
    section[data-testid="stSidebar"] h2 {{
        color: {RUTGERS_SCARLET};
    }}

    div.stButton > button, a[data-testid="stBaseLinkButton-secondary"] {{
        border-color: {RUTGERS_SCARLET} !important;
        color: {RUTGERS_SCARLET} !important;
    }}
    div.stButton > button:hover {{
        background-color: {RUTGERS_SCARLET} !important;
        color: white !important;
    }}
    </style>

    <div class="wanglab-banner">
        <h1>🧪 WangLab</h1>
        <p>Rutgers University · Self-hosted LLM Chat</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Settings")
    model_label = st.selectbox("Model", options=list(MODEL_OPTIONS.keys()), index=0)
    MODEL = MODEL_OPTIONS[model_label]

    st.divider()
    st.link_button("🔌 Use the API", API_DOCS_URL, use_container_width=True)
    st.caption("Docs on calling this model from your own code.")

    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

BASE_URL = st.secrets["VLLM_BASE_URL"]  # e.g. "https://xxxx.trycloudflare.com/v1"
API_KEY = st.secrets["VLLM_API_KEY"]

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
