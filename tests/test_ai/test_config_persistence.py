"""
plotwright fork — AIConfig persistence tests
============================================

Verifies AIConfig round-trips through save/load and that defaults survive
upgrades (a config file written by an older fork build still loads cleanly
when a new feature is added).
"""
from __future__ import annotations

import json

from pathlib import Path

import pytest

from novelwriter.ai.config import AIConfig, AIFeature


def test_fresh_load_when_no_file(tmp_path: Path):
    config = AIConfig.load(tmp_path)
    assert config.enabled is False
    for feature in AIFeature:
        assert config.features[feature] is False
        assert config.providers[feature] is None


def test_round_trip_off_to_on(tmp_path: Path):
    config = AIConfig()
    config.enabled = True
    config.features[AIFeature.REWRITE] = True
    config.providers[AIFeature.REWRITE] = "mock"
    config.save(tmp_path)

    reloaded = AIConfig.load(tmp_path)
    assert reloaded.enabled is True
    assert reloaded.features[AIFeature.REWRITE] is True
    assert reloaded.features[AIFeature.CONSISTENCY] is False
    assert reloaded.providers[AIFeature.REWRITE] == "mock"
    assert reloaded.providers[AIFeature.CONSISTENCY] is None


def test_corrupted_json_falls_back_to_defaults(tmp_path: Path):
    """If the config file is unreadable, we MUST default to off, never up."""
    (tmp_path / "ai-config.json").write_text("{not valid json", encoding="utf-8")
    config = AIConfig.load(tmp_path)
    assert config.enabled is False, "Corrupted config must fail safe to off"


def test_unknown_keys_in_file_are_ignored(tmp_path: Path):
    """Forward-compat: a file with a future feature key shouldn't blow up."""
    payload = {
        "schema_version": 99,
        "enabled": True,
        "features": {
            "rewrite": True,
            "consistency": False,
            "future_unknown_feature": True,
        },
        "providers": {
            "rewrite": "mock",
            "consistency": None,
            "future_unknown_feature": "imaginary",
        },
        "extra_top_level_key": "ignored",
    }
    (tmp_path / "ai-config.json").write_text(json.dumps(payload), encoding="utf-8")
    config = AIConfig.load(tmp_path)
    assert config.enabled is True
    assert config.features[AIFeature.REWRITE] is True
    assert config.features[AIFeature.CONSISTENCY] is False


def test_feature_active_requires_both_switches():
    config = AIConfig()
    assert config.feature_active(AIFeature.REWRITE) is False

    config.enabled = True
    assert config.feature_active(AIFeature.REWRITE) is False, (
        "Master switch on alone must NOT activate any feature"
    )

    config.features[AIFeature.REWRITE] = True
    assert config.feature_active(AIFeature.REWRITE) is True

    config.enabled = False
    assert config.feature_active(AIFeature.REWRITE) is False, (
        "Turning master off must immediately deactivate every feature"
    )


def test_save_writes_pretty_sorted_json(tmp_path: Path):
    """Persisted config must be diff-friendly (sorted keys, indented)."""
    config = AIConfig()
    config.enabled = True
    config.save(tmp_path)
    content = (tmp_path / "ai-config.json").read_text(encoding="utf-8")
    assert content.endswith("\n")
    parsed = json.loads(content)
    assert parsed["enabled"] is True
    # sort_keys=True is contractual so reviewers can read diffs.
    keys = list(parsed.keys())
    assert keys == sorted(keys)
