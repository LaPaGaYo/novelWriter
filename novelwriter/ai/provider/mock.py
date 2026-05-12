"""
plotwright fork — MockProvider
==============================

Deterministic provider for tests. Never makes a network call. Returns
predictable transformations of the input prompt so tests can assert exact
output without depending on a real model.

This is the only provider Sprint 1 ships. Real Ollama and cloud providers
arrive in Sprint 2.
"""
from __future__ import annotations

from novelwriter.ai.provider.base import Provider, ProviderResponse
from novelwriter.ai.tokens import estimate_tokens


class MockProvider(Provider):
    """Deterministic in-process provider used by tests.

    The transformation is a simple uppercase reversal of the prompt's first
    line; this is intentionally absurd so it cannot be confused with a real
    model output during manual testing.
    """

    @property
    def name(self) -> str:
        return "mock"

    @property
    def is_local(self) -> bool:
        # Mock provider runs in-process; no network involved.
        return True

    def generate(self, prompt: str, **opts: object) -> ProviderResponse:
        first_line = prompt.splitlines()[0] if prompt else ""
        text = first_line.upper()[::-1] if first_line else ""
        return ProviderResponse(
            text=text,
            provider_name=self.name,
            is_local=self.is_local,
            estimated_tokens_in=estimate_tokens(prompt),
            estimated_tokens_out=estimate_tokens(text),
        )

    def estimate_tokens(self, text: str) -> int:
        return estimate_tokens(text)

    def health_check(self) -> bool:
        # Mock provider is always healthy by definition.
        return True
