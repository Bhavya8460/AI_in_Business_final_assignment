"""edgartools wrapper.

Hides the XBRL-tag soup behind a clean API the agents can consume.

Public surface:
  * ``get_company_overview(ticker)`` — basic company info + latest 10-K filing
  * ``get_filing_text(ticker, form='10-K')`` — Item 1 / Item 1A / Item 7 strings
  * ``get_financials_5yr(ticker)`` — five-year metrics (Revenue, NI, FCF, debt,
    equity, shares, ROE/ROIC, owner-earnings) ready for downstream agents.
  * ``get_proxy_excerpt(ticker)`` — best-effort excerpt of the most recent
    DEF 14A.

We use the ``EntityFacts`` route (``Company.income_statement(periods=N)``) as
the primary source since it normalizes XBRL tags across years, and we fuzzy
match concept rows so different reporting tags still resolve.
"""

from __future__ import annotations

import logging
import math
import os
import re
from functools import lru_cache
from typing import Any, Optional

import edgar
import pandas as pd

from config import SEC_USER_AGENT

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Identity is required by SEC fair-access rules.
# ---------------------------------------------------------------------------
_IDENTITY_SET = False


def _ensure_identity() -> None:
    global _IDENTITY_SET
    if _IDENTITY_SET:
        return
    identity = (
        os.environ.get("SEC_USER_AGENT")
        or _try_streamlit_secret("SEC_USER_AGENT")
        or SEC_USER_AGENT
    )
    edgar.set_identity(identity)
    _IDENTITY_SET = True


def _try_streamlit_secret(key: str) -> Optional[str]:
    try:
        import streamlit as st

        return st.secrets.get(key)  # type: ignore[union-attr]
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Concept-lookup helpers
# ---------------------------------------------------------------------------
# Each metric maps to a list of XBRL concept name patterns (regex). The first
# concept whose row name matches one of these patterns wins.
CONCEPT_PATTERNS: dict[str, list[str]] = {
    "revenue": [
        r"^RevenueFromContractWithCustomerExcludingAssessedTax$",
        r"^RevenueFromContractWithCustomerIncludingAssessedTax$",
        r"^Revenues$",
        r"^SalesRevenueNet$",
        r"^SalesRevenueGoodsNet$",
    ],
    "net_income": [
        r"^NetIncomeLoss$",
        r"^ProfitLoss$",
        r"^NetIncomeLossAvailableToCommonStockholdersBasic$",
    ],
    "gross_profit": [r"^GrossProfit$"],
    "eps_diluted": [r"^EarningsPerShareDiluted$"],
    "shares_diluted": [r"^WeightedAverageNumberOfDilutedSharesOutstanding$"],
    "operating_cash_flow": [
        r"^NetCashProvidedByUsedInOperatingActivities$",
        r"^CashProvidedByUsedInOperatingActivities$",
    ],
    "capex": [
        r"^PaymentsToAcquirePropertyPlantAndEquipment$",
        r"^PaymentsToAcquireProductiveAssets$",
    ],
    "depreciation_amortization": [
        r"^DepreciationDepletionAndAmortization$",
        r"^DepreciationAndAmortization$",
        r"^Depreciation$",
    ],
    "long_term_debt": [
        r"^LongTermDebtNoncurrent$",
        r"^LongTermDebt$",
    ],
    "short_term_debt": [
        r"^LongTermDebtCurrent$",
        r"^ShortTermBorrowings$",
        r"^DebtCurrent$",
        r"^CommercialPaper$",
    ],
    "stockholders_equity": [
        r"^StockholdersEquity$",
        r"^StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest$",
    ],
    "total_assets": [r"^Assets$"],
    "current_liabilities": [r"^LiabilitiesCurrent$"],
    "current_assets": [r"^AssetsCurrent$"],
    "cash": [
        r"^CashAndCashEquivalentsAtCarryingValue$",
        r"^Cash$",
    ],
}


