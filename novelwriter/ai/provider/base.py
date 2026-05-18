"""
plotwright fork — Provider ABC
==============================

The contract every AI provider implements. The contract test
(`tests/test_ai/test_provider_contract.py`) runs against every concrete
provider to verify uniform behavior.

Sprint 2 widening: every `Provider` now carries an `auth: Auth` attribute. The
default is `NoAuth()` so the existing MockProvider / OllamaProvider stay
trivially compliant without method-signature change. Cloud providers
(`AnthropicProvider`, `GeminiProvider`) override `auth` with the appropriate
`ApiKeyAuth` / `OAuthCreds` instance at construction time.
"""
from __future__ import annotations

import abc

from dataclasses import dataclass


class ProviderError(Exception):
    """A provider call failed for a non-privacy reason (timeout, model error, etc.)."""


class ProviderDependencyError(ProviderError):
    """A provider's optional SDK is not installed in this environment.

    Raised at provider construction time when the lazy SDK import fails.
    Surfaced to the user as a re-install hint rather than an opaque ImportError.
    The keep-it-narrow rule: `import` failures get wrapped here, every other
    runtime failure inside the SDK propagates as `ProviderError`.
    """


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

    Sprint 2: every provider also carries an `auth: Auth` attribute used by
    `transport.py` when building outbound requests. Defaulting to `NoAuth()`
    on the ABC means MockProvider and OllamaProvider need no constructor
    change. Concrete cloud providers set `self.auth` in `__init__`.
    """

    # Default Auth strategy. Cloud providers override in __init__.
    # The import is deferred to a property so this base module never imports
    # auth.py at class-construction time, which would create an ai-package
    # import cycle.
    @property
    def auth(self):  # noqa: D401 - short docstring style
        """Return this provider's Auth strategy.

        The default is a fresh `NoAuth()`. Subclasses with credentials set
        `self._auth` in `__init__` and the property returns that instead.
        """
        from novelwriter.ai.auth import NoAuth
        return getattr(self, "_auth", None) or NoAuth()

    @auth.setter
    def auth(self, value) -> None:
        self._auth = value

    # ---- Privacy gate plumbing (S-1 fix, /review Pass 1) ----------------
    # Concrete providers may set `self._gate` and `self._feature` at
    # construction time. When both are set, `_enforce_privacy_gate()` calls
    # `gate.guard(feature)` and raises `PrivacyGatingError` if the call is
    # not allowed by the current `AIConfig`. When neither is set, the helper
    # is a no-op (test-only construction shape). Misconfiguration (one
    # without the other) raises `ProviderError` loudly rather than
    # silently skipping the gate.
    #
    # Cloud providers MUST call `self._enforce_privacy_gate()` at the top of
    # `generate()` before any client / network work. The Preferences
    # "Dry-run" path (`preferences_panel._run_dry_run`) constructs each cloud
    # provider with a gate + feature wired through `make_provider`, so the
    # privacy contract is enforced on the only S2 user-facing call path.
    def _enforce_privacy_gate(self) -> None:
        """Enforce the configured privacy gate, or no-op if none set."""
        gate = getattr(self, "_gate", None)
        feature = getattr(self, "_feature", None)
        if gate is not None:
            if feature is None:
                raise ProviderError(
                    f"{type(self).__name__} has gate but no feature; "
                    f"both required together",
                )
            gate.guard(feature)
        elif feature is not None:
            raise ProviderError(
                f"{type(self).__name__} has feature but no gate; "
                f"both required together",
            )

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
