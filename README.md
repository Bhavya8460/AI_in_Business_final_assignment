# 🎯 Quorum — Buffett-Inspired Investment Due Diligence

> **9 specialized AI agents. Real SEC filings. Verdicts tailored to you.**

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://github.com/langchain-ai/langgraph)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-orange.svg)](https://www.anthropic.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)](https://streamlit.io/)
[![SEC EDGAR](https://img.shields.io/badge/data-SEC%20EDGAR-darkgreen.svg)](https://www.sec.gov/edgar)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](#license)

---

## ⚠️ Disclaimer

**Quorum is an educational tool, not a financial advisor.** All output is
AI-generated analysis based on public data. Past performance does not predict
future returns. Always consult a licensed financial advisor before making
investment decisions. The creators are not liable for investment outcomes.

---

## The Problem

Retail investors lose roughly **$200B per year** on bad picks driven by
hype, FOMO, and a Twitter feed full of dubious "due diligence." Real
due diligence — reading 10-Ks, computing return on invested capital,
modeling intrinsic value, separating temporary noise from permanent
moats — takes a senior analyst a full day per name.

## The Solution

**Quorum** turns that day into three minutes by orchestrating nine
specialized AI agents, each grounded in a single Warren Buffett
principle. The system reads the actual SEC filings, runs three
independent valuation models, and delivers a verdict that's *tailored
to the user's risk tolerance*.

The agents are independent skills that can be invoked one at a time
(Skill Lab) or chained into one of four pre-built modes — the same
**skills + modes** pattern used in
[`santifer/career-ops`](https://github.com/santifer/career-ops).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Streamlit UI (4 pages)                           │
│   Run Analysis  ·  Skill Lab  ·  Buffett's Wisdom  ·  About          │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
            ┌──────────────▼──────────────┐
            │   Risk Profiler (UI form)    │   captured *before* the graph
            └──────────────┬──────────────┘
                           │ risk_profile → seeded into AgentState
            ┌──────────────▼──────────────┐
            │      LangGraph (StateGraph)  │
            │                              │
            │   entry → router ──────┐     │
            │     ▲                  ▼     │
            │     │   ┌─ business ──┐      │
            │     │   ├─ financials ┤      │
            │     │   ├─ moat       │      │ ← every node returns
            │     │   ├─ management │      │   to the same router
            │     └───┤ valuation   │      │
            │         ├─ sentiment  │      │
            │         ├─ macro      │      │
            │         └─ thesis ────┘      │ ← synthesis-only
            │                              │
            └──────────────┬───────────────┘
                           │ shared AgentState
            ┌──────────────▼───────────────┐
            │   Tools                       │
            │   • SEC EDGAR  (edgartools)   │
            │   • Yahoo Finance (yfinance)  │
            │   • Tavily web search         │
            │   • Anthropic Claude          │
            └───────────────────────────────┘
```

**Why a router?** A single conditional edge after every node lets the
same compiled graph serve every mode — Quick Screen completes after 3
agents, Full Buffett Brief walks all 8. No per-mode graph re-compilation.

**Risk Profiler is special.** It runs in the Streamlit form *before*
the graph, captures the user's risk tolerance, horizon, goal, and
experience, then seeds the result into `AgentState.risk_profile`. The
Thesis Synthesizer reads it from shared state and tailors the verdict
accordingly.

---

## The 9 Agents

| Agent | Job | Buffett principle |
|---|---|---|
| 🧭 **Risk Profiler** | Capture investor profile (UI form) | *"Risk comes from not knowing what you're doing."* |
| 🏢 **Business**      | Read 10-K Item 1 + Item 1A; classify franchise vs commodity | *"Never invest in a business you cannot understand."* |
| 💰 **Financials**    | Compute 5-yr ROE/ROIC/D-E/FCF/Owner Earnings | *"Beware of geeks bearing formulas — but understand the numbers."* |
| 🛡️ **Moat**          | Score the 5 moat types (brand / switching / network / cost / intangible) | *"Find a business with a wide and long-lasting moat."* |
| 👔 **Management**    | Read DEF 14A; score capital allocation, candor, compensation | *"Hire well-managed companies."* |
| 🧮 **Valuation**     | Run DCF + Owner Earnings × Multiple + EPV; compute MoS | *"Price is what you pay, value is what you get."* |
| 📰 **Sentiment**     | Surface news + analyst consensus; flag over-reactions | *"Be fearful when others are greedy, and greedy when others are fearful."* |
| 🌍 **Macro**         | Industry outlook, competitors, regulation | *"A wonderful company at a fair price beats a fair company at a wonderful price."* |
| 🎯 **Thesis**        | Weighted-score synthesis + Buffett checklist + risk-adjusted verdict | *"The most important thing is the size of the moat and the price you pay."* |

The Thesis Synthesizer is **synthesis-only** — no web searches, no SEC reads.
It reads every prior agent's output from shared state and produces a
final memo + a 12-item Buffett checklist with PASS/FAIL/NEUTRAL per item.

---

## The 4 Modes

| Mode | Pipeline | ETA |
|---|---|---|
| 🚀 **Full Buffett Brief** | business → financials → moat → management → valuation → sentiment → macro → thesis | ~3 min |
| ⚡ **Quick Screen**       | business → financials → moat | ~60 sec |
| 💎 **Deep Value Hunt**    | financials → valuation → macro → thesis | ~90 sec |
| 🛡️ **Portfolio Risk Audit** | financials → management → macro → thesis | ~75 sec |

---

## Quick Start

```bash
git clone <your-fork> quorum && cd quorum
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill in API keys
streamlit run app.py
```

Visit <http://localhost:8501>.

### API keys

Three values go in `.env` (or `.streamlit/secrets.toml` for Streamlit Cloud):

```bash
ANTHROPIC_API_KEY=sk-ant-...                # https://console.anthropic.com/
TAVILY_API_KEY=tvly-...                     # https://tavily.com  (free tier OK)
SEC_USER_AGENT=Quorum Project you@domain.com  # SEC requires identification
```

`edgartools` and `yfinance` need no keys.

---

## Deployment — Streamlit Community Cloud

1. Push the repo to GitHub.
2. Go to <https://share.streamlit.io>, click **New app**.
3. Pick branch `main`, file `app.py`.
4. **Advanced settings → Secrets**, paste:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   TAVILY_API_KEY    = "tvly-..."
   SEC_USER_AGENT    = "Quorum Project you@example.com"
   ```
5. **Deploy**. ~3 minutes later you have a public URL.

---

## Project layout

```
quorum/
├── app.py                          # main page (Run Analysis)
├── agent.py                        # LangGraph graph + router
├── config.py                       # MODES, BUFFETT_CHECKLIST, thresholds
├── prompts.py                      # all Buffett-voice LLM prompts
├── agents/
│   ├── base.py                     # AgentState + agent_node decorator
│   ├── risk_profiler.py            # UI-driven (not in LangGraph)
│   ├── business.py
│   ├── financials.py
│   ├── moat.py
│   ├── management.py
│   ├── valuation.py
│   ├── sentiment.py
│   ├── macro.py
│   └── thesis.py                   # synthesis-only
├── tools/
│   ├── sec_edgar.py                # edgartools wrapper (10-K, DEF 14A, financials)
│   ├── stock_data.py               # yfinance wrapper
│   ├── search.py                   # Tavily wrapper
│   └── llm.py                      # Claude wrapper + retry + JSON parse
├── valuation/
│   ├── dcf.py                      # 10-yr DCF + perpetuity terminal
│   ├── owner_earnings.py           # owner earnings × multiple
│   └── epv.py                      # earnings power value
├── ui/
│   ├── components.py               # cards, gauges, banners, badges, CSS
│   ├── progress.py                 # live agent progress
│   ├── dashboard.py                # results renderer (per-tab functions)
│   └── risk_form.py                # risk profiler form
├── utils/
│   ├── pdf_export.py               # ReportLab Buffett brief
│   ├── formatting.py               # money/pct formatters, color helpers
│   └── caching.py
├── pages/
│   ├── 1_🧪_Skill_Lab.py
│   ├── 2_📜_Buffett_Wisdom.py
│   └── 3_📚_About.py
└── .streamlit/
    ├── config.toml                 # green "Berkshire" theme, serif font
    └── secrets.toml.example
```

---

## Tech stack

- 🎨 **Streamlit** — multi-page UI with live agent streaming
- 🕸️ **LangGraph** — `StateGraph` with conditional router edges
- 🤖 **Anthropic Claude** — `claude-sonnet-4-5-20250929`
- 📑 **edgartools** — direct read of 10-K, 10-Q, DEF 14A from SEC EDGAR
- 📈 **yfinance** — live price, market cap, ratios
- 🔎 **Tavily** — supplemental web search
- 🧮 **Plotly** — gauges, radar charts, line + bar charts
- 📄 **ReportLab** — PDF export

---

## Inspiration

- **Skills + modes architecture** —
  [`santifer/career-ops`](https://github.com/santifer/career-ops)
- **Investment philosophy** — *The Warren Buffett Way* by Robert Hagstrom
  and the Berkshire Hathaway annual letters (1977-present).

---

## ⚠️ One more time

**Quorum is an educational tool, not a financial advisor.** All output is
AI-generated analysis based on public data. Past performance does not predict
future returns. Always consult a licensed financial advisor before making
investment decisions. The creators are not liable for investment outcomes.

---

## License

MIT
