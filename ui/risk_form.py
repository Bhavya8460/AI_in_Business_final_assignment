"""Streamlit form that captures the user's risk profile.

This is the Risk Profiler "agent" from the spec — implemented as a UI
form rather than a LangGraph node, since its data has to be collected
*before* the analysis pipeline runs.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st

from agents.risk_profiler import build_risk_profile
from config import (
    EXPERIENCE_LEVELS,
    INVESTMENT_GOALS,
    INVESTMENT_HORIZONS,
    RISK_TOLERANCE_LABELS,
)


def _ss_get(key: str, default):
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def render_risk_form(*, key_prefix: str = "rp") -> Optional[dict]:
    """Render the risk-profile form. Returns a profile dict if Save was clicked.

    Persists across runs in ``st.session_state['risk_profile']``.
    """
    existing = st.session_state.get("risk_profile") or {}

    with st.form(f"{key_prefix}_form", clear_on_submit=False):
        st.markdown("#### 🧭 Tell me about you (so the verdict fits)")
        st.caption(
            "*Buffett: \"Risk comes from not knowing what you're doing.\" "
            "Your answers shape the required margin of safety and the position-size suggestion.*"
        )

        risk_tolerance = st.slider(
            "Risk tolerance (1 = capital preservation, 10 = max growth)",
            min_value=1,
            max_value=10,
            value=int(existing.get("risk_tolerance", 5)),
            help="The slider sets the margin-of-safety threshold the verdict must clear.",
        )
        st.caption(f"_{RISK_TOLERANCE_LABELS.get(risk_tolerance, '')}_")

        c1, c2 = st.columns(2)
        with c1:
            horizon = st.radio(
                "Investment horizon",
                INVESTMENT_HORIZONS,
                index=_safe_index(INVESTMENT_HORIZONS, existing.get("horizon"), 2),
            )
            goal = st.radio(
                "Primary goal",
                INVESTMENT_GOALS,
                index=_safe_index(INVESTMENT_GOALS, existing.get("goal"), 2),
            )
        with c2:
            experience = st.radio(
                "Experience level",
                EXPERIENCE_LEVELS,
                index=_safe_index(EXPERIENCE_LEVELS, existing.get("experience"), 1),
            )
            portfolio_context = st.text_area(
                "Existing portfolio (optional)",
                value=existing.get("portfolio_context", ""),
                placeholder="e.g. 60% S&P 500 ETF, 20% bonds, AAPL position…",
                height=120,
            )

        saved = st.form_submit_button("💾 Save Profile", type="primary", use_container_width=True)

    if saved:
        profile = build_risk_profile(
            risk_tolerance=risk_tolerance,
            horizon=horizon,
            goal=goal,
            experience=experience,
            portfolio_context=portfolio_context,
        )
        st.session_state["risk_profile"] = profile
        st.toast(f"Risk profile saved (required MoS: {profile['required_margin_of_safety']:.0%})", icon="✅")
        return profile

    return None


def render_profile_summary() -> None:
    """Compact summary chip used after the form is collapsed."""
    profile = st.session_state.get("risk_profile")
    if not profile:
        return
    cols = st.columns(5)
    cols[0].metric("Risk tolerance", f"{profile['risk_tolerance']}/10")
    cols[1].metric("Horizon", profile.get("horizon", "—"))
    cols[2].metric("Goal", profile.get("goal", "—"))
    cols[3].metric("Experience", profile.get("experience", "—"))
    cols[4].metric("Required MoS", f"{profile['required_margin_of_safety']:.0%}")


def _safe_index(options: list[str], value, default: int) -> int:
    if value in options:
        return options.index(value)
    return default
