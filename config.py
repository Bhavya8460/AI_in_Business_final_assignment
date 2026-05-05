"""Central configuration for Quorum.

All thresholds, model parameters, mode definitions, and Buffett-checklist
items live here so the rest of the codebase imports a single source of
truth.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Disclaimer — referenced by the UI and PDF export
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "Quorum is an educational tool, not a financial advisor. All output "
    "is AI-generated analysis based on public data. Past performance does "
    "not predict future returns. Always consult a licensed financial "
    "advisor before making investment decisions. The creators are not "
    "liable for investment outcomes."
)


# ---------------------------------------------------------------------------
# LLM configuration
# ---------------------------------------------------------------------------
MODEL_NAME = "claude-sonnet-4-5-20250929"
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # low for analytical accuracy


# ---------------------------------------------------------------------------
# SEC EDGAR — required identification per SEC fair-access rules
# ---------------------------------------------------------------------------
SEC_USER_AGENT = "Quorum Educational Project student@university.edu"


# ---------------------------------------------------------------------------
# Buffett quantitative thresholds
# ---------------------------------------------------------------------------
BUFFETT_MIN_ROE = 0.15           # 15%
BUFFETT_MIN_ROIC = 0.12          # 12%
BUFFETT_MAX_DEBT_TO_EQUITY = 0.5
BUFFETT_MIN_FCF_MARGIN = 0.10    # 10%

# Required margin of safety per risk-tolerance score (1 = conservative).
BUFFETT_REQUIRED_MOS_BY_RISK: dict[int, float] = {
    1: 0.50, 2: 0.45, 3: 0.40,
    4: 0.35, 5: 0.30, 6: 0.25,
    7: 0.20, 8: 0.15, 9: 0.10,
    10: 0.05,
}


# ---------------------------------------------------------------------------
# Valuation defaults
# ---------------------------------------------------------------------------
DCF_DISCOUNT_RATE = 0.10
DCF_TERMINAL_GROWTH = 0.03
DCF_PROJECTION_YEARS = 10
DCF_MAX_GROWTH_CAP = 0.15      # cap projected FCF growth at 15%

OWNER_EARNINGS_DEFAULT_MULTIPLE = 15  # midpoint of 12-18 range
EPV_DEFAULT_COST_OF_CAPITAL = 0.10


# ---------------------------------------------------------------------------
# Tavily search defaults
# ---------------------------------------------------------------------------
TAVILY_MAX_RESULTS = 5
TAVILY_SEARCH_DEPTH = "advanced"
SEARCH_CACHE_TTL = 60 * 30  # 30 min


# ---------------------------------------------------------------------------
# Agent metadata — used by the UI for cards, tabs, and labels
# ---------------------------------------------------------------------------
AGENT_META: dict[str, dict[str, str]] = {
    "risk_profiler": {
        "label": "Risk Profiler",
        "emoji": "🧭",
        "tagline": "Capture investor profile",
        "principle": "Risk comes from not knowing what you're doing.",
    },
    "business": {
        "label": "Business",
        "emoji": "🏢",
        "tagline": "Understand the business",
        "principle": "Never invest in a business you cannot understand.",
    },
    "financials": {
        "label": "Financials",
        "emoji": "💰",
        "tagline": "Five-year financials",
        "principle": "Beware of geeks bearing formulas — but understand the numbers.",
    },
    "moat": {
        "label": "Moat",
        "emoji": "🛡️",
        "tagline": "Economic moat",
        "principle": "Find a business with a wide and long-lasting moat.",
    },
    "management": {
        "label": "Management",
        "emoji": "👔",
        "tagline": "Quality of management",
        "principle": "Hire well-managed companies.",
    },
    "valuation": {
        "label": "Valuation",
        "emoji": "🧮",
        "tagline": "Intrinsic value + MoS",
        "principle": "Price is what you pay, value is what you get.",
    },
    "sentiment": {
        "label": "Sentiment",
        "emoji": "📰",
        "tagline": "Market sentiment",
        "principle": "Be fearful when others are greedy, and greedy when others are fearful.",
    },
    "macro": {
        "label": "Macro",
        "emoji": "🌍",
        "tagline": "Industry & macro",
        "principle": "A wonderful company at a fair price beats a fair company at a wonderful price.",
    },
    "thesis": {
        "label": "Thesis",
        "emoji": "🎯",
        "tagline": "Final verdict",
        "principle": "The most important thing is the size of the moat and the price you pay.",
    },
}


# ---------------------------------------------------------------------------
# Pipeline modes
# ---------------------------------------------------------------------------
MODES: dict[str, dict] = {
    "full_buffett_brief": {
        "label": "🚀 Full Buffett Brief",
        "description": "Complete due diligence — all 8 analysis agents",
        # Note: risk_profiler is collected via UI before the graph runs.
        "agents": [
            "business",
            "financials",
            "moat",
            "management",
            "valuation",
            "sentiment",
            "macro",
            "thesis",
        ],
        "estimated_time": "~3 min",
    },
    "quick_screen": {
        "label": "⚡ Quick Screen",
        "description": "Initial filter — business + numbers + moat",
        "agents": ["business", "financials", "moat"],
        "estimated_time": "~60 sec",
    },
    "deep_value": {
        "label": "💎 Deep Value Hunt",
        "description": "Hunt for undervalued opportunities",
        "agents": ["financials", "valuation", "macro", "thesis"],
        "estimated_time": "~90 sec",
    },
    "risk_audit": {
        "label": "🛡️ Portfolio Risk Audit",
        "description": "Stress-test an existing holding",
        "agents": ["financials", "management", "macro", "thesis"],
        "estimated_time": "~75 sec",
    },
}


# ---------------------------------------------------------------------------
# Buffett checklist — scored by the Thesis Synthesizer
# ---------------------------------------------------------------------------
BUFFETT_CHECKLIST: list[dict] = [
    {"id": "understand_business",   "question": "Can I understand this business?",                       "weight": 1.0},
    {"id": "long_term_prospects",   "question": "Does the business have favorable long-term prospects?", "weight": 1.0},
    {"id": "rational_management",   "question": "Is management rational and capable?",                   "weight": 1.0},
    {"id": "candid_management",     "question": "Is management candid with shareholders?",               "weight": 1.0},
    {"id": "consistent_earnings",   "question": "Is the operating history consistent?",                  "weight": 1.0},
    {"id": "high_roe",              "question": "Is ROE consistently above 15%?",                        "weight": 1.5},
    {"id": "low_debt",              "question": "Is debt manageable (D/E < 0.5)?",                       "weight": 1.0},
    {"id": "high_margins",          "question": "Are profit margins high and stable?",                   "weight": 1.0},
    {"id": "owner_earnings_growth", "question": "Are owner earnings growing?",                           "weight": 1.5},
    {"id": "moat",                  "question": "Does it have a durable competitive moat?",              "weight": 2.0},
    {"id": "intrinsic_value",       "question": "Is it trading below intrinsic value?",                  "weight": 2.0},
    {"id": "margin_of_safety",      "question": "Margin of safety meets your risk threshold?",           "weight": 2.0},
]


# ---------------------------------------------------------------------------
# Famous tickers shown as quick-pick chips
# ---------------------------------------------------------------------------
EXAMPLE_TICKERS = ["AAPL", "MSFT", "BRK-B", "KO", "AMZN", "TSLA", "NVDA", "GOOGL"]


# ---------------------------------------------------------------------------
# Risk profile defaults
# ---------------------------------------------------------------------------
RISK_TOLERANCE_LABELS: dict[int, str] = {
    1: "I want to preserve capital. Treasury bonds only.",
    2: "Capital preservation with very mild equity exposure.",
    3: "Conservative: dividend stalwarts + some bonds.",
    4: "Mildly conservative: blue chips with steady dividends.",
    5: "Balanced: blue chips with steady dividends.",
    6: "Moderate growth tilt with quality names.",
    7: "Growth tilt — willing to ride volatility.",
    8: "Aggressive: I'll tolerate 30% drawdowns.",
    9: "Very aggressive: high-growth, expect big swings.",
    10: "Maximum growth. I can stomach 50% drawdowns.",
}

INVESTMENT_HORIZONS = ["< 1 year", "1-3 years", "3-10 years", "10+ years"]
INVESTMENT_GOALS = ["Income", "Growth", "Balanced"]
EXPERIENCE_LEVELS = ["Beginner", "Intermediate", "Advanced"]
