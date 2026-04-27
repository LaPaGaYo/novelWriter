"""
Plotwright – Deterministic mock provider
========================================

Sprint 1's only working provider. Useful for:

* CI tests that must never touch a network.
* Reproducible local development and demos.
* Anchoring the contract test suite in :file:`tests/test_ai_provider_contract.py`.

The mock supports five named transformations matching the Sprint 3 inline-
rewrite feature surface (rewrite / expand / contract / change-tense /
change-pov), but Sprint 1 only exercises ``rewrite`` and the default echo.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from typing import Any

from novelwriter.ai.provider.base import Provider

_TRANSFORMATIONS: dict[str, str] = {
    "rewrite":      "[mock-rewrite] {text}",
    "expand":       "[mock-expand] {text} {text}",
    "contract":     "[mock-contract] {text_short}",
    "change_tense": "[mock-tense] {text}",
    "change_pov":   "[mock-pov] {text}",
}


class MockProvider(Provider):
    """Deterministic provider for tests and local-only flows.

    The mock honours an ``operation`` keyword in :meth:`generate` so the
    same provider can stand in for any of the five Sprint 3 transformations
    in tests, but keeps a sane default (echo with a tag) for callers that
    don't care.
    """

    name = "mock"
    is_local = True

    def generate(self, prompt: str, **opts: Any) -> str:
        operation = str(opts.get("operation", "echo"))
        if operation == "echo":
            return f"[mock] {prompt}"
        template = _TRANSFORMATIONS.get(operation)
        if template is None:
            return f"[mock:{operation}] {prompt}"
        return template.format(text=prompt, text_short=prompt[: max(1, len(prompt) // 2)])

    def health_check(self) -> bool:
        # No network, no resources — always healthy.
        return True
