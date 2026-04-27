"""
Plotwright – Network Gating Tests (Sprint 1, gate item 4)
==========================================================

Direct unit coverage of :func:`novelwriter.ai.network.gated_request`.
Every refusal path must raise :class:`PrivacyGatingError`, and every
``PrivacyGatingError`` must be a subclass of :class:`AIError` so call
sites can ``except AIError`` without leaking sub-exceptions.

The verification matrix flags this as gate item 4 of the Sprint 1
contract; combined with :file:`test_ai_privacy.py` it forms the
foundational privacy guarantee for the fork.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import pytest

from novelwriter.ai import AIConfig, AIError, PrivacyGatingError
from novelwriter.ai.config import FEATURE_REWRITE
from novelwriter.ai.network import EgressRequest, gated_request


def _request(**overrides: object) -> EgressRequest:
    """Build an EgressRequest with sane defaults; overrides win per-test."""
    base = {
        "feature": FEATURE_REWRITE,
        "endpoint": "https://example.invalid/v1/complete",
        "byte_count": 64,
        "has_credential": True,
    }
    base.update(overrides)
    return EgressRequest(**base)  # type: ignore[arg-type]


def test_privacy_gating_error_is_ai_error_subclass() -> None:
    assert issubclass(PrivacyGatingError, AIError)


def test_gate_refuses_when_master_toggle_off() -> None:
    cfg = AIConfig()  # enabled=False
    with pytest.raises(PrivacyGatingError) as ei:
        gated_request(cfg, _request())
    assert "master AI toggle" in str(ei.value)
    assert ei.value.feature == FEATURE_REWRITE


def test_gate_refuses_when_feature_flag_off() -> None:
    cfg = AIConfig(enabled=True)
    # feature_flags default to False — the request feature is not opted in.
    with pytest.raises(PrivacyGatingError) as ei:
        gated_request(cfg, _request())
    assert "feature is not opted in" in str(ei.value)


def test_gate_refuses_when_endpoint_missing() -> None:
    cfg = AIConfig(enabled=True, feature_flags={FEATURE_REWRITE: True})
    with pytest.raises(PrivacyGatingError) as ei:
        gated_request(cfg, _request(endpoint=""))
    assert "no endpoint configured" in str(ei.value)


def test_gate_refuses_when_credential_missing() -> None:
    cfg = AIConfig(enabled=True, feature_flags={FEATURE_REWRITE: True})
    with pytest.raises(PrivacyGatingError) as ei:
        gated_request(cfg, _request(has_credential=False))
    assert "no credential" in str(ei.value)


def test_gate_allows_when_all_conditions_satisfied(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Happy path returns None and emits a metadata-only privacy log line."""
    cfg = AIConfig(enabled=True, feature_flags={FEATURE_REWRITE: True})

    with caplog.at_level("INFO", logger="novelwriter.ai.network"):
        result = gated_request(cfg, _request())

    assert result is None
    # The privacy log must include endpoint+bytes (metadata) but never the body.
    log_text = "\n".join(rec.getMessage() for rec in caplog.records)
    assert "ai-egress" in log_text
    assert "example.invalid" in log_text
    assert "bytes=64" in log_text


def test_gate_error_carries_feature_attribute() -> None:
    cfg = AIConfig()
    try:
        gated_request(cfg, _request(feature="consistency"))
    except PrivacyGatingError as exc:
        assert exc.feature == "consistency"
    else:  # pragma: no cover — gate must always refuse here
        pytest.fail("gated_request did not refuse a disabled-AI call")
