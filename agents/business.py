"""Business agent.

Buffett principle: "Never invest in a business you cannot understand."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, business_prompt
from tools import llm, search, sec_edgar


@agent_node("business")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    overview = sec_edgar.get_company_overview(ticker)
    company_name = overview.get("name") or ticker
    filing_text = sec_edgar.get_filing_text(ticker, form="10-K")

    web = search.search_many(
        [
            f"{ticker} business model 2025",
            f"{company_name} revenue segments",
        ],
        max_results=4,
    )

    data = llm.call_json(
        JSON_SYSTEM,
        business_prompt(
            company_name=company_name,
            ticker=ticker,
            filing_date=filing_text.get("filing_date") or overview.get("latest_10k_filing_date") or "—",
            business_text=filing_text.get("business") or "",
            risk_factors_text=filing_text.get("risk_factors") or "",
            search_context=web,
        ),
    )

    # Make sure we always know the canonical name/ticker even if the model omits.
    data.setdefault("company_name", company_name)
    data.setdefault("ticker", ticker)
    if not data.get("industry"):
        data["industry"] = overview.get("industry") or ""

    detail = (
        f"Read 10-K filed {filing_text.get('filing_date') or overview.get('latest_10k_filing_date') or '?'}"
    )
    return {
        "business": data,
        "_status_detail": detail,
        "_filings_used": [
            {
                "form": "10-K",
                "filing_date": filing_text.get("filing_date"),
                "accession": filing_text.get("accession"),
                "agent": "business",
            }
        ],
    }
