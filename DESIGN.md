# Plotwright Design Contract

This file is the design contract for Plotwright (a fork of novelWriter). It
is referenced by code (`novelwriter/gui/status_bar_ai.py`,
`novelwriter/preferences/ai_panel.py`) and by Sprint 1's
`.planning/current/plan/design-contract.md`. Any visible UI work must
respect what is captured here.

## Visual language

| Token            | Hex        | Usage                                                       |
|------------------|------------|-------------------------------------------------------------|
| Foxing           | `#7A6A4F`  | Default chrome text and muted indicators (e.g. AI off).     |
| Hooker's Green   | `#2C5F5D`  | "Ready" indicators (AI ready, save complete).               |
| Vermilion        | `#9B2C2C`  | AI-touch only — staged proposals, in-flight model work.     |
| Parchment        | `#F5EFE0`  | Document background tint (light theme).                      |
| Charcoal         | `#1F1A14`  | Primary text on Parchment.                                   |

**AI surfaces use a dedicated accent (Vermilion) reserved for AI-touch.**
No non-AI surface uses Vermilion.

## Typography

* Body text: project-default editor font (currently inherited from upstream).
* Status bar / chrome: 11pt sans-serif via Qt's default style; preserve the
  upstream cadence so the new AI indicator does not visually dominate.
* The status-bar AI label is a single text run (`● AI: <state>`); the dot is
  rendered via inline HTML span, the label is Foxing.

## Components — Sprint 1

### Status bar — AI indicator

Owner module: `novelwriter/gui/status_bar_ai.py`.

* **Always visible.** Sits to the left of the session clock.
* States and labels:
  * `OFF` → `● AI: off` with Foxing dot. Default.
  * `READY_LOCAL` → `● AI: ready (mock)` with Hooker's Green dot.
  * `READY_CLOUD` → `● AI: ready (cloud)` with Hooker's Green dot.
  * `WORKING` → `● AI: working...` with Vermilion dot (used in Sprint 3+).
* **Cursor:** pointing hand. **Tooltip:** "AI status — click to open AI
  preferences."
* Click opens the Preferences dialog at the AI section.

### Preferences > AI

Owner module: `novelwriter/preferences/ai_panel.py`.

* Section title: `AI`. Lives at the end of the dialog after `Features`.
* Master toggle: `Enable AI features` (default off). Help text explains the
  privacy contract: "Per-project opt-in. AI features remain disabled across
  all projects unless you turn this on. With AI off, the application
  performs zero outbound network requests."
* Per-feature toggles: `Inline rewrite (Sprint 3)` and
  `Consistency check (Sprint 4)`. Both are `disabled` (greyed) in Sprint 1
  with the help text "Available in next sprint."
* Provider rows: hidden in Sprint 1. Land in Sprint 2 alongside real
  providers.

## Out of scope (Sprint 1)

The other six surfaces named in `.planning/current/frame/design-intent.json`
— project shell, scene-card view, character panel, AI inspector dock, AI
review pane, consistency-check inline markers — are deferred to Sprints
2-5. The visual language above is locked in Sprint 1 so those surfaces
inherit it.

## Change protocol

Any change to the colour tokens, status-bar states, or AI section structure
requires updating this file in the same PR as the code change. The AI panel
and status-bar widget reference this file in their docstrings and CI lint
catches drift via the design-review skill.
