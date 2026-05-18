# Design Verification — Sprint 2 foundation phase

**Run:** `run-2026-05-12T01-45-20-695Z`
**QA attempt:** qa-2026-05-17T17-00-00-000Z
**Design contract:** `.planning/current/plan/design-contract.md` (607 lines, substantive)
**DESIGN.md state:** extended at /design-consultation with 3 new component specs (tab-bar, marginalia-rail empty-state, auth-flow state machine)

## Scope of visual verification

Sprint 2 foundation phase delivers two of the three design-contract component surfaces in code form: AI Preferences panel (Component 3 OAuth state machine, partial) and status bar widget (extends DESIGN.md "Status bar" component with v1.1.1 ERROR state). The four-tab IA and marginalia rail primitive (Components 1 and 2 of the design contract) are explicitly deferred to follow-on `/build` per `build-result.md:35-37`.

Verification was performed at code-inspection level + Qt offscreen smoke. No screenshot comparison because this is a native desktop app, not a web surface — the equivalent evidence is state-machine inspection (captured in qa-report.md Health Check 3) plus design-token grep against DESIGN.md anchors.

## Components verified

### Status bar widget (extends DESIGN.md "Status bar" component)

| DESIGN.md anchor | Implementation | Verdict |
|---|---|---|
| 1Hz vermilion pulse on working state only | `_PULSE_DURATION_MS = 500` half-period (1Hz cycle) at `status_bar_ai.py:88`; `_COLOR_WORKING = "#9B2C2C"` Vermilion at `:89` | ✓ pass |
| Working state is the ONLY chrome use of vermilion | grep `9B2C2C` in `status_bar_ai.py` returns one hit (working state) and zero hits elsewhere in chrome | ✓ pass |
| Error state uses Error `#7A2222`, NOT Vermilion | `_COLOR_ERROR = "#7A2222"` at `:90`; smoke test set_error → state="error" + provider="anthropic" rendered with Error color | ✓ pass |
| Provider-name label is lowercase, no model name | smoke test: `provider_label` stored verbatim from caller; convention enforcement happens at caller site (registry returns names like "anthropic", not "anthropic:claude-sonnet-4-5" for the label) | ⚠ partial — see Q-2 below |
| Multi-feature mixed providers: label = `(mixed)` | `_LABEL_MIXED = "mixed"` defined at `:91`; logic path enabled via `update_from_config` when config has different providers per feature | ✓ pass |
| Tooltip uses Qt-default style (no custom popup) | smoke test: no custom QToolTip subclass detected; widget relies on `setToolTip()` | ✓ pass |
| Keyboard reachable + accessibleName | smoke test: widget has Tab focus policy + keyPressEvent override visible at `:323`; accessibleName set per state in `_refresh_accessible_name` at `:272` | ✓ pass |

**Status bar verdict:** design contract honored. Anti-slop: vermilion only appears on the working-state dot. Error state correctly uses `#7A2222` (the design-specified deeper red).

### AI Preferences panel (Component 3 OAuth state machine, partial)

| DESIGN.md anchor | Implementation | Verdict |
|---|---|---|
| ZERO vermilion in any OAuth state | grep `9B2C2C\|Vermilion\|vermilion` in `preferences_panel.py` returns zero hits | ✓ pass |
| Plain text "Sign in with Google" — no Google branded artwork | `_GeminiConfigRow._on_signin_clicked` and the sign-in button construction at `:738-750` use a plain QPushButton with text only, no QIcon | ✓ pass |
| Disabled state when API-key radio selected: button disabled, NOT hidden | `preferences_panel.py:807` uses `_oauth_container.setVisible(False)` on radio-flip, hiding the whole container including the OAuth button. **DEVIATION from design contract** which says "Disabled state ... disabled, not hidden, for tab-order stability." | ⚠ S-18 advisory (gemini audit finding) |
| Idle state: Secondary button (transparent, 1px Foxing border, Ink label) | grep DESIGN.md colors `7A6A4F` (Foxing), `1C1B17` (Ink) in `preferences_panel.py` — present in stylesheet declarations | ✓ pass |
| Pending state: 1px Hooker's Green progress strip, no spinner | NOT IMPLEMENTED — `_on_signin_clicked` only changes button text. **DEVIATION; S-6 advisory** | ⚠ deferred to follow-on |
| Error state: Error `#7A2222` helper text | `_COLOR_ERROR` referenced; pattern matches DESIGN.md | ✓ pass |
| Signed-in row: Hooker's Green dot + email (IBM Plex Mono Foxing) + Sign out button | UI elements present in code but full UX path is stubbed (sign-in handler doesn't fire the real OAuth flow) | ⚠ deferred |

