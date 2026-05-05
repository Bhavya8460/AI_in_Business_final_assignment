"""About / architecture page."""

from __future__ import annotations

import streamlit as st

from config import AGENT_META, MODES
from ui.components import disclaimer_banner, hero, inject_css

st.set_page_config(page_title="About — OracleIQ", page_icon="📚", layout="wide")
inject_css()

hero("📚 Architecture", "How OracleIQ uses skills + modes to power Buffett-style due diligence.")
disclaimer_banner()

# ---------------------------------------------------------------------------
# Tech stack
# ---------------------------------------------------------------------------
st.markdown("### Tech stack")
st.markdown(
    """
- 🎨 **Streamlit** — multi-page UI with live agent streaming
- 🕸️ **LangGraph** — `StateGraph` with conditional router edges
- 🤖 **Anthropic Claude** — `claude-sonnet-4-5-20250929` for analytical reasoning
- 📑 **edgartools** — direct read of 10-K, 10-Q, and DEF 14A from SEC EDGAR
- 📈 **yfinance** — live price, market cap, and ratios
- 🔎 **Tavily** — supplemental web search
- 🧮 **Plotly** — gauges, radar charts, line charts
- 📄 **ReportLab** — PDF export
"""
)

st.divider()

# ---------------------------------------------------------------------------
# Skills + Modes pattern
# ---------------------------------------------------------------------------
st.markdown("### The Skills + Modes Pattern")
st.markdown(
    """
OracleIQ borrows the **skills + modes** pattern from
[`santifer/career-ops`](https://github.com/santifer/career-ops):

- **Skills** are independent, single-job agents grounded in a Buffett principle.
- **Modes** are pre-baked pipelines that compose multiple agents.
- A shared `AgentState` lets later agents read the work of earlier agents.
- A single LangGraph router dispatches the next agent — no per-mode graph.
"""
)

st.code(
    """Risk Profiler (UI form)
        │
        ▼
   entry → router → business → router → financials → router → moat → … → thesis → END
                                ▲                                        │
                                └─── completed_nodes ◄───────────────────┘
""",
    language="text",
)

st.divider()

# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------
st.markdown("### The 9 Buffett-inspired agents")
agent_rows = [
    {
        "Agent": f"{meta['emoji']} {meta['label']}",
        "Job": meta["tagline"],
        "Buffett principle": meta["principle"],
    }
    for meta in AGENT_META.values()
]
st.dataframe(agent_rows, hide_index=True, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------
st.markdown("### The 4 pipeline modes")
mode_rows = [
    {
        "Mode": cfg["label"],
        "Agents": " → ".join(cfg["agents"]),
        "Estimated time": cfg["estimated_time"],
        "Use case": cfg["description"],
    }
    for cfg in MODES.values()
]
st.dataframe(mode_rows, hide_index=True, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------------
# Inspiration / credits
# ---------------------------------------------------------------------------
st.markdown("### Inspiration & credits")
st.markdown(
    """
- **Skills + modes architecture** —
  [`santifer/career-ops`](https://github.com/santifer/career-ops)
- **Investment philosophy** — *The Warren Buffett Way* by Robert Hagstrom,
  and Berkshire Hathaway annual letters (1977-present).

Built as a capstone for *AI in Business*, March 2026.
"""
)
