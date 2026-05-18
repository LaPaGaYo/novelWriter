"""
plotwright fork — Provider contract tests
=========================================

Every concrete Provider implementation must pass this same test suite. The
contract guarantees uniform behavior across local and cloud backends so
features can rely on the abstraction without per-provider branching.

Sprint 2 parametrizes over MockProvider + OllamaProvider + AnthropicProvider +
GeminiProvider. Cloud providers use `httpx.MockTransport` so no real network
is touched. The local Ollama path also goes through `MockTransport` because
this is a unit-level contract test, not a Ollama-daemon smoke test (the
real-Ollama smoke runs in /qa).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx
import pytest

from novelwriter.ai.auth import ApiKeyAuth, OAuthCreds, RefreshedCreds
from novelwriter.ai.provider.anthropic import AnthropicProvider
from novelwriter.ai.provider.base import Provider, ProviderResponse
from novelwriter.ai.provider.gemini import GeminiProvider
from novelwriter.ai.provider.mock import MockProvider
from novelwriter.ai.provider.ollama import OllamaProvider


# ---- Mock transports ------------------------------------------------------


def _ollama_transport() -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/generate":
            return httpx.Response(200, json={"response": "OLLAMA_OK"})
        if request.url.path == "/api/tags":
            return httpx.Response(200, json={"models": []})
        return httpx.Response(404)
    return httpx.MockTransport(_handler)


def _anthropic_transport() -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/messages":
            return httpx.Response(
                200,
                json={
                    "content": [{"type": "text", "text": "ANTHROPIC_OK"}],
                    "usage": {"input_tokens": 1, "output_tokens": 1},
                },
            )
        return httpx.Response(404)
    return httpx.MockTransport(_handler)


def _gemini_transport() -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        if "generateContent" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": "GEMINI_OK"}]}},
                    ],
                },
            )
        return httpx.Response(404)
    return httpx.MockTransport(_handler)


def _stub_oauth_creds() -> OAuthCreds:
    def _refresher(_c: OAuthCreds) -> RefreshedCreds:  # pragma: no cover - never fires
        return RefreshedCreds(
            access_token="x", refresh_token="x",
            expiry=datetime.now(timezone.utc) + timedelta(hours=1),
            scope="x",
        )
    return OAuthCreds(
        access_token="ya29.test",
        refresh_token="rt",
        expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        scope="test",
        refresher=_refresher,
    )


def all_providers() -> list[Provider]:
    """Return every concrete Provider for contract testing.

    Cloud providers use `httpx.MockTransport` so no real network is touched.
    """
    return [
        MockProvider(),
        OllamaProvider(model="llama3.1", transport=_ollama_transport()),
        AnthropicProvider(
            api_key="sk-test",
            model="claude-sonnet-4-5",
            transport=_anthropic_transport(),
        ),
        GeminiProvider(
            auth=ApiKeyAuth(api_key="api-test", header_name="x-goog-api-key"),
            model="gemini-2.5-flash",
            transport=_gemini_transport(),
        ),
    ]


@pytest.mark.parametrize("provider", all_providers(), ids=lambda p: p.name)
class TestProviderContract:
    """Run the same checks against every concrete Provider."""

    def test_name_is_nonempty_str(self, provider: Provider):
        assert isinstance(provider.name, str)
        assert provider.name, "Provider.name must be a non-empty string"

    def test_is_local_returns_bool(self, provider: Provider):
        assert isinstance(provider.is_local, bool)

    def test_estimate_tokens_returns_int(self, provider: Provider):
        n = provider.estimate_tokens("a sample prompt")
        assert isinstance(n, int)
        assert n >= 0

    def test_estimate_tokens_empty_returns_zero(self, provider: Provider):
        assert provider.estimate_tokens("") == 0

    def test_health_check_returns_bool(self, provider: Provider):
        assert isinstance(provider.health_check(), bool)

    def test_generate_returns_response(self, provider: Provider):
        response = provider.generate("hello world")
        assert isinstance(response, ProviderResponse)
        assert isinstance(response.text, str)
        assert response.provider_name == provider.name
        assert response.is_local == provider.is_local
        assert response.estimated_tokens_in >= 0
        assert response.estimated_tokens_out >= 0

    def test_auth_is_present_on_every_provider(self, provider: Provider):
        """SC-13 widening: every provider exposes an Auth strategy with a stable mode."""
        auth = provider.auth
        assert auth is not None
        assert auth.mode in ("none", "api_key", "oauth")


# Separate Gemini-OAuth case so the auth-mode assertion above covers all four
# modes. OAuth providers behave identically to API-key providers from the
# contract's perspective, so we run them through a subset of the same suite.
def test_gemini_oauth_satisfies_contract():
    provider = GeminiProvider(
        auth=_stub_oauth_creds(),
        model="gemini-2.5-flash",
        transport=_gemini_transport(),
    )
    response = provider.generate("hello")
    assert isinstance(response, ProviderResponse)
    assert response.text == "GEMINI_OK"
    assert provider.auth.mode == "oauth"
