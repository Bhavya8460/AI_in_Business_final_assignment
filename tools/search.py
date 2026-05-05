"""Tavily search wrapper with simple in-memory caching."""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any

from tavily import TavilyClient

from config import SEARCH_CACHE_TTL, TAVILY_MAX_RESULTS, TAVILY_SEARCH_DEPTH

logger = logging.getLogger(__name__)

_CACHE: dict[str, tuple[float, list[dict]]] = {}


def _api_key() -> str:
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key
    try:
        import streamlit as st

        return st.secrets["TAVILY_API_KEY"]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "TAVILY_API_KEY is not set. Add it to .env or "
            ".streamlit/secrets.toml."
        ) from exc


def _cache_key(query: str, max_results: int, depth: str) -> str:
    return hashlib.sha256(f"{query}|{max_results}|{depth}".encode()).hexdigest()


def _normalize(results: dict[str, Any]) -> list[dict]:
    out: list[dict] = []
    for item in results.get("results") or []:
        out.append(
            {
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score", 0.0),
            }
        )
    return out


def search(
    query: str,
    *,
    max_results: int = TAVILY_MAX_RESULTS,
    depth: str = TAVILY_SEARCH_DEPTH,
) -> list[dict]:
    """Run a single Tavily search. Returns [] on any failure."""
    key = _cache_key(query, max_results, depth)
    cached = _CACHE.get(key)
    if cached and time.time() - cached[0] < SEARCH_CACHE_TTL:
        return cached[1]

    try:
        client = TavilyClient(api_key=_api_key())
        raw = client.search(query=query, max_results=max_results, search_depth=depth)
        results = _normalize(raw)
    except Exception as exc:
        logger.warning("Tavily search failed for %r: %s", query, exc)
        return []

    _CACHE[key] = (time.time(), results)
    return results


def search_many(queries: list[str], **kwargs: Any) -> list[dict]:
    """Run several queries, merge results, de-dup by URL."""
    seen: set[str] = set()
    merged: list[dict] = []
    for q in queries:
        for row in search(q, **kwargs):
            url = row.get("url") or row.get("title")
            if url and url in seen:
                continue
            if url:
                seen.add(url)
            merged.append(row)
    return merged
