"""Reusable Streamlit + Plotly building blocks for Quorum.

Things every page might want: themed CSS, a hero, agent status cards, a
verdict banner, a Buffett-checklist row, gauges, etc.
"""

from __future__ import annotations

from typing import Iterable, Optional

import plotly.graph_objects as go
import streamlit as st

from config import AGENT_META, DISCLAIMER
from utils.formatting import verdict_color

# ---------------------------------------------------------------------------
# Global CSS — Berkshire Hathaway-meets-fintech aesthetic
# ---------------------------------------------------------------------------
GLOBAL_CSS = """
<style>
    .stApp {
        background: linear-gradient(180deg, #ffffff 0%, #f0fdf4 100%);
    }
    .main .block-container { padding-top: 1.6rem; max-width: 1200px; }

    /* Hero */
    .ciq-hero h1 {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #047857 0%, #10b981 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0 0 0.25rem 0;
    }
    .ciq-hero p {
        color: #475569;
        font-size: 1.05rem;
        margin: 0;
    }

    /* Disclaimer banner */
    .ciq-disclaimer {
        background: #fef3c7;
        border-left: 4px solid #d97706;
        color: #78350f;
        padding: 8px 14px;
        border-radius: 6px;
        font-size: 0.85rem;
        margin: 12px 0 16px 0;
    }

    /* Card */
    .ciq-card {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 1px 3px rgba(15,23,42,0.04);
        height: 100%;
    }
    .ciq-card h4 { margin: 0 0 6px 0; font-size: 1rem; }
    .ciq-card .ciq-sub { color: #475569; font-size: 0.85rem; }

    /* Mode picker */
    .ciq-mode-card {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 6px;
        transition: border-color 0.15s ease, box-shadow 0.15s ease;
    }
    .ciq-mode-card.selected {
        border-color: #10b981;
        box-shadow: 0 0 0 3px rgba(16,185,129,0.15);
    }
    .ciq-mode-card .ciq-mode-title { font-weight: 700; font-size: 1.05rem; }
    .ciq-mode-card .ciq-mode-desc { color: #475569; font-size: 0.85rem; margin: 4px 0 6px 0; }
    .ciq-mode-card .ciq-mode-meta { color: #6b7280; font-size: 0.78rem; }

    /* Agent status cards */
    .ciq-agent-card {
        background: #ffffff;
        border: 1px solid #d1fae5;
        border-radius: 12px;
        padding: 12px 14px;
        text-align: center;
        height: 100%;
    }
    .ciq-agent-card.running { border-color: #10b981; background: #ecfdf5; }
    .ciq-agent-card.complete { border-color: #047857; background: #d1fae5; }
    .ciq-agent-card.failed { border-color: #ef4444; background: #fef2f2; }
    .ciq-agent-card .ciq-agent-emoji { font-size: 1.6rem; }
    .ciq-agent-card .ciq-agent-name { font-weight: 600; font-size: 0.95rem; margin: 4px 0 2px; }
    .ciq-agent-card .ciq-agent-status { font-size: 0.75rem; color: #475569; min-height: 2.4em; }

    /* Badges */
    .ciq-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        color: #ffffff;
    }

    /* Verdict banner */
    .ciq-verdict {
        border-radius: 14px;
        padding: 22px 28px 24px 28px;
        color: #ffffff !important;
        margin: 4px 0 18px 0;
        box-shadow: 0 2px 6px rgba(15,23,42,0.08);
    }
    .ciq-verdict h2 {
        font-family: Georgia, serif;
        margin: 0 0 6px 0;
        font-size: 1.9rem;
        line-height: 1.2;
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }
    .ciq-verdict p {
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.5;
        color: #ffffff !important;
        opacity: 0.95;
    }

    /* Top summary spacing — gauges row needs breathing room before tabs */
    .ciq-summary-spacer { height: 18px; }

    /* Streamlit tabs polish */
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        margin-top: 8px;
        border-bottom: 1px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 14px;
    }

    /* Checklist row */
    .ciq-check-row {
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-bottom: 1px solid #e2e8f0;
    }
    .ciq-check-row .ciq-q { flex: 1; font-size: 0.92rem; }
    .ciq-check-row .ciq-c { color: #64748b; font-size: 0.82rem; flex: 1.5; }

    /* News */
    .ciq-news-item {
        border-left: 3px solid #10b981;
        padding: 8px 14px;
        margin-bottom: 10px;
        background: #ffffff;
        border-radius: 6px;
        box-shadow: 0 1px 2px rgba(15,23,42,0.04);
    }
    .ciq-news-date { color: #94a3b8; font-size: 0.75rem; }
    .ciq-news-headline { font-weight: 600; font-size: 0.95rem; }
    .ciq-news-summary { color: #475569; font-size: 0.85rem; margin-top: 4px; }

    /* Empty state */
    .ciq-empty {
        background: #f8fafc;
        border: 1px dashed #cbd5e1;
        border-radius: 12px;
        padding: 24px;
        text-align: center;
        color: #475569;
    }

    /* Buffett quote */
    .ciq-quote {
        background: #f0fdf4;
        border-left: 4px solid #047857;
        padding: 10px 16px;
        border-radius: 6px;
        font-style: italic;
        color: #064e3b;
        margin: 10px 0;
        font-family: Georgia, serif;
    }
</style>
"""


