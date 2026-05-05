"""Thesis Synthesizer agent.

Buffett principle: "The most important thing is the size of the moat
and the price you pay."

Pure synthesis — no web searches, no SEC reads. Reads every prior agent's
output from the shared state and produces the final verdict, tailored to
the user's risk profile.
"""

from __future__ import annotations

from typing import Optional

from agents.base import AgentState, agent_node
from agents.risk_profiler import required_mos_for
from config import BUFFETT_CHECKLIST
from prompts import JSON_SYSTEM, thesis_prompt
from tools import llm


def _ideal_entry_price(intrinsic_mid: Optional[float], required_mos: float) -> Optional[float]:
    """Solve for the price that would deliver the user's required MoS."""
    if intrinsic_mid is None or intrinsic_mid <= 0:
        return None
    return intrinsic_mid * (1 - required_mos)


@agent_node("thesis")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    risk_profile = state.get("risk_profile") or {}
    required_mos = required_mos_for(risk_profile)

    # Trim each prior agent's payload — Thesis only needs the highlights.
    prior = _summarize_prior_state(state)

    data = llm.call_json(
        JSON_SYSTEM,
        thesis_prompt(
            ticker=ticker,
            risk_profile=risk_profile,
            prior_state=prior,
            checklist_template=BUFFETT_CHECKLIST,
            required_mos=required_mos,
        ),
    )

    # If Claude didn't compute an ideal-entry, do it ourselves from valuation.
    valuation = state.get("valuation") or {}
    iv_mid = (valuation.get("intrinsic_value_range") or {}).get("mid")
    if not data.get("ideal_entry_price") and iv_mid:
        data["ideal_entry_price"] = _ideal_entry_price(iv_mid, required_mos)

    verdict = data.get("verdict", "—")
    score = data.get("buffett_score")
    detail = f"{verdict} · Buffett score {score}/100" if score is not None else verdict
    return {"thesis": data, "_status_detail": detail}


def _summarize_prior_state(state: AgentState) -> dict:
    """Strip oversized payloads (e.g. full 5-yr metric arrays) for the prompt."""
    business = state.get("business") or {}
    financials = state.get("financials") or {}
    moat = state.get("moat") or {}
    management = state.get("management") or {}
    valuation = state.get("valuation") or {}
    sentiment = state.get("sentiment") or {}
    macro = state.get("macro") or {}

    fin_summary = {
        "buffett_grade": financials.get("buffett_grade"),
        "financial_strength_score": financials.get("financial_strength_score"),
        "current_metrics": financials.get("current_metrics"),
        "growth_rates": financials.get("growth_rates"),
        "red_flags": financials.get("red_flags"),
        "buffett_assessment": financials.get("buffett_assessment"),
    }

    val_summary = {
        "current_price": valuation.get("current_price"),
        "valuations": valuation.get("valuations"),
        "intrinsic_value_range": valuation.get("intrinsic_value_range"),
        "margin_of_safety_pct": valuation.get("margin_of_safety_pct"),
        "valuation_verdict": valuation.get("valuation_verdict"),
        "current_pe": valuation.get("current_pe"),
        "buffett_assessment": valuation.get("buffett_assessment"),
    }

    sentiment_summary = {
        "sentiment_classification": sentiment.get("sentiment_classification"),
        "analyst_consensus": sentiment.get("analyst_consensus"),
        "key_catalysts": sentiment.get("key_catalysts"),
        "buffett_assessment": sentiment.get("buffett_assessment"),
    }

    return {
        "business": business,
        "financials": fin_summary,
        "moat": moat,
        "management": management,
        "valuation": val_summary,
        "sentiment": sentiment_summary,
        "macro": macro,
    }
