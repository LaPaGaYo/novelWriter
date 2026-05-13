"""
plotwright fork — OAuth flow tests (SC-11)
==========================================

Covers the PKCE flow against an in-process stub. We do NOT speak to a real
Google endpoint; instead `httpx.MockTransport` short-circuits the token and
revoke endpoints, and a synthetic "browser" callable issues the loopback
request that a real browser would issue.

Required assertions per SC-11:
- PKCE handshake produces a `code_challenge` derived from the verifier.
- Refresh-token round-trip exchanges a refresh token for a fresh access
  token and updates `OAuthCreds` in place.
- Revoke-on-disable hits the revoke endpoint.
- State-parameter CSRF check rejects a mismatched state.
"""
from __future__ import annotations

import base64
import hashlib
import threading
import time
import urllib.parse
import urllib.request

import httpx
import pytest

from novelwriter.ai.auth import OAuthCreds, OAuthInvalidGrantError, RefreshedCreds
from novelwriter.ai.oauth import (
    OAuthFlowConfig,
    _build_authorize_url,
    _pkce_pair,
    authorize,
    creds_from_blob,
    creds_to_blob,
    revoke,
)


# ----- PKCE primitives ------------------------------------------------------


def test_pkce_pair_uses_s256_derivation():
    """code_challenge must be `base64url(sha256(verifier))` with no padding."""
    verifier, challenge = _pkce_pair()
    expected = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest(),
    ).rstrip(b"=").decode("ascii")
    assert challenge == expected
    # Verifier must be in the RFC 7636 valid character range and adequately long.
    assert 43 <= len(verifier) <= 128


def test_pkce_pair_is_random_per_call():
    a = _pkce_pair()
    b = _pkce_pair()
    assert a != b


def test_authorize_url_includes_state_and_challenge():
    config = OAuthFlowConfig(client_id="client-test", scope="gen-lang")
    url = _build_authorize_url(
        config,
        challenge="ch",
        state="st",
        redirect_uri="http://127.0.0.1:9999/callback",
    )
    parsed = urllib.parse.urlparse(url)
    query = urllib.parse.parse_qs(parsed.query)
    assert query["client_id"] == ["client-test"]
    assert query["state"] == ["st"]
    assert query["code_challenge"] == ["ch"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == ["gen-lang"]
    assert query["access_type"] == ["offline"]


# ----- Full PKCE flow via MockTransport -------------------------------------


def _token_response(*, access: str, refresh: str, expires_in: int = 3600) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "access_token": access,
            "refresh_token": refresh,
            "expires_in": expires_in,
            "scope": "gen-lang",
            "token_type": "Bearer",
        },
    )


class _StubBrowser:
    """Simulates the user approving the consent screen and following the redirect."""

    def __init__(self, *, state_override: str | None = None, error: str | None = None):
        self.state_override = state_override
        self.error = error
        self.last_url: str | None = None

    def __call__(self, url: str) -> None:
        self.last_url = url
        query = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
        state = query["state"][0]
        if self.state_override is not None:
            state = self.state_override
        redirect_uri = query["redirect_uri"][0]

        if self.error:
            callback = f"{redirect_uri}?error={self.error}&state={state}"
        else:
            callback = f"{redirect_uri}?code=auth-code-test&state={state}"

        # Hit the loopback listener from a thread so authorize() can still
        # observe the synchronous request that the real browser would make.
        def _fire() -> None:
            for _ in range(50):
                try:
                    urllib.request.urlopen(callback, timeout=1.0).close()
                    return
                except Exception:
                    time.sleep(0.05)

        threading.Thread(target=_fire, daemon=True).start()


def _exchange_handler():
    """MockTransport handler that responds to /token requests with a fixed payload."""

    def _handler(request: httpx.Request) -> httpx.Response:
        body = urllib.parse.parse_qs(request.content.decode("utf-8"))
        grant_type = body.get("grant_type", [""])[0]
        if grant_type == "authorization_code":
            assert body["code"] == ["auth-code-test"]
            assert body["client_id"] == ["client-test"]
            assert body["code_verifier"], "PKCE verifier must be sent"
            return _token_response(access="ya29.access", refresh="rt-initial")
        if grant_type == "refresh_token":
            assert body["refresh_token"] == ["rt-initial"]
            return _token_response(access="ya29.refreshed", refresh="rt-rotated")
        return httpx.Response(400, json={"error": "unsupported_grant_type"})

    return _handler


