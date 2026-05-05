"""Earnings Power Value (Bruce Greenwald-style).

EPV assumes no growth and asks: what's the company worth if it just keeps
generating its current normalized earnings forever? It anchors the lower
bound of intrinsic value.
"""

from __future__ import annotations

from typing import Optional

from config import EPV_DEFAULT_COST_OF_CAPITAL


def epv_per_share(
    normalized_earnings: Optional[float],
    shares_outstanding: Optional[float],
    *,
    cost_of_capital: float = EPV_DEFAULT_COST_OF_CAPITAL,
) -> Optional[float]:
    """Return per-share EPV. ``normalized_earnings`` is typically owner earnings."""
    if normalized_earnings is None or shares_outstanding is None:
        return None
    if normalized_earnings <= 0 or shares_outstanding <= 0 or cost_of_capital <= 0:
        return None

    return (normalized_earnings / cost_of_capital) / shares_outstanding
