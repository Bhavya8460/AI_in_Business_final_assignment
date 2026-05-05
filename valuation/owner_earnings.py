"""Owner Earnings × Multiple valuation.

Buffett's preferred earnings measure × an industry-appropriate multiple
gives a quick sanity-check intrinsic value.
"""

from __future__ import annotations

from typing import Optional

from config import OWNER_EARNINGS_DEFAULT_MULTIPLE


def owner_earnings_per_share(
    owner_earnings: Optional[float],
    shares_outstanding: Optional[float],
    *,
    multiple: float = OWNER_EARNINGS_DEFAULT_MULTIPLE,
) -> Optional[float]:
    """Return per-share intrinsic value via owner-earnings × multiple."""
    if owner_earnings is None or shares_outstanding is None:
        return None
    if owner_earnings <= 0 or shares_outstanding <= 0:
        return None

    return (owner_earnings * multiple) / shares_outstanding
