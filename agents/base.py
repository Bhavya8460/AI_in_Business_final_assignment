"""Shared agent scaffolding for OracleIQ.

Defines:
  * ``AgentState`` — the TypedDict that flows through LangGraph.
  * ``agent_node`` — decorator that wraps each agent's ``run`` with status
    messaging, error capture, and ``completed_nodes`` bookkeeping.
"""

from __future__ import annotations

import logging
import time
from functools import wraps
from operator import add
from typing import Annotated, Any, Callable, Optional, TypedDict

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Shared state
# ---------------------------------------------------------------------------
class AgentState(TypedDict, total=False):
    """The single state object passed through the LangGraph."""

    # Input ----------------------------------------------------------------
    ticker: str
    mode: str
    nodes_to_run: list[str]

    # Captured from the UI before the pipeline runs ------------------------
    risk_profile: Optional[dict]

    # Per-agent outputs ----------------------------------------------------
    business: Optional[dict]
    financials: Optional[dict]
    moat: Optional[dict]
    management: Optional[dict]
    valuation: Optional[dict]
    sentiment: Optional[dict]
    macro: Optional[dict]
    thesis: Optional[dict]

    # Meta -----------------------------------------------------------------
    started_at: Optional[float]
    finished_at: Optional[float]
    messages: Annotated[list, add]
    errors: Annotated[list, add]
    completed_nodes: Annotated[list, add]
    sec_filings_used: Annotated[list, add]


# ---------------------------------------------------------------------------
# Streaming-friendly status messages
# ---------------------------------------------------------------------------
def status_message(node: str, status: str, detail: str = "") -> dict:
    return {"node": node, "status": status, "detail": detail, "ts": time.time()}


# ---------------------------------------------------------------------------
# agent_node decorator
# ---------------------------------------------------------------------------
AgentRunner = Callable[[AgentState], dict[str, Any]]


def agent_node(node_id: str) -> Callable[[AgentRunner], AgentRunner]:
    """Wrap an agent's ``run`` with cross-cutting plumbing."""

    def decorator(fn: AgentRunner) -> AgentRunner:
        @wraps(fn)
        def wrapper(state: AgentState) -> dict[str, Any]:
            ticker = state.get("ticker", "?")
            logger.info("agent[%s] start ticker=%s", node_id, ticker)
            start_msg = status_message(node_id, "running", f"Analyzing {ticker}…")
            try:
                result = fn(state) or {}
                detail = result.pop("_status_detail", "Done")
                done_msg = status_message(node_id, "complete", detail)
                update = {
                    **result,
                    "messages": [start_msg, done_msg],
                    "completed_nodes": [node_id],
                }
                # Auto-track filings used.
                filings = result.pop("_filings_used", None)
                if filings:
                    update["sec_filings_used"] = filings if isinstance(filings, list) else [filings]
                logger.info("agent[%s] complete", node_id)
                return update
            except Exception as exc:  # noqa: BLE001 — never crash the graph
                logger.exception("agent[%s] failed: %s", node_id, exc)
                fail_msg = status_message(node_id, "failed", str(exc))
                return {
                    node_id: {"error": str(exc), "agent": node_id},
                    "messages": [start_msg, fail_msg],
                    "errors": [{"node": node_id, "error": str(exc)}],
                    "completed_nodes": [node_id],
                }

        return wrapper

    return decorator
