"""OracleIQ — main Streamlit entry point."""

from __future__ import annotations

import logging
import os
import time

import streamlit as st
from dotenv import load_dotenv

from agent import stream_run
from config import EXAMPLE_TICKERS, MODES
from ui.components import (
    disclaimer_banner,
    empty_block,
    hero,
    inject_css,
    mode_card_html,
)
from ui.dashboard import render_dashboard
from ui.progress import make_panel
from ui.risk_form import render_profile_summary, render_risk_form
from utils.pdf_export import build_pdf

# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

st.set_page_config(
    page_title="OracleIQ — Buffett-Inspired Due Diligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()


def _init_session() -> None:
    st.session_state.setdefault("mode", "full_buffett_brief")
    st.session_state.setdefault("ticker", "")
    st.session_state.setdefault("final_state", None)
    st.session_state.setdefault("running", False)
    st.session_state.setdefault("risk_profile", None)
    st.session_state.setdefault("show_risk_form", True)


_init_session()


# ---------------------------------------------------------------------------
# Hero + disclaimer
# ---------------------------------------------------------------------------
hero(
    "OracleIQ — Buffett-Inspired Investment Due Diligence",
    "9 specialized AI agents · Real SEC filings · Verdict tailored to you.",
)
disclaimer_banner()


# ---------------------------------------------------------------------------
# Missing-key guard
# ---------------------------------------------------------------------------
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
    st.warning(
        "Missing API keys: **" + ", ".join(_missing) + "**. "
        "Add them to a `.env` file or `.streamlit/secrets.toml` before running an analysis."
    )


# ---------------------------------------------------------------------------
# Section 1 — Risk Profiler
# ---------------------------------------------------------------------------
profile = st.session_state.get("risk_profile")
with st.expander("🧭 Step 1 · Risk profile", expanded=(profile is None)):
    if profile is not None:
        render_profile_summary()
        if st.button("✏️ Edit profile", key="edit_profile"):
            st.session_state["risk_profile"] = None
            st.rerun()
    else:
        render_risk_form()


# ---------------------------------------------------------------------------
# Section 2 — Mode selector
# ---------------------------------------------------------------------------
st.markdown("### 📋 Step 2 · Pick an analysis mode")

mode_keys = list(MODES.keys())
cols = st.columns(len(mode_keys))
for col, mode_key in zip(cols, mode_keys):
    cfg = MODES[mode_key]
    with col:
        st.markdown(
            mode_card_html(
                cfg["label"],
                cfg["description"],
                cfg["agents"],
                cfg["estimated_time"],
                selected=(st.session_state.mode == mode_key),
            ),
            unsafe_allow_html=True,
        )
        if st.button(
            "Select" if st.session_state.mode != mode_key else "✓ Selected",
            key=f"pick_{mode_key}",
            use_container_width=True,
            type="primary" if st.session_state.mode == mode_key else "secondary",
        ):
            st.session_state.mode = mode_key
            st.rerun()


# ---------------------------------------------------------------------------
# Section 3 — Ticker input + run
# ---------------------------------------------------------------------------
st.markdown("### 🎯 Step 3 · Enter a US ticker")

input_col, run_col = st.columns([3, 1])
with input_col:
    st.session_state.ticker = st.text_input(
        "Stock ticker",
        value=st.session_state.ticker,
        placeholder="e.g. AAPL",
        label_visibility="collapsed",
    ).upper().strip()
with run_col:
    can_run = (
        not _missing
        and bool(st.session_state.ticker)
        and not st.session_state.running
        and (st.session_state.risk_profile is not None)
    )
    run_clicked = st.button(
        "🚀 Run Analysis",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
    )

if st.session_state.risk_profile is None:
    st.caption("Save your risk profile (Step 1) before running.")

st.caption("Or pick an example:")
chip_cols = st.columns(len(EXAMPLE_TICKERS))
for col, t in zip(chip_cols, EXAMPLE_TICKERS):
    with col:
        if st.button(t, key=f"chip_{t}", use_container_width=True):
            st.session_state.ticker = t
            st.rerun()


# ---------------------------------------------------------------------------
# Section 4 — Live agent execution
# ---------------------------------------------------------------------------
if run_clicked and st.session_state.ticker:
    ticker = st.session_state.ticker
    mode_key = st.session_state.mode
    agent_ids = MODES[mode_key]["agents"]
    risk_profile = st.session_state.risk_profile

    st.session_state.running = True
    st.session_state.final_state = None

    st.divider()
    st.markdown(f"### 🔄 Step 4 · Live agents working on *{ticker}*")
    panel = make_panel(agent_ids)

    if agent_ids:
        panel.update(agent_ids[0], "running", "Reading SEC filings…")

    final_state: dict = {"sec_filings_used": []}
    started = time.time()
    try:
        for node_name, node_output in stream_run(ticker, mode_key, risk_profile):
            if node_name == "entry":
                continue

            err = next(
                (e for e in (node_output.get("errors") or []) if e.get("node") == node_name),
                None,
            )
            if err:
                panel.update(node_name, "failed", err.get("error", ""))
            else:
                msgs = node_output.get("messages") or []
                detail = ""
                for m in reversed(msgs):
                    if m.get("node") == node_name and m.get("status") == "complete":
                        detail = m.get("detail", "")
                        break
                panel.update(node_name, "complete", detail)

            for k, v in node_output.items():
                if k in {"messages", "errors", "completed_nodes", "sec_filings_used"}:
                    final_state.setdefault(k, [])
                    final_state[k].extend(v or [])
                else:
                    final_state[k] = v

            completed = set(final_state.get("completed_nodes") or [])
            for nxt in agent_ids:
                if nxt not in completed:
                    panel.update(nxt, "running", "Working…")
                    break
    except Exception as exc:
        st.error(f"Pipeline crashed: {exc}")
    finally:
        st.session_state.running = False

    final_state.setdefault("ticker", ticker)
    final_state.setdefault("mode", mode_key)
    final_state["risk_profile"] = risk_profile
    final_state["started_at"] = started
    final_state["finished_at"] = time.time()
    st.session_state.final_state = final_state
    st.toast(f"Analysis complete in {final_state['finished_at'] - started:.1f}s", icon="✅")


# ---------------------------------------------------------------------------
# Section 5 — Results dashboard
# ---------------------------------------------------------------------------
final = st.session_state.final_state
if final:
    st.divider()
    header_col, action_col = st.columns([3, 1])
    with header_col:
        st.markdown(f"### 📊 Results — *{final.get('ticker', '')}*")
    with action_col:
        try:
            pdf_bytes = build_pdf(final)
            st.download_button(
                "📥 Download PDF",
                data=pdf_bytes,
                file_name=f"oracleiq_{final.get('ticker', 'report').lower()}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.warning(f"PDF export unavailable: {exc}")

    if final.get("sec_filings_used"):
        with st.expander(f"📑 SEC filings consulted ({len(final['sec_filings_used'])})"):
            for f in final["sec_filings_used"]:
                st.markdown(
                    f"- **{f.get('form', '?')}** filed {f.get('filing_date', '?')} "
                    f"(`{f.get('accession', '?')}`) — used by `{f.get('agent', '?')}` agent"
                )

    render_dashboard(final)
elif not st.session_state.running:
    st.divider()
    empty_block("Save your risk profile, pick a mode, enter a ticker, and run the agents.")
