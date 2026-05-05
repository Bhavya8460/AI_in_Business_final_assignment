"""Financials agent.

Buffett principle: "Beware of geeks bearing formulas — but understand the numbers."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, financials_prompt
from tools import llm, sec_edgar


@agent_node("financials")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    snapshot = sec_edgar.get_financials_5yr(ticker)

    metrics_5yr = snapshot["metrics_5yr"]
    current = snapshot["current_metrics"]
    growth = snapshot["growth_rates"]

    # Trim the 5yr metrics dict for the prompt to keep tokens manageable.
    trimmed_5yr = {
        "years": snapshot.get("years"),
        "revenue": metrics_5yr.get("revenue"),
        "net_income": metrics_5yr.get("net_income"),
        "fcf": metrics_5yr.get("fcf"),
        "owner_earnings": metrics_5yr.get("owner_earnings"),
        "roe": metrics_5yr.get("roe"),
        "roic": metrics_5yr.get("roic"),
        "debt_to_equity": metrics_5yr.get("debt_to_equity"),
    }

    qualitative = llm.call_json(
        JSON_SYSTEM,
        financials_prompt(
            ticker=ticker,
            metrics_5yr=trimmed_5yr,
            current_metrics=current,
            growth_rates=growth,
        ),
    )

    out = {
        "ticker": ticker,
        "years": snapshot.get("years"),
        "metrics_5yr": metrics_5yr,
        "current_metrics": current,
        "growth_rates": growth,
        **qualitative,
    }

    detail = f"Computed {len(snapshot.get('years') or [])} years of metrics"
    return {"financials": out, "_status_detail": detail}
