"""
plotwright fork — Provider abstraction
======================================

Every AI provider (local Ollama, cloud Anthropic/OpenAI/Gemini, mock for tests)
implements the same `Provider` ABC. New providers can be added without touching
feature code.

Concrete provider classes are NOT re-exported here. Importing them at this
package level would defeat the lazy-SDK rule: pulling `AnthropicProvider`
into `sys.modules` happens only when something explicitly imports
`novelwriter.ai.provider.anthropic`, which the registry does on demand.
"""
from __future__ import annotations

from novelwriter.ai.provider.base import (
    Provider,
    ProviderDependencyError,
    ProviderError,
    ProviderResponse,
)
from novelwriter.ai.provider.mock import MockProvider
from novelwriter.ai.provider.registry import (
    available_providers,
    make_provider,
)

__all__ = [
    "MockProvider",
    "Provider",
    "ProviderDependencyError",
    "ProviderError",
    "ProviderResponse",
    "available_providers",
    "make_provider",
]
