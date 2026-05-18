"""
plotwright fork — In-memory KeyStore for tests
==============================================

`FakeKeyStore` satisfies the `KeyStore` Protocol structurally without
touching the real OS keychain. Used by every test that needs to exercise
keychain-dependent code paths (`test_keychain_oauth.py`, the provider
registry, the OAuth round-trip).

The implementation is deliberately the simplest dict-backed thing that
satisfies the Protocol. If a future test needs to simulate keychain
failure (e.g. `KeychainUnavailableError`), it can subclass and override.
"""
from __future__ import annotations


class FakeKeyStore:
    """In-memory KeyStore for tests."""

    def __init__(self) -> None:
        self._secrets: dict[str, str] = {}
        self._oauth_blobs: dict[str, dict] = {}

    # API-key surface

    def get(self, provider_id: str) -> str | None:
        return self._secrets.get(provider_id)

    def put(self, provider_id: str, key: str) -> None:
        self._secrets[provider_id] = key

    def delete(self, provider_id: str) -> None:
        self._secrets.pop(provider_id, None)

    # OAuth blob surface

    def get_oauth(self, provider_id: str) -> dict | None:
        blob = self._oauth_blobs.get(provider_id)
        # Return a copy so the caller cannot mutate the stored state without
        # going through `put_oauth`.
        return dict(blob) if blob is not None else None

    def put_oauth(self, provider_id: str, blob: dict) -> None:
        self._oauth_blobs[provider_id] = dict(blob)

    def delete_oauth(self, provider_id: str) -> None:
        self._oauth_blobs.pop(provider_id, None)
