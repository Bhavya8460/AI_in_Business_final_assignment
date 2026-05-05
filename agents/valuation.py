"""Valuation agent.

Buffett principle: "Price is what you pay, value is what you get."

Combines three deterministic models — DCF, Owner Earnings × multiple, and
Earnings Power Value — into a single intrinsic-value range, then asks
Claude to write a Buffett-voice verdict.
"""

from __future__ import annotations

from typing import Optional

from agents.base import AgentState, agent_node
from prompts import JSON_SYSTEM, valuation_prompt
from tools import llm, sec_edgar, stock_data
from valuation import dcf_per_share, epv_per_share, owner_earnings_per_share


def _safe_min(values: list[Optional[float]]) -> Optional[float]:
    vs = [v for v in values if v is not None]
    return min(vs) if vs else None


def _safe_max(values: list[Optional[float]]) -> Optional[float]:
    vs = [v for v in values if v is not None]
    return max(vs) if vs else None


def _safe_avg(values: list[Optional[float]]) -> Optional[float]:
    vs = [v for v in values if v is not None]
    return sum(vs) / len(vs) if vs else None


def _margin_of_safety(intrinsic_mid: Optional[float], price: Optional[float]) -> Optional[float]:
    if intrinsic_mid is None or price is None or intrinsic_mid == 0:
        return None
    return (intrinsic_mid - price) / intrinsic_mid


@agent_node("valuation")
def run(state: AgentState) -> dict:
    ticker = state["ticker"]

    quote = stock_data.get_quote(ticker)

    # Prefer cached financials from prior agent; otherwise fetch fresh.
    financials = state.get("financials") or {}
    if not financials.get("current_metrics"):
        snapshot = sec_edgar.get_financials_5yr(ticker)
        current = snapshot.get("current_metrics") or {}
        growth = snapshot.get("growth_rates") or {}
    else:
        current = financials.get("current_metrics") or {}
        growth = financials.get("growth_rates") or {}

    base_fcf = current.get("fcf")
    owner_earnings_ttm = current.get("owner_earnings_ttm")
    fcf_growth = growth.get("fcf_cagr") or growth.get("revenue_cagr") or 0.05
    shares_from_quote = quote.get("shares_outstanding")
    shares = shares_from_quote or current.get("shares_diluted")

    dcf_val = dcf_per_share(
        base_fcf=base_fcf,
        growth_rate=fcf_growth,
        shares_outstanding=shares,
    )
    oe_val = owner_earnings_per_share(
        owner_earnings=owner_earnings_ttm,
        shares_outstanding=shares,
    )
    epv_val = epv_per_share(
        normalized_earnings=owner_earnings_ttm or current.get("net_income"),
        shares_outstanding=shares,
    )

    valuations = {
        "dcf_value": dcf_val,
        "owner_earnings_value": oe_val,
        "epv_value": epv_val,
    }
    iv_low = _safe_min([dcf_val, oe_val, epv_val])
    iv_high = _safe_max([dcf_val, oe_val, epv_val])
    iv_mid = _safe_avg([dcf_val, oe_val, epv_val])
    intrinsic_value_range = {"low": iv_low, "mid": iv_mid, "high": iv_high}

    price = quote.get("current_price")
    mos = _margin_of_safety(iv_mid, price)

    # Ratios for the dashboard
    pe = quote.get("trailing_pe")
    pfcf = None
    fcf_per_share = (base_fcf / shares) if (base_fcf and shares) else None
    if price and fcf_per_share and fcf_per_share > 0:
        pfcf = price / fcf_per_share

    qualitative = llm.call_json(
        JSON_SYSTEM,
        valuation_prompt(
            ticker=ticker,
            quote={
                "current_price": price,
                "market_cap": quote.get("market_cap"),
                "trailing_pe": pe,
                "shares_outstanding": shares,
            },
            valuations=valuations,
            margin_of_safety_pct=mos if mos is not None else 0.0,
            intrinsic_value_range=intrinsic_value_range,
        ),
    )

    out = {
        "current_price": price,
        "market_cap": quote.get("market_cap"),
        "shares_outstanding": shares,
        "valuations": valuations,
        "intrinsic_value_range": intrinsic_value_range,
        "margin_of_safety_pct": mos,
        "current_pe": pe,
        "current_pfcf": pfcf,
        "dividend_yield": quote.get("dividend_yield"),
        **qualitative,
    }

    if mos is not None:
        detail = f"Margin of safety: {mos:.0%}"
    elif price is not None:
        detail = f"Price: ${price:.2f}, intrinsic value unknown"
    else:
        detail = "Valuation complete"
    return {"valuation": out, "_status_detail": detail}
