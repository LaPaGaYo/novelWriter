"""
Plotwright – AI provider ABC
=============================

The Provider abstract base class is the contract every AI backend must
satisfy. ``tests/test_ai_provider_contract.py`` runs the same suite against
every concrete provider; Sprint 1 only verifies :class:`MockProvider`, but
the contract suite is structured so Sprint 2 can add Ollama / Anthropic /
OpenAI / Gemini providers without touching the test file.

Design notes
------------

* ``generate()`` returns a ``str``. Streaming arrives in Sprint 2 alongside
  the real providers and gets bolted on as an *additional* method
  (``stream()``); the synchronous ``generate()`` stays as the canonical
  contract test entry point.
* ``health_check()`` is allowed to be cheap and approximate. It must not
  contact the network unless the privacy gate has already authorised the
  parent call.
* ``estimate_tokens()`` uses :mod:`novelwriter.ai.tokens` as a default; real
  providers override with their tokenizer of choice.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from novelwriter.ai.tokens import estimate_tokens as default_estimate


class Provider(ABC):
    """Abstract base class for any AI provider.

    Implementations live one-per-module under :mod:`novelwriter.ai.provider`.
    """

    #: Stable provider identifier (e.g. ``"mock"``, ``"ollama"``).
    name: str = "abstract"

    #: ``True`` if the provider runs on the user's machine and never needs
    #: an outbound connection. Drives privacy UX and the network gate.
    is_local: bool = False

    @abstractmethod
    def generate(self, prompt: str, **opts: Any) -> str:
        """Run a single completion and return the generated text."""

    def estimate_tokens(self, text: str) -> int:
        """Return an estimate of how many tokens ``text`` would consume.

        Defaults to a 4-chars-per-token heuristic from
        :mod:`novelwriter.ai.tokens`. Real providers should override with
        their own tokenizer.
        """
        return default_estimate(text)

    @abstractmethod
    def health_check(self) -> bool:
        """Return ``True`` if the provider is currently usable.

        Cheap, side-effect-free implementation expected. Must not perform
        network I/O outside the privacy gate.
        """
