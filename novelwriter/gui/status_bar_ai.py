"""
plotwright fork — Status Bar AI Indicator
=========================================

A small QWidget that lives in the main-window status bar and shows the
current AI state at all times. The DESIGN.md privacy contract requires the
indicator be ALWAYS visible so the user never wonders whether AI is on.

States:
- "AI: off"          — neutral grey, master switch is False
- "AI: ready (mock)" — Hooker's Green dot, master switch True, provider name in parens
- "AI: working..."   — Vermilion dot pulsing (Sprint 2), during a live call

Sprint 1 only ships the off / ready states. The working pulse animation lands
with the first real provider in Sprint 2 when there is something to pulse for.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

if TYPE_CHECKING:
    from novelwriter.ai.config import AIConfig

logger = logging.getLogger(__name__)


# DESIGN.md token: Hooker's Green for "ready," Foxing for "off". Vermilion is
# reserved for working/AI-touched-region states only.
_COLOR_OFF = "#7A6A4F"      # Foxing
_COLOR_READY = "#2C5F5D"    # Hooker's Green
_COLOR_WORKING = "#9B2C2C"  # Vermilion (sacred — AI only)


class StatusBarAI(QWidget):
    """Status-bar widget showing AI feature state.

    Click the widget to open AI Preferences. Sprint 1 emits the click signal
    but the receiver (main window) wires it to GuiPreferences in a later sprint
    when the menu integration lands; for now the click is a no-op.
    """

    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("StatusBarAI")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._dot = QLabel(self)
        self._dot.setText("●")
        self._dot.setStyleSheet(f"color: {_COLOR_OFF}; font-size: 9pt;")

        self._label = QLabel(self.tr("AI: off"), self)
        self._label.setContentsMargins(4, 0, 8, 0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)

    def update_from_config(self, config: AIConfig, provider_name: str | None = None) -> None:
        """Refresh the indicator from an AIConfig (and optional active provider)."""
        if not config.enabled:
            self._dot.setStyleSheet(f"color: {_COLOR_OFF}; font-size: 9pt;")
            self._label.setText(self.tr("AI: off"))
            return
        # Master switch is on. Show ready and (if available) the provider name.
        self._dot.setStyleSheet(f"color: {_COLOR_READY}; font-size: 9pt;")
        if provider_name:
            self._label.setText(self.tr("AI: ready ({0})").format(provider_name))
        else:
            self._label.setText(self.tr("AI: ready"))

    def set_working(self, busy: bool) -> None:
        """Toggle the working state. Sprint 1 uses static color; pulse lands in Sprint 2."""
        if busy:
            self._dot.setStyleSheet(f"color: {_COLOR_WORKING}; font-size: 9pt;")
            self._label.setText(self.tr("AI: working..."))
        # If not busy, the caller is expected to call update_from_config() to
        # restore the off / ready state.

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: D102 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
