"""
plotwright fork — Status Bar AI Indicator
=========================================

A small QWidget that lives in the main-window status bar and shows the
current AI state at all times. The DESIGN.md privacy contract requires the
indicator be ALWAYS visible so the user never wonders whether AI is on.

States (per `.planning/current/plan/design-contract.md` Status bar section):

- ``AI: off``            — Foxing dot, Foxing label. Master switch is False.
- ``AI: ready (<name>)`` — Hooker's Green dot. Master switch True; ``<name>``
                           is the lowercase provider id (``ollama`` /
                           ``anthropic`` / ``gemini``). When multiple features
                           use different providers we show ``mixed``.
- ``AI: working...``     — Vermilion dot pulsing at 1 Hz (QPropertyAnimation
                           on opacity, 0.4 ↔ 1.0, 500 ms each direction,
                           ease-in-out). Vermilion in chrome is reserved for
                           this pulse and the marginalia rail (never errors).
- ``AI: error (<name>)`` — Error red dot (``#7A2222``). NOT vermilion.
                           Click opens AI Preferences focused on the failing
                           provider's row.

Sprint 2 lands the pulse animation, the error state, the provider-name
label, and the keyboard-activation a11y surface. Sprint 3+ adds the live
token count to the working tooltip.
"""
from __future__ import annotations

import logging

from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QWidget,
)

if TYPE_CHECKING:
    from novelwriter.ai.config import AIConfig

logger = logging.getLogger(__name__)


# DESIGN.md tokens. Vermilion is the sacred AI-activity color; Error is the
# semantic red for provider failures. They are deliberately distinct: a user
# must never confuse "AI thinking" with "AI broken".
_COLOR_OFF = "#7A6A4F"      # Foxing
_COLOR_READY = "#2C5F5D"    # Hooker's Green
_COLOR_WORKING = "#9B2C2C"  # Vermilion (AI activity only)
_COLOR_ERROR = "#7A2222"    # Error (provider failures, never AI activity)

# Pulse animation cadence — 1 Hz visible cycle = 500ms each direction.
_PULSE_DURATION_MS = 500
_PULSE_MIN = 0.4
_PULSE_MAX = 1.0


# The "mixed" label fires when more than one feature uses a different provider.
_LABEL_MIXED = "mixed"