def _pick_row(df: pd.DataFrame, patterns: list[str]) -> Optional[pd.Series]:
    """First row whose index (XBRL concept) matches any of the patterns."""
    if df is None or df.empty:
        return None
    idx = df.index.astype(str)
    for pat in patterns:
        rgx = re.compile(pat)
        for i, name in enumerate(idx):
            if rgx.match(name):
                return df.iloc[i]
    return None


def _fy_columns(df: pd.DataFrame) -> list[str]:
    """Return the FY/CY columns sorted oldest → newest."""
    cols = [c for c in df.columns if isinstance(c, str) and re.match(r"^(FY|CY)\s+\d{4}$", c)]

    def _year(c: str) -> int:
        return int(c.split()[-1])

    return sorted(cols, key=_year)


def _row_to_series(df: pd.DataFrame, metric: str) -> list[Optional[float]]:
    """Pull the metric across every fiscal-year column. Returns oldest→newest."""
    row = _pick_row(df, CONCEPT_PATTERNS.get(metric, []))
    if row is None:
        return []
    cols = _fy_columns(df)
    out: list[Optional[float]] = []
    for c in cols:
        v = row.get(c)
        if v is None or (isinstance(v, float) and math.isnan(v)):
            out.append(None)
        else:
            try:
                out.append(float(v))
            except (TypeError, ValueError):
                out.append(None)
    return out


