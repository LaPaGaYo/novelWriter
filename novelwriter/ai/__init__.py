"""
novelWriter / Plotwright – AI Substrate Package
===============================================

This package owns every AI-related capability in the application: provider
abstraction, privacy gating, single-egress networking, prompt/staging plumbing,
and per-feature configuration.

Sprint 1 scope: substrate only. No real AI feature ships from here yet — the
only provider that does anything useful is :class:`MockProvider`. Real provider
implementations land in Sprint 2.

Privacy contract: nothing in this package may issue a network request unless
:func:`novelwriter.ai.network.gated_request` agrees the call is allowed. CI
enforces that ``httpx`` / ``requests`` are not imported anywhere else in the
project.

File History:
Created: 2026-04-26 [Sprint 1] Fork bootstrap

This file is a part of novelWriter / Plotwright (a fork of novelWriter)
Copyright (C) 2026 Plotwright contributors

Plotwright is licensed under GNU GPL v3 — see LICENSE.md and CREDITS.md.
"""  # noqa
from __future__ import annotations

from novelwriter.ai.config import AIConfig
from novelwriter.ai.error import AIError, ProviderError, PrivacyGatingError
from novelwriter.ai.provider.base import Provider
from novelwriter.ai.provider.mock import MockProvider

__all__ = [
    "AIConfig",
    "AIError",
    "MockProvider",
    "PrivacyGatingError",
    "Provider",
    "ProviderError",
]
