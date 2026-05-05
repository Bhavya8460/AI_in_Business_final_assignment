"""Sentiment agent.

Buffett principle: "Be fearful when others are greedy, and greedy when others are fearful."
"""

from __future__ import annotations

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, sentiment_prompt
from tools import llm, search, stock_data


@agent_node("sentiment")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]
    quote = stock_data.get_quote(ticker)
    name = quote.get("name") or ticker

    web = search.search_many(
        [
            f"{ticker} news 2025",
            f"{ticker} analyst rating upgrade downgrade",
            f"{ticker} earnings reaction",
            f"{name} reddit sentiment",
        ],
        max_results=4,
    )

    data = llm.call_json(JSON_SYSTEM, sentiment_prompt(ticker=ticker, search_context=web))

    classification = data.get("sentiment_classification") or "—"
    detail = f"Sentiment: {classification}"
    return {"sentiment": data, "_status_detail": detail}
