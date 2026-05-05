"""LangGraph wiring for OracleIQ.

Same router pattern that makes the skills+modes architecture work:

  entry → router → [business|financials|moat|...|thesis] ─┐
                ▲                                          │
                └──────────────────────────────────────────┘

Risk Profiler is *not* a graph node — it runs in the Streamlit UI before
this graph is invoked. Its output is folded into ``initial_state`` so the
Thesis Synthesizer can read it from shared state.
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

from langgraph.graph import END, StateGraph

from agents import AGENT_FUNCTIONS
from agents.base import AgentState
from config import MODES


# ---------------------------------------------------------------------------
# Router — picks the next uncompleted node from ``nodes_to_run``
# ---------------------------------------------------------------------------
def router(state: AgentState) -> str:
    completed = set(state.get("completed_nodes") or [])
    for node in state.get("nodes_to_run") or []:
        if node not in completed:
            return node
    return END


def entry_node(state: AgentState) -> dict:
    """Stamp the start time and pass through."""
    return {"started_at": time.time()}


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("entry", entry_node)
    for name, fn in AGENT_FUNCTIONS.items():
        graph.add_node(name, fn)

    graph.set_entry_point("entry")

    edge_map = {name: name for name in AGENT_FUNCTIONS}
    edge_map[END] = END

    graph.add_conditional_edges("entry", router, edge_map)
    for name in AGENT_FUNCTIONS:
        graph.add_conditional_edges(name, router, edge_map)

    return graph.compile()


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------
_APP = None


def get_app():
    global _APP
    if _APP is None:
        _APP = build_graph()
    return _APP


def initial_state(
    ticker: str,
    mode: str,
    risk_profile: Optional[dict] = None,
) -> AgentState:
    """Build the starting state for a run."""
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    return {
        "ticker": ticker.upper().strip(),
        "mode": mode,
        "nodes_to_run": list(MODES[mode]["agents"]),
        "risk_profile": risk_profile or {},
        "messages": [],
        "errors": [],
        "completed_nodes": [],
        "sec_filings_used": [],
    }


def stream_run(
    ticker: str,
    mode: str,
    risk_profile: Optional[dict] = None,
) -> Iterator[tuple[str, dict]]:
    """Stream ``(node_name, node_output)`` tuples as the graph executes."""
    app = get_app()
    state = initial_state(ticker, mode, risk_profile)
    for event in app.stream(state, stream_mode="updates"):
        for node_name, node_output in event.items():
            yield node_name, node_output


def run_single_agent(
    ticker: str,
    agent_name: str,
    risk_profile: Optional[dict] = None,
) -> dict:
    """Run one agent in isolation (Skill Lab page)."""
    if agent_name not in AGENT_FUNCTIONS:
        raise ValueError(f"Unknown agent: {agent_name}")
    state: AgentState = {
        "ticker": ticker.upper().strip(),
        "mode": "single",
        "nodes_to_run": [agent_name],
        "risk_profile": risk_profile or {},
        "messages": [],
        "errors": [],
        "completed_nodes": [],
        "sec_filings_used": [],
    }
    return AGENT_FUNCTIONS[agent_name](state)


def run_full(ticker: str, mode: str, risk_profile: Optional[dict] = None) -> AgentState:
    """Synchronous helper — run the full pipeline and return final state."""
    return get_app().invoke(initial_state(ticker, mode, risk_profile))
