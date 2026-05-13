"""
plotwright fork — Privacy regression test
=========================================

THE HARD GATE.

Sprint 1's central success criterion: with `AIConfig.enabled = False`, the AI
substrate makes ZERO outbound network connections. We enforce that by
monkey-patching `socket.socket.connect` at module load and asserting it's
never invoked while the substrate exercises its surface.

Sprint 2 extension (SC-7, SC-8): after `import novelwriter.ai` no provider
SDK module is allowed to appear in `sys.modules`. The provider modules
import their SDK lazily inside the call sites that need it; the privacy
test asserts that the substrate's package import does NOT trigger an SDK
import as a side effect (which a future contributor might introduce
accidentally by adding a top-level `import anthropic` to `provider/anthropic.py`).

If this test fails, Sprint 2 is BLOCKED regardless of any other green check.
The whole "100% NOT AI slop" positioning of the fork rests on this guarantee.
"""
from __future__ import annotations

import socket
import sys

from contextlib import contextmanager

import pytest

from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import NetworkGate, PrivacyGatingError
from novelwriter.ai.provider.mock import MockProvider


# SDK modules that MUST stay out of sys.modules after `import novelwriter.ai`.
# Top-level package names only — `import anthropic.beta` would put both
# `anthropic` and `anthropic.beta` in sys.modules; we check the parent.
_FORBIDDEN_SDK_MODULES = (
    "anthropic",
    "google",
    "google.generativeai",
    "openai",
    "tiktoken",
)


@contextmanager
def network_sentinel():
    """Replace socket.socket.connect with a fail-loud sentinel.

    Any attempt by the substrate (or any code path it triggers) to open a
    real outbound connection raises immediately. Yields the call counter so
    the test can assert zero invocations.
    """
    calls: list[tuple] = []
    original = socket.socket.connect

    def fail(self, address, *args, **kwargs):  # noqa: ANN001 - matches socket signature
        calls.append((self, address))
        raise AssertionError(
            f"Privacy regression: socket.connect({address!r}) attempted "
            f"while AI was off. The substrate must never make a network "
            f"call when the master switch is False.",
        )

    socket.socket.connect = fail
    try:
        yield calls
    finally:
        socket.socket.connect = original


def test_no_network_with_master_off():
    """With AIConfig.enabled=False, no substrate path may open a connection."""
    config = AIConfig()
    assert config.enabled is False, "AIConfig must default to off"

    with network_sentinel() as calls:
        # Exercise the surfaces that exist in Sprint 1.
        gate = NetworkGate(config)
        with pytest.raises(PrivacyGatingError):
            gate.guard(AIFeature.REWRITE)
        with pytest.raises(PrivacyGatingError):
            gate.guard(AIFeature.CONSISTENCY)

        provider = MockProvider()
        # MockProvider is local-only, but exercise it anyway so we catch a
        # future regression where someone makes the mock secretly network-y.
        provider.health_check()
        provider.generate("test prompt")
        provider.estimate_tokens("any text")

    assert len(calls) == 0, (
        f"Privacy regression: {len(calls)} socket.connect attempts while "
        f"AI master switch was off"
    )


def test_no_network_with_master_on_but_feature_off():
    """Master switch on but per-feature off -> still no network for that feature."""
    config = AIConfig()
    config.enabled = True
    # All per-feature flags remain False.

    with network_sentinel() as calls:
        gate = NetworkGate(config)
        with pytest.raises(PrivacyGatingError):
            gate.guard(AIFeature.REWRITE)
        with pytest.raises(PrivacyGatingError):
            gate.guard(AIFeature.CONSISTENCY)

    assert len(calls) == 0


def test_default_aiconfig_is_off():
    """A freshly constructed AIConfig has every flag at False."""
    config = AIConfig()
    assert config.enabled is False
    for feature in AIFeature:
        assert config.features[feature] is False, (
            f"AIConfig.features[{feature}] must default to False"
        )
        assert config.providers[feature] is None, (
            f"AIConfig.providers[{feature}] must default to None"
        )


def test_no_provider_sdk_in_sys_modules_after_import():
    """Sprint 2 SC-7: importing the substrate must NOT pull provider SDKs.

    We do this with a subprocess so the test is hermetic — running it
    inside the same interpreter that has already loaded test fixtures could
    yield a misleading result if a different test polluted `sys.modules`.
    """
    import subprocess
    import textwrap

    script = textwrap.dedent(
        """
        import sys
        import novelwriter.ai  # noqa: F401  — side-effect import only
        forbidden = ("anthropic", "google", "google.generativeai", "openai", "tiktoken")
        present = [m for m in forbidden if m in sys.modules]
        if present:
            raise SystemExit(f"SDK leak: {present!r}")
        """
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, (
        f"SC-7 privacy assertion failed: {result.stdout}{result.stderr}"
    )


def test_registry_resolves_known_providers():
    """The registry surfaces the four S2 providers + mock as known ids."""
    from novelwriter.ai.provider.registry import available_providers
    ids = available_providers()
    for required in ("mock", "ollama", "anthropic", "gemini"):
        assert required in ids, f"Provider id {required!r} missing from registry"
