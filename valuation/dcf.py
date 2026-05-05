"""Discounted Cash Flow model.

Projects FCF for ``DCF_PROJECTION_YEARS`` using a capped growth rate, applies
a perpetuity terminal value, discounts everything to present value at
``DCF_DISCOUNT_RATE``, and returns per-share intrinsic value.
"""

from __future__ import annotations

from typing import Optional

from config import (
    DCF_DISCOUNT_RATE,
    DCF_MAX_GROWTH_CAP,
    DCF_PROJECTION_YEARS,
    DCF_TERMINAL_GROWTH,
)


def dcf_per_share(
    base_fcf: Optional[float],
    growth_rate: Optional[float],
    shares_outstanding: Optional[float],
    *,
    discount_rate: float = DCF_DISCOUNT_RATE,
    terminal_growth: float = DCF_TERMINAL_GROWTH,
    years: int = DCF_PROJECTION_YEARS,
    max_growth: float = DCF_MAX_GROWTH_CAP,
) -> Optional[float]:
    """Return per-share intrinsic value, or None if inputs are missing/invalid."""
    if base_fcf is None or shares_outstanding is None:
        return None
    if base_fcf <= 0 or shares_outstanding <= 0:
        return None

    g = growth_rate if growth_rate is not None else 0.05
    g = max(min(g, max_growth), -0.05)  # clamp [-5%, +max]

    if discount_rate <= terminal_growth:
        return None

    # Project explicit-period FCF + discount
    pv_explicit = 0.0
    fcf = base_fcf
    for year in range(1, years + 1):
        fcf = fcf * (1 + g)
        pv_explicit += fcf / ((1 + discount_rate) ** year)

    # Terminal value at end of year `years`
    terminal_fcf = fcf * (1 + terminal_growth)
    terminal_value = terminal_fcf / (discount_rate - terminal_growth)
    pv_terminal = terminal_value / ((1 + discount_rate) ** years)

    intrinsic_value = pv_explicit + pv_terminal
    return intrinsic_value / shares_outstanding
