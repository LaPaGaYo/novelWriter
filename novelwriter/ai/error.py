"""
Plotwright – AI error hierarchy
================================

Sprint 1 contract — every AI subsystem error inherits from :class:`AIError`,
and any privacy-gating refusal is a :class:`PrivacyGatingError` (a subclass of
``AIError``). The contract test ``tests/test_ai_network_gating.py`` checks
this invariant directly.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations


class AIError(Exception):
    """Base class for any error raised by the AI substrate."""


class PrivacyGatingError(AIError):
    """Raised when a network call is refused by the privacy gate.

    The gate refuses the call if any of the following are true:

    * ``AIConfig.enabled`` is ``False``
    * the caller-supplied ``feature`` flag is not enabled
    * no provider credential or local URL is configured for the call

    Catching this error in calling code is allowed only for surface-level
    UX feedback — never to retry the call without flipping the gate first.
    """

    def __init__(self, reason: str, *, feature: str | None = None) -> None:
        self.reason = reason
        self.feature = feature
        msg = f"Privacy gate refused AI call: {reason}"
        if feature:
            msg += f" (feature={feature!r})"
        super().__init__(msg)


class ProviderError(AIError):
    """Raised when a provider implementation fails to fulfill the contract."""
