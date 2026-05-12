"""
plotwright fork — Output Staging (interface only in Sprint 1)
=============================================================

The inline-rewrite feature stages AI-generated text in a side-by-side review
pane before any source-document text is replaced. Sprint 1 ships only the
data class so the provider abstraction can name its return type. The full
staging widget and undo-friendly accept/reject semantics land in Sprint 3.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StagedRewrite:
    """A proposed rewrite that has not yet been applied to the source document.

    Fields are intentionally minimal in Sprint 1; the full staging model
    (cursor position, undo step, source range, accept/reject metadata) lands
    with the rewrite feature implementation in Sprint 3.
    """

    original: str
    proposed: str
    transformation: str
    provider_name: str
    is_local: bool
