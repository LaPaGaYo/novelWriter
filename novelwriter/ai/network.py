"""
Plotwright – AI single-egress network gate
==========================================

Every outbound call to a real AI provider routes through this module. Nothing
else in the application is permitted to import ``httpx`` or ``requests`` —
``tests/test_ai_no_external_imports.py`` enforces that statically as part of
the Sprint 1 verification gate (item 11).

Sprint 1 ships the *gate*, not the wire. No actual HTTP transport is invoked
yet — all Sprint 1 tests use :class:`MockProvider` and never reach this far.
The structure is in place so Sprint 2 can drop in real providers without
re-deriving the privacy contract.

Privacy guarantee
-----------------

A call is allowed if and only if **all** of these are true at the moment of
the call:

1. ``AIConfig.enabled is True`` (master toggle).
2. The caller-supplied ``feature`` is enabled in ``AIConfig.feature_flags``.
3. The caller has supplied either an authentication credential (cloud
   providers) or a non-empty endpoint URL (local providers).

Any failure of those three conditions raises
:class:`PrivacyGatingError` *before* any socket work is attempted. The error
is the only signal callers should see when the gate refuses the call.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import TYPE_CHECKING

from novelwriter.ai.error import PrivacyGatingError

if TYPE_CHECKING:
    from novelwriter.ai.config import AIConfig

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EgressRequest:
    """The minimal request envelope the gate inspects.

    Bodies are intentionally not part of this envelope: the gate's
    privacy log records *metadata only* (endpoint + byte count), never
    the request payload, and the body is forwarded straight to the
    transport layer in Sprint 2 without ever being read by this module.
    """

    feature: str
    endpoint: str
    byte_count: int
    has_credential: bool


def gated_request(config: AIConfig, request: EgressRequest) -> None:
    """Run the privacy gate against ``request`` using ``config``.

    Raises :class:`PrivacyGatingError` (subclass of ``AIError``) when the
    call must be refused. Returns ``None`` when the call is allowed; the
    caller then performs the real I/O. This split keeps the gate cheap to
    test (no transport mocking required) and keeps the transport layer
    free of policy code.
    """
    if not config.enabled:
        raise PrivacyGatingError(
            "master AI toggle is off",
            feature=request.feature,
        )

    if not config.feature_flags.get(request.feature, False):
        raise PrivacyGatingError(
            "feature is not opted in",
            feature=request.feature,
        )

    if not request.endpoint:
        raise PrivacyGatingError(
            "no endpoint configured",
            feature=request.feature,
        )

    if not request.has_credential:
        raise PrivacyGatingError(
            "no credential or local URL configured",
            feature=request.feature,
        )

    # Metadata-only privacy log. Body is never logged.
    logger.info(
        "ai-egress feature=%s endpoint=%s bytes=%d",
        request.feature, request.endpoint, request.byte_count,
    )


# Re-export the canonical error so callers can ``except`` it without dragging
# the ``error`` module into their imports.
__all__ = ["EgressRequest", "PrivacyGatingError", "gated_request"]
