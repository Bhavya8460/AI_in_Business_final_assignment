"""Skill Lab — run any single agent in isolation."""

from __future__ import annotations

import json
import logging
import os
import time

import streamlit as st
from dotenv import load_dotenv

from agent import run_single_agent
from config import AGENT_META, EXAMPLE_TICKERS
from ui.components import disclaimer_banner, empty_block, hero, inject_css
from ui.dashboard import render_single_agent

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

st.set_page_config(page_title="Skill Lab — OracleIQ", page_icon="🧪", layout="wide")
inject_css()

hero("🧪 Skill Lab", "Fire any single Buffett agent. See its raw and formatted output.")
disclaimer_banner()

st.session_state.setdefault("lab_ticker", "")
st.session_state.setdefault("lab_agent", "business")
st.session_state.setdefault("lab_result", None)


def _missing_keys() -> list[str]:
    missing: list[str] = []
    for key in ("ANTHROPIC_API_KEY", "TAVILY_API_KEY"):
        if os.environ.get(key):
            continue
        try:
            if st.secrets.get(key):
                continue
        except Exception:
            pass
        missing.append(key)
    return missing


_missing = _missing_keys()
if _missing:
    st.warning("Missing API keys: **" + ", ".join(_missing) + "**.")


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
left, right = st.columns(2)
with left:
    st.session_state.lab_ticker = st.text_input(
        "Ticker",
        value=st.session_state.lab_ticker,
        placeholder="e.g. AAPL",
    ).upper().strip()
    st.caption("Or pick:")
    chip_cols = st.columns(len(EXAMPLE_TICKERS))
    for col, t in zip(chip_cols, EXAMPLE_TICKERS):
        with col:
            if st.button(t, key=f"lab_chip_{t}", use_container_width=True):
                st.session_state.lab_ticker = t
                st.rerun()

with right:
    options = [a for a in AGENT_META.keys() if a != "risk_profiler"]
    st.session_state.lab_agent = st.selectbox(
        "Agent",
        options=options,
        index=options.index(st.session_state.lab_agent) if st.session_state.lab_agent in options else 0,
        format_func=lambda a: f"{AGENT_META[a]['emoji']} {AGENT_META[a]['label']} — {AGENT_META[a]['tagline']}",
    )

    if st.session_state.lab_agent in {"thesis", "moat", "valuation"}:
        st.info(
            "ℹ️ This agent works best after upstream agents have populated state. "
            "Running it alone gives a less informed answer than running through Full Buffett Brief."
        )

    run_clicked = st.button(
        "🚀 Run agent",
        type="primary",
        disabled=bool(_missing) or not st.session_state.lab_ticker,
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if run_clicked and st.session_state.lab_ticker:
    ticker = st.session_state.lab_ticker
    agent_id = st.session_state.lab_agent
    risk_profile = st.session_state.get("risk_profile")
    started = time.time()
    with st.spinner(f"Running {AGENT_META[agent_id]['label']} on {ticker}…"):
        try:
            update = run_single_agent(ticker, agent_id, risk_profile)
            update["ticker"] = ticker
            update["_runtime"] = time.time() - started
            st.session_state.lab_result = update
        except Exception as exc:
            st.error(f"Agent crashed: {exc}")
            st.session_state.lab_result = None


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------
result = st.session_state.lab_result
if result:
    agent_id = st.session_state.lab_agent
    st.divider()
    st.success(f"Completed in {result.get('_runtime', 0):.1f}s")

    formatted_tab, raw_tab = st.tabs(["🎨 Formatted", "🧾 Raw JSON"])
    with formatted_tab:
        render_single_agent(agent_id, result)
    with raw_tab:
        agent_payload = result.get(agent_id) or {}
        st.code(json.dumps(agent_payload, indent=2, default=str), language="json")
elif not run_clicked:
    empty_block("Pick an agent and a ticker, then run it to see the output.")
