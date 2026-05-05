"""Risk Profiler agent — captured from the UI before the graph runs.

Buffett principle: "Risk comes from not knowing what you're doing."

Unlike the other 8 agents, this one is not registered as a LangGraph node.
It is invoked directly by the Streamlit UI; its output is stored in
``session_state['risk_profile']`` and folded into the ``AgentState`` that
seeds the graph.
"""

from __future__ import annotations

from typing import Optional

from config import BUFFETT_REQUIRED_MOS_BY_RISK


def build_risk_profile(
    risk_tolerance: int,
    horizon: str,
    goal: str,
    experience: str,
    portfolio_context: str = "",
) -> dict:
    """Validate and package the risk-profile dict."""
    rt = max(1, min(int(risk_tolerance), 10))
    required_mos = BUFFETT_REQUIRED_MOS_BY_RISK.get(rt, 0.30)

    return {
        "risk_tolerance": rt,
        "horizon": horizon,
        "goal": goal,
        "experience": experience,
        "portfolio_context": (portfolio_context or "").strip(),
        "required_margin_of_safety": required_mos,
    }


def required_mos_for(profile: Optional[dict]) -> float:
    """Helper used by other agents (esp. Thesis) to pull the MoS threshold."""
    if not profile:
        return 0.30
    rt = profile.get("risk_tolerance")
    if rt is None:
        return profile.get("required_margin_of_safety") or 0.30
    return BUFFETT_REQUIRED_MOS_BY_RISK.get(int(rt), 0.30)
