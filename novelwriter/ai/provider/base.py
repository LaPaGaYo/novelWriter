"""
plotwright fork — Provider ABC
==============================

The contract every AI provider implements. The contract test
(`tests/test_ai/test_provider_contract.py`) runs against every concrete
provider to verify uniform behavior.
"""
from __future__ import annotations

import abc

from dataclasses import dataclass


class ProviderError(Exception):
    """A provider call failed for a non-privacy reason (timeout, model error, etc.)."""


@dataclass(frozen=True, slots=True)
class ProviderResponse:
    """The structured result of a `Provider.generate()` call."""

    text: str
    provider_name: str
    is_local: bool
    estimated_tokens_in: int
    estimated_tokens_out: int


class Provider(abc.ABC):
    """Abstract base class for AI providers.

    Every concrete provider must implement four methods. The contract test
    runs the same suite against each implementation to guarantee uniform
    behavior across local and cloud backends.
    """

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """A short, stable identifier (e.g. 'mock', 'ollama:llama3.1-8b')."""

    @property
    @abc.abstractmethod
    def is_local(self) -> bool:
        """True if calls never leave the user's machine."""

    @abc.abstractmethod
    def generate(self, prompt: str, **opts: object) -> ProviderResponse:
        """Run a prompt through the model and return a ProviderResponse.

        Cloud providers MUST call `NetworkGate.guard(feature)` before issuing
        any outbound request. Local providers MAY skip the gate (their is_local
        is True), but they SHOULD still respect master switch state via the
        feature flag pattern, so that "AI off" disables local providers too.
        """

    @abc.abstractmethod
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for `text` using this provider's tokenizer."""

    @abc.abstractmethod
    def health_check(self) -> bool:
        """Return True if the provider is reachable and ready.

        For local providers, this means the local daemon (Ollama) is up. For
        cloud providers, this means a key is present and a low-cost API call
        succeeds. Health checks MUST respect the privacy gate just like
        `generate()` does.
        """
