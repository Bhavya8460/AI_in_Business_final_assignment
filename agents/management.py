"""Management agent.

Buffett principle: "Hire well-managed companies."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, management_prompt
from tools import llm, search, sec_edgar


@agent_node("management")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    overview = sec_edgar.get_company_overview(ticker)
    company_name = overview.get("name") or ticker

    proxy = sec_edgar.get_proxy_excerpt(ticker)
    filing_text = sec_edgar.get_filing_text(ticker, form="10-K")
    mdna = filing_text.get("management_discussion") or ""

    web = search.search_many(
        [
            f"{company_name} CEO compensation 2025",
            f"{ticker} insider trading",
            f"{company_name} shareholder letter",
        ],
        max_results=4,
    )

    data = llm.call_json(
        JSON_SYSTEM,
        management_prompt(
            company_name=company_name,
            ticker=ticker,
            proxy_excerpt=proxy.get("text") or "",
            shareholder_letter_excerpt=mdna,
            search_context=web,
        ),
    )

    score = data.get("overall_management_score")
    detail = f"Management score {score}/10" if score is not None else "Management analysis complete"

    filings_used = []
    if proxy.get("filing_date"):
        filings_used.append(
            {
                "form": "DEF 14A",
                "filing_date": proxy.get("filing_date"),
                "accession": proxy.get("accession"),
                "agent": "management",
            }
        )

    update: dict = {"management": data, "_status_detail": detail}
    if filings_used:
        update["_filings_used"] = filings_used
    return update
