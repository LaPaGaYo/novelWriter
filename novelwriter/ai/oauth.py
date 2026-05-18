"""
plotwright fork — Browser-loopback OAuth (PKCE)
================================================

The Sprint 2 release lede: "Sign in with Google" sign-in for Gemini in 30
seconds, no credit card. This module implements RFC 7636 (PKCE) over
RFC 8252 (OAuth for native apps via loopback redirect).

Flow:

1. Generate a PKCE code verifier + challenge, plus a 256-bit state nonce
   for CSRF protection.
2. Bind a localhost listener on `127.0.0.1` to a random free port (the
   listener decides the port at bind time so we never clash with an
   existing process; this is what `socket.bind(("127.0.0.1", 0))` does).
3. Open the system browser at Google's `/o/oauth2/v2/auth` URL with
   `redirect_uri=http://127.0.0.1:<port>/callback`, the PKCE challenge,
   the scope, and the state nonce.
4. The user approves. Google redirects the user's browser to our loopback
   URL with a `code` query parameter. The listener captures it, verifies
   the state nonce matches, and shuts down.
5. We exchange the code (and verifier) for an access + refresh token at
   Google's `/token` endpoint.
6. We return an `OAuthCreds` carrying a refresher closure that knows how to
   exchange a refresh token for a new access token. The keychain serializes
   the blob (sans closure) for restart-survival; `creds_from_blob`
   rehydrates with the same refresher.

The whole thing runs on `transport.make_client` so the privacy contract
holds: every HTTP call goes through the single egress, headers included,
test injection via `httpx.MockTransport` supported.

`OAuthInvalidGrantError` is raised on refresh failure; the AI Preferences
panel catches it and surfaces a re-auth modal.
"""
from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import socket
import threading

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlencode, urlparse

from novelwriter.ai.auth import (
    OAuthCreds,
    OAuthInvalidGrantError,
    RefreshedCreds,
)
from novelwriter.ai.provider.gemini import GEMINI_SCOPE
from novelwriter.ai.transport import make_client


logger = logging.getLogger(__name__)


# Google OAuth endpoints. Pinned at module level so the test injector can
# monkey-patch (or pass a `transport=MockTransport`) to redirect to a stub.
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Default loopback callback wait. 5 minutes is generous; the design contract
# says "We'll keep waiting" so don't be aggressive about timeout.
_DEFAULT_CALLBACK_TIMEOUT = 300.0


@dataclass(frozen=True, slots=True)
class OAuthFlowConfig:
    """Static config for a PKCE OAuth flow.

    `client_id` is the OAuth client id registered with the provider.
    `scope` is the OAuth scope; for Gemini this is the `GEMINI_SCOPE`
    constant. `auth_url` / `token_url` are pinned per provider.
    """

    client_id: str
    scope: str = GEMINI_SCOPE
    auth_url: str = GOOGLE_AUTH_URL
    token_url: str = GOOGLE_TOKEN_URL
    revoke_url: str = GOOGLE_REVOKE_URL