def inject_css() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="ciq-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def disclaimer_banner(text: Optional[str] = None) -> None:
    msg = text or DISCLAIMER
    st.markdown(
        f'<div class="ciq-disclaimer"><b>⚠️ Disclaimer.</b> {msg}</div>',
        unsafe_allow_html=True,
    )


def buffett_quote(text: str) -> None:
    st.markdown(f'<div class="ciq-quote">"{text}"<br/>— Warren Buffett</div>', unsafe_allow_html=True)


def badge(text: str, color: str = "#10b981") -> str:
    return f'<span class="ciq-badge" style="background:{color};">{text}</span>'


# ---------------------------------------------------------------------------
# Agent status card
# ---------------------------------------------------------------------------
_STATUS_LABEL = {
    "pending": "⏳ Waiting",
    "running": "🔄 Running…",
    "complete": "✅ Complete",
    "failed": "❌ Failed",
}


def render_agent_card(agent_id: str, status: str, detail: str = "") -> None:
    meta = AGENT_META.get(agent_id, {"label": agent_id, "emoji": "🤖", "tagline": ""})
    cls = status if status in {"running", "complete", "failed"} else "pending"
    label = _STATUS_LABEL.get(status, status)
    detail_text = detail or meta.get("tagline", "")

    st.markdown(
        f"""
        <div class="ciq-agent-card {cls}">
            <div class="ciq-agent-emoji">{meta['emoji']}</div>
            <div class="ciq-agent-name">{meta['label']}</div>
            <div class="ciq-agent-status"><b>{label}</b><br/>{detail_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Mode picker card
# ---------------------------------------------------------------------------
def mode_card_html(label: str, description: str, agents: Iterable[str], eta: str, selected: bool) -> str:
    cls = "ciq-mode-card selected" if selected else "ciq-mode-card"
    count = len(list(agents))
    return f"""
    <div class="{cls}">
        <div class="ciq-mode-title">{label}</div>
        <div class="ciq-mode-desc">{description}</div>
        <div class="ciq-mode-meta">{count} agents · {eta}</div>
    </div>
    """


# ---------------------------------------------------------------------------
# Verdict banner
# ---------------------------------------------------------------------------
def verdict_banner(verdict: Optional[str], summary_line: str = "") -> None:
    color = verdict_color(verdict)
    label = verdict or "PENDING"
    summary_html = (
        f'<p style="margin:0;color:#ffffff;font-size:0.95rem;line-height:1.5;opacity:0.95;">{summary_line}</p>'
        if summary_line
        else ""
    )
    st.markdown(
        f"""
        <div class="ciq-verdict" style="background:linear-gradient(135deg, {color}e6 0%, {color} 100%);">
            <h2 style="margin:0 0 6px 0;color:#ffffff;font-family:Georgia,serif;font-size:1.9rem;line-height:1.2;letter-spacing:0.5px;">{label}</h2>
            {summary_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Plotly gauges
# ---------------------------------------------------------------------------
def buffett_score_gauge(score: Optional[float]) -> go.Figure:
    has_data = score is not None
    val = float(score) if has_data else 0.0
    bar_color = "#047857" if has_data else "rgba(0,0,0,0)"
    gauge_cfg: dict = {
        "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8"},
        "bar": {"color": bar_color, "thickness": 0.18},
        "bgcolor": "#f8fafc",
        "borderwidth": 0,
        "steps": [
            {"range": [0, 40], "color": "#fee2e2"},
            {"range": [40, 65], "color": "#fef3c7"},
            {"range": [65, 100], "color": "#dcfce7"},
        ],
    }
    if has_data:
        gauge_cfg["threshold"] = {
            "line": {"color": "#047857", "width": 3},
            "thickness": 0.75,
            "value": val,
        }
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"font": {"size": 26, "color": "#0f172a"}, "suffix": "/100"},
            gauge=gauge_cfg,
            title={"text": "Buffett Score", "font": {"size": 14, "color": "#475569"}},
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def margin_of_safety_gauge(mos: Optional[float]) -> go.Figure:
    has_data = mos is not None
    val = float(mos) * 100 if has_data else 0.0
    bar_color = "#047857" if has_data else "rgba(0,0,0,0)"
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"font": {"size": 24, "color": "#0f172a"}, "suffix": "%"},
            gauge={
                "axis": {"range": [-50, 60]},
                "bar": {"color": bar_color, "thickness": 0.25},
                "steps": [
                    {"range": [-50, 0], "color": "#fee2e2"},
                    {"range": [0, 25], "color": "#fef3c7"},
                    {"range": [25, 60], "color": "#dcfce7"},
                ],
            },
            title={"text": "Margin of Safety", "font": {"size": 14, "color": "#475569"}},
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=40, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def empty_block(message: str) -> None:
    st.markdown(f'<div class="ciq-empty">{message}</div>', unsafe_allow_html=True)
