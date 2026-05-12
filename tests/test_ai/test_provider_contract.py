"""
plotwright fork — Provider contract tests
=========================================

Every concrete Provider implementation must pass this same test suite. The
contract guarantees uniform behavior across local and cloud backends so
features can rely on the abstraction without per-provider branching.

Sprint 1 only ships MockProvider; this suite parametrizes over a list that
will grow as Ollama/Anthropic/OpenAI/Gemini providers land in Sprint 2.
"""
from __future__ import annotations

import pytest

from novelwriter.ai.provider.base import Provider, ProviderResponse
from novelwriter.ai.provider.mock import MockProvider


def all_providers() -> list[Provider]:
    """Return every concrete Provider for contract testing.

    Sprint 2 will append OllamaProvider, AnthropicProvider, OpenAIProvider,
    GeminiProvider when they exist. Cloud providers will gate behind
    `pytest.skip` if no API key is configured in the test env.
    """
    return [MockProvider()]


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