def test_full_pkce_flow_returns_usable_creds():
    config = OAuthFlowConfig(client_id="client-test", scope="gen-lang")
    transport = httpx.MockTransport(_exchange_handler())
    browser = _StubBrowser()

    creds = authorize(
        config,
        open_browser=browser,
        transport=transport,
        callback_timeout=5.0,
    )

    assert creds.mode == "oauth"
    assert creds.access_token == "ya29.access"
    assert creds.refresh_token == "rt-initial"
    assert creds.headers() == {"Authorization": "Bearer ya29.access"}
    assert browser.last_url is not None and browser.last_url.startswith(config.auth_url)


def test_state_mismatch_is_treated_as_csrf():
    config = OAuthFlowConfig(client_id="client-test")
    transport = httpx.MockTransport(_exchange_handler())
    browser = _StubBrowser(state_override="attacker-state")
    with pytest.raises(RuntimeError, match="state mismatch"):
        authorize(config, open_browser=browser, transport=transport, callback_timeout=5.0)


def test_provider_returned_error_is_invalid_grant():
    config = OAuthFlowConfig(client_id="client-test")
    transport = httpx.MockTransport(_exchange_handler())
    browser = _StubBrowser(error="access_denied")
    with pytest.raises(OAuthInvalidGrantError, match="access_denied"):
        authorize(config, open_browser=browser, transport=transport, callback_timeout=5.0)


def test_refresh_round_trip_via_creds():
    """Refresh path: build creds, force expiry, refresh, observe rotated tokens."""
    config = OAuthFlowConfig(client_id="client-test")
    transport = httpx.MockTransport(_exchange_handler())

    # Build credentials by running a full flow once.
    browser = _StubBrowser()
    creds = authorize(
        config, open_browser=browser, transport=transport, callback_timeout=5.0,
    )

    # Force expiry to fire the refresh path.
    from datetime import datetime, timedelta, timezone
    creds.expiry = datetime.now(timezone.utc) - timedelta(seconds=10)
    creds.refresh_if_needed()
    assert creds.access_token == "ya29.refreshed"
    assert creds.refresh_token == "rt-rotated"


def test_refresh_invalid_grant_raises():
    """Token endpoint returning 400 must surface OAuthInvalidGrantError."""

    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant"})

    transport = httpx.MockTransport(_handler)
    config = OAuthFlowConfig(client_id="client-test")

    # Construct creds manually with a refresher bound to the 400-returning transport.
    from novelwriter.ai.oauth import _build_refresher
    refresher = _build_refresher(config, transport=transport)
    from datetime import datetime, timedelta, timezone
    creds = OAuthCreds(
        access_token="stale",
        refresh_token="rt",
        expiry=datetime.now(timezone.utc) - timedelta(seconds=1),
        scope="s",
        refresher=refresher,
    )
    with pytest.raises(OAuthInvalidGrantError):
        creds.refresh_if_needed()


# ----- Revoke ---------------------------------------------------------------


def test_revoke_posts_refresh_token():
    seen: dict[str, str] = {}

    def _handler(request: httpx.Request) -> httpx.Response:
        body = urllib.parse.parse_qs(request.content.decode("utf-8"))
        seen["token"] = body["token"][0]
        return httpx.Response(200)

    transport = httpx.MockTransport(_handler)
    config = OAuthFlowConfig(client_id="client-test")
    from datetime import datetime, timedelta, timezone

    def _noop(c):
        return RefreshedCreds(
            access_token=c.access_token, refresh_token=c.refresh_token,
            expiry=c.expiry, scope=c.scope,
        )

    creds = OAuthCreds(
        access_token="a", refresh_token="rt-to-revoke",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="s", refresher=_noop,
    )
    assert revoke(creds, config, transport=transport) is True
    assert seen["token"] == "rt-to-revoke"


def test_revoke_non_200_returns_false():
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    transport = httpx.MockTransport(_handler)
    config = OAuthFlowConfig(client_id="client-test")
    from datetime import datetime, timedelta, timezone

    creds = OAuthCreds(
        access_token="a", refresh_token="rt",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="s",
        refresher=lambda c: RefreshedCreds(
            access_token=c.access_token, refresh_token=c.refresh_token,
            expiry=c.expiry, scope=c.scope,
        ),
    )
    assert revoke(creds, config, transport=transport) is False


# ----- Blob round-trip ------------------------------------------------------


def test_creds_blob_round_trip_preserves_headers():
    from datetime import datetime, timedelta, timezone

    creds = OAuthCreds(
        access_token="ya29.blob",
        refresh_token="rt-blob",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="gen-lang",
        refresher=lambda c: RefreshedCreds(
            access_token=c.access_token, refresh_token=c.refresh_token,
            expiry=c.expiry, scope=c.scope,
        ),
    )
    blob = creds_to_blob(creds)
    rehydrated = creds_from_blob(blob)
    assert rehydrated.headers() == {"Authorization": "Bearer ya29.blob"}
    assert rehydrated.scope == "gen-lang"
