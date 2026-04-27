"""
Plotwright – Provider Contract Tests (Sprint 1, gate item 3)
=============================================================

Every concrete :class:`Provider` must satisfy the same contract:

1. ``name`` is a non-empty string identifier.
2. ``is_local`` is a bool (drives privacy UX).
3. ``generate(prompt: str, **opts) -> str`` returns a string.
4. ``estimate_tokens(text: str) -> int`` returns a non-negative int.
5. ``health_check() -> bool`` returns a bool, with no network I/O of
   its own (Sprint 1 only verifies behaviour for the local mock).

Sprint 1 only ships :class:`MockProvider`. Sprint 2 will register real
providers (Ollama / Anthropic / OpenAI / Gemini) and they pick up these
same tests automatically by being added to :data:`PROVIDERS_UNDER_TEST`.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import pytest

from novelwriter.ai import MockProvider, Provider

# Each entry is a callable that returns a fresh provider instance. New
# providers in Sprint 2 register themselves here without touching the
# test bodies.
PROVIDERS_UNDER_TEST: list[tuple[str, callable]] = [
    ("MockProvider", MockProvider),
]


@pytest.fixture(params=PROVIDERS_UNDER_TEST, ids=lambda p: p[0])
def provider(request: pytest.FixtureRequest) -> Provider:
    _, factory = request.param
    return factory()


def test_provider_is_subclass(provider: Provider) -> None:
    assert isinstance(provider, Provider)


def test_provider_has_stable_identity(provider: Provider) -> None:
    assert isinstance(provider.name, str)
    assert provider.name.strip(), "name must not be empty"
    assert isinstance(provider.is_local, bool)


def test_provider_generate_returns_string(provider: Provider) -> None:
    out = provider.generate("the quick brown fox")
    assert isinstance(out, str)
    assert out, "generate() must not return an empty string"


def test_provider_generate_accepts_extra_options(provider: Provider) -> None:
    """Providers accept arbitrary opts so feature code can pass operation
    hints without a per-provider signature dance."""
    out = provider.generate("hello", operation="rewrite", temperature=0.0)
    assert isinstance(out, str)


def test_provider_estimate_tokens_returns_nonneg_int(provider: Provider) -> None:
    n = provider.estimate_tokens("hello world")
    assert isinstance(n, int)
    assert n >= 0
    # Sanity: non-empty strings should not estimate to zero tokens.
    assert n > 0


def test_provider_health_check_returns_bool(provider: Provider) -> None:
    h = provider.health_check()
    assert isinstance(h, bool)


def test_mock_provider_is_deterministic() -> None:
    """The mock must be deterministic — it underpins every other test."""
    p = MockProvider()
    assert p.generate("hi") == p.generate("hi")
    assert p.generate("hi", operation="rewrite") == "[mock-rewrite] hi"
    assert p.generate("hi", operation="expand") == "[mock-expand] hi hi"