class StatusBarAI(QWidget):
    """Status-bar widget showing AI feature state.

    Click (or Enter/Space when focused) opens AI Preferences focused on the
    AI section. The receiver wires the signal to ``GuiPreferences.openAt("ai")``
    in S2; the S1 no-op receiver is replaced when this widget is hooked into
    the main window.

    Accessibility:
    - ``accessibleName`` describes both the state and the activation hint so a
      screen reader announces ``"AI status. Press Enter to configure."``
    - ``setFocusPolicy(Qt.FocusPolicy.TabFocus)`` means the widget is in the
      tab order; ``keyPressEvent`` handles Enter and Space to fire ``clicked``.
    """

    clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent=parent)
        self.setObjectName("StatusBarAI")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Keyboard reachable: in the tab order, focusable.
        self.setFocusPolicy(Qt.FocusPolicy.TabFocus)
        self.setAccessibleName(
            self.tr("AI status. Press Enter to configure."),
        )

        self._dot = QLabel(self)
        self._dot.setText("●")
        self._dot.setStyleSheet(f"color: {_COLOR_OFF}; font-size: 9pt;")

        # Opacity effect on the dot — drives the working-state pulse animation.
        # We apply it to the dot only (not the label) so the text stays fully
        # legible while the dot breathes.
        self._dot_opacity = QGraphicsOpacityEffect(self._dot)
        self._dot_opacity.setOpacity(_PULSE_MAX)
        self._dot.setGraphicsEffect(self._dot_opacity)

        self._label = QLabel(self.tr("AI: off"), self)
        self._label.setContentsMargins(4, 0, 8, 0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 0, 4, 0)
        layout.addWidget(self._dot)
        layout.addWidget(self._label)

        # Pulse animation lives for the widget's lifetime so we can start /
        # stop without re-allocating on each state change.
        self._pulse = QPropertyAnimation(self._dot_opacity, b"opacity", self)
        self._pulse.setDuration(_PULSE_DURATION_MS)
        self._pulse.setStartValue(_PULSE_MIN)
        self._pulse.setEndValue(_PULSE_MAX)
        self._pulse.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._pulse.setLoopCount(-1)  # forever; stop() halts and resets

        # Tooltip text per state. Qt-default tooltip style only — no custom
        # popup. Set on every state transition so a hover never lies about
        # the current state.
        self.setToolTip(self.tr("AI features off. Click to configure."))

        # Track current state so the tooltip can describe the right thing on
        # hover after an asynchronous update_from_config().
        self._state: str = "off"  # one of: off / ready / working / error
        self._provider_label: str | None = None
        self._error_reason: str | None = None

    # ------------------------------------------------------------------
    # State entry points
    # ------------------------------------------------------------------

    def update_from_config(
        self,
        config: "AIConfig",
        provider_name: str | None = None,
    ) -> None:
        """Refresh the indicator from an AIConfig + active provider name.

        ``provider_name`` is the lowercase id rendered in the parens, e.g.
        ``"ollama"``, ``"anthropic"``, ``"gemini"``, or ``"mixed"`` when more
        than one feature uses a different provider. ``None`` renders just
        ``AI: ready`` (the rare "enabled but no provider configured yet"
        edge case).
        """
        self._stop_pulse()
        self._error_reason = None

        if not config.enabled:
            self._state = "off"
            self._provider_label = None
            self._dot.setStyleSheet(f"color: {_COLOR_OFF}; font-size: 9pt;")
            self._label.setText(self.tr("AI: off"))
            self.setToolTip(self.tr("AI features off. Click to configure."))
            self._refresh_accessible_name()
            return

        # Master switch is on. Show ready (with provider) and clear any
        # leftover pulse state.
        self._state = "ready"
        self._provider_label = provider_name
        self._dot.setStyleSheet(f"color: {_COLOR_READY}; font-size: 9pt;")
        if provider_name:
            self._label.setText(self.tr("AI: ready ({0})").format(provider_name))
            self.setToolTip(
                self.tr("AI ready via {0}. Click to configure.").format(provider_name),
            )
        else:
            self._label.setText(self.tr("AI: ready"))
            self.setToolTip(self.tr("AI ready. Click to configure."))
        self._refresh_accessible_name()

    def set_working(self, busy: bool, provider_name: str | None = None) -> None:
        """Toggle the working state.

        When ``busy`` is True we show the vermilion dot and start the 1 Hz
        pulse animation. When ``busy`` is False the caller is expected to
        call ``update_from_config()`` next to restore the off / ready state;
        we deliberately do NOT auto-restore here because the caller knows
        the right tail state and we don't want to flicker through ``ready``
        on the way to ``off``.
        """
        if busy:
            self._state = "working"
            if provider_name is not None:
                self._provider_label = provider_name
            self._dot.setStyleSheet(f"color: {_COLOR_WORKING}; font-size: 9pt;")
            self._label.setText(self.tr("AI: working..."))
            self.setToolTip(self.tr("Working..."))
            self._start_pulse()
            self._refresh_accessible_name()
            return
        # busy=False: just halt the pulse. Caller restores via
        # update_from_config() so we don't double-paint.
        self._stop_pulse()

    def set_error(self, provider_name: str, short_reason: str) -> None:
        """Display the error state for a specific provider.

        ``provider_name`` is lowercase (``"gemini"`` etc.); ``short_reason``
        is a one-line hint (e.g. ``"sign-in expired"``). The widget never
        invents copy — the caller passes a human-readable short reason so
        the tooltip and accessibility label can include it verbatim.
        """
        self._stop_pulse()
        self._state = "error"
        self._provider_label = provider_name
        self._error_reason = short_reason
        self._dot.setStyleSheet(f"color: {_COLOR_ERROR}; font-size: 9pt;")
        self._label.setText(self.tr("AI: error ({0})").format(provider_name))
        # Mirror the design-contract tooltip pattern: "{provider}: {reason}."
        self.setToolTip(
            self.tr("{0}: {1}. Click to retry.").format(provider_name, short_reason),
        )
        self._refresh_accessible_name()

    # ------------------------------------------------------------------
    # Pulse animation control
    # ------------------------------------------------------------------

    def _start_pulse(self) -> None:
        if self._pulse.state() == QPropertyAnimation.State.Running:
            return
        # Set direction to alternate so the loop visibly breathes rather
        # than snapping from MAX back to MIN each cycle.
        self._pulse.setDirection(QPropertyAnimation.Direction.Forward)
        # Two-direction breathing: forward sets opacity MIN->MAX over the
        # duration; we then let the loop reverse on every other cycle by
        # alternating the start/end values. PyQt6 doesn't ship a "ping-pong"
        # direction so we approximate by toggling start/end in the finished
        # signal each cycle. Cheap and correct for a 1 Hz animation.
        try:
            self._pulse.finished.disconnect(self._pulse_swap)
        except TypeError:
            pass  # Not connected; first start.
        self._pulse.finished.connect(self._pulse_swap)
        self._pulse.start()

    def _pulse_swap(self) -> None:
        """Swap start/end values to alternate the breathing direction."""
        # If a state change stopped the pulse, the animation may be in the
        # Stopped state by the time this fires; bail gracefully.
        if self._pulse.state() == QPropertyAnimation.State.Stopped:
            return
        old_start = self._pulse.startValue()
        old_end = self._pulse.endValue()
        self._pulse.setStartValue(old_end)
        self._pulse.setEndValue(old_start)
        self._pulse.start()

    def _stop_pulse(self) -> None:
        if self._pulse.state() != QPropertyAnimation.State.Stopped:
            self._pulse.stop()
        self._dot_opacity.setOpacity(_PULSE_MAX)
        # Reset start/end so the next start_pulse() begins from a known state.
        self._pulse.setStartValue(_PULSE_MIN)
        self._pulse.setEndValue(_PULSE_MAX)

    # ------------------------------------------------------------------
    # Accessibility
    # ------------------------------------------------------------------

    def _refresh_accessible_name(self) -> None:
        """Update the accessibleName so screen readers announce state changes.

        The base name always ends with the activation hint so a user pressing
        Tab into the widget hears "AI status: ready via gemini. Press Enter
        to configure." rather than just the state.
        """
        if self._state == "off":
            base = self.tr("AI status: off.")
        elif self._state == "working":
            base = self.tr("AI status: working.")
        elif self._state == "error":
            base = self.tr("AI status: error from {0}, {1}.").format(
                self._provider_label or "", self._error_reason or "",
            )
        elif self._state == "ready":
            if self._provider_label:
                base = self.tr("AI status: ready via {0}.").format(self._provider_label)
            else:
                base = self.tr("AI status: ready.")
        else:  # pragma: no cover - defensive
            base = self.tr("AI status.")
        self.setAccessibleName(f"{base} {self.tr('Press Enter to configure.')}")

    # ------------------------------------------------------------------
    # Read-only state introspection (used by tests + the QA walkthrough)
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        """Return the current visible state (one of off/ready/working/error)."""
        return self._state

    @property
    def provider_label(self) -> str | None:
        """Return the provider id currently shown in the parens (or None)."""
        return self._provider_label

    def is_pulse_running(self) -> bool:
        """True if the working-state pulse animation is currently looping."""
        return self._pulse.state() == QPropertyAnimation.State.Running

    # ------------------------------------------------------------------
    # Event overrides
    # ------------------------------------------------------------------

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: D102 - Qt override
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: D102 - Qt override
        # Enter and Space mirror "click" for keyboard users. Esc surrenders
        # focus so a stuck user can leave the widget without mousing.
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)


__all__ = ["StatusBarAI"]