def _pkce_pair() -> tuple[str, str]:
    """Generate a (verifier, challenge) PKCE pair.

    Verifier is 32 random bytes base64url-encoded (43 chars). Challenge is
    `base64url(sha256(verifier))`. Per RFC 7636 we use S256, not plain.
    """
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")
    challenge_digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(challenge_digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _free_loopback_port() -> int:
    """Return a free localhost port and release the binding.

    The kernel may reuse the port immediately, but in practice (and per RFC
    8252) the OAuth flow is fast enough that no other process steals it.
    Race-windows are acceptable here.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@dataclass
class _CallbackResult:
    """Single-shot container for the loopback handler's parsed query string."""

    code: str | None = None
    state: str | None = None
    error: str | None = None


def _build_authorize_url(
    config: OAuthFlowConfig,
    *,
    challenge: str,
    state: str,
    redirect_uri: str,
) -> str:
    params = {
        "response_type": "code",
        "client_id": config.client_id,
        "redirect_uri": redirect_uri,
        "scope": config.scope,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{config.auth_url}?{urlencode(params)}"


def _make_handler(result: _CallbackResult, done_event: threading.Event):
    """Build a one-shot HTTP request handler that fills `result` and signals done."""

    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401
            # Silence the default stderr access log; this is a desktop app,
            # not a server.
            return

        def do_GET(self) -> None:  # noqa: N802 - HTTP framework dispatch
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            result.code = (query.get("code") or [None])[0]
            result.state = (query.get("state") or [None])[0]
            result.error = (query.get("error") or [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            # The browser tab sees this; copy is deliberately plain and
            # offers no AI-magic language.
            self.wfile.write(
                b"plotwright sign-in received. You can close this tab.",
            )
            done_event.set()

    return _Handler


def _run_callback_listener(
    port: int,
    *,
    timeout: float = _DEFAULT_CALLBACK_TIMEOUT,
) -> _CallbackResult:
    """Bind a one-shot HTTP listener on `127.0.0.1:port` and wait for the redirect.

    Raises `TimeoutError` if `timeout` seconds elapse without a callback.
    The handler thread is daemonic so process exit is never blocked by a
    stuck OAuth flow.
    """
    result = _CallbackResult()
    done_event = threading.Event()
    handler_cls = _make_handler(result, done_event)
    server = HTTPServer(("127.0.0.1", port), handler_cls)

    serve_thread = threading.Thread(
        target=server.serve_forever, name="oauth-loopback", daemon=True,
    )
    serve_thread.start()
    try:
        if not done_event.wait(timeout=timeout):
            raise TimeoutError(
                f"OAuth callback not received within {timeout:.0f} seconds",
            )
    finally:
        server.shutdown()
        server.server_close()
        serve_thread.join(timeout=1.0)
    return result


def _exchange_code(
    config: OAuthFlowConfig,
    *,
    code: str,
    verifier: str,
    redirect_uri: str,
    transport: Any = None,
) -> dict[str, Any]:
    """Exchange a one-time auth code for an access + refresh token."""
    client = make_client(transport=transport)
    try:
        resp = client.post(
            config.token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": config.client_id,
                "redirect_uri": redirect_uri,
                "code_verifier": verifier,
            },
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        client.close()


def _build_refresher(
    config: OAuthFlowConfig,
    *,
    transport: Any = None,
) -> Callable[[OAuthCreds], RefreshedCreds]:
    """Build the refresher closure carried by `OAuthCreds`.

    The closure captures the OAuth client_id + token url so `OAuthCreds`
    itself stays SDK-free. The closure is excluded from `repr` on the
    dataclass so it never accidentally appears in a log.
    """

    def _refresh(creds: OAuthCreds) -> RefreshedCreds:
        client = make_client(transport=transport)
        try:
            resp = client.post(
                config.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": creds.refresh_token,
                    "client_id": config.client_id,
                },
            )
        finally:
            client.close()
        if resp.status_code in (400, 401):
            # Google returns 4xx with body `{"error": "invalid_grant"}`
            # when the refresh token has been revoked or rotated. Surface
            # the dedicated error class so the UI can route to re-auth.
            raise OAuthInvalidGrantError(
                f"OAuth refresh denied (status={resp.status_code}); re-auth required",
            )
        if resp.status_code >= 400:
            raise OAuthInvalidGrantError(
                f"OAuth refresh failed (status={resp.status_code})",
            )
        payload = resp.json()
        # Google often omits a new refresh_token on rotation; reuse the old
        # one in that case so persistence stays atomic.
        return RefreshedCreds(
            access_token=str(payload["access_token"]),
            refresh_token=str(payload.get("refresh_token") or creds.refresh_token),
            expiry=_expiry_from_payload(payload),
            scope=str(payload.get("scope") or creds.scope),
        )

    return _refresh


def _expiry_from_payload(payload: dict[str, Any]) -> datetime:
    """Compute an absolute expiry from a token endpoint payload.

    Google returns `expires_in` (seconds). We add a 5-second cushion so the
    REFRESH_WINDOW check is honored even when the local clock drifts a hair
    behind Google's.
    """
    expires_in = int(payload.get("expires_in", 0)) or 3600
    return datetime.now(timezone.utc) + timedelta(seconds=max(0, expires_in - 5))


def authorize(
    config: OAuthFlowConfig,
    *,
    open_browser: Callable[[str], Any] | None = None,
    transport: Any = None,
    callback_timeout: float = _DEFAULT_CALLBACK_TIMEOUT,
    listener_port: int | None = None,
) -> OAuthCreds:
    """Run a full PKCE flow and return ready-to-use `OAuthCreds`.

    `open_browser` is a single-arg callable that opens a URL in the user's
    browser. Defaults to `QDesktopServices.openUrl` when Qt is around, with
    a fallback to `webbrowser.open`. Tests pass a callable that simulates
    the browser making the loopback request itself.

    `transport` is forwarded to every HTTP call, so tests can use
    `httpx.MockTransport` to short-circuit Google's endpoints.

    `listener_port` is the loopback port. Defaults to a free port chosen at
    call time. Tests pass an explicit port so the redirect URL is
    predictable.

    Raises:
        OAuthInvalidGrantError: if Google returns an error code on either
            the authorize or token-exchange step.
        TimeoutError: if the callback never arrives within
            `callback_timeout` seconds.
        RuntimeError: if the state nonce mismatch indicates a CSRF attempt.
    """
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(32)
    port = listener_port or _free_loopback_port()
    redirect_uri = f"http://127.0.0.1:{port}/callback"

    auth_url = _build_authorize_url(
        config, challenge=challenge, state=state, redirect_uri=redirect_uri,
    )

    if open_browser is None:
        open_browser = _default_open_browser

    # Start the listener BEFORE opening the browser so a fast user never
    # hits a closed port.
    result_holder: list[_CallbackResult] = []
    listener_error: list[BaseException] = []

    def _run_listener() -> None:
        try:
            result_holder.append(_run_callback_listener(port, timeout=callback_timeout))
        except BaseException as exc:  # noqa: BLE001 - propagate to caller
            listener_error.append(exc)

    listener_thread = threading.Thread(target=_run_listener, name="oauth-wait", daemon=True)
    listener_thread.start()

    try:
        open_browser(auth_url)
    except Exception as exc:
        raise OAuthInvalidGrantError(f"Could not open browser: {exc}") from exc

    listener_thread.join(timeout=callback_timeout + 5.0)
    if listener_error:
        raise listener_error[0]
    if not result_holder:
        raise TimeoutError("OAuth listener exited without a result")

    result = result_holder[0]
    if result.error:
        raise OAuthInvalidGrantError(f"OAuth error from provider: {result.error}")
    if result.state != state:
        raise RuntimeError(
            "OAuth state mismatch — possible CSRF; aborting sign-in",
        )
    if not result.code:
        raise OAuthInvalidGrantError("OAuth callback missing 'code' parameter")

    token_payload = _exchange_code(
        config,
        code=result.code,
        verifier=verifier,
        redirect_uri=redirect_uri,
        transport=transport,
    )

    return OAuthCreds(
        access_token=str(token_payload["access_token"]),
        refresh_token=str(token_payload.get("refresh_token") or ""),
        expiry=_expiry_from_payload(token_payload),
        scope=str(token_payload.get("scope") or config.scope),
        refresher=_build_refresher(config, transport=transport),
    )


def revoke(creds: OAuthCreds, config: OAuthFlowConfig, *, transport: Any = None) -> bool:
    """Revoke the refresh token at the provider.

    Returns True on a 200 response; False otherwise. Failures are logged
    but never raised — revocation is best-effort and a stale refresh token
    on the provider side cannot be exploited without the local secret.
    """
    client = make_client(transport=transport)
    try:
        resp = client.post(
            config.revoke_url,
            data={"token": creds.refresh_token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return resp.status_code == 200
    except Exception as exc:
        logger.warning("OAuth revoke failed: %s", exc)
        return False
    finally:
        client.close()


def creds_to_blob(creds: OAuthCreds) -> dict[str, Any]:
    """Serialize `OAuthCreds` for keychain storage.

    The `refresher` callable is intentionally NOT serialized — it is
    rebuilt at load time via `creds_from_blob`. Storing only the data
    fields keeps the keychain blob portable and JSON-safe.
    """
    return {
        "access_token": creds.access_token,
        "refresh_token": creds.refresh_token,
        "expiry": creds.expiry.astimezone(timezone.utc).isoformat(),
        "scope": creds.scope,
    }


def creds_from_blob(
    blob: dict[str, Any],
    *,
    config: OAuthFlowConfig | None = None,
    transport: Any = None,
) -> OAuthCreds:
    """Rehydrate `OAuthCreds` from a keychain blob.

    `config` provides the client_id used by the refresher closure. Real
    callers (the Gemini factory in `provider/registry.py`) construct a
    Gemini-specific `OAuthFlowConfig` from the application's OAuth client
    id; tests pass a synthetic config.

    If `config` is None we build a refresher that refuses to run; this
    matches the safe-default posture for a credentials blob restored from
    keychain when no OAuth client is configured yet.
    """
    if config is None:
        def _no_config_refresher(_creds: OAuthCreds) -> RefreshedCreds:
            raise OAuthInvalidGrantError(
                "OAuth client config not provided; cannot refresh",
            )
        refresher: Callable[[OAuthCreds], RefreshedCreds] = _no_config_refresher
    else:
        refresher = _build_refresher(config, transport=transport)

    expiry = datetime.fromisoformat(str(blob["expiry"]))
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    return OAuthCreds(
        access_token=str(blob["access_token"]),
        refresh_token=str(blob["refresh_token"]),
        expiry=expiry,
        scope=str(blob.get("scope") or GEMINI_SCOPE),
        refresher=refresher,
    )


def _default_open_browser(url: str) -> None:
    """Open `url` in the user's system browser.

    Prefers `QDesktopServices.openUrl` when a `QGuiApplication` is alive so
    Qt's per-platform handling is honored. Falls back to `webbrowser.open`
    for headless or non-Qt callers.
    """
    try:
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices, QGuiApplication
        if QGuiApplication.instance() is not None:
            QDesktopServices.openUrl(QUrl(url))
            return
    except Exception:  # noqa: BLE001 - any Qt failure falls back
        pass
    import webbrowser
    webbrowser.open(url)


__all__ = [
    "GEMINI_SCOPE",
    "OAuthFlowConfig",
    "authorize",
    "creds_from_blob",
    "creds_to_blob",
    "revoke",
]
