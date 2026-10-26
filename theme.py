import streamlit as st

CLAY = "#D97757"
CLAY_DARK = "#C15F3C"
INK = "#141413"
MUTED = "#6B6A63"
BORDER = "#E3DFD3"

_CSS = f"""
<style>
.block-container {{ padding-top: 2.5rem; max-width: 780px; }}
header[data-testid="stHeader"] {{ background: transparent; }}

h1, h2, h3, .wanglab-title {{
    font-family: Georgia, "Times New Roman", serif;
    font-weight: 500;
    color: {INK};
    letter-spacing: -0.01em;
}}

.wanglab-banner {{ margin-bottom: 1.75rem; padding-bottom: 1.25rem; border-bottom: 1px solid {BORDER}; }}
.wanglab-title {{ margin: 0; font-size: 2.1rem; line-height: 1.2; }}
.wanglab-title .mark {{ color: {CLAY}; }}
.wanglab-sub {{ margin: 0.4rem 0 0 0; color: {MUTED}; font-size: 0.95rem; }}

section[data-testid="stSidebar"] {{ background: #F0EEE6; border-right: 1px solid {BORDER}; }}
section[data-testid="stSidebar"] h2 {{ font-size: 1.15rem; }}

div.stButton > button, a[data-testid="stBaseLinkButton-secondary"] {{
    background: #FFFFFF;
    border: 1px solid {BORDER} !important;
    color: {INK} !important;
    border-radius: 10px;
}}
div.stButton > button:hover, a[data-testid="stBaseLinkButton-secondary"]:hover {{
    border-color: {CLAY} !important;
    color: {CLAY_DARK} !important;
    background: #FFFFFF !important;
}}

div[data-testid="stChatMessage"] {{
    background: transparent;
    border-radius: 14px;
    padding: 0.75rem 0.5rem;
}}
div[data-testid="stChatInput"] {{
    border-radius: 16px;
    border: 1px solid {BORDER};
    box-shadow: 0 2px 10px rgba(20, 20, 19, 0.06);
}}

div[data-testid="stMetric"] {{
    background: #FFFFFF;
    border: 1px solid {BORDER};
    border-radius: 12px;
    padding: 0.9rem 1rem;
}}
div[data-testid="stMetricLabel"] {{ color: {MUTED}; }}
hr {{ border-color: {BORDER}; }}
</style>
"""


def apply_theme(title: str, subtitle: str, mark: str = "✻"):
    st.markdown(
        _CSS
        + f"""
        <div class="wanglab-banner">
            <h1 class="wanglab-title"><span class="mark">{mark}</span> {title}</h1>
            <p class="wanglab-sub">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
