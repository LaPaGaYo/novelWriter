"""
plotwright fork — Provider gating regression tests (S-1)
========================================================

/review Pass 1 found that cloud providers' ``generate()`` did not invoke
``NetworkGate.guard()`` despite the ABC contract requiring it. The
Preferences "Dry-run" path therefore could call cloud APIs even when the
master toggle was off or the per-feature flag was off.

S-1 fix threads ``gate`` + ``feature`` into cloud provider construction
(and the staging orchestration layer) so ``generate()`` calls
``gate.guard(feature)`` BEFORE any client / network work. This module
verifies the contract end-to-end:

- Direct provider construction with ``gate`` + ``feature``: ``generate()``
  raises ``PrivacyGatingError`` when master switch off, OR when this
  feature flag off.
- Registry-built providers honor ``gate`` + ``feature`` passed through
  ``make_provider``.
- ``staging.stage()`` belt-and-suspenders: refuses to proceed when its own
  ``gate`` + ``feature`` parameters report the call is unauthorized.
- Misconfiguration (one of gate/feature without the other) is refused
  loudly rather than silently skipping the gate.
- Backward compat: constructing without gate+feature still works for
  test-only paths (no enforcement).

The test never makes a real network call. Any provider that DID reach
``httpx`` would still be flagged by the privacy-sentinel infrastructure
elsewhere; here we assert the gate fires first.
"""
from __future__ import annotations

import pytest

from novelwriter.ai.auth import ApiKeyAuth
from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import NetworkGate, PrivacyGatingError
from novelwriter.ai.provider.anthropic import AnthropicProvider
from novelwriter.ai.provider.base import ProviderError
from novelwriter.ai.provider.gemini import GeminiProvider
from novelwriter.ai.provider.ollama import OllamaProvider


def _make_config(*, enabled: bool, rewrite: bool = True) -> AIConfig:
    """Build an AIConfig with the master switch and rewrite-feature flags set."""
    config = AIConfig()
    config.enabled = enabled
    config.features[AIFeature.REWRITE] = rewrite
    return config


def _gated_anthropic(config: AIConfig, feature: AIFeature) -> AnthropicProvider:
    """Build an AnthropicProvider with the privacy gate wired."""
    return AnthropicProvider(
        api_key="sk-test",
        model="claude-sonnet-4-5",
        transport=_should_never_run_transport(),
        gate=NetworkGate(config),
        feature=feature,
    )


def _gated_gemini(config: AIConfig, feature: AIFeature) -> GeminiProvider:
    return GeminiProvider(
        auth=ApiKeyAuth(api_key="api-test", header_name="x-goog-api-key"),
        model="gemini-2.5-flash",
        transport=_should_never_run_transport(),
        gate=NetworkGate(config),
        feature=feature,
    )


def _gated_ollama(config: AIConfig, feature: AIFeature) -> OllamaProvider:
    return OllamaProvider(
        base_url="http://test",
        model="llama3.1",
        transport=_should_never_run_transport(),
        gate=NetworkGate(config),
        feature=feature,
    )


def _should_never_run_transport():
    """A transport that asserts it was never invoked.

    If a provider bypasses the gate and reaches `make_client`, the transport
    handler runs and the assertion fires — surfacing the regression as a
    clear test failure rather than a network call.
    """
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:  # pragma: no cover
        raise AssertionError(
            f"Provider made a network call ({request.method} {request.url}) "
            f"despite privacy gate being off — S-1 regression!"
        )

    return httpx.MockTransport(handler)


# ---- Master switch off -----------------------------------------------


def test_anthropic_generate_refuses_when_master_off():
    config = _make_config(enabled=False, rewrite=True)
    provider = _gated_anthropic(config, AIFeature.REWRITE)
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        provider.generate("test prompt")


def test_gemini_generate_refuses_when_master_off():
    config = _make_config(enabled=False, rewrite=True)
    provider = _gated_gemini(config, AIFeature.REWRITE)
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        provider.generate("test prompt")


def test_ollama_generate_refuses_when_master_off():
    """Local providers also honor the master switch."""
    config = _make_config(enabled=False, rewrite=True)
    provider = _gated_ollama(config, AIFeature.REWRITE)
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        provider.generate("test prompt")


# ---- Master on, per-feature off --------------------------------------


