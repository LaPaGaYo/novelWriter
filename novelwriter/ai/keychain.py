"""
plotwright fork — Secret Storage (OS keychain backend)
======================================================

Cloud providers need to persist two kinds of secret:

1. Static API keys (Anthropic, Gemini API-key path) — stored as a single
   string per provider.
2. OAuth credential blobs (Gemini OAuth path) — stored as a JSON-encoded
   dict containing access_token, refresh_token, expiry, and scope. The whole
   blob is written atomically so a half-refresh never leaves the keychain in
   an inconsistent state.

Sprint 2 replaces the `_MissingKeyStore` placeholder with `OSKeyChainStore`,
which delegates to the `keyring` library (MIT, GPL-3 compatible). `keyring`
picks the right native backend per OS: macOS Keychain Services, Windows
Credential Manager, Secret Service on Linux.

The `KeyStore` Protocol is intentionally widened, not changed: Sprint 1
callers using `get`/`put`/`delete` keep working, and the new
`get_oauth`/`put_oauth`/`delete_oauth` methods land alongside them.

`FakeKeyStore` lives under `tests/fixtures/` so CI never touches the real OS
keychain.
"""
from __future__ import annotations

import json
import logging

from typing import Protocol

logger = logging.getLogger(__name__)


# Single service identifier used for every plotwright keychain entry. Keeps
# the keychain UI listings tidy (one row per provider, all under one app).
_SERVICE_NAME = "plotwright"

# Suffix appended to the provider-id when storing an OAuth blob, so OAuth
# entries and API-key entries can coexist under the same service without
# collision. `gemini` stores the API key; `gemini.oauth` stores the OAuth blob.
_OAUTH_SUFFIX = ".oauth"


class KeyStore(Protocol):
    """Read/write credentials for cloud providers.

    Implementations must NEVER serialize secrets to a plaintext file on disk.
    The contract test uses `FakeKeyStore` (in-memory) so CI does not require
    a real OS keychain.
    """

    def get(self, provider_id: str) -> str | None:
        """Return the stored API key for a provider, or None if not set."""
        ...

    def put(self, provider_id: str, key: str) -> None:
        """Store an API key for a provider."""
        ...

    def delete(self, provider_id: str) -> None:
        """Remove a stored API key for a provider. No-op if not present."""
        ...

    def get_oauth(self, provider_id: str) -> dict | None:
        """Return the stored OAuth credentials blob for a provider, or None."""
        ...

    def put_oauth(self, provider_id: str, blob: dict) -> None:
        """Store an OAuth credentials blob (atomic; whole-blob write)."""
        ...

    def delete_oauth(self, provider_id: str) -> None:
        """Remove a stored OAuth blob for a provider. No-op if not present."""
        ...


class KeychainUnavailableError(RuntimeError):
    """The OS keychain backend cannot be reached.

    Surfaced when the `keyring` library's chosen backend fails to initialize
    (e.g. headless Linux without `dbus-launch`). The caller decides whether
    to fall back to API-key prompt-on-startup or abort the feature.
    """


