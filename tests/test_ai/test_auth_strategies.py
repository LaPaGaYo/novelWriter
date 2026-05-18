"""
plotwright fork — Auth strategy unit tests (SC-14)
==================================================

Direct unit tests on the three Auth strategies (`NoAuth`, `ApiKeyAuth`,
`OAuthCreds`) in isolation. Provider-level concerns (lazy SDK imports,
network calls) live in the provider tests; this suite covers strategy
behavior only.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from novelwriter.ai.auth import (
    REFRESH_WINDOW,
    ApiKeyAuth,
    NoAuth,
    OAuthCreds,
    OAuthInvalidGrantError,
    RefreshedCreds,
)


def test_noauth_mode_and_headers():
    auth = NoAuth()
    assert auth.mode == "none"
    assert auth.headers() == {}
    # Refresh is a no-op; calling it twice does nothing observable.
    auth.refresh_if_needed()
    auth.refresh_if_needed()


def test_apikeyauth_emits_header_pair():
    auth = ApiKeyAuth(api_key="sk-test-1234", header_name="x-api-key")
    assert auth.mode == "api_key"
    assert auth.headers() == {"x-api-key": "sk-test-1234"}


def test_apikeyauth_default_header_name_is_x_api_key():
    """Anthropic uses the default; Gemini passes `header_name=x-goog-api-key`."""
    auth = ApiKeyAuth(api_key="k")
    assert "x-api-key" in auth.headers()


def test_apikeyauth_refresh_is_noop():
    auth = ApiKeyAuth(api_key="k")
    auth.refresh_if_needed()  # must not raise


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _fake_refresher(new_access: str, new_refresh: str = "rt-rotated"):
    """Build a refresher that returns a deterministic new credential pair."""

    def _refresh(_creds: OAuthCreds) -> RefreshedCreds:
        return RefreshedCreds(
            access_token=new_access,
            refresh_token=new_refresh,
            expiry=_now_utc() + timedelta(hours=1),
            scope="test-scope",
        )

    return _refresh


def test_oauthcreds_mode_and_bearer_header():
    creds = OAuthCreds(
        access_token="access-1",
        refresh_token="refresh-1",
        expiry=_now_utc() + timedelta(hours=1),
        scope="test-scope",
        refresher=_fake_refresher("unused"),
    )
    assert creds.mode == "oauth"
    assert creds.headers() == {"Authorization": "Bearer access-1"}


def test_oauthcreds_is_expiring_soon_inside_window():
    creds = OAuthCreds(
        access_token="t",
        refresh_token="r",
        expiry=_now_utc() + REFRESH_WINDOW - timedelta(seconds=5),
        scope="s",
        refresher=_fake_refresher("unused"),
    )
    assert creds.is_expiring_soon() is True


def test_oauthcreds_is_expiring_soon_outside_window():
    creds = OAuthCreds(
        access_token="t",
        refresh_token="r",
        expiry=_now_utc() + timedelta(hours=2),
        scope="s",
        refresher=_fake_refresher("unused"),
    )
    assert creds.is_expiring_soon() is False


def test_oauthcreds_refresh_replaces_fields_in_place():
    creds = OAuthCreds(
        access_token="old-access",
        refresh_token="old-refresh",
        expiry=_now_utc() + REFRESH_WINDOW - timedelta(seconds=10),
        scope="initial-scope",
        refresher=_fake_refresher("new-access", "new-refresh"),
    )
    creds.refresh_if_needed()
    assert creds.access_token == "new-access"
    assert creds.refresh_token == "new-refresh"
    # Scope from the refresher's response replaces the original.
    assert creds.scope == "test-scope"


def test_oauthcreds_refresh_skips_when_not_expiring():
    """No refresher invocation when the token still has plenty of life."""
    calls: list[int] = []

    def counting_refresher(_creds: OAuthCreds) -> RefreshedCreds:
        calls.append(1)
        return RefreshedCreds(
            access_token="unused",
            refresh_token="unused",
            expiry=_now_utc() + timedelta(hours=1),
            scope="unused",
        )

    creds = OAuthCreds(
        access_token="still-good",
        refresh_token="r",
        expiry=_now_utc() + timedelta(hours=2),
        scope="s",
        refresher=counting_refresher,
    )
    creds.refresh_if_needed()
    assert calls == []
    assert creds.access_token == "still-good"


def test_oauthcreds_refresh_propagates_invalid_grant():
    """Refresher errors must surface to the caller for re-auth modal UX."""

    def bad_refresher(_creds: OAuthCreds) -> RefreshedCreds:
        raise OAuthInvalidGrantError("Google rejected the refresh token")

    creds = OAuthCreds(
        access_token="t",
        refresh_token="r",
        expiry=_now_utc() + REFRESH_WINDOW - timedelta(seconds=1),
        scope="s",
        refresher=bad_refresher,
    )
    with pytest.raises(OAuthInvalidGrantError):
        creds.refresh_if_needed()


def test_oauthcreds_naive_expiry_is_normalized_to_utc():
    """A caller storing a naive datetime should not be silently treated as local time."""
    naive_expiry = (
        datetime.now(timezone.utc).replace(tzinfo=None)
        + REFRESH_WINDOW
        - timedelta(seconds=1)
    )
    creds = OAuthCreds(
        access_token="t",
        refresh_token="r",
        expiry=naive_expiry,
        scope="s",
        refresher=_fake_refresher("rotated"),
    )
    assert creds.is_expiring_soon() is True


def test_repr_redacts_secrets():
    """S-2 regression: dataclass __repr__ MUST NOT expose secret-bearing fields.

    Secrets must be suppressed because any `logger.X("...", auth)`,
    f-string, or unhandled exception traceback involving these dataclasses
    would otherwise write API keys / bearer tokens to stderr (and to disk
    if the debug log is enabled). The fix is `field(repr=False)` on the
    secret fields; this test pins that contract.
    """
    # ApiKeyAuth: api_key must NOT appear in repr; header_name MAY appear.
    api_auth = ApiKeyAuth(api_key="sk-SECRET-ANTHROPIC-KEY-DO-NOT-LEAK", header_name="x-api-key")
    api_repr = repr(api_auth)
    assert "sk-SECRET-ANTHROPIC-KEY-DO-NOT-LEAK" not in api_repr
    assert "api_key" not in api_repr  # field name itself absent when repr=False
    # header_name remains visible for debugging — it's not a secret.
    assert "x-api-key" in api_repr

    # OAuthCreds: access_token + refresh_token must NOT appear; expiry + scope MAY.
    creds = OAuthCreds(
        access_token="SECRET_ACCESS_TOKEN_DO_NOT_LEAK",
        refresh_token="SECRET_REFRESH_TOKEN_DO_NOT_LEAK",
        expiry=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scope="test-scope-marker",
        refresher=_fake_refresher("rotated"),
    )
    creds_repr = repr(creds)
    assert "SECRET_ACCESS_TOKEN_DO_NOT_LEAK" not in creds_repr
    assert "SECRET_REFRESH_TOKEN_DO_NOT_LEAK" not in creds_repr
    assert "access_token" not in creds_repr  # field name itself absent
    assert "refresh_token" not in creds_repr
    # Non-secret fields remain visible.
    assert "scope" in creds_repr
    assert "test-scope-marker" in creds_repr

    # RefreshedCreds: same contract — access_token + refresh_token suppressed.
    refreshed = RefreshedCreds(
        access_token="SECRET_NEW_ACCESS_DO_NOT_LEAK",
        refresh_token="SECRET_NEW_REFRESH_DO_NOT_LEAK",
        expiry=datetime(2099, 1, 1, tzinfo=timezone.utc),
        scope="test-scope-marker",
    )
    refreshed_repr = repr(refreshed)
    assert "SECRET_NEW_ACCESS_DO_NOT_LEAK" not in refreshed_repr
    assert "SECRET_NEW_REFRESH_DO_NOT_LEAK" not in refreshed_repr
    assert "access_token" not in refreshed_repr
    assert "refresh_token" not in refreshed_repr
    assert "test-scope-marker" in refreshed_repr

    # Sanity: secrets are still present in headers() — the test isn't accidentally
    # asserting against a broken `__init__` that silently dropped the values.
    assert api_auth.headers() == {"x-api-key": "sk-SECRET-ANTHROPIC-KEY-DO-NOT-LEAK"}
    assert creds.headers()["Authorization"] == "Bearer SECRET_ACCESS_TOKEN_DO_NOT_LEAK"
