"""
Plotwright – AI provider implementations
========================================

Sprint 1 ships only :class:`MockProvider`. Real providers (Ollama, Anthropic,
OpenAI, Gemini) land in Sprint 2, each as its own module under this package
and each conforming to the :class:`Provider` ABC.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from novelwriter.ai.provider.base import Provider
from novelwriter.ai.provider.mock import MockProvider

__all__ = ["MockProvider", "Provider"]
