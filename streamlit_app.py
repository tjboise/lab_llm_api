import re

import plotly.graph_objects as go
import requests
import streamlit as st
from openai import OpenAI

RUTGERS_SCARLET = "#CC0033"
API_DOCS_URL = "https://github.com/tjboise/lab_llm_api#readme"

MODEL_OPTIONS = {
    "Qwen3-32B": "qwen3-32b",
}

# Pricing, $ per 1M tokens (input, output). Checked manually — update if prices change.
COMPARISON_MODELS = {
    "Self-hosted": (0.0, 0.0, "#2a78d6"),
    "Gemini 2.5 Flash": (0.30, 2.50, "#eb6834"),
    "GPT-5": (1.25, 10.00, "#1baf7a"),
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

BASE_URL = st.secrets["VLLM_BASE_URL"]  # e.g. "https://xxxx.ngrok-free.dev/v1"
API_KEY = st.secrets["VLLM_API_KEY"]


@st.cache_data(ttl=30)
def fetch_token_totals():
    metrics_url = BASE_URL.removesuffix("/v1") + "/metrics"
    resp = requests.get(
        metrics_url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=10
    )
    resp.raise_for_status()
    text = resp.text

    def read_counter(metric_name: str) -> float:
        total = 0.0
        for line in text.splitlines():
            if line.startswith(metric_name + "{") or line.startswith(metric_name + " "):
                match = re.search(r"}\s+([\d.eE+-]+)$", line) or re.search(r"\s+([\d.eE+-]+)$", line)
                if match:
                    total += float(match.group(1))
        return total

    return read_counter("vllm:prompt_tokens_total"), read_counter("vllm:generation_tokens_total")


with st.sidebar:
    st.divider()
    st.markdown("## 💰 Usage & Savings")
    try:
        prompt_tokens, completion_tokens = fetch_token_totals()
        st.metric("Total tokens", f"{prompt_tokens + completion_tokens:,.0f}")

        costs, colors, labels = [], [], []
        for name, (price_in, price_out, color) in COMPARISON_MODELS.items():
            costs.append(prompt_tokens / 1e6 * price_in + completion_tokens / 1e6 * price_out)
            colors.append(color)
            labels.append(name)

        fig = go.Figure(
            go.Bar(
                x=costs,
                y=labels,
                orientation="h",
                marker=dict(color=colors),
                text=[f"${c:,.3f}" for c in costs],
                textposition="outside",
                cliponaxis=False,
            )
        )
        fig.update_layout(
            height=180,
            margin=dict(l=10, r=45, t=10, b=25),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(size=11),
            xaxis=dict(title=None),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        st.caption(
            f"Saved **${costs[1]:,.3f}** vs Gemini 2.5 Flash, "
            f"**${costs[2]:,.3f}** vs GPT-5 — since last server restart."
        )
    except Exception as e:
        st.caption(f"Usage stats unavailable: {e}")

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
