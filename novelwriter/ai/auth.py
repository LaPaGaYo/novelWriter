"""
plotwright fork — Auth strategy abstraction
===========================================

Every cloud provider's authentication concern lives behind the `Auth` ABC.
Three concrete strategies cover Sprint 2's needs:

- `NoAuth`        — local providers (Ollama, MockProvider) carry no credentials.
- `ApiKeyAuth`    — Anthropic, and the API-key path for Gemini.
- `OAuthCreds`    — Gemini's "Sign in with Google" path (the S2 release lede).

The ABC is deliberately tight: provider code only needs `mode`, `headers()`, and
`refresh_if_needed()`. Keychain serialization, refresh-token rotation, and the
browser-loopback PKCE flow live in `keychain.py` and `oauth.py` respectively, so
this module stays small enough to read in one sitting.

Design decisions logged here (carry-forward to /review):

- `OAuthCreds.refresh_if_needed()` raises `OAuthInvalidGrantError` (subclass of
  `ProviderError`) on refresh failure. Matches the existing ProviderError
  hierarchy in `provider/base.py`; transport-layer code uses the same
  `except ProviderError` it already uses for generate() failures.

- `OAuthCreds.refresher` is a `Callable[[OAuthCreds], OAuthCreds]` that returns
  a NEW credentials object with refreshed access_token / refresh_token /
  expiry. `refresh_if_needed()` copies the new field values into self. This
  keeps mutation localised to one method and makes the refresher trivially
  testable (no shared state).

- Refresh window: 60s before expiry, at call-start only (never mid-call). This
  matches Sprint 2's frame decision on token-refresh-during-call race
  mitigation. See `.planning/current/plan/sprint-contract.md` "OAuth refresh"
  risk row.
"""
from __future__ import annotations

import abc

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Literal

from novelwriter.ai.provider.base import ProviderError


# How early before token expiry we refresh. Matches the framing decision so
# the value is greppable from one place.
REFRESH_WINDOW = timedelta(seconds=60)

AuthMode = Literal["none", "api_key", "oauth"]


class OAuthInvalidGrantError(ProviderError):
    """The OAuth refresh token was rejected by the provider.

    Surfaced as a re-auth modal in the AI Preferences panel; never retried
    silently. See `design-contract.md` "Component 3" State 4 ERROR sub-case
    "Auth failed".
    """


class Auth(abc.ABC):
    """Authentication strategy for a Provider.

    Concrete subclasses describe how a provider proves identity to its model
    backend. The ABC is intentionally minimal so MockProvider and Ollama
    (which carry no credentials) stay trivially compliant via `NoAuth()`.
    """

    @property
    @abc.abstractmethod
    def mode(self) -> AuthMode:
        """Stable identifier for this auth strategy.

        Used by AIConfig serialization to round-trip the user's auth choice
        without storing the secret itself.
        """

    @abc.abstractmethod
    def headers(self) -> dict[str, str]:
        """Return HTTP headers required for an authenticated request.

        Cloud providers merge this dict into every outbound request built by
        `transport.py`. Local providers return `{}` (the default for NoAuth).
        """

    def refresh_if_needed(self) -> None:
        """Refresh credentials if they're near expiry.

        Default is a no-op for the static-credential strategies. `OAuthCreds`
        overrides this to check expiry and call the refresher. Always invoked
        at call-start, never mid-call, per the Sprint 2 frame decision.
        """
        return None


class NoAuth(Auth):
    """No credentials at all. Used by MockProvider and Ollama (local)."""

    @property
    def mode(self) -> AuthMode:
        return "none"

    def headers(self) -> dict[str, str]:
        return {}


@dataclass(frozen=True, slots=True)
class ApiKeyAuth(Auth):
    """Static API key passed in a single HTTP header.

    Anthropic uses `x-api-key`; Gemini's API-key path uses
    `x-goog-api-key`. Providers know which header name to inject when
    instantiating this strategy, so the strategy itself stays generic.
    """

    api_key: str
    header_name: str = "x-api-key"

    @property
    def mode(self) -> AuthMode:
        return "api_key"

    def headers(self) -> dict[str, str]:
        return {self.header_name: self.api_key}


# Returned by an OAuthCreds.refresher. A plain dataclass so test refreshers
# can construct one in a single literal without importing anything heavy.
@dataclass(frozen=True, slots=True)
class RefreshedCreds:
    access_token: str
    refresh_token: str
    expiry: datetime
    scope: str


@dataclass(slots=True)
class OAuthCreds(Auth):
    """OAuth 2.0 credentials with caller-supplied refresh logic.

    The `refresher` callable is the dependency-injection seam: tests pass a
    fake, production passes the real Google-token-endpoint exchange from
    `oauth.py`. Refresher takes the current creds and returns a
    `RefreshedCreds` payload; `refresh_if_needed()` copies the new field
    values into self so a single shared instance round-trips through the
    keychain without churn.

    On refresh failure the refresher must raise `OAuthInvalidGrantError`;
    `refresh_if_needed()` re-raises it. Callers (status-bar widget,
    preferences pane) catch and surface the re-auth modal per
    `design-contract.md` Component 3 State 4.
    """

    access_token: str
    refresh_token: str
    expiry: datetime
    scope: str
    refresher: Callable[["OAuthCreds"], RefreshedCreds] = field(repr=False)

    @property
    def mode(self) -> AuthMode:
        return "oauth"

    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.access_token}"}

    def is_expiring_soon(self, *, now: datetime | None = None) -> bool:
        """True if expiry is within the refresh window from `now` (or wall clock)."""
        ref_now = now or datetime.now(timezone.utc)
        # Normalize naive datetimes to UTC so callers can pass either shape.
        cutoff = self.expiry
        if cutoff.tzinfo is None:
            cutoff = cutoff.replace(tzinfo=timezone.utc)
        return ref_now + REFRESH_WINDOW >= cutoff

    def refresh_if_needed(self) -> None:
        """Refresh credentials if within `REFRESH_WINDOW` of expiry.

        Idempotent: calling this twice without expiry crossing the window
        is a no-op. Refresher errors propagate; no silent retry.
        """
        if not self.is_expiring_soon():
            return
        refreshed = self.refresher(self)
        # In-place update keeps the object identity stable so anyone holding
        # a reference (keychain cache, transport client) sees fresh values.
        self.access_token = refreshed.access_token
        self.refresh_token = refreshed.refresh_token
        self.expiry = refreshed.expiry
        self.scope = refreshed.scope


__all__ = [
    "Auth",
    "AuthMode",
    "ApiKeyAuth",
    "NoAuth",
    "OAuthCreds",
    "OAuthInvalidGrantError",
    "REFRESH_WINDOW",
    "RefreshedCreds",
]
