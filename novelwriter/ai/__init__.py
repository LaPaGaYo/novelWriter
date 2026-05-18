"""
plotwright fork — AI substrate
==============================

Privacy-first, opt-in AI features for the plotwright fork. Every feature is off
by default; outbound network is blocked unless `AIConfig.enabled` is True AND
the per-feature flag is True. See `docs/ai/architecture.md` and
`docs/ai/privacy.md` for the contract.

This package is the only place in the fork that ever talks to a model. All
egress is funneled through `novelwriter.ai.transport` so a single CI test can
verify the privacy promise.

Sprint 2 extends the substrate with real cloud providers (Ollama, Anthropic,
Gemini), the Auth strategy abstraction, OAuth, and OS keychain backing.
Concrete provider classes (`OllamaProvider`, `AnthropicProvider`,
`GeminiProvider`) are intentionally NOT re-exported here so importing
`novelwriter.ai` does not pull their SDKs into `sys.modules`. Use
`novelwriter.ai.provider.make_provider("anthropic")` to instantiate by name.
"""
from __future__ import annotations

from novelwriter.ai.auth import (
    ApiKeyAuth,
    Auth,
    AuthMode,
    NoAuth,
    OAuthCreds,
    OAuthInvalidGrantError,
    RefreshedCreds,
)
from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import AIError, NetworkGate, PrivacyGatingError
from novelwriter.ai.provider.base import (
    Provider,
    ProviderDependencyError,
    ProviderError,
    ProviderResponse,
)
from novelwriter.ai.provider.mock import MockProvider
from novelwriter.ai.provider.registry import available_providers, make_provider
from novelwriter.ai.staging import StagedRewrite, stage
from novelwriter.ai.tokens import estimate_tokens

__all__ = [
    "AIConfig",
    "AIError",
    "AIFeature",
    "ApiKeyAuth",
    "Auth",
    "AuthMode",
    "MockProvider",
    "NetworkGate",
    "NoAuth",
    "OAuthCreds",
    "OAuthInvalidGrantError",
    "PrivacyGatingError",
    "Provider",
    "ProviderDependencyError",
    "ProviderError",
    "ProviderResponse",
    "RefreshedCreds",
    "StagedRewrite",
    "available_providers",
    "estimate_tokens",
    "make_provider",
    "stage",
]
