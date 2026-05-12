"""
plotwright fork — Network Egress Gate
=====================================

The single egress point for any AI-related network call. Every cloud provider
implementation MUST make its outbound request through `NetworkGate.guard()`
or it will be flagged by the static check in CI (no `httpx`/`requests` import
allowed outside this module).

The gate refuses calls when:
1. `AIConfig.enabled` is False (master switch off)
2. The feature requesting the call has its per-feature flag off
3. The caller has not declared which feature the call is for

The privacy regression test (`tests/test_ai/test_privacy.py`) monkey-patches
`socket.socket.connect` to assert that no real outbound connection occurs while
the master switch is off. This module does NOT make any network call itself in
Sprint 1; the real provider implementations land in Sprint 2.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from novelwriter.ai.config import AIConfig, AIFeature

logger = logging.getLogger(__name__)


class AIError(Exception):
    """Base exception for the plotwright AI substrate."""


class PrivacyGatingError(AIError):
    """Raised when an AI feature attempts a network call that is not allowed.

    This is the privacy guarantee in code form. If the master switch is off, or
    the feature flag is off, the gate refuses the call. The test suite asserts
    that this exception is raised on every disallowed path.
    """


class NetworkGate:
    """Wraps an AIConfig and gates outbound calls per (feature, request)."""

    def __init__(self, config: AIConfig) -> None:
        self._config = config

    def guard(self, feature: AIFeature) -> None:
        """Raise PrivacyGatingError if the call cannot proceed.

        Call this from any provider implementation immediately before issuing
        an outbound request. Pass the `AIFeature` that the call is for, so the
        gate can verify the per-feature opt-in (not just the master switch).
        """
        if not self._config.enabled:
            raise PrivacyGatingError(
                f"AI master switch is off; cannot make a network call "
                f"for feature {feature.value!r}",
            )
        if not self._config.features.get(feature, False):
            raise PrivacyGatingError(
                f"AI feature {feature.value!r} is not enabled for this project; "
                f"cannot make a network call",
            )
        # All checks passed; caller may proceed to issue its request.
        # We deliberately do NOT make the request here; provider impls own
        # transport, this gate only authorizes.
        logger.debug("NetworkGate authorized call for feature %s", feature.value)
