"""
Plotwright – AI configuration persistence
=========================================

Sprint 1 stores per-project AI configuration as a JSON file inside the
project directory (``<project>/ai-config.json``). This is a deliberate
short-cut: the upstream project file format is XML and binding the AI
config to it touches a lot of surface area; deferring that integration
to Sprint 2 keeps Sprint 1 bounded while still satisfying the
"AI config round-trips" verification gate.

The on-disk format is plain JSON because:

* It is easy to inspect by humans (privacy posture is the kind of thing
  users will want to grep for).
* It avoids leaking AI-specific schema into the upstream XML format,
  which keeps the migration round-trip test (Sprint 5) clean.
* JSON tolerates schema additions (new feature flags) without versioning.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

import json
import logging

from pathlib import Path

from novelwriter.ai.config import AIConfig

logger = logging.getLogger(__name__)

AI_CONFIG_FILENAME = "ai-config.json"


def config_path(project_path: Path | str) -> Path:
    """Return the canonical AI config file path for a project directory."""
    return Path(project_path) / AI_CONFIG_FILENAME


def save_ai_config(project_path: Path | str, config: AIConfig) -> None:
    """Persist ``config`` to the project directory.

    Any prior file is overwritten. The directory must already exist —
    callers are expected to be operating on an already-opened project.
    """
    path = config_path(project_path)
    path.write_text(json.dumps(config.to_dict(), indent=2, sort_keys=True))
    logger.debug("Saved AI config to %s", path)


def load_ai_config(project_path: Path | str) -> AIConfig:
    """Load AI config from the project directory.

    Returns a fresh default :class:`AIConfig` if no file exists or the
    file is unreadable. The fail-safe default is "AI off, every feature
    off" — i.e. we never expose a project to the AI substrate just
    because its config file rotted.
    """
    path = config_path(project_path)
    if not path.exists():
        return AIConfig()

    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Could not load AI config at %s: %s", path, exc)
        return AIConfig()

    return AIConfig.from_dict(data)
