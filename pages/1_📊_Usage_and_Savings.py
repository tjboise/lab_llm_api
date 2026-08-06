import re

import plotly.graph_objects as go
import requests
import streamlit as st

RUTGERS_SCARLET = "#CC0033"

# Pricing, $ per 1M tokens (input, output). Checked manually — update if prices change.
COMPARISON_MODELS = {
    "Self-hosted (Qwen3-32B)": (0.0, 0.0, "#2a78d6"),
    "Gemini 2.5 Flash": (0.30, 2.50, "#eb6834"),
    "GPT-5": (1.25, 10.00, "#1baf7a"),
}

st.set_page_config(page_title="WangLab — Usage & Savings", page_icon="📊", layout="centered")

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
    .wanglab-banner h1 {{ margin: 0; font-size: 1.8rem; color: white; }}
    .wanglab-banner p {{ margin: 0.25rem 0 0 0; opacity: 0.9; font-size: 0.95rem; }}
    </style>
    <div class="wanglab-banner">
        <h1>📊 Usage &amp; Savings</h1>
        <p>Rutgers University · Self-hosted LLM Chat</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=30)
def fetch_token_totals():
    base_url = st.secrets["VLLM_BASE_URL"].removesuffix("/v1")
    api_key = st.secrets["VLLM_API_KEY"]
    resp = requests.get(
        f"{base_url}/metrics",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
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

    prompt_tokens = read_counter("vllm:prompt_tokens_total")
    completion_tokens = read_counter("vllm:generation_tokens_total")
    return prompt_tokens, completion_tokens


try:
    prompt_tokens, completion_tokens = fetch_token_totals()
except Exception as e:
    st.error(f"Couldn't reach the model API to read usage stats: {e}")
    st.stop()

total_tokens = prompt_tokens + completion_tokens

st.caption(
    "Counts are read live from the model server and cover **every** request "
    "through the API (chat UI, CLI, or your own code) — but they reset to "
    "zero whenever the server restarts, so this is usage **since the last "
    "restart**, not lifetime."
)

col1, col2, col3 = st.columns(3)
col1.metric("Prompt tokens", f"{prompt_tokens:,.0f}")
col2.metric("Completion tokens", f"{completion_tokens:,.0f}")
col3.metric("Total tokens", f"{total_tokens:,.0f}")

st.divider()
st.subheader("What this would have cost elsewhere")
st.caption(
    "Same token volume, priced at each provider's public per-token API rate "
    "(input/output priced separately, since output costs more everywhere)."
)

labels, costs, colors = [], [], []
for name, (price_in, price_out, color) in COMPARISON_MODELS.items():
    cost = (prompt_tokens / 1_000_000 * price_in) + (completion_tokens / 1_000_000 * price_out)
    labels.append(name)
    costs.append(cost)
    colors.append(color)

fig = go.Figure(
    go.Bar(
        x=costs,
        y=labels,
        orientation="h",
        marker=dict(color=colors),
        text=[f"${c:,.4f}" for c in costs],
        textposition="outside",
        cliponaxis=False,
    )
)
fig.update_layout(
    xaxis_title="Cost (USD)",
    yaxis=dict(autorange="reversed"),
    height=280,
    margin=dict(l=10, r=60, t=10, b=40),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=14),
)
st.plotly_chart(fig, use_container_width=True)

gemini_cost = costs[1]
gpt5_cost = costs[2]

save_col1, save_col2 = st.columns(2)
save_col1.metric("💰 Saved vs Gemini 2.5 Flash", f"${gemini_cost:,.4f}")
save_col2.metric("💰 Saved vs GPT-5", f"${gpt5_cost:,.4f}")

st.caption(
    "Pricing as of Aug 2026 — Gemini 2.5 Flash: $0.30 / $2.50 per 1M "
    "input/output tokens. GPT-5: $1.25 / $10.00 per 1M input/output tokens. "
    "Self-hosting cost here is treated as $0 (API cost only — not "
    "accounting for hardware or electricity)."
)
