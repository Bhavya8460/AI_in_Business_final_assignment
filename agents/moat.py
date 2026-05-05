"""Moat agent.

Buffett principle: "Find a business with a wide and long-lasting moat."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, moat_prompt
from tools import llm, search, sec_edgar


@agent_node("moat")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    overview = sec_edgar.get_company_overview(ticker)
    company_name = overview.get("name") or ticker
    filing_text = sec_edgar.get_filing_text(ticker, form="10-K")

    # Use prior financials if available — the LLM benefits from concrete metrics.
    financials = state.get("financials") or {}
    fin_summary = {
        "current_metrics": financials.get("current_metrics") or {},
        "growth_rates": financials.get("growth_rates") or {},
        "buffett_grade": financials.get("buffett_grade"),
    }

    web = search.search_many(
        [
            f"{ticker} competitive advantage moat",
            f"{company_name} pricing power switching costs",
        ],
        max_results=4,
    )

    data = llm.call_json(
        JSON_SYSTEM,
        moat_prompt(
            company_name=company_name,
            ticker=ticker,
            business_text=filing_text.get("business") or "",
            mdna_text=filing_text.get("management_discussion") or "",
            financials_summary=fin_summary,
            search_context=web,
        ),
    )

    composite = data.get("composite_moat_score")
    detail = f"Moat score {composite}/10" if composite is not None else "Moat analysis complete"
    return {"moat": data, "_status_detail": detail}
