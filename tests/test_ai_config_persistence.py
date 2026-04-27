"""
Plotwright – AIConfig Persistence (Sprint 1, gate item 5)
==========================================================

Verifies that ``AIConfig`` round-trips through the project-local JSON
storage in :mod:`novelwriter.ai.persistence` without losing or silently
mutating the privacy posture.

The Sprint 1 storage shortcut is a per-project ``ai-config.json`` file.
Sprint 2 will integrate the same dict serialisation with the upstream
project XML format; this test will move with it once that lands.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import json

from pathlib import Path

import pytest

from novelwriter.ai.config import (
    AIConfig, FEATURE_CONSISTENCY, FEATURE_REWRITE, PROVIDER_MOCK,
)
from novelwriter.ai.persistence import (
    AI_CONFIG_FILENAME, config_path, load_ai_config, save_ai_config,
)


def test_default_config_roundtrips_through_disk(tmp_path: Path) -> None:
    save_ai_config(tmp_path, AIConfig())
    loaded = load_ai_config(tmp_path)

    assert loaded.enabled is False
    assert loaded.feature_flags == {
        FEATURE_REWRITE: False,
        FEATURE_CONSISTENCY: False,
    }
    assert loaded.feature_providers == {
        FEATURE_REWRITE: PROVIDER_MOCK,
        FEATURE_CONSISTENCY: PROVIDER_MOCK,
    }


def test_optin_state_survives_roundtrip(tmp_path: Path) -> None:
    """Once a user opts in, the opt-in must survive close/reopen."""
    cfg = AIConfig(
        enabled=True,
        feature_flags={FEATURE_REWRITE: True, FEATURE_CONSISTENCY: False},
    )
    save_ai_config(tmp_path, cfg)
    loaded = load_ai_config(tmp_path)

    assert loaded.enabled is True
    assert loaded.is_feature_enabled(FEATURE_REWRITE) is True
    assert loaded.is_feature_enabled(FEATURE_CONSISTENCY) is False


def test_missing_file_returns_safe_defaults(tmp_path: Path) -> None:
    """No file on disk = AI off. Never expose a fresh project to the substrate."""
    loaded = load_ai_config(tmp_path)
    assert loaded.enabled is False
    assert loaded.is_feature_enabled(FEATURE_REWRITE) is False


def test_corrupt_file_falls_back_to_defaults(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    """A rotted config file must never bias the privacy posture toward "on"."""
    config_path(tmp_path).write_text("{not valid json")

    with caplog.at_level("WARNING", logger="novelwriter.ai.persistence"):
        loaded = load_ai_config(tmp_path)

    assert loaded.enabled is False
    assert any("Could not load AI config" in r.getMessage() for r in caplog.records)


def test_unknown_provider_is_replaced_with_mock(tmp_path: Path) -> None:
    """A project pinned to a provider this build does not know must
    fall back to the mock, not silently keep the unknown identifier."""
    raw = {
        "enabled": True,
        "feature_flags": {FEATURE_REWRITE: True},
        "feature_providers": {FEATURE_REWRITE: "imaginary"},
    }
    config_path(tmp_path).write_text(json.dumps(raw))

    loaded = load_ai_config(tmp_path)
    assert loaded.feature_providers[FEATURE_REWRITE] == PROVIDER_MOCK


def test_save_uses_documented_filename(tmp_path: Path) -> None:
    save_ai_config(tmp_path, AIConfig())
    assert (tmp_path / AI_CONFIG_FILENAME).is_file()
