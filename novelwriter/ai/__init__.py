"""
plotwright fork — AI substrate
==============================

Privacy-first, opt-in AI features for the plotwright fork. Every feature is off
by default; outbound network is blocked unless `AIConfig.enabled` is True AND
the per-feature flag is True. See `docs/ai/architecture.md` and
`docs/ai/privacy.md` for the contract.

This package is the only place in the fork that ever talks to a model. All
egress is funneled through `novelwriter.ai.network` so a single CI test can
verify the privacy promise.

Sprint 1 ships only the substrate (provider ABC, MockProvider, config,
gating, status bar widget, AI Preferences pane). Real Ollama / cloud
providers and the two AI features land in later sprints.
"""
from __future__ import annotations

from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import AIError, NetworkGate, PrivacyGatingError
from novelwriter.ai.provider.base import Provider, ProviderError, ProviderResponse
from novelwriter.ai.provider.mock import MockProvider
from novelwriter.ai.staging import StagedRewrite
from novelwriter.ai.tokens import estimate_tokens

__all__ = [
    "AIConfig",
    "AIError",
    "AIFeature",
    "MockProvider",
    "NetworkGate",
    "PrivacyGatingError",
    "Provider",
    "ProviderError",
    "ProviderResponse",
    "StagedRewrite",
    "estimate_tokens",
]
