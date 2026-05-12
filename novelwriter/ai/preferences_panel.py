"""
plotwright fork — AI Preferences Panel
======================================

The Preferences > AI section. Sprint 1 ships only the master toggle and
disabled per-feature toggles ("available next sprint"). Sprint 2 wires
provider selection. Sprint 3+4 enables the per-feature toggles when the
features themselves land.

Sprint contract path note:
The sprint contract listed this as `novelwriter/preferences/ai_panel.py`. We
chose `novelwriter/ai/preferences_panel.py` instead so all fork-specific code
lives under `novelwriter/ai/`, minimizing merge conflict surface with upstream
`novelwriter/dialogs/preferences.py`. This deviation is recorded in
`.planning/current/build/build-result.md`.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QFormLayout, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget,
)

from novelwriter.ai.config import AIConfig, AIFeature

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# DESIGN.md tokens — repeated locally to avoid coupling to a theme system that
# doesn't exist yet. These match `DESIGN.md`.
_COLOR_MUTED = "#7A6A4F"  # Foxing


class AIPreferencesPanel(QWidget):
    """Preferences > AI section.

    Sprint 1 contract:
    - Master toggle ("Enable AI for this project") with a sub-label.
    - Per-feature toggles greyed out with "available in next sprint" copy.
    - Provider rows hidden until enabled (Sprint 2).
    """

    def __init__(self, config: AIConfig, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("AIPreferencesPanel")

        self._config = config

        # Header
        self._title = QLabel(self.tr("AI features"), self)
        font = self._title.font()
        font.setBold(True)
        font.setPointSizeF(font.pointSizeF() + 2.0)
        self._title.setFont(font)

        self._desc = QLabel(
            self.tr(
                "Each feature stays off until you turn it on for this project. "
                "We never make a network call without explicit permission.",
            ),
            self,
        )
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet(f"color: {_COLOR_MUTED};")

        # Master toggle (Sprint 1 uses a checkbox-flavored stand-in via QLabel
        # + click handler so we don't pull in NSwitch from the upstream
        # extension tree before Sprint 2 design integration). Replaced by the
        # real switch widget when the panel gets embedded into the main
        # Preferences dialog in Sprint 2.
        self._master_toggle = _ToggleRow(
            label=self.tr("Enable AI for this project"),
            sub=self.tr("Master switch. Required for any AI feature below."),
            initial=self._config.enabled,
            parent=self,
        )
        self._master_toggle.toggled.connect(self._on_master_toggled)

        # Per-feature toggles (Sprint 1: disabled, with a "next sprint" sub-line)
        self._feature_rows: dict[AIFeature, _ToggleRow] = {}
        for feature, label, sub in (
            (
                AIFeature.REWRITE,
                self.tr("Inline rewrite"),
                self.tr("Available next sprint. Will let you select prose and request a rewrite."),
            ),
            (
                AIFeature.CONSISTENCY,
                self.tr("Consistency check"),
                self.tr(
                    "Available next sprint. Will cross-reference characters and timeline against your notes.",
                ),
            ),
        ):
            row = _ToggleRow(label=label, sub=sub, initial=False, parent=self)
            row.set_locked(True)
            self._feature_rows[feature] = row

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(self._title)
        layout.addWidget(self._desc)

        sep = QFrame(self)
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {_COLOR_MUTED};")
        layout.addWidget(sep)

        layout.addWidget(self._master_toggle)
        layout.addWidget(self._feature_rows[AIFeature.REWRITE])
        layout.addWidget(self._feature_rows[AIFeature.CONSISTENCY])
        layout.addStretch(1)

    def _on_master_toggled(self, checked: bool) -> None:
        self._config.enabled = checked
        # In Sprint 1 the per-feature toggles stay locked regardless of the
        # master switch state because no feature is shippable yet. Sprint 3
        # unlocks REWRITE and Sprint 4 unlocks CONSISTENCY.

    def config(self) -> AIConfig:
        """Return the AIConfig this panel is editing in-place."""
        return self._config


class _ToggleRow(QWidget):
    """Internal: a labelled row with a checkbox-flavored toggle.

    Sprint 1 uses a minimal native checkbox so we don't depend on upstream's
    NSwitch widget at this stage. Sprint 2 swaps to NSwitch when the panel is
    embedded into GuiPreferences.
    """

    from PyQt6.QtCore import pyqtSignal as _Sig

    toggled = _Sig(bool)

    def __init__(
        self,
        label: str,
        sub: str,
        initial: bool,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent=parent)

        from PyQt6.QtWidgets import QCheckBox  # local import keeps top-level small

        self._main = QLabel(label, self)
        font = self._main.font()
        font.setBold(True)
        self._main.setFont(font)

        self._sub = QLabel(sub, self)
        self._sub.setStyleSheet(f"color: {_COLOR_MUTED};")
        self._sub.setWordWrap(True)

        self._checkbox = QCheckBox(self)
        self._checkbox.setChecked(initial)
        self._checkbox.toggled.connect(self.toggled)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)
        text_layout.addWidget(self._main)
        text_layout.addWidget(self._sub)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        layout.addLayout(text_layout, 1)
        layout.addWidget(self._checkbox, 0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def set_locked(self, locked: bool) -> None:
        """Disable the toggle and grey the labels (Sprint 1 'available next sprint' state)."""
        self._checkbox.setEnabled(not locked)
        if locked:
            self._main.setStyleSheet(f"color: {_COLOR_MUTED};")
        else:
            self._main.setStyleSheet("")

    def is_checked(self) -> bool:
        return self._checkbox.isChecked()
