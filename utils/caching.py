"""Streamlit-aware caching helper."""

from __future__ import annotations

from typing import Any, Callable


def memoize(ttl_seconds: int = 600) -> Callable:
    try:
        import streamlit as st

        return st.cache_data(ttl=ttl_seconds, show_spinner=False)
    except Exception:
        store: dict[tuple, Any] = {}

        def decorator(fn: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                key = (args, tuple(sorted(kwargs.items())))
                if key not in store:
                    store[key] = fn(*args, **kwargs)
                return store[key]

            return wrapper

        return decorator
