"""
Plotwright – Preferences extension package
==========================================

Holds preference-pane code that doesn't belong inside the existing
``novelwriter/dialogs/preferences.py`` because it's fork-specific (e.g.
the AI section) or large enough to deserve its own module.

The existing :class:`GuiPreferences` dialog imports from this package and
calls in to add sections during ``buildForm``.

File History:
Created: 2026-04-26 [Sprint 1]
"""
