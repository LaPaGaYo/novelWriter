"""
plotwright fork — Keychain OAuth round-trip (SC-15)
===================================================

Covers the OAuth-blob get/put/delete surface using `FakeKeyStore`. The real
`OSKeyChainStore` is verified separately in `test_keychain_oauth_integration.py`
(intentionally omitted from CI; runs only on a developer machine with the
real OS keychain available).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from novelwriter.ai.auth import OAuthCreds, OAuthInvalidGrantError, RefreshedCreds
from novelwriter.ai.oauth import creds_from_blob, creds_to_blob

from tests.fixtures.fake_keystore import FakeKeyStore


def _make_creds(access: str = "access-1") -> OAuthCreds:
    def _refresher(_c: OAuthCreds) -> RefreshedCreds:
        return RefreshedCreds(
            access_token="rotated",
            refresh_token="rotated-rt",
            expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            scope="test-scope",
        )

    return OAuthCreds(
        access_token=access,
        refresh_token="refresh-1",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="test-scope",
        refresher=_refresher,
    )


def test_put_then_get_round_trips_blob():
    store = FakeKeyStore()
    creds = _make_creds()
    store.put_oauth("gemini", creds_to_blob(creds))

    blob = store.get_oauth("gemini")
    assert isinstance(blob, dict)
    assert blob["access_token"] == "access-1"
    assert blob["refresh_token"] == "refresh-1"
    assert "expiry" in blob
    assert blob["scope"] == "test-scope"


def test_get_missing_returns_none():
    store = FakeKeyStore()
    assert store.get_oauth("nope") is None


def test_blob_is_atomic_replace_not_merge():
    """Writing a partial blob must replace, never merge, to avoid mixed creds."""
    store = FakeKeyStore()
    store.put_oauth("gemini", {"access_token": "a", "refresh_token": "r"})
    store.put_oauth("gemini", {"access_token": "b"})  # no refresh_token

    after = store.get_oauth("gemini")
    assert after == {"access_token": "b"}, (
        "Atomic replace contract: a second put must overwrite, not patch"
    )


def test_delete_removes_blob():
    store = FakeKeyStore()
    store.put_oauth("gemini", {"access_token": "a"})
    store.delete_oauth("gemini")
    assert store.get_oauth("gemini") is None


def test_delete_missing_blob_is_noop():
    store = FakeKeyStore()
    # Must not raise.
    store.delete_oauth("never-stored")


def test_get_returns_copy_not_reference():
    """Caller mutation must not corrupt the stored blob."""
    store = FakeKeyStore()
    store.put_oauth("gemini", {"access_token": "a"})
    returned = store.get_oauth("gemini")
    assert returned is not None
    returned["access_token"] = "tampered"
    fresh = store.get_oauth("gemini")
    assert fresh == {"access_token": "a"}, "stored blob must be immutable to callers"


def test_full_round_trip_via_creds_blob():
    """End-to-end: build creds -> serialize -> store -> reload -> use headers."""
    store = FakeKeyStore()
    original = _make_creds("access-rt")
    store.put_oauth("gemini", creds_to_blob(original))

    rehydrated = creds_from_blob(store.get_oauth("gemini") or {})
    assert rehydrated.headers() == {"Authorization": "Bearer access-rt"}
    assert rehydrated.refresh_token == "refresh-1"
    assert rehydrated.scope == "test-scope"


def test_rehydrated_creds_refuse_to_refresh_without_config():
    """Safety: an OAuth blob loaded without a config cannot refresh silently."""
    store = FakeKeyStore()
    original = _make_creds()
    store.put_oauth("gemini", creds_to_blob(original))

    rehydrated = creds_from_blob(store.get_oauth("gemini") or {})
    # Force expiry so refresh_if_needed would normally fire.
    rehydrated.expiry = datetime.now(timezone.utc) - timedelta(seconds=10)
    with pytest.raises(OAuthInvalidGrantError):
        rehydrated.refresh_if_needed()
