"""
plotwright fork — Offline provider construction (SC-16)
=======================================================

Every cloud provider must be constructible inside `network_sentinel()` without
any socket activity. This is the lazy-init contract: providers MUST NOT make a
network call (or even open a connection) until `generate()` / `health_check()`
fires.

Privacy guarantee: a user who never clicks a feature toggle never triggers
network egress, even if every provider is wired into `AIConfig`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from novelwriter.ai.auth import ApiKeyAuth, OAuthCreds, RefreshedCreds
from novelwriter.ai.provider.anthropic import AnthropicProvider
from novelwriter.ai.provider.gemini import GeminiProvider
from novelwriter.ai.provider.mock import MockProvider
from novelwriter.ai.provider.ollama import OllamaProvider
from tests.test_ai.test_privacy import network_sentinel


def _stub_oauth_creds() -> OAuthCreds:
    def _refresh(_c):  # pragma: no cover - never triggered in this suite
        return RefreshedCreds(
            access_token="x",
            refresh_token="x",
            expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            scope="x",
        )
    return OAuthCreds(
        access_token="ya29.test",
        refresh_token="rt",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="test",
        refresher=_refresh,
    )


def test_mock_provider_constructs_offline():
    with network_sentinel() as calls:
        MockProvider()
    assert calls == []


def test_ollama_provider_constructs_offline():
    with network_sentinel() as calls:
        OllamaProvider(base_url="http://127.0.0.1:11434", model="llama3.1")
    assert calls == []


def test_anthropic_provider_constructs_offline():
    with network_sentinel() as calls:
        AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-5")
    assert calls == []


def test_gemini_provider_constructs_offline_with_api_key():
    with network_sentinel() as calls:
        GeminiProvider(
            auth=ApiKeyAuth(api_key="api-test", header_name="x-goog-api-key"),
            model="gemini-2.5-flash",
        )
    assert calls == []


def test_gemini_provider_constructs_offline_with_oauth():
    with network_sentinel() as calls:
        GeminiProvider(auth=_stub_oauth_creds(), model="gemini-2.5-flash")
    assert calls == []


def test_cloud_clients_built_lazily_only_on_first_request():
    """Construction does not build the httpx.Client; the first generate() does."""
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-5")
    # Internal: _client is None until generate() / health_check() fires.
    assert provider._client is None  # noqa: SLF001 - lifecycle check


def test_anthropic_health_check_is_offline_when_only_api_key_present():
    """Sprint 2's health_check uses an in-memory signal, not a network call."""
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-5")
    with network_sentinel() as calls:
        ok = provider.health_check()
    assert ok is True
    assert calls == []


def test_gemini_health_check_is_offline_when_creds_present():
    provider = GeminiProvider(
        auth=ApiKeyAuth(api_key="api-test", header_name="x-goog-api-key"),
        model="gemini-2.5-flash",
    )
    with network_sentinel() as calls:
        ok = provider.health_check()
    assert ok is True
    assert calls == []


def test_anthropic_provider_carries_apikey_auth():
    provider = AnthropicProvider(api_key="sk-test", model="claude-sonnet-4-5")
    assert provider.auth.mode == "api_key"
    headers = provider.auth.headers()
    assert headers == {"x-api-key": "sk-test"}


def test_gemini_oauth_provider_carries_bearer():
    provider = GeminiProvider(auth=_stub_oauth_creds(), model="gemini-2.5-flash")
    assert provider.auth.mode == "oauth"
    assert provider.auth.headers().get("Authorization", "").startswith("Bearer ")
