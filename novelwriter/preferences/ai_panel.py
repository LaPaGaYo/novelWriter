"""
Plotwright – AI preferences pane
================================

Sprint 1 surface (per design contract — see DESIGN.md "Preferences > AI"):

* A master "Enable AI features" toggle.
* Per-feature opt-ins for ``rewrite`` and ``consistency``, *disabled* in
  Sprint 1 with the help text "Available in next sprint".
* No provider rows — those appear in Sprint 2 once real providers exist.

The panel is a free function that injects rows into the existing
:class:`GuiPreferences` form rather than a sub-dialog of its own. That
keeps search/scroll behaviour consistent with the rest of the dialog.

File History:
Created: 2026-04-26 [Sprint 1]
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from novelwriter.ai.config import AIConfig, FEATURE_CONSISTENCY, FEATURE_REWRITE
from novelwriter.extensions.switch import NSwitch

if TYPE_CHECKING:
    from novelwriter.dialogs.preferences import GuiPreferences


class AIPreferencesPanel:
    """Sprint 1 AI preferences section.

    Owns the QWidgets it creates. The hosting dialog is responsible for
    calling :meth:`build` during its own ``buildForm()`` and reading
    :attr:`config` back when saving. Sprint 2 will replace the
    in-memory ``config`` with project-bound persistence.
    """

    SECTION_TITLE = "AI"
    NEXT_SPRINT_HELP = "Available in next sprint."

    def __init__(self, dialog: GuiPreferences, initial: AIConfig | None = None) -> None:
        self._dialog = dialog
        self.config: AIConfig = initial or AIConfig()

        # Widgets — created lazily in build() so we can use the dialog's tr().
        self.aiEnabled: NSwitch | None = None
        self.featureRewrite: NSwitch | None = None
        self.featureConsistency: NSwitch | None = None

    def build(self, section_index: int) -> int:
        """Add the AI section to the dialog's sidebar + form.

        Returns the section index used so the caller can keep counting.
        """
        dialog = self._dialog
        title = dialog.tr(self.SECTION_TITLE)
        dialog.sidebar.addButton(title, section_index)
        dialog.mainForm.addGroupLabel(title, section_index)

        # Master toggle
        self.aiEnabled = NSwitch(dialog)
        self.aiEnabled.setChecked(self.config.enabled)
        dialog.mainForm.addRow(
            dialog.tr("Enable AI features"),
            self.aiEnabled,
            dialog.tr(
                "Per-project opt-in. AI features remain disabled across all "
                "projects unless you turn this on. With AI off, the application "
                "performs zero outbound network requests."
            ),
        )

        # Per-feature toggles — Sprint 1 keeps these greyed.
        self.featureRewrite = self._buildDisabledFeatureSwitch(
            FEATURE_REWRITE,
            dialog.tr("Inline rewrite (Sprint 3)"),
        )
        self.featureConsistency = self._buildDisabledFeatureSwitch(
            FEATURE_CONSISTENCY,
            dialog.tr("Consistency check (Sprint 4)"),
        )

        return section_index

    def applyTo(self, target: AIConfig) -> AIConfig:
        """Mirror current widget state into ``target`` and return it.

        Sprint 1 saves only the master toggle — the per-feature switches
        are presentation-only until their owning feature ships.
        """
        if self.aiEnabled is not None:
            target.enabled = bool(self.aiEnabled.isChecked())
        return target

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _buildDisabledFeatureSwitch(self, feature: str, label: str) -> NSwitch:
        dialog = self._dialog
        switch = NSwitch(dialog)
        switch.setChecked(self.config.feature_flags.get(feature, False))
        switch.setEnabled(False)
        dialog.mainForm.addRow(label, switch, dialog.tr(self.NEXT_SPRINT_HELP))
        return switch
