"""All LLM prompts used by Quorum agents.

Each prompt asks Claude to take on the voice of a Warren Buffett-style
analyst. We keep prompts in one file so tone-tuning is a single edit.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Shared system instructions for any JSON-emitting agent
# ---------------------------------------------------------------------------
JSON_SYSTEM = (
    "You are a Warren Buffett-style investment analyst. You write with the "
    "voice of Berkshire Hathaway annual letters: plain English, dry wit, "
    "patient, focused on durable economics rather than short-term price action. "
    "You answer ONLY with a single valid JSON object that matches the schema "
    "described in the user message. Do not wrap the JSON in markdown code "
    "fences. Do not add any text before or after the JSON. If a value is "
    "unknown, use null or 'unknown' — never invent specific numbers."
)


def _format_search(results: list[dict]) -> str:
    """Render Tavily-style results as compact context."""
    if not results:
        return "(no search results)"
    out: list[str] = []
    for i, item in enumerate(results, 1):
        out.append(
            f"[{i}] {item.get('title', '')}\n"
            f"URL: {item.get('url', '')}\n"
            f"{item.get('content', '')}\n"
        )
    return "\n".join(out)


def _truncate(text: str | None, max_chars: int = 8000) -> str:
    if not text:
        return ""
    s = str(text)
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n…(truncated)"


# ---------------------------------------------------------------------------
# Business agent
# ---------------------------------------------------------------------------
def business_prompt(
    company_name: str,
    ticker: str,
    filing_date: str,
    business_text: str,
    risk_factors_text: str,
    search_context: list[dict],
) -> str:
    return f"""BUFFETT PRINCIPLE: "Never invest in a business you cannot understand."

You have been given Item 1 (Business) and Item 1A (Risk Factors) from {ticker}'s
10-K filed on {filing_date}, plus recent web context. Evaluate whether this
business is understandable and whether it sits inside a typical investor's
circle of competence.

Apply Buffett's tests:
  1. Is this a "franchise" (needed product, no close substitutes, pricing power)
     or a commodity (price-takers, undifferentiated)?
  2. Could the average investor understand it in five minutes?
  3. Is the business model durable for 10+ years?

Return a JSON object with this exact shape:
{{
  "company_name": string,
  "ticker": string,
  "industry": string,
  "business_description": string,           // <= 200 words, plain English
  "revenue_segments": [
    {{"name": string, "pct_of_revenue": number}}
  ],
  "is_franchise": boolean,                   // franchise vs commodity
  "circle_of_competence_score": number,      // 1-10 (10 = trivially understandable)
  "key_risk_factors": [string, string, string, string, string],
  "buffett_assessment": string               // ~100 words, Buffett voice
}}

Company: {company_name} ({ticker})
10-K Filing Date: {filing_date}

— ITEM 1: BUSINESS DESCRIPTION —
{_truncate(business_text)}

— ITEM 1A: RISK FACTORS —
{_truncate(risk_factors_text)}

— RECENT WEB CONTEXT —
{_format_search(search_context)}
"""


# ---------------------------------------------------------------------------
# Financials agent
# ---------------------------------------------------------------------------
def financials_prompt(
    ticker: str,
    metrics_5yr: dict,
    current_metrics: dict,
    growth_rates: dict,
) -> str:
    return f"""BUFFETT PRINCIPLE: "Beware of geeks bearing formulas — but understand the numbers."

You have been given five years of computed financial metrics for {ticker}. Read them
the way Buffett reads a business: look for consistency, durable returns on
capital, and conservative balance sheets.

Buffett's quantitative bar:
  - ROE consistently above 15%
  - ROIC consistently above 12%
  - Debt-to-equity below 0.5
  - Owner earnings growing
  - Margins stable, not erratic

Return a JSON object with this exact shape:
{{
  "buffett_grade": string,                  // "A", "B", "C", "D", or "F"
  "financial_strength_score": number,       // 1-10
  "red_flags": [string, ...],               // up to 5
  "buffett_assessment": string              // ~150 words, Buffett voice
}}

Ticker: {ticker}

— FIVE-YEAR METRICS —
{json.dumps(metrics_5yr, indent=2, default=str)}

— CURRENT METRICS —
{json.dumps(current_metrics, indent=2, default=str)}

— GROWTH RATES (5yr CAGR) —
{json.dumps(growth_rates, indent=2, default=str)}
"""


# ---------------------------------------------------------------------------
# Moat agent
# ---------------------------------------------------------------------------
def moat_prompt(
    company_name: str,
    ticker: str,
    business_text: str,
    mdna_text: str,
    financials_summary: dict,
    search_context: list[dict],
) -> str:
    return f"""BUFFETT PRINCIPLE: "The most important thing is finding a business with a