def _years_from_columns(df: pd.DataFrame) -> list[int]:
    return [int(c.split()[-1]) for c in _fy_columns(df)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
@lru_cache(maxsize=64)
def get_company_overview(ticker: str) -> dict:
    """Return basic company info + latest 10-K metadata."""
    _ensure_identity()
    ticker = ticker.upper().strip()
    company = edgar.Company(ticker)

    overview: dict[str, Any] = {
        "ticker": ticker,
        "name": getattr(company, "name", ticker),
        "cik": getattr(company, "cik", None),
        "industry": _safe_attr(company, "sic_description") or "",
        "exchange": _safe_attr(company, "exchange") or "",
    }

    try:
        latest = company.latest(form="10-K")
        overview["latest_10k_filing_date"] = str(latest.filing_date)
        overview["latest_10k_accession"] = latest.accession_no
        overview["latest_10k_period_of_report"] = str(getattr(latest, "period_of_report", ""))
    except Exception as exc:
        logger.warning("Could not fetch latest 10-K for %s: %s", ticker, exc)
        overview["latest_10k_filing_date"] = None

    return overview


def _safe_attr(obj: Any, name: str, default: Any = None) -> Any:
    try:
        return getattr(obj, name, default)
    except Exception:
        return default


@lru_cache(maxsize=64)
def get_filing_text(ticker: str, form: str = "10-K") -> dict[str, str]:
    """Pull Item 1 (Business), Item 1A (Risk Factors), Item 7 (MD&A) text.

    Falls back to empty strings if any item is unavailable. Trimmed to a
    sensible length per item so downstream prompts stay within budget.
    """
    _ensure_identity()
    ticker = ticker.upper().strip()
    company = edgar.Company(ticker)

    out = {"business": "", "risk_factors": "", "management_discussion": "",
           "filing_date": "", "accession": ""}

    try:
        filing = company.latest(form=form)
        out["filing_date"] = str(filing.filing_date)
        out["accession"] = filing.accession_no
        tk = filing.obj()
        for key in ("business", "risk_factors", "management_discussion"):
            try:
                val = getattr(tk, key, "")
                if isinstance(val, str):
                    out[key] = val
            except Exception as exc:
                logger.warning("%s: failed to read %s: %s", ticker, key, exc)
    except Exception as exc:
        logger.warning("get_filing_text(%s, %s) failed: %s", ticker, form, exc)

    return out


@lru_cache(maxsize=32)
def get_financials_5yr(ticker: str) -> dict:
    """Return a normalized 5-year snapshot of the metrics agents need."""
    _ensure_identity()
    ticker = ticker.upper().strip()
    company = edgar.Company(ticker)

    inc_df: pd.DataFrame = pd.DataFrame()
    bal_df: pd.DataFrame = pd.DataFrame()
    cf_df: pd.DataFrame = pd.DataFrame()

    try:
        inc_df = company.income_statement(periods=5).to_dataframe()
    except Exception as exc:
        logger.warning("income_statement failed for %s: %s", ticker, exc)
    try:
        bal_df = company.balance_sheet(periods=5).to_dataframe()
    except Exception as exc:
        logger.warning("balance_sheet failed for %s: %s", ticker, exc)
    try:
        cf_df = company.cash_flow_statement(periods=5).to_dataframe()
    except Exception as exc:
        logger.warning("cash_flow_statement failed for %s: %s", ticker, exc)

    revenue = _row_to_series(inc_df, "revenue")
    net_income = _row_to_series(inc_df, "net_income")
    gross_profit = _row_to_series(inc_df, "gross_profit")
    eps_diluted = _row_to_series(inc_df, "eps_diluted")
    shares_diluted = _row_to_series(inc_df, "shares_diluted")

    op_cash_flow = _row_to_series(cf_df, "operating_cash_flow")
    capex_raw = _row_to_series(cf_df, "capex")
    # CapEx is reported as a positive cash outflow in some companies and as
    # a negative number in others. We normalize to a positive absolute value
    # so FCF = OCF − |CapEx|.
    capex = [abs(c) if c is not None else None for c in capex_raw]
    da = _row_to_series(cf_df, "depreciation_amortization")

    long_term_debt = _row_to_series(bal_df, "long_term_debt")
    short_term_debt = _row_to_series(bal_df, "short_term_debt")
    equity = _row_to_series(bal_df, "stockholders_equity")
    total_assets = _row_to_series(bal_df, "total_assets")
    current_liabilities = _row_to_series(bal_df, "current_liabilities")
    current_assets = _row_to_series(bal_df, "current_assets")

    years = _years_from_columns(inc_df) or _years_from_columns(bal_df) or _years_from_columns(cf_df)

    def _fcf_year(i: int) -> Optional[float]:
        ocf = _at(op_cash_flow, i)
        cx = _at(capex, i)
        if ocf is None or cx is None:
            return None
        return ocf - cx

    def _owner_earnings(i: int) -> Optional[float]:
        ni = _at(net_income, i)
        d_a = _at(da, i)
        cx = _at(capex, i)
        if ni is None or cx is None:
            return None
        wc_change = _wc_change(current_assets, current_liabilities, i)
        return ni + (d_a or 0) - cx - (wc_change or 0)

    def _total_debt(i: int) -> Optional[float]:
        lt = _at(long_term_debt, i) or 0
        st_ = _at(short_term_debt, i) or 0
        if lt == 0 and st_ == 0:
            return None
        return lt + st_

    def _roe(i: int) -> Optional[float]:
        ni = _at(net_income, i)
        eq = _at(equity, i)
        if ni is None or eq is None or eq == 0:
            return None
        return ni / eq

    def _roic(i: int) -> Optional[float]:
        ni = _at(net_income, i)
        eq = _at(equity, i)
        debt = _total_debt(i) or 0
        invested = (eq or 0) + debt
        if ni is None or invested == 0:
            return None
        return ni / invested

    def _de(i: int) -> Optional[float]:
        debt = _total_debt(i)
        eq = _at(equity, i)
        if debt is None or eq is None or eq == 0:
            return None
        return debt / eq

    fcf = [_fcf_year(i) for i in range(len(years))]
    owner_earnings = [_owner_earnings(i) for i in range(len(years))]
    roe = [_roe(i) for i in range(len(years))]
    roic = [_roic(i) for i in range(len(years))]
    debt_to_equity = [_de(i) for i in range(len(years))]
    total_debt = [_total_debt(i) for i in range(len(years))]

    growth = {
        "revenue_cagr": _cagr(revenue),
        "eps_cagr": _cagr(eps_diluted),
        "fcf_cagr": _cagr(fcf),
        "owner_earnings_cagr": _cagr(owner_earnings),
        "net_income_cagr": _cagr(net_income),
    }

    last = lambda series: next((v for v in reversed(series) if v is not None), None)
    current = {
        "revenue": last(revenue),
        "net_income": last(net_income),
        "fcf": last(fcf),
        "owner_earnings_ttm": last(owner_earnings),
        "roe": last(roe),
        "roic": last(roic),
        "debt_to_equity": last(debt_to_equity),
        "fcf_margin": _safe_div(last(fcf), last(revenue)),
        "gross_margin": _safe_div(last(gross_profit), last(revenue)),
        "eps_diluted": last(eps_diluted),
        "shares_diluted": last(shares_diluted),
        "equity": last(equity),
        "total_debt": last(total_debt),
    }

    return {
        "ticker": ticker,
        "years": years,
        "metrics_5yr": {
            "revenue": revenue,
            "net_income": net_income,
            "gross_profit": gross_profit,
            "operating_cash_flow": op_cash_flow,
            "capex": capex,
            "fcf": fcf,
            "owner_earnings": owner_earnings,
            "depreciation_amortization": da,
            "eps_diluted": eps_diluted,
            "shares_diluted": shares_diluted,
            "long_term_debt": long_term_debt,
            "short_term_debt": short_term_debt,
            "total_debt": total_debt,
            "stockholders_equity": equity,
            "total_assets": total_assets,
            "current_assets": current_assets,
            "current_liabilities": current_liabilities,
            "roe": roe,
            "roic": roic,
            "debt_to_equity": debt_to_equity,
        },
        "current_metrics": current,
        "growth_rates": growth,
    }


# ---------------------------------------------------------------------------
# Proxy / shareholder letter
# ---------------------------------------------------------------------------
@lru_cache(maxsize=32)
def get_proxy_excerpt(ticker: str, max_chars: int = 8000) -> dict[str, str]:
    """Pull a best-effort excerpt of the most recent DEF 14A proxy filing.

    Returns ``{"text": ..., "filing_date": ..., "accession": ...}``. Empty
    strings on failure.
    """
    _ensure_identity()
    ticker = ticker.upper().strip()
    company = edgar.Company(ticker)
    out = {"text": "", "filing_date": "", "accession": ""}

    try:
        latest = company.latest(form="DEF 14A")
        out["filing_date"] = str(latest.filing_date)
        out["accession"] = latest.accession_no
        text = ""
        try:
            text = getattr(latest, "text", "") or ""
        except Exception:
            pass
        if not text:
            try:
                text = getattr(latest, "markdown", "") or ""
            except Exception:
                pass
        out["text"] = text[:max_chars] if text else ""
    except Exception as exc:
        logger.warning("get_proxy_excerpt(%s) failed: %s", ticker, exc)

    return out


# ---------------------------------------------------------------------------
# Tiny helpers
# ---------------------------------------------------------------------------
def _at(series: list, i: int):
    if 0 <= i < len(series):
        return series[i]
    return None


def _safe_div(a, b) -> Optional[float]:
    if a is None or b is None or b == 0:
        return None
    try:
        return a / b
    except (TypeError, ZeroDivisionError):
        return None


def _wc_change(
    current_assets: list[Optional[float]],
    current_liabilities: list[Optional[float]],
    i: int,
) -> Optional[float]:
    if i == 0:
        return None
    ca_now, cl_now = _at(current_assets, i), _at(current_liabilities, i)
    ca_prev, cl_prev = _at(current_assets, i - 1), _at(current_liabilities, i - 1)
    if None in (ca_now, cl_now, ca_prev, cl_prev):
        return None
    return (ca_now - cl_now) - (ca_prev - cl_prev)


def _cagr(series: list[Optional[float]]) -> Optional[float]:
    """Compound annual growth rate from oldest to newest non-null value."""
    vals = [v for v in series if v is not None]
    if len(vals) < 2:
        return None
    start, end = vals[0], vals[-1]
    if start is None or end is None or start <= 0 or end <= 0:
        return None
    n = len(vals) - 1
    try:
        return (end / start) ** (1 / n) - 1
    except (ZeroDivisionError, ValueError):
        return None
