"""Tiny string/number helpers used across UI and agents."""

from __future__ import annotations

from typing import Any, Optional


def safe_get(obj: Any, *keys: str, default: Any = "—") -> Any:
    cur = obj
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


def truncate(text: str | None, max_chars: int = 200) -> str:
    if not text:
        return ""
    s = str(text).strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def fmt_pct(v: Optional[float], digits: int = 1) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def fmt_money(v: Optional[float], digits: int = 2) -> str:
    if v is None:
        return "—"
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    sign = "-" if f < 0 else ""
    f = abs(f)
    if f >= 1e12:
        return f"{sign}${f / 1e12:.{digits}f}T"
    if f >= 1e9:
        return f"{sign}${f / 1e9:.{digits}f}B"
    if f >= 1e6:
        return f"{sign}${f / 1e6:.{digits}f}M"
    if f >= 1e3:
        return f"{sign}${f / 1e3:.{digits}f}K"
    return f"{sign}${f:.{digits}f}"


def fmt_price(v: Optional[float]) -> str:
    if v is None:
        return "—"
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return "—"


def verdict_color(verdict: Optional[str]) -> str:
    """Map a verdict label to a CSS color."""
    if not verdict:
        return "#6b7280"
    v = verdict.upper()
    if "STRONG BUY" in v:
        return "#059669"
    if "STRONG AVOID" in v:
        return "#dc2626"
    if "BUY" in v:
        return "#10b981"
    if "AVOID" in v or "SELL" in v:
        return "#ef4444"
    if "HOLD" in v:
        return "#f59e0b"
    return "#6b7280"


def grade_color(grade: Optional[str]) -> str:
    if not grade:
        return "#6b7280"
    g = grade.upper().strip()
    return {
        "A": "#059669",
        "B": "#10b981",
        "C": "#f59e0b",
        "D": "#f97316",
        "F": "#dc2626",
    }.get(g, "#6b7280")


def sentiment_color(label: Optional[str]) -> str:
    if not label:
        return "#6b7280"
    l = label.lower()
    if "overly bearish" in l:
        return "#059669"  # contrarian green
    if "bearish" in l:
        return "#10b981"
    if "overly bullish" in l:
        return "#dc2626"
    if "bullish" in l:
        return "#f59e0b"
    return "#6b7280"


def feasibility_color(level: Optional[str]) -> str:
    if not level:
        return "#6b7280"
    return {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"}.get(level.lower(), "#6b7280")
