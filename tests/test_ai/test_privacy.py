"""
plotwright fork — Privacy regression test
=========================================

THE HARD GATE.

Sprint 1's central success criterion: with `AIConfig.enabled = False`, the AI
substrate makes ZERO outbound network connections. We enforce that by
monkey-patching `socket.socket.connect` at module load and asserting it's
never invoked while the substrate exercises its surface.

If this test fails, Sprint 1 is BLOCKED regardless of any other green check.
The whole "100% NOT AI slop" positioning of the fork rests on this guarantee.
"""
from __future__ import annotations

import socket

from contextlib import contextmanager

import pytest

from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import NetworkGate, PrivacyGatingError
from novelwriter.ai.provider.mock import MockProvider


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
