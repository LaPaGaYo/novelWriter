"""
plotwright fork — Provider abstraction
======================================

Every AI provider (local Ollama, cloud Anthropic/OpenAI/Gemini, mock for tests)
implements the same `Provider` ABC. New providers can be added without touching
feature code.
"""
from __future__ import annotations

from novelwriter.ai.provider.base import Provider, ProviderError, ProviderResponse
from novelwriter.ai.provider.mock import MockProvider

__all__ = [
    "MockProvider",
    "Provider",
    "ProviderError",
    "ProviderResponse",
]