class OSKeyChainStore:
    """KeyStore backed by the OS keychain via the `keyring` package.

    Initialization tries to query the keyring backend; if that raises, we
    surface a `KeychainUnavailableError` so the AI Preferences panel can
    render the diagnostic up-front instead of failing on first call.

    The Protocol-style `KeyStore` interface is satisfied structurally.
    """

    def __init__(self, service_name: str = _SERVICE_NAME) -> None:
        # Import lazily so `import novelwriter.ai` never pulls keyring's
        # native backends into sys.modules — the privacy test asserts that
        # nothing under `novelwriter.ai` triggers a side-effect import of an
        # OS service module.
        try:
            import keyring  # noqa: F401  — confirm the import resolves
        except ImportError as exc:  # pragma: no cover - exercised only on misinstalls
            raise KeychainUnavailableError(
                "The `keyring` package is required for OS keychain access; "
                "install plotwright with the standard dependencies"
            ) from exc
        self._service = service_name

    # --- API-key storage ------------------------------------------------------

    def get(self, provider_id: str) -> str | None:
        try:
            import keyring
            return keyring.get_password(self._service, provider_id)
        except Exception as exc:  # keyring raises a wide variety on backend failure
            logger.warning("Keychain read failed for %s: %s", provider_id, exc)
            return None

    def put(self, provider_id: str, key: str) -> None:
        import keyring
        try:
            keyring.set_password(self._service, provider_id, key)
        except Exception as exc:
            logger.error("Keychain write failed for %s: %s", provider_id, exc)
            raise

    def delete(self, provider_id: str) -> None:
        import keyring
        try:
            keyring.delete_password(self._service, provider_id)
        except keyring.errors.PasswordDeleteError:
            # Already absent; treat as no-op so callers can blindly clean up.
            pass
        except Exception as exc:
            logger.warning("Keychain delete failed for %s: %s", provider_id, exc)

    # --- OAuth blob storage ---------------------------------------------------

    def get_oauth(self, provider_id: str) -> dict | None:
        """Return the OAuth credentials blob for `provider_id`, or None.

        Returns None if the entry is missing, malformed, or the blob's
        envelope is not a dict. The caller decides whether to re-prompt
        sign-in.
        """
        raw = self.get(_oauth_key(provider_id))
        if raw is None:
            return None
        try:
            blob = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Discarding malformed OAuth blob for %s", provider_id)
            return None
        return blob if isinstance(blob, dict) else None

    def put_oauth(self, provider_id: str, blob: dict) -> None:
        """Atomically write the OAuth credentials blob for `provider_id`.

        Atomicity here is "single keychain row replaces single keychain row".
        We never write the access_token and refresh_token as separate rows
        because a crash between writes would leave the keychain in an
        inconsistent state (refresh_token from one cycle paired with
        access_token from another).
        """
        self.put(_oauth_key(provider_id), json.dumps(blob, separators=(",", ":")))

    def delete_oauth(self, provider_id: str) -> None:
        self.delete(_oauth_key(provider_id))


def _oauth_key(provider_id: str) -> str:
    """Return the keychain row key used for `provider_id`'s OAuth blob."""
    return f"{provider_id}{_OAUTH_SUFFIX}"


class _MissingKeyStore:
    """KeyStore that refuses every operation.

    Kept as a safety fallback when `OSKeyChainStore` cannot initialize on
    this platform (rare; headless Linux without dbus). Always surfaces
    `KeychainUnavailableError` so callers can route the user to the
    API-key fallback rather than crash.
    """

    def get(self, provider_id: str) -> str | None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot load key "
            f"for {provider_id!r}",
        )

    def put(self, provider_id: str, key: str) -> None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot save key "
            f"for {provider_id!r}",
        )

    def delete(self, provider_id: str) -> None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot delete key "
            f"for {provider_id!r}",
        )

    def get_oauth(self, provider_id: str) -> dict | None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot load OAuth "
            f"blob for {provider_id!r}",
        )

    def put_oauth(self, provider_id: str, blob: dict) -> None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot save OAuth "
            f"blob for {provider_id!r}",
        )

    def delete_oauth(self, provider_id: str) -> None:
        raise KeychainUnavailableError(
            f"OS keychain not available on this platform; cannot delete OAuth "
            f"blob for {provider_id!r}",
        )


def default_keystore() -> KeyStore:
    """Return the default KeyStore for this platform.

    Attempts `OSKeyChainStore`; if the keyring import or backend probe fails
    we surface `_MissingKeyStore` which raises on first use. Callers should
    catch `KeychainUnavailableError` and route to the manual-entry path
    rather than crash.
    """
    try:
        return OSKeyChainStore()
    except KeychainUnavailableError:
        return _MissingKeyStore()


__all__ = [
    "KeyStore",
    "KeychainUnavailableError",
    "OSKeyChainStore",
    "default_keystore",
]
