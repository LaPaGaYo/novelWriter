"""
plotwright fork — Staging Consumer Boundary (Sprint 2 stub)
===========================================================

The Sprint 3 inline-rewrite review pane is the real consumer of
`StagedRewrite` objects. Sprint 2 commits this stub so the boundary is named
and importable from day one. Sprint 3 fills in `apply()` / `reject()`
semantics against a live editor cursor.

Committing the stub now is the cheap way to lock the interface before any
review-pane code is written. The Sprint 2 verification matrix references
this file as the S3 boundary marker.
"""
from __future__ import annotations

import abc

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from novelwriter.ai.staging import StagedRewrite


class StagingConsumer(abc.ABC):
    """The interface the Sprint 3 review pane will implement.

    The substrate produces `StagedRewrite` objects; a `StagingConsumer`
    decides what to do with them (render diff, apply on accept, discard on
    reject). Sprint 2 contains the contract; Sprint 3 provides the concrete
    `GuiReviewPaneConsumer`.

    The decision to keep `accept` / `reject` separate (instead of a single
    `resolve(staged, accepted: bool)` method) means the review pane can
    implement bespoke side effects on each path — undo stack on accept,
    audit log on reject — without branching inside one method.
    """

    @abc.abstractmethod
    def accept(self, staged: "StagedRewrite") -> None:
        """Apply `staged.proposed` to the source document.

        Implementations replace the text in `[staged.source_start_pos,
        staged.source_end_pos)` with `staged.proposed`. The text replacement
        must register a single undo step.
        """

    @abc.abstractmethod
    def reject(self, staged: "StagedRewrite") -> None:
        """Discard `staged` without touching the source document."""


__all__ = ["StagingConsumer"]
