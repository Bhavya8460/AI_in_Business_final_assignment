"""Anthropic Claude wrapper with retry and JSON-mode parsing."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any

from anthropic import Anthropic, APIError, APITimeoutError, RateLimitError

from config import MAX_TOKENS, MODEL_NAME, TEMPERATURE

logger = logging.getLogger(__name__)


def _api_key() -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import streamlit as st

        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Add it to .env or "
            ".streamlit/secrets.toml."
        ) from exc


_CLIENT: Anthropic | None = None


def _client() -> Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Anthropic(api_key=_api_key())
    return _CLIENT


_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", re.DOTALL)


def _extract_json(text: str) -> dict | list:
    """Pull a JSON object/array out of an LLM response."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = _JSON_FENCE.search(text)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    for opener, closer in (("{", "}"), ("[", "]")):
        first = text.find(opener)
        last = text.rfind(closer)
        if first != -1 and last != -1 and last > first:
            try:
                return json.loads(text[first : last + 1])
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract JSON from LLM response: {text[:200]!r}")


def call_text(
    system: str,
    user: str,
    *,
    model: str = MODEL_NAME,
    max_tokens: int = MAX_TOKENS,
    temperature: float = TEMPERATURE,
    max_retries: int = 3,
) -> str:
    """Call Claude and return raw text."""
    last_exc: Exception | None = None
    backoff = 1.0
    for attempt in range(max_retries):
        try:
            response = _client().messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            parts = [b.text for b in response.content if getattr(b, "type", None) == "text"]
            return "\n".join(parts).strip()
        except (RateLimitError, APITimeoutError) as exc:
            last_exc = exc
            logger.warning("LLM transient error attempt %d: %s", attempt + 1, exc)
            time.sleep(backoff)
            backoff *= 2
        except APIError as exc:
            last_exc = exc
            logger.warning("LLM API error attempt %d: %s", attempt + 1, exc)
            time.sleep(backoff)
            backoff *= 2

    raise RuntimeError(f"LLM failed after {max_retries} attempts: {last_exc}")


def call_json(system: str, user: str, **kwargs: Any) -> dict | list:
    """Call Claude and parse a JSON response."""
    text = call_text(system, user, **kwargs)
    return _extract_json(text)
