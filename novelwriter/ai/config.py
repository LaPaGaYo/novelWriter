"""
Plotwright – AI configuration
=============================

Per-project AI configuration. Stored *inside the project* (not user-global),
because privacy posture is a per-manuscript decision and we never want a
"once enabled everywhere, enabled forever" mode.

Sprint 1 scope:

* ``enabled`` master toggle (default ``False``).
* Per-feature opt-in flags for the two v1 features (``rewrite``,
  ``consistency``). Both default ``False`` and remain disabled in S1 — the
  Preferences pane greys them with "available in next sprint".
* Provider choice slots, one per feature. Default ``"mock"``. Real provider
  identifiers (``"ollama"``, ``"anthropic"``, ``"openai"``, ``"gemini"``)
  arrive in Sprint 2 with their implementations.

The config object knows how to round-trip itself through a JSON-friendly
``dict``, so the calling project save/load path can persist it alongside
the rest of project state without learning AI internals.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Feature names. Kept stable; downstream code references them as constants.
FEATURE_REWRITE = "rewrite"
FEATURE_CONSISTENCY = "consistency"

KNOWN_FEATURES: tuple[str, ...] = (FEATURE_REWRITE, FEATURE_CONSISTENCY)

# Provider identifiers. ``"mock"`` is the only one Sprint 1 actually uses.
PROVIDER_MOCK = "mock"
KNOWN_PROVIDERS: tuple[str, ...] = (
    PROVIDER_MOCK,
    "ollama",
    "anthropic",
    "openai",
    "gemini",
)


@dataclass
class AIConfig:
    """Per-project AI configuration.

    Defaults are deliberately conservative: AI off, every feature off, every
    feature pointed at the deterministic mock provider. A freshly opened
    project has zero capability to talk to any external service until a
    human flips the master toggle *and* the feature flag in Preferences.
    """

    enabled: bool = False
    feature_flags: dict[str, bool] = field(
        default_factory=lambda: {f: False for f in KNOWN_FEATURES}
    )
    feature_providers: dict[str, str] = field(
        default_factory=lambda: {f: PROVIDER_MOCK for f in KNOWN_FEATURES}
    )

    def is_feature_enabled(self, feature: str) -> bool:
        """Return True iff the master toggle AND the per-feature flag are on."""
        return bool(self.enabled and self.feature_flags.get(feature, False))

    def provider_for(self, feature: str) -> str:
        """Resolve which provider id should handle a given feature."""
        return self.feature_providers.get(feature, PROVIDER_MOCK)

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a JSON-friendly dict for project storage."""
        return {
            "enabled": self.enabled,
            "feature_flags": dict(self.feature_flags),
            "feature_providers": dict(self.feature_providers),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> AIConfig:
        """Deserialise from a project-stored dict, tolerating partial input.

        Unknown features in the persisted data are dropped; missing known
        features fall back to the safe default (off, mock provider). This
        keeps the substrate forward- and backward-compatible across sprints
        without bumping a schema version.
        """
        if not data:
            return cls()

        cfg = cls()
        cfg.enabled = bool(data.get("enabled", False))

        flags = data.get("feature_flags", {}) or {}
        cfg.feature_flags = {
            f: bool(flags.get(f, False)) for f in KNOWN_FEATURES
        }

        providers = data.get("feature_providers", {}) or {}
        cfg.feature_providers = {
            f: str(providers.get(f, PROVIDER_MOCK))
            if str(providers.get(f, PROVIDER_MOCK)) in KNOWN_PROVIDERS
            else PROVIDER_MOCK
            for f in KNOWN_FEATURES
        }
        return cfg