wide and long-lasting moat."

Score the economic moat of {company_name} ({ticker}) across the five classic
moat types. Use Item 1 (Business) and Item 7 (MD&A) from the 10-K, plus the
financial metrics and recent web context.

Each moat type is scored 0-10:
  - Brand power            (premium pricing, customer loyalty)
  - Switching costs        (lock-in, integration depth, retraining cost)
  - Network effects        (value grows with users)
  - Cost advantage         (scale, location, process)
  - Intangible assets      (patents, licenses, regulatory barriers)

Return a JSON object with this exact shape:
{{
  "moat_scores": {{
    "brand": number,
    "switching_costs": number,
    "network_effects": number,
    "cost_advantage": number,
    "intangibles": number
  }},
  "composite_moat_score": number,      // weighted 0-10
  "moat_trajectory": "Widening" | "Stable" | "Eroding",
  "primary_moat_source": string,
  "evidence": [string, string, string, string, string],   // 3-5 specifics
  "buffett_assessment": string         // ~150 words, Buffett voice
}}

— ITEM 1: BUSINESS —
{_truncate(business_text, 5000)}

— ITEM 7: MD&A —
{_truncate(mdna_text, 5000)}

— FINANCIAL METRICS SUMMARY —
{json.dumps(financials_summary, indent=2, default=str)}

— RECENT WEB CONTEXT —
{_format_search(search_context)}
"""


# ---------------------------------------------------------------------------
# Management agent
# ---------------------------------------------------------------------------
def management_prompt(
    company_name: str,
    ticker: str,
    proxy_excerpt: str,
    shareholder_letter_excerpt: str,
    search_context: list[dict],
) -> str:
    return f"""BUFFETT PRINCIPLE: "Hire well-managed companies. The CEO who misleads
others in public may eventually mislead himself in private."

Evaluate management quality at {company_name} ({ticker}) using the proxy
statement, the most recent shareholder letter, and recent news.

Score each dimension 0-10:
  - Capital allocation     (reinvestment at high ROIC, smart buybacks, dividends)
  - Candor                 (do letters discuss mistakes openly?)
  - Insider ownership      (skin in the game)
  - Compensation alignment (long-term, performance-based)

Return a JSON object with this exact shape:
{{
  "ceo_name": string,
  "ceo_tenure_years": number,
  "insider_ownership_pct": number,
  "capital_allocation_score": number,
  "candor_score": number,
  "compensation_alignment_score": number,
  "overall_management_score": number,         // 0-10
  "recent_capital_decisions": [string, ...],
  "red_flags": [string, ...],
  "buffett_assessment": string                  // ~150 words, Buffett voice
}}

— PROXY (DEF 14A) EXCERPT —
{_truncate(proxy_excerpt, 5000)}

— SHAREHOLDER LETTER / MD&A EXCERPT —
{_truncate(shareholder_letter_excerpt, 5000)}

— RECENT WEB CONTEXT —
{_format_search(search_context)}
"""


# ---------------------------------------------------------------------------
# Valuation agent (qualitative wrapper around our deterministic models)
# ---------------------------------------------------------------------------
def valuation_prompt(
    ticker: str,
    quote: dict,
    valuations: dict,
    margin_of_safety_pct: float,
    intrinsic_value_range: dict,
) -> str:
    return f"""BUFFETT PRINCIPLE: "Price is what you pay, value is what you get."

You have been given the deterministic outputs of three valuation models for
{ticker}: a 10-year DCF, an Owner Earnings multiple, and an Earnings Power
Value. Reconcile them and write a Buffett-voice verdict on whether the market
is offering a margin of safety.

Buffett's rule of thumb: require at least 30% margin of safety before buying.

Return a JSON object with this exact shape:
{{
  "valuation_verdict": "Significantly Undervalued" | "Fair Value" | "Overvalued",
  "buffett_assessment": string,               // ~150 words, Buffett voice
  "key_assumptions": [string, ...]
}}

— CURRENT MARKET QUOTE —
{json.dumps(quote, indent=2, default=str)}

— MODEL OUTPUTS (per-share) —
{json.dumps(valuations, indent=2, default=str)}

— INTRINSIC VALUE RANGE (per-share) —
{json.dumps(intrinsic_value_range, indent=2, default=str)}

Margin of safety vs. mid-range estimate: {margin_of_safety_pct:.1%}
"""


# ---------------------------------------------------------------------------
# Sentiment agent
# ---------------------------------------------------------------------------
def sentiment_prompt(ticker: str, search_context: list[dict]) -> str:
    return f"""BUFFETT PRINCIPLE: "Be fearful when others are greedy, and greedy when
