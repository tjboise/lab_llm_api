from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

RUTGERS_SCARLET = "#CC0033"

# Pricing, $ per 1M tokens (input, output). Checked manually — update if prices change.
COMPARISON_MODELS = {
    "Self-hosted": (0.0, 0.0, "#2a78d6"),
    "Gemini 2.5 Flash": (0.30, 2.50, "#eb6834"),
    "GPT-5": (1.25, 10.00, "#1baf7a"),
}

st.set_page_config(page_title="WangLab — Usage Stats", page_icon="📊", layout="centered")

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
        <h1>📊 Usage Stats</h1>
        <p>Rutgers University · Self-hosted LLM Chat</p>
    </div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=15)
def fetch_usage():
    usage_url = st.secrets["VLLM_BASE_URL"].removesuffix("/v1") + "/usage"
    resp = requests.get(usage_url, timeout=10)
    resp.raise_for_status()
    return resp.json()


try:
    usage = fetch_usage()
except Exception as e:
    st.error(f"Couldn't reach the model API to read usage stats: {e}")
    st.stop()

st.caption(
    "Persisted on the server — survives restarts and redeploys. "
    "**Chat** = used on the WangLab chat page. **API** = everyone calling "
    "the API directly with their own code."
)

chat_prompt, chat_completion = usage["chat"]["prompt_tokens"], usage["chat"]["completion_tokens"]
api_prompt, api_completion = usage["api"]["prompt_tokens"], usage["api"]["completion_tokens"]
total_prompt, total_completion = chat_prompt + api_prompt, chat_completion + api_completion

col1, col2, col3 = st.columns(3)
col1.metric("Total tokens", f"{total_prompt + total_completion:,.0f}")
col2.metric("Chat", f"{chat_prompt + chat_completion:,.0f}")
col3.metric("API", f"{api_prompt + api_completion:,.0f}")

st.divider()
st.subheader("What this would have cost elsewhere")
st.caption("Same total token volume, priced at each provider's public per-token API rate.")

costs, colors, labels = [], [], []
for name, (price_in, price_out, color) in COMPARISON_MODELS.items():
    costs.append(total_prompt / 1e6 * price_in + total_completion / 1e6 * price_out)
    colors.append(color)
    labels.append(name)

fig = go.Figure(
    go.Bar(
        x=costs, y=labels, orientation="h", marker=dict(color=colors),
        text=[f"${c:,.4f}" for c in costs], textposition="outside", cliponaxis=False,
    )
)
fig.update_layout(
    xaxis_title="Cost (USD)",
    yaxis=dict(autorange="reversed"),
    height=260,
    margin=dict(l=10, r=60, t=10, b=40),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(size=14),
)
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

save_col1, save_col2 = st.columns(2)
save_col1.metric("💰 Saved vs Gemini 2.5 Flash", f"${costs[1]:,.4f}")
save_col2.metric("💰 Saved vs GPT-5", f"${costs[2]:,.4f}")

st.divider()
st.subheader("Who's using it")

by_user = usage.get("by_user", {})
if not by_user:
    st.caption("No per-user data yet.")
else:
    rows = []
    for ip, u in by_user.items():
        last_seen = u.get("last_seen")
        if last_seen:
            dt = datetime.fromisoformat(last_seen)
            age = datetime.now(timezone.utc) - dt
            minutes = int(age.total_seconds() // 60)
            last_seen_display = (
                "just now" if minutes < 1
                else f"{minutes}m ago" if minutes < 60
                else f"{minutes // 60}h ago" if minutes < 1440
                else f"{minutes // 1440}d ago"
            )
        else:
            last_seen_display = "—"
        rows.append({
            "Caller (IP)": ip,
            "Source": u.get("source", "?"),
            "Total tokens": u["prompt_tokens"] + u["completion_tokens"],
            "Prompt": u["prompt_tokens"],
            "Completion": u["completion_tokens"],
            "Last seen": last_seen_display,
        })

    df = pd.DataFrame(rows).sort_values("Total tokens", ascending=False).reset_index(drop=True)
    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(
        "Caller identified by source IP address. Everyone on the WangLab "
        "chat page shares one \"chat\" source; direct API callers each show "
        "their own IP."
    )
