"""Macro & Industry agent.

Buffett principle: "It's far better to buy a wonderful company at a fair
price than a fair company at a wonderful price."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, macro_prompt
from tools import llm, search, stock_data


@agent_node("macro")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    quote = stock_data.get_quote(ticker)
    industry = quote.get("industry") or quote.get("sector") or ""

    business = state.get("business") or {}
    if not industry:
        industry = business.get("industry") or "the company's industry"

    web = search.search_many(
        [
            f"{industry} outlook 2025 2026",
            f"{industry} regulation",
            f"{ticker} competitors market share",
        ],
        max_results=4,
    )

    data = llm.call_json(
        JSON_SYSTEM,
        macro_prompt(ticker=ticker, industry_hint=industry, search_context=web),
    )

    outlook = data.get("industry_outlook") or "—"
    detail = f"Industry outlook: {outlook}"
    return {"macro": data, "_status_detail": detail}