def test_anthropic_generate_refuses_when_feature_off():
    config = _make_config(enabled=True, rewrite=False)
    provider = _gated_anthropic(config, AIFeature.REWRITE)
    with pytest.raises(PrivacyGatingError, match="not enabled"):
        provider.generate("test prompt")


def test_gemini_generate_refuses_when_feature_off():
    config = _make_config(enabled=True, rewrite=False)
    provider = _gated_gemini(config, AIFeature.REWRITE)
    with pytest.raises(PrivacyGatingError, match="not enabled"):
        provider.generate("test prompt")


# ---- Misconfiguration: half-set gate/feature is refused --------------


def test_anthropic_misconfigured_gate_without_feature_raises():
    config = _make_config(enabled=True, rewrite=True)
    provider = AnthropicProvider(
        api_key="sk-test",
        transport=_should_never_run_transport(),
        gate=NetworkGate(config),
        feature=None,  # misconfigured
    )
    with pytest.raises(ProviderError, match="gate but no feature"):
        provider.generate("test prompt")


def test_anthropic_misconfigured_feature_without_gate_raises():
    provider = AnthropicProvider(
        api_key="sk-test",
        transport=_should_never_run_transport(),
        gate=None,
        feature=AIFeature.REWRITE,  # misconfigured
    )
    with pytest.raises(ProviderError, match="feature but no gate"):
        provider.generate("test prompt")


# ---- Backward compat: no gate + no feature = no enforcement ----------


def test_anthropic_without_gate_does_not_enforce():
    """Test-only construction shape (no gate) preserves S2 contract test
    behavior. Production callers MUST pass a gate."""
    # MockTransport that returns a valid Anthropic response shape.
    import httpx

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"content": [{"type": "text", "text": "ok"}]},
        )

    provider = AnthropicProvider(
        api_key="sk-test",
        transport=httpx.MockTransport(handler),
        # gate=None, feature=None — explicit no-enforcement shape.
    )
    # Should NOT raise PrivacyGatingError because no gate is wired.
    response = provider.generate("test prompt")
    assert response.text == "ok"


# ---- staging.stage() orchestration-layer gating ----------------------


def test_staging_stage_refuses_with_master_off():
    """Belt-and-suspenders: stage() also gates when caller passes gate+feature."""
    from novelwriter.ai.provider.mock import MockProvider
    from novelwriter.ai.staging import stage

    config = _make_config(enabled=False, rewrite=True)
    gate = NetworkGate(config)
    # MockProvider never calls out so the staging-layer gate is the only
    # protection that fires here. This exercises the belt-and-suspenders
    # role: even providers that don't gate internally (e.g. MockProvider
    # which is unauthenticated) are guarded by stage().
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        stage(
            "test prompt",
            MockProvider(),
            gate=gate,
            feature=AIFeature.REWRITE,
        )


def test_staging_stage_misconfigured_gate_or_feature_raises():
    from novelwriter.ai.provider.mock import MockProvider
    from novelwriter.ai.staging import stage

    config = _make_config(enabled=True, rewrite=True)
    with pytest.raises(ProviderError, match="gate and feature must be passed together"):
        stage(
            "test prompt",
            MockProvider(),
            gate=NetworkGate(config),
            feature=None,  # half-configured
        )


# ---- Both layers cooperate (provider + staging) ---------------------


def test_both_layers_gate_independently():
    """When both the provider AND staging.stage() are gate-aware, EITHER
    layer alone catches a master-off attempt. The test simulates: provider
    has the gate; staging gets called without a gate. The provider's own
    gate should still fire."""
    config = _make_config(enabled=False, rewrite=True)
    from novelwriter.ai.staging import stage
    provider = _gated_anthropic(config, AIFeature.REWRITE)
    # No gate at the staging layer — relies on provider's gate.
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        stage("test prompt", provider)


# ---- Registry threading: make_provider passes gate through ----------


def test_make_provider_threads_gate_to_cloud_provider():
    from novelwriter.ai.provider.registry import make_provider
    config = _make_config(enabled=False, rewrite=True)
    gate = NetworkGate(config)
    provider = make_provider(
        "anthropic",
        settings={"api_key": "sk-test"},
        keystore=None,
        gate=gate,
        feature=AIFeature.REWRITE,
    )
    # The provider built through the registry is gate-aware: generate() raises.
    with pytest.raises(PrivacyGatingError, match="master switch is off"):
        provider.generate("test prompt")
