"""Buffett's Wisdom page — educational content driving the agents."""

from __future__ import annotations

import streamlit as st

from config import AGENT_META, BUFFETT_CHECKLIST
from ui.components import buffett_quote, hero, inject_css

st.set_page_config(page_title="Buffett's Wisdom — OracleIQ", page_icon="📜", layout="wide")
inject_css()

hero("📜 Buffett's Wisdom", "The principles that drive every agent in the system.")

st.markdown(
    """
OracleIQ encodes Warren Buffett's investing philosophy into nine specialized
agents. Each agent is built around a single principle from Buffett's
letters and Berkshire Hathaway's annual reports — and the system as a
whole is inspired by the framework laid out in *The Warren Buffett Way*
by Robert Hagstrom.
"""
)

st.divider()

# ---------------------------------------------------------------------------
# The agents and their principles
# ---------------------------------------------------------------------------
st.markdown("### Each agent's guiding principle")
for agent_id, meta in AGENT_META.items():
    with st.container(border=True):
        cols = st.columns([1, 8])
        with cols[0]:
            st.markdown(f"<div style='font-size:2rem; text-align:center;'>{meta['emoji']}</div>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"**{meta['label']}** — *{meta['tagline']}*")
            buffett_quote(meta["principle"])

st.divider()

# ---------------------------------------------------------------------------
# The 12-point checklist
# ---------------------------------------------------------------------------
st.markdown("### Buffett's 12-Point Checklist")
st.caption(
    "*The Thesis Synthesizer scores every stock against these twelve "
    "questions. Items with weight 2.0 carry the most influence on the "
    "Buffett Score.*"
)

rows = [
    {
        "ID": item["id"],
        "Question": item["question"],
        "Weight": item["weight"],
    }
    for item in BUFFETT_CHECKLIST
]
st.dataframe(rows, hide_index=True, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# A few extra Buffett quotes for ambiance
# ---------------------------------------------------------------------------
st.markdown("### Quotes that shape the system")

extras = [
    "Rule No. 1: Never lose money. Rule No. 2: Never forget rule No. 1.",
    "Our favorite holding period is forever.",
    "It's better to hang out with people better than you. Pick out associates whose behavior is better than yours and you'll drift in that direction.",
    "Time is the friend of the wonderful business, the enemy of the mediocre.",
    "If you don't feel comfortable owning a stock for 10 years, you shouldn't own it for 10 minutes.",
]
for q in extras:
    buffett_quote(q)

st.divider()
st.caption(
    "*Inspired by* The Warren Buffett Way *by Robert Hagstrom and the "
    "Berkshire Hathaway annual letters (1977-present).*"
)
