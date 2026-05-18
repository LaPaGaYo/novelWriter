"""
plotwright fork — AIConfig persistence tests
============================================

Verifies AIConfig round-trips through save/load and that defaults survive
upgrades (a config file written by an older fork build still loads cleanly
when a new feature is added).

Sprint 2 (SC-3): schema_version bumps from 1 to 2. The forward-compat
contract requires:
- A v1 file (no `provider_configs` key) loads at v2 with an empty
  `provider_configs` dict and round-trips at v2.
- A v2 file with `provider_configs` survives round-trip without dropping
  per-provider settings.
- An unknown future key (e.g. v3 surprise) is ignored without raising.
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
    assert config.provider_configs == {}


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


# ---- Sprint 2: schema_version 2 + provider_configs ----------------------


def test_schema_version_is_2_on_save(tmp_path: Path):
    config = AIConfig()
    config.save(tmp_path)
    parsed = json.loads((tmp_path / "ai-config.json").read_text(encoding="utf-8"))
    assert parsed["schema_version"] == 2


def test_provider_configs_round_trip(tmp_path: Path):
    """Per-provider settings slice survives save/load wholesale."""
    config = AIConfig()
    config.set_provider_config("ollama", {"base_url": "http://127.0.0.1:11434", "model": "llama3.1"})
    config.set_provider_config("gemini", {"auth_mode": "oauth", "model": "gemini-2.5-flash"})
    config.save(tmp_path)

    reloaded = AIConfig.load(tmp_path)
    assert reloaded.provider_config("ollama") == {
        "base_url": "http://127.0.0.1:11434",
        "model": "llama3.1",
    }
    assert reloaded.provider_config("gemini") == {
        "auth_mode": "oauth",
        "model": "gemini-2.5-flash",
    }


def test_provider_config_returns_copy_not_reference():
    """Caller mutation through provider_config() must not corrupt in-memory state."""
    config = AIConfig()
    config.set_provider_config("ollama", {"base_url": "http://example"})
    fetched = config.provider_config("ollama")
    fetched["base_url"] = "tampered"
    assert config.provider_config("ollama") == {"base_url": "http://example"}


def test_v1_file_loads_at_v2_without_provider_configs(tmp_path: Path):
    """A v1 file (pre-S2 schema) loads cleanly under the v2 reader."""
    legacy = {
        "schema_version": 1,
        "enabled": True,
        "features": {"rewrite": False, "consistency": False},
        "providers": {"rewrite": None, "consistency": None},
    }
    (tmp_path / "ai-config.json").write_text(json.dumps(legacy), encoding="utf-8")
    config = AIConfig.load(tmp_path)
    assert config.enabled is True
    assert config.provider_configs == {}, "v1 file must load with empty provider_configs"


def test_malformed_provider_configs_value_is_ignored(tmp_path: Path):
    """A non-dict entry inside provider_configs is dropped rather than fail-loud."""
    payload = {
        "schema_version": 2,
        "enabled": False,
        "features": {"rewrite": False, "consistency": False},
        "providers": {"rewrite": None, "consistency": None},
        "provider_configs": {
            "ollama": {"base_url": "http://ok"},
            "broken": "should be a dict, not a string",
        },
    }
    (tmp_path / "ai-config.json").write_text(json.dumps(payload), encoding="utf-8")
    config = AIConfig.load(tmp_path)
    assert config.provider_config("ollama") == {"base_url": "http://ok"}
    assert "broken" not in config.provider_configs
