"""Buffett-inspired specialist agents.

Each module exposes a single ``run(state)`` function. The ``risk_profiler``
is special: it doesn't run inside the LangGraph pipeline because its
input comes from the Streamlit form before the graph starts.
"""

from agents import (
    business,
    financials,
    macro,
    management,
    moat,
    sentiment,
    thesis,
    valuation,
)

# Map of node-id -> callable. Used by ``agent.py`` to register graph nodes.
AGENT_FUNCTIONS = {
    "business": business.run,
    "financials": financials.run,
    "moat": moat.run,
    "management": management.run,
    "valuation": valuation.run,
    "sentiment": sentiment.run,
    "macro": macro.run,
    "thesis": thesis.run,
}

__all__ = ["AGENT_FUNCTIONS"]
