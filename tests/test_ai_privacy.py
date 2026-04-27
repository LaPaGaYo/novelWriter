"""
Plotwright – Privacy Regression Test (Sprint 1, gate item 2)
=============================================================

Hard gate: with the AI master toggle off, the AI substrate must produce
**zero outbound TCP/UDP traffic**. This is the foundational privacy
contract for the fork — every other AI feature is layered on top of the
network-zero default.

Test strategy
-------------

We monkeypatch ``socket.socket.connect``, ``socket.create_connection``,
and ``socket.getaddrinfo`` with a tripwire that records every call. Then
we exercise the AI substrate at the level a real session would: import
the package, create an AIConfig (default off), instantiate the
MockProvider, save and reload config to disk, run the privacy gate.

Any sentinel call is a fatal failure. The original sprint contract
described a "60-second scripted GUI session"; this lower-level
substrate-only equivalent gives us a faster, deterministic gate that
exercises the same code paths the GUI session would (config load,
provider construction, gate evaluation).

A separate test (``test_ai_no_external_imports.py``) statically asserts
that ``httpx`` / ``requests`` are not imported anywhere outside
``novelwriter/ai/network.py``, preventing future contributors from
silently routing around the gate.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import socket

from pathlib import Path

import pytest


@pytest.fixture
def network_tripwire(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, object]]:
    """Replace every socket-egress entry point with a recorder.

    Returns a list of (call_name, args) tuples populated by the
    monkeypatch for assertions in the test body. Any non-empty list at
    the end of the test is a privacy failure.
    """
    calls: list[tuple[str, object]] = []

    def _record(name: str):
        def _hook(*args: object, **_: object) -> object:
            calls.append((name, args))
            raise AssertionError(
                f"Privacy regression: {name}() reached the network with AI off."
            )
        return _hook

    monkeypatch.setattr(socket.socket, "connect", _record("socket.connect"))
    monkeypatch.setattr(socket, "create_connection", _record("create_connection"))
    monkeypatch.setattr(socket, "getaddrinfo", _record("getaddrinfo"))
    return calls


def test_substrate_import_makes_no_network_calls(network_tripwire) -> None:
    """Importing the AI substrate must not contact the network."""
    import novelwriter.ai  # noqa: F401  (import is the test)
    import novelwriter.ai.config  # noqa: F401
    import novelwriter.ai.network  # noqa: F401
    import novelwriter.ai.persistence  # noqa: F401
    import novelwriter.ai.provider.mock  # noqa: F401

    assert network_tripwire == []


def test_default_config_is_disabled(network_tripwire) -> None:
    """A freshly constructed AIConfig is fully disabled and never opens a socket."""
    from novelwriter.ai import AIConfig

    cfg = AIConfig()
    assert cfg.enabled is False
    for feature in ("rewrite", "consistency"):
        assert cfg.is_feature_enabled(feature) is False

    assert network_tripwire == []


def test_mock_provider_makes_no_network_calls(network_tripwire) -> None:
    """The MockProvider must satisfy the contract without any I/O."""
    from novelwriter.ai import MockProvider

    provider = MockProvider()
    assert provider.is_local is True
    assert provider.health_check() is True
    assert provider.generate("hello") == "[mock] hello"
    assert provider.generate("hello", operation="rewrite") == "[mock-rewrite] hello"
    assert provider.estimate_tokens("hello world") > 0

    assert network_tripwire == []


def test_config_roundtrip_makes_no_network_calls(
    network_tripwire, tmp_path: Path,
) -> None:
    """Persisting and reloading AIConfig must not touch the network."""
    from novelwriter.ai import AIConfig
    from novelwriter.ai.persistence import load_ai_config, save_ai_config

    cfg = AIConfig()
    save_ai_config(tmp_path, cfg)
    reloaded = load_ai_config(tmp_path)

    assert reloaded.enabled is False
    assert reloaded.feature_flags == cfg.feature_flags
    assert network_tripwire == []


def test_privacy_gate_refuses_call_with_ai_off(network_tripwire) -> None:
    """The gate must short-circuit BEFORE any I/O when AI is off."""
    from novelwriter.ai import AIConfig, PrivacyGatingError
    from novelwriter.ai.network import EgressRequest, gated_request

    cfg = AIConfig()  # enabled=False by default
    request = EgressRequest(
        feature="rewrite",
        endpoint="https://example.invalid/v1/complete",
        byte_count=128,
        has_credential=True,
    )

    with pytest.raises(PrivacyGatingError):
        gated_request(cfg, request)

    # The gate must refuse before the transport layer ever runs.
    assert network_tripwire == []
