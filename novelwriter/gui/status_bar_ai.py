"""
Plotwright – Status-bar AI widget
=================================

A small click-to-open indicator that lives in the main window's status bar.
Sprint 1 surface (per ``DESIGN.md`` "Components > Status bar"):

* Always visible — the user never has to wonder whether AI is on.
* Default reads ``● AI: off`` in muted (Foxing) colour.
* When the AI master toggle is on it reads ``● AI: ready (mock)`` with a
  Hooker's Green dot.
* Click opens the AI Preferences pane.

Sprint 1 only emits the click signal; wiring it to the preferences dialog is
the host application's job (``GuiMain``) — the widget stays decoupled so it
can be unit-tested without the rest of the GUI.

The widget is also state-driven, not event-driven: callers update its state
by calling :meth:`setAiState` whenever the AIConfig changes. That avoids
binding the widget to any specific config-change signal.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from enum import Enum

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import QLabel, QWidget


class AIIndicatorState(str, Enum):
    """The visible states for the status-bar AI widget."""

    OFF = "off"
    READY_LOCAL = "ready_local"
    READY_CLOUD = "ready_cloud"
    WORKING = "working"


# Design tokens are duplicated here so the widget renders correctly even
# before a global Qt stylesheet exists. Update DESIGN.md if these change.
_DOT_COLORS: dict[AIIndicatorState, str] = {
    AIIndicatorState.OFF:         "#7A6A4F",  # Foxing
    AIIndicatorState.READY_LOCAL: "#2C5F5D",  # Hooker's Green
    AIIndicatorState.READY_CLOUD: "#2C5F5D",  # Hooker's Green
    AIIndicatorState.WORKING:     "#9B2C2C",  # Vermilion (AI-touch only)
}

_LABELS: dict[AIIndicatorState, str] = {
    AIIndicatorState.OFF:         "AI: off",
    AIIndicatorState.READY_LOCAL: "AI: ready (mock)",
    AIIndicatorState.READY_CLOUD: "AI: ready (cloud)",
    AIIndicatorState.WORKING:     "AI: working...",
}


class GuiStatusBarAI(QLabel):
    """Status-bar AI indicator. Click to open AI Preferences."""

    #: Emitted when the user clicks the indicator.
    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GuiStatusBarAI")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("AI status — click to open AI preferences.")
        self._state = AIIndicatorState.OFF
        self._refresh()

    # Public API ----------------------------------------------------------------

    def aiState(self) -> AIIndicatorState:
        """Return the current state. Useful for tests."""
        return self._state

    def setAiState(self, state: AIIndicatorState) -> None:
        """Update visible state. Idempotent."""
        if state != self._state:
            self._state = state
            self._refresh()

    # Qt events -----------------------------------------------------------------

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if ev is not None and ev.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
            ev.accept()
            return
        super().mousePressEvent(ev)

    # Internal ------------------------------------------------------------------

    def _refresh(self) -> None:
        dot = _DOT_COLORS[self._state]
        label = _LABELS[self._state]
        # Dot rendered in the dot's accent colour; the label stays Foxing for
        # consistency with the rest of the status bar chrome.
        self.setText(
            f'<span style="color:{dot}">●</span> '
            f'<span style="color:#7A6A4F">{label}</span>'
        )
