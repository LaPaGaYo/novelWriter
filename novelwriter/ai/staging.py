"""
Plotwright – AI output staging
==============================

Sprint 1 ships the *interface only*. The real proposed-vs-source diff
model with undo-friendly application lives in Sprint 3 alongside the
inline-rewrite feature, which is the first surface that actually stages
output. Defining the boundary here lets the Sprint 1 substrate be a
faithful skeleton without pulling in editor internals.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class StagedProposal:
    """A proposed transformation pending user accept/reject.

    ``feature`` is the AIConfig feature key the proposal originated from;
    ``original`` and ``proposed`` are the source and target strings; the
    optional ``anchor`` is an opaque token the calling editor uses to
    reattach the proposal to the document if the cursor moved.
    """

    feature: str
    original: str
    proposed: str
    anchor: str | None = None


class Staging(ABC):
    """Sprint 3 will bind this to the editor's undo stack and document model.

    Sprint 1 only declares the surface so the rest of the substrate can
    type-check against ``Staging`` without pulling in GUI code.
    """

    @abstractmethod
    def stage(self, proposal: StagedProposal) -> str:
        """Stage a proposal and return an opaque staging id."""

    @abstractmethod
    def accept(self, staging_id: str) -> None:
        """Apply the staged proposal to the document."""

    @abstractmethod
    def reject(self, staging_id: str) -> None:
        """Discard the staged proposal, leaving document state untouched."""