others are fearful."

Read the recent news flow on {ticker} and classify the market mood. We are
hunting for over-reactions in either direction — they create opportunities
for the patient investor.

Return a JSON object with this exact shape:
{{
  "recent_news": [
    {{
      "date": string,
      "headline": string,
      "source": string,
      "url": string,
      "sentiment": "positive" | "neutral" | "negative",
      "significance": "low" | "medium" | "high"
    }}
  ],
  "analyst_consensus": "Strong Buy" | "Buy" | "Hold" | "Sell" | "Strong Sell" | "Mixed",
  "sentiment_score": number,                    // -1.0 to +1.0
  "sentiment_classification": "Overly Bearish" | "Bearish" | "Neutral" | "Bullish" | "Overly Bullish",
  "key_catalysts": [string, ...],
  "buffett_assessment": string                  // ~120 words, Buffett voice
}}

Provide 5-8 news items, most recent first.

— SEARCH RESULTS —
{_format_search(search_context)}
"""


# ---------------------------------------------------------------------------
# Macro agent
# ---------------------------------------------------------------------------
def macro_prompt(
    ticker: str,
    industry_hint: str,
    search_context: list[dict],
) -> str:
    return f"""BUFFETT PRINCIPLE: "It's far better to buy a wonderful company at a fair
price than a fair company at a wonderful price."

Assess the industry context for {ticker} (industry hint: {industry_hint}).
Identify regulation, competition, and macro tailwinds/headwinds that affect
the long-term thesis.

Return a JSON object with this exact shape:
{{
  "industry_outlook": "Strong Tailwinds" | "Mild Tailwinds" | "Neutral" | "Mild Headwinds" | "Strong Headwinds",
  "industry_growth_rate": string,
  "competitive_position": "Market Leader" | "Strong Challenger" | "Niche Player" | "Laggard",
  "top_competitors": [
    {{"name": string, "threat_level": "low" | "medium" | "high"}}
  ],
  "regulatory_risks": [string, ...],
  "macro_tailwinds": [string, ...],
  "macro_headwinds": [string, ...],
  "buffett_assessment": string                  // ~150 words, Buffett voice
}}

— SEARCH RESULTS —
{_format_search(search_context)}
"""


# ---------------------------------------------------------------------------
# Thesis Synthesizer — pure synthesis, no search
# ---------------------------------------------------------------------------
def thesis_prompt(
    ticker: str,
    risk_profile: dict,
    prior_state: dict,
    checklist_template: list[dict],
    required_mos: float,
) -> str:
    return f"""BUFFETT PRINCIPLE: "The most important thing is the size of the moat
and the price you pay."

You are writing the final memo for {ticker}. Read EVERY prior agent's output
below, then deliver a verdict tailored to the user's risk profile.

User's required margin of safety (based on risk tolerance): {required_mos:.0%}

Score the verdict according to the weighted rubric:
  - Financial Strength:   25%
  - Moat:                 20%
  - Management:           15%
  - Valuation / MoS:      25%
  - Sentiment + Macro:    15%

Adjust the recommendation based on the user's risk tolerance:
  - Tolerance 1-3: Require MoS ≥40% AND low D/E AND ideally a dividend.
  - Tolerance 4-6: Require MoS ≥25% with moderate metrics.
  - Tolerance 7-10: Accept MoS ≥10%; growth + quality acceptable.

Score every Buffett checklist item PASS / FAIL / NEUTRAL with a short comment.

Return a JSON object with this exact shape:
{{
  "verdict": "STRONG BUY" | "BUY" | "HOLD" | "AVOID" | "STRONG AVOID",
  "buffett_score": number,                      // 0-100, weighted
  "risk_adjusted_verdict": string,              // 1-2 sentences explaining how risk affected the call
  "thesis_memo": string,                        // ~300 words, Buffett voice
  "top_reasons_to_buy": [string, ...],          // 3-5 bullets
  "top_reasons_to_avoid": [string, ...],        // 3-5 bullets
  "key_risks": [string, ...],
  "ideal_entry_price": number,                  // price that hits required MoS
  "position_sizing_suggestion": "Small" | "Medium" | "Large",
  "checklist_results": [
    {{"id": string, "question": string, "result": "PASS" | "FAIL" | "NEUTRAL", "comment": string}}
  ]
}}

USER RISK PROFILE:
{json.dumps(risk_profile, indent=2, default=str)}

PRIOR AGENT OUTPUTS:
{json.dumps(prior_state, indent=2, default=str)}

BUFFETT CHECKLIST (score every item):
{json.dumps(checklist_template, indent=2)}
"""
