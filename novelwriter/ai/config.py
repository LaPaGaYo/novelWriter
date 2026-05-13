"""
plotwright fork — AI Config
===========================

Project-scoped AI configuration. Every flag defaults to off. Config persists
inside the project directory (NOT in user-global config) so that opting in for
one project never opts in another.

Persistence is JSON-on-disk (a single `ai-config.json` file in the project
root) rather than threading through novelWriter's NWConfigParser, both to keep
the privacy contract auditable and to keep the merge surface with upstream
small.

Sprint 2 widening:
- Schema bumped from 1 to 2 — adds `provider_configs: dict[str, dict]` for
  per-provider settings (Ollama base URL, Gemini `auth_mode`, model
  selection, etc.). `from_dict` ignores unknown keys, so a v1 file loads
  cleanly without provider_configs and re-saves at v2.
- `provider_configs` is intentionally shapeless at the AIConfig level; each
  provider validates its own slice when instantiated through the registry.
"""
from __future__ import annotations

import enum
import json
import logging

from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class AIFeature(str, enum.Enum):
    """Names of the AI features the substrate registers.

    Sprint 2 still only registers the names. Sprint 3 builds REWRITE, Sprint 4
    builds CONSISTENCY. The post-MVP features are not registered yet because
    each one needs its own framing pass.
    """

    REWRITE = "rewrite"
    CONSISTENCY = "consistency"


_CONFIG_FILENAME = "ai-config.json"
_SCHEMA_VERSION = 2


class AIConfig:
    """Project-scoped AI configuration.

    Defaults are deliberately conservative: master switch off, every feature
    off, no provider chosen. Loading from disk merges over the defaults so a
    config file that pre-dates a new feature does not silently leave that
    feature in some unknown state.
    """

    def __init__(self) -> None:
        self.enabled: bool = False
        self.features: dict[AIFeature, bool] = {f: False for f in AIFeature}
        self.providers: dict[AIFeature, str | None] = {f: None for f in AIFeature}
        # Per-provider settings. Keyed by provider id (`"ollama"`,
        # `"anthropic"`, `"gemini"`). Each value is a plain dict; the
        # provider class validates its own slice at instantiation time. We
        # keep it shapeless here so adding a provider does not require
        # changing AIConfig.
        self.provider_configs: dict[str, dict[str, Any]] = {}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AIConfig:
        """Parse a config dict, ignoring unknown keys (forward compat)."""
        config = cls()
        config.enabled = bool(data.get("enabled", False))
        for feature in AIFeature:
            features = data.get("features", {})
            config.features[feature] = bool(features.get(feature.value, False))
            providers = data.get("providers", {})
            value = providers.get(feature.value)
            config.providers[feature] = str(value) if value else None
        raw_pc = data.get("provider_configs", {})
        if isinstance(raw_pc, dict):
            # Coerce: only string keys + dict values survive into memory.
            # A malformed entry from a future / corrupted file is dropped
            # silently rather than fail-loud, matching the "default to off"
            # privacy posture.
            config.provider_configs = {
                str(k): dict(v) for k, v in raw_pc.items() if isinstance(v, dict)
            }
        return config

    def to_dict(self) -> dict[str, Any]:
        """Serialize config to a JSON-safe dict."""
        return {
            "schema_version": _SCHEMA_VERSION,
            "enabled": self.enabled,
            "features": {f.value: self.features[f] for f in AIFeature},
            "providers": {f.value: self.providers[f] for f in AIFeature},
            "provider_configs": self.provider_configs,
        }

    @classmethod
    def load(cls, project_path: Path) -> AIConfig:
        """Load AI config from a project directory.

        Returns a fresh default config (everything off) if no file exists or
        the file is unreadable. We deliberately fail safe to off rather than
        raising, because a corrupted config must never accidentally enable AI.
        """
        config_path = Path(project_path) / _CONFIG_FILENAME
        if not config_path.exists():
            return cls()
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Could not read AI config at %s: %s", config_path, exc)
            return cls()
        return cls.from_dict(data)

    def save(self, project_path: Path) -> None:
        """Write AI config to the project directory."""
        config_path = Path(project_path) / _CONFIG_FILENAME
        config_path.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def feature_active(self, feature: AIFeature) -> bool:
        """Return True only if the master switch AND the feature flag are on."""
        return self.enabled and self.features.get(feature, False)

    def provider_config(self, provider_id: str) -> dict[str, Any]:
        """Return the saved settings slice for `provider_id`, or an empty dict.

        Returns a copy so a caller mutating the dict cannot corrupt the
        in-memory config without going through `set_provider_config`.
        """
        return dict(self.provider_configs.get(provider_id, {}))

    def set_provider_config(self, provider_id: str, settings: dict[str, Any]) -> None:
        """Replace the saved settings slice for `provider_id` wholesale."""
        self.provider_configs[provider_id] = dict(settings)


__all__ = ["AIConfig", "AIFeature"]
