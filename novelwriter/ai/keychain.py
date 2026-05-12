"""
plotwright fork — API Key Storage (interface only in Sprint 1)
==============================================================

Cloud providers need API keys. The DESIGN.md privacy contract requires keys
NEVER live in plaintext on disk. Sprint 1 ships only the interface so the
provider abstraction can name its dependency. Real OS-keychain backends
(macOS Keychain, Windows Credential Manager, libsecret on Linux) land in
Sprint 2 with the cloud provider implementations.
"""
from __future__ import annotations

from typing import Protocol


class KeyStore(Protocol):
    """Read/write API keys for cloud providers, never in plaintext on disk."""

    def get(self, provider_id: str) -> str | None:
        """Return the stored API key for a provider, or None if not set."""
        ...

    def put(self, provider_id: str, key: str) -> None:
        """Store an API key for a provider. Implementation MUST use the OS keychain."""
        ...

    def delete(self, provider_id: str) -> None:
        """Remove a stored API key for a provider."""
        ...


class _MissingKeyStore:
    """Placeholder KeyStore that refuses every operation.

    This is what the substrate ships with in Sprint 1. Cloud providers are not
    available yet, so any attempt to reach a real keystore is a programming
    error. Replaced in Sprint 2 by `OSKeyChainStore`.
    """

    def get(self, provider_id: str) -> str | None:
        raise NotImplementedError(
            f"Real keystore not available until Sprint 2; cannot load key "
            f"for {provider_id!r}",
        )

    def put(self, provider_id: str, key: str) -> None:
        raise NotImplementedError(
            f"Real keystore not available until Sprint 2; cannot save key "
            f"for {provider_id!r}",
        )

    def delete(self, provider_id: str) -> None:
        raise NotImplementedError(
            f"Real keystore not available until Sprint 2; cannot delete key "
            f"for {provider_id!r}",
        )


def default_keystore() -> KeyStore:
    """Return the default keystore for this platform.

    Sprint 1: returns a placeholder. Sprint 2 will dispatch on platform.
    """
    return _MissingKeyStore()
