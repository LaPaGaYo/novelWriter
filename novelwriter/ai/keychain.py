"""
Plotwright – AI keychain interface
==================================

Sprint 1 ships the *interface only*. Real backends (OS keychain on macOS,
DPAPI on Windows, libsecret on Linux) land in Sprint 2 alongside the cloud
provider implementations that actually need stored credentials.

The interface is deliberately small: ``get`` / ``set`` / ``delete`` keyed by
``(provider_id, account)``. Anything beyond that — rotation, expiry, sync —
is out of scope for v1.

Privacy contract: cloud API keys MUST never be written to disk in plaintext.
The Sprint 6 verification criterion ``privacy-keychain-never-plaintext``
enforces this with a grep + integration test once real backends ship.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class Keychain(ABC):
    """Abstract keychain backend.

    Sprint 1 has no concrete implementation. Sprint 2 will add at least one
    OS-native backend and one in-memory backend (for tests).
    """

    @abstractmethod
    def get(self, provider_id: str, account: str) -> str | None:
        """Return the stored secret, or ``None`` if absent."""

    @abstractmethod
    def set(self, provider_id: str, account: str, secret: str) -> None:
        """Store a secret. Must never persist plaintext to disk."""

    @abstractmethod
    def delete(self, provider_id: str, account: str) -> None:
        """Remove a stored secret. No-op if absent."""
