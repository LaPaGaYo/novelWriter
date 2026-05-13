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
