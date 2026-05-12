"""
plotwright fork — NetworkGate gating tests
==========================================

Direct unit tests on the gate. Verifies that PrivacyGatingError is raised on
every disallowed call attempt and that legitimate calls are authorized.
"""
from __future__ import annotations

import pytest

from novelwriter.ai.config import AIConfig, AIFeature
from novelwriter.ai.network import AIError, NetworkGate, PrivacyGatingError


def test_master_switch_off_raises_for_every_feature():
    config = AIConfig()
    gate = NetworkGate(config)
    for feature in AIFeature:
        with pytest.raises(PrivacyGatingError):
            gate.guard(feature)


def test_master_on_feature_off_raises():
    config = AIConfig()
    config.enabled = True
    # All features remain False.
    gate = NetworkGate(config)
    for feature in AIFeature:
        with pytest.raises(PrivacyGatingError):
            gate.guard(feature)


def test_master_on_feature_on_authorizes():
    config = AIConfig()
    config.enabled = True
    config.features[AIFeature.REWRITE] = True
    gate = NetworkGate(config)
    # Should NOT raise.
    gate.guard(AIFeature.REWRITE)


def test_master_on_one_feature_on_does_not_authorize_other_feature():
    config = AIConfig()
    config.enabled = True
    config.features[AIFeature.REWRITE] = True
    # CONSISTENCY remains off.
    gate = NetworkGate(config)
    with pytest.raises(PrivacyGatingError):
        gate.guard(AIFeature.CONSISTENCY)


def test_privacy_gating_error_is_subclass_of_aierror():
    """PrivacyGatingError MUST be a subclass of AIError so callers can
    catch the AI base or the privacy-specific subclass."""
    config = AIConfig()
    gate = NetworkGate(config)
    with pytest.raises(AIError):
        gate.guard(AIFeature.REWRITE)


def test_message_mentions_feature_name():
    """The error message MUST name the offending feature so the user / log
    knows which call was refused."""
    config = AIConfig()
    gate = NetworkGate(config)
    with pytest.raises(PrivacyGatingError) as excinfo:
        gate.guard(AIFeature.REWRITE)
    assert AIFeature.REWRITE.value in str(excinfo.value)
