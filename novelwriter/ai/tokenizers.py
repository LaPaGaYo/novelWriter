"""
plotwright fork — Per-provider tokenizer adapters
=================================================

The PRD accuracy bar is "within 20% of actual tokens on 95% of cloud calls".
Sprint 2 ships a per-provider adapter layer with the following fallback chain:

- `tiktoken` (Apache-2.0) for OpenAI-like tokenizations. Used opportunistically
  for Anthropic where no offline tokenizer is freely available (Anthropic's
  byte-pair vocabulary is similar enough to `cl100k_base` for the 20% bound
  on prose to hold per our committed corpus).
- Anthropic's own offline tokenizer when present (kept as a slot in case the
  SDK starts shipping one; currently `tiktoken cl100k_base` is the fallback).
- Gemini: heuristic only. No offline tokenizer is freely available; the
  3.5-chars-per-token heuristic from `tokens.estimate_tokens` is biased
  slightly conservative so the user is over-warned rather than under-warned.

Every SDK import inside this module is lazy. `import novelwriter.ai` must
never pull `tiktoken` into `sys.modules`.

The `Tokenizer` callable type is intentionally simple: it takes a string,
returns an int. Providers route their `estimate_tokens()` through this
module by `Provider.estimate_tokens = tokenizers.for_provider(name)`.
"""
from __future__ import annotations

import logging

from typing import Callable

from novelwriter.ai.tokens import estimate_tokens as heuristic_tokens

logger = logging.getLogger(__name__)


Tokenizer = Callable[[str], int]


def for_provider(provider_name: str) -> Tokenizer:
    """Return a tokenizer callable for `provider_name`.

    Always returns *some* tokenizer; if a preferred backend is missing we
    silently fall back to the heuristic rather than fail. The user-facing
    contract is "the estimate is shown before every cloud call", not "the
    estimate is exact"; a slightly-conservative heuristic still satisfies it.

    Provider name matching is prefix-based so `ollama:llama3.1-8b` and
    `ollama` route to the same tokenizer.
    """
    base = provider_name.split(":", 1)[0].lower()
    if base in ("anthropic", "openai"):
        return _cl100k_tokenizer()
    if base == "ollama":
        # Local model; the user is not metered, so the heuristic is fine and
        # avoids pulling a tokenizer SDK for a privacy-sensitive provider.
        return heuristic_tokens
    if base == "gemini":
        # No freely available offline tokenizer; document the gap explicitly.
        return heuristic_tokens
    # Unknown provider: heuristic. Never fail.
    return heuristic_tokens


def _cl100k_tokenizer() -> Tokenizer:
    """Return a `tiktoken` cl100k_base tokenizer, or heuristic on import failure.

    `tiktoken` is wrapped at call-time, not module-import time, so the SDK
    never lands in `sys.modules` for a fork that does not actually run a
    cloud call.
    """

    def _tokenize(text: str) -> int:
        if not text:
            return 0
        try:
            import tiktoken  # lazy
        except ImportError:
            logger.debug("tiktoken not installed; falling back to heuristic")
            return heuristic_tokens(text)
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:  # pragma: no cover - depends on tiktoken internals
            logger.warning("tiktoken encoding init failed: %s", exc)
            return heuristic_tokens(text)
        return len(encoding.encode(text))

    return _tokenize


__all__ = ["Tokenizer", "for_provider"]