**AI Preferences panel verdict:** design contract substantially honored on the parts that landed (vermilion discipline, plain-text Google button, color palette). Two design-contract deviations recorded as `/review` advisories: hide-vs-disable on radio toggle (S-18 sub) and PENDING state UX not implemented (S-6). Both deferred to follow-on /build per build-result.md.

### Components NOT verified (deferred to follow-on /build)

- **Component 1: Four-tab top-level IA (tab-bar)** — not implemented in this foundation phase. SC-10 explicitly deferred per build-result.md.
- **Component 2: Marginalia rail primitive (empty-state)** — not implemented. Deferred with Component 1.

These components remain in the design contract and will be verified by the QA pass after the follow-on /build lands them.

## Anti-slop audit (DESIGN.md "Anti-Slop Rules")

| Anti-slop rule | Status |
|---|---|
| No purple/violet | ✓ (zero `#[6-9][0-9A-F]00[6-9][0-9A-F]` or named purple in `novelwriter/ai/`) |
| No gradient buttons / hero / anything | ✓ (zero `linear-gradient` or `qlineargradient` in `novelwriter/ai/`) |
| No 3-column icon grids in colored circles | ✓ |
| No "✨ AI" sparkle / wand / star / magic | ✓ (zero `✨` or `sparkle` or `wand` in `novelwriter/ai/`) |
| No chat-bubble UI for AI output | ✓ (no chat surface in this foundation build; AI output is marginalia per locked decision #1) |
| No "Generated by AI" badges on accepted content | n/a (no accepted content yet — rewrite ships S3) |
| No stock-photo hero shots | ✓ |
| No decorative blobs / waves / abstract shapes | ✓ |
| No centered everything; asymmetry default | ✓ (Preferences panel uses left-aligned headings per code inspection) |
| No Google branded button artwork | ✓ (NEW anti-slop rule added at /design-consultation; verified above) |
| No success modals on auth flow completion | ✓ (NEW anti-slop rule; verified: signed-in state shows a row, not a modal) |

**Anti-slop verdict:** clean. Every locked anti-slop rule is honored in the code that landed.

## Two Locked Risk Decisions (DESIGN.md "Two Locked Risk Decisions")

| Locked decision | Status in S2 foundation |
|---|---|
| #1 AI as marginalia, not chat | Honored. No chat surface in this build. AI tab and marginalia rail are deferred to follow-on /build per build-result.md but the design contract reserves them. |
| #2 Manuscript theme canonical (cream paper default) | Not exercised in foundation phase — theme toggle is not yet wired and the existing upstream stylesheet is unchanged. Will be verified in the WS-4 follow-on /build that ships the project shell IA. |

## Re-verification at write time

- `grep -c 9B2C2C novelwriter/ai/preferences_panel.py` → 0 (zero vermilion in preferences chrome)
- `grep -c 9B2C2C novelwriter/gui/status_bar_ai.py` → 1 (working state only)
- `grep -c sparkle\|✨\|wand novelwriter/ai/ novelwriter/gui/` → 0
- `grep -c "Sign in with Google" novelwriter/ai/preferences_panel.py` → present as plain text

All grep evidence reproduces at report-write time. No transients.

## Design verification verdict

**partial-pass with deferred items.**

Implemented surfaces (status bar widget + AI Preferences panel) honor the design contract on every locked rule that applies to this foundation phase. Two design-contract deviations are recorded as `/review` advisories (S-6 PENDING UX, S-18 hide-vs-disable) and are tracked for the follow-on /build. Components 1 and 2 (four-tab IA, marginalia rail) are not implemented; deferred per build-result.md. The deferral is honest and the design contract remains the source of truth when the follow-on /build runs.

No design-contract violations were silently introduced. Anti-slop rules are clean. Vermilion discipline is enforced (zero use in chrome except the documented status-bar pulse).
