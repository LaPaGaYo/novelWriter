"""
plotwright fork — Output Staging
================================

The inline-rewrite feature stages AI-generated text in a side-by-side review
pane before any source-document text is replaced. Sprint 2 widens the data
class with cursor / source-range / per-call metadata so the Sprint 3 review
pane can render diffs without re-asking the provider where the rewrite came
from. Real UI rendering still ships in Sprint 3.

`stage(prompt, provider)` is the orchestration entry point for the AI
Preferences "Dry-run" button (the S2 smoke surface). It calls the provider
through the standard `Provider.generate` contract and packages the result in
a `StagedRewrite`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from novelwriter.ai.tokens import estimate_tokens

if TYPE_CHECKING:
    from novelwriter.ai.config import AIFeature
    from novelwriter.ai.network import NetworkGate
    from novelwriter.ai.provider.base import Provider


@dataclass(frozen=True, slots=True)
class StagedRewrite:
    """A proposed rewrite that has not yet been applied to the source document.

    Sprint 2 widening: cursor + source-range + estimated-token fields are now
    populated. The S3 review pane keys off `source_start_pos` /
    `source_end_pos` to render the diff inline; the dry-run button uses
    `estimated_tokens_in` to show the cost preview.

    Backwards compatibility: every new field has a default, and `original`
    plus `proposed` are still positional. Existing S1 call sites that only
    pass those two keep working.
    """

    original: str
    proposed: str
    transformation: str = "rewrite"
    provider_name: str = "mock"
    is_local: bool = True

    # Sprint 2 fields — anticipating the S3 review pane.
    # `source_start_pos` / `source_end_pos` are character offsets into the
    # full source document; for a dry-run on synthetic input both are 0 and
    # `len(original)` respectively.
    source_start_pos: int = 0
    source_end_pos: int = 0
    estimated_tokens_in: int = 0
    estimated_tokens_out: int = 0
    metadata: dict[str, str] = field(default_factory=dict)


def stage(
    prompt: str,
    provider: "Provider",
    *,
    transformation: str = "rewrite",
    gate: "NetworkGate | None" = None,
    feature: "AIFeature | None" = None,
) -> StagedRewrite:
    """Run `prompt` through `provider` and stage the result.

    Used by the Preferences "Dry-run" button to exercise the staging path end
    to end (provider call → token estimate → StagedRewrite) without
    committing the proposed text to a real document. The S3 review pane
    consumes the same return type, so the staging interface is stable across
    sprints.

    Privacy gate (S-1 fix, /review Pass 1): if `gate` + `feature` are passed
    explicitly, `stage()` calls `gate.guard(feature)` BEFORE
    `provider.generate()` as belt-and-suspenders. The provider itself ALSO
    gates internally when constructed with a gate (see
    `provider/base.py::_enforce_privacy_gate`). Either layer alone catches
    the regression; both layers ensure no future refactor accidentally
    bypasses the contract.
    """
    if gate is not None and feature is not None:
        gate.guard(feature)
    elif (gate is None) != (feature is None):
        # Half-configured = misconfigured. Refuse loudly.
        from novelwriter.ai.provider.base import ProviderError
        raise ProviderError(
            "staging.stage(): gate and feature must be passed together; "
            f"got gate={gate!r}, feature={feature!r}",
        )
    response = provider.generate(prompt)
    return StagedRewrite(
        original=prompt,
        proposed=response.text,
        transformation=transformation,
        provider_name=response.provider_name,
        is_local=response.is_local,
        source_start_pos=0,
        source_end_pos=len(prompt),
        estimated_tokens_in=response.estimated_tokens_in or estimate_tokens(prompt),
        estimated_tokens_out=response.estimated_tokens_out or estimate_tokens(response.text),
    )


__all__ = ["StagedRewrite", "stage"]
