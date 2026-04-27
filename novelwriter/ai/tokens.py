"""
Plotwright – Token estimation
=============================

Sprint 1 ships a deliberately crude heuristic: 4 characters per token. It
is wrong but bounded — the verification matrix's
``rewrite-token-estimate-accuracy`` criterion (within 20% on 95% of cloud
calls) is owned by Sprint 3 once a real tokenizer is wired in. For now we
just need a number that callers can reason about.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

# Rough average for English prose under most modern BPE tokenizers. Cloud
# providers will override this in Sprint 2 with a real tokenizer call.
_CHARS_PER_TOKEN = 4


def estimate_tokens(text: str) -> int:
    """Return a non-negative integer token estimate for ``text``."""
    if not text:
        return 0
    # Round up so callers never under-budget when they cap output.
    return -(-len(text) // _CHARS_PER_TOKEN)
