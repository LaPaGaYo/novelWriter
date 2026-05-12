"""
plotwright fork — Token Estimation
==================================

The DESIGN.md privacy contract requires that we show the user a token estimate
before any cloud call. Sprint 1 ships a simple character-based heuristic; the
PRD accuracy bar (within 20% of actual on 95% of cloud calls) is a Sprint 2
benchmark target where we can plug in tiktoken or each provider's own counter.

We deliberately keep the heuristic pessimistic (slightly over-counts) so the
user is never under-warned about a metered call.
"""
from __future__ import annotations


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in `text`.

    Uses a 3.5-chars-per-token heuristic. English prose averages ~4 chars per
    token in modern tokenizers; biasing slightly down (3.5) makes the estimate
    pessimistic for the user (more tokens reported than actual), which is the
    safer side to err on for cost-disclosure.

    Returns 0 for empty input. Always returns a non-negative integer.
    """
    if not text:
        return 0
    # Strip leading/trailing whitespace before counting; whitespace at
    # boundaries does not meaningfully add tokens.
    stripped = text.strip()
    if not stripped:
        return 0
    char_count = len(stripped)
    # Round up so a 1-char input still reports >=1 token.
    return max(1, (char_count + 2) // 3)
