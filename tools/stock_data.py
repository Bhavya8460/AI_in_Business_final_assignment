"""yfinance wrapper for current price, market cap, and other live quotes.

Wrapped behind a thin API so agents stay readable. We swallow yfinance
errors and return ``{}`` so callers can degrade gracefully.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Optional

import yfinance as yf

logger = logging.getLogger(__name__)


@lru_cache(maxsize=64)
def get_quote(ticker: str) -> dict[str, Any]:
    """Return the live quote, market cap, ratios, and a short business summary."""
    ticker = ticker.upper().strip()
    try:
        info = yf.Ticker(ticker).info or {}
    except Exception as exc:
        logger.warning("yfinance Ticker(%s).info failed: %s", ticker, exc)
        return {"ticker": ticker, "error": str(exc)}

    if not info:
        return {"ticker": ticker, "error": "no quote returned"}

    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "current_price": _coerce_float(info.get("currentPrice") or info.get("regularMarketPrice")),
        "market_cap": _coerce_float(info.get("marketCap")),
        "shares_outstanding": _coerce_float(info.get("sharesOutstanding")),
        "trailing_pe": _coerce_float(info.get("trailingPE")),
        "forward_pe": _coerce_float(info.get("forwardPE")),
        "price_to_book": _coerce_float(info.get("priceToBook")),
        "price_to_sales": _coerce_float(info.get("priceToSalesTrailing12Months")),
        "ev_to_ebitda": _coerce_float(info.get("enterpriseToEbitda")),
        "dividend_yield": _coerce_float(info.get("dividendYield")),
        "beta": _coerce_float(info.get("beta")),
        "fifty_two_week_high": _coerce_float(info.get("fiftyTwoWeekHigh")),
        "fifty_two_week_low": _coerce_float(info.get("fiftyTwoWeekLow")),
        "industry": info.get("industry") or "",
        "sector": info.get("sector") or "",
        "currency": info.get("currency") or "USD",
        "country": info.get("country") or "",
        "website": info.get("website") or "",
        "long_business_summary": info.get("longBusinessSummary") or "",
        "full_time_employees": _coerce_float(info.get("fullTimeEmployees")),
        "average_analyst_rating": info.get("averageAnalystRating") or "",
        "recommendation_key": info.get("recommendationKey") or "",
    }


@lru_cache(maxsize=64)
def get_price_history_summary(ticker: str, period: str = "1y") -> dict[str, float]:
    """Compact summary of price history for sentiment context."""
    ticker = ticker.upper().strip()
    try:
        hist = yf.Ticker(ticker).history(period=period)
    except Exception as exc:
        logger.warning("yfinance history(%s) failed: %s", ticker, exc)
        return {}
    if hist is None or hist.empty:
        return {}

    close = hist["Close"]
    return {
        "start_price": float(close.iloc[0]),
        "end_price": float(close.iloc[-1]),
        "high": float(close.max()),
        "low": float(close.min()),
        "return_pct": float((close.iloc[-1] / close.iloc[0]) - 1.0),
    }


def _coerce_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN
        return None
    return f
