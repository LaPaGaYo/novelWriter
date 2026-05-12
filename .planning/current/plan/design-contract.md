# Design Contract — Sprint 2

Substantive design contract for the WS-4 surfaces that Sprint 2 introduces. Replaces
the day-1 scheduling placeholder. Produced by `/design-consultation` on 2026-05-12.

`/handoff` transition rule: this file must exceed 200 lines OR contain the
`## DESIGN.md Component Amendments` header. Both are now true.

## Locked anchors (carry forward from DESIGN.md)

Three rules cannot bend in any S2 component spec:

1. **Vermilion `#9B2C2C` is reserved for AI-touched regions.** Authentication, tabs,
   loading states, errors, focus rings — none of these get vermilion. The only place
   vermilion appears in chrome is the status-bar "AI: working..." pulsing dot, which
   semantically is AI activity.
2. **Cream paper (Cotton `#F4EFE6` / Ink `#1C1B17`) is the canonical theme.** Dark mode
   exists but is secondary. Every spec below assumes Cotton canvas first.
3. **AI as marginalia, never chat.** The AI tab is the marginalia surface, not a chat
   sidebar. The empty-state must teach the marginalia metaphor, not invite typing.

Spacing base is 4px. Radius is 2px on every surface. No gradients. No sparkles. No
wands. No "✨ AI" iconography anywhere.

---

## Component 1: Four-tab top-level IA (tab-bar)

### Why

Sprint 2 is the first sprint where a returning upstream-novelWriter user sees that
plotwright is a different product. The four-tab structure is the visual differentiator
that anchors the rest of the v1 IA work in S3-S5.

### Geometry

Tab bar sits at the top of the main window, below the menu bar, above the three-column
content area. Full window width.

```
+------------------------------------------------------------------+
| File  Edit  View  Project  Tools  AI  Help                       |
+------+--------+--------+--------+--------------------------------+
| Out  | Manu   | Notes  | AI     |                                |
| line | script |        |        |     (active-tab underline)     |
+------+--------+--------+--------+--------------------------------+
| (three-column content area below: tree | manuscript | rail)      |
```

### Tab labels

Full words. No icons (anti-slop rule: no decorative icons; tab labels read better).

- **Outline** (Cmd/Ctrl+1)
- **Manuscript** (Cmd/Ctrl+2)
- **Notes** (Cmd/Ctrl+3)
- **AI** (Cmd/Ctrl+4)

Order rationale: writing flow is plan → write → reference → review. AI sits last
because it operates ON the prior three, not parallel to them.

### Typography

- Tab label: **IBM Plex Sans 13px / 500 weight / Ink color** in default state
- Hover / unfocused-active distinction is via underline width, not weight change (avoids
  layout shift from weight changes)
- Letter-spacing: 0 (default for IBM Plex Sans at 13px)
- Capitalization: title case ("Outline", not "OUTLINE")

### States

| State | Visual | Color | Underline |
|-------|--------|-------|-----------|
| Inactive | Ink label, no underline | Ink `#1C1B17` | none |
| Hover | Ink label, 1px Foxing underline 2px below baseline | Ink `#1C1B17` | 1px Foxing `#7A6A4F` |
| Active | Ink label, 2px Hooker's Green underline 2px below baseline | Ink `#1C1B17` | 2px Hooker's Green `#2C5F5D` |
| Focused (keyboard) | adds 1px Hooker's Green outline at 2px offset around the tab cell | Ink | 2px Hooker's Green (if also active) |

No background color change between states. The underline does the entire job. Avoids
the "button-fight" feel of pill-shaped tabs.

### Spacing

- Tab cell: 8px vertical / 16px horizontal padding (compact density per DESIGN.md
  "chrome" rule)
- Gap between tabs: 0 (cells abut). Visual separation comes from the active underline,
  not from gaps.
- Bottom border of tab bar: 1px Foxing across full width, broken only by the active tab's
  underline (which sits on the same baseline)

### Keyboard

- Cmd/Ctrl+1..4: jump to that tab (global shortcut)
- Tab order: tab bar receives focus after the menu bar, before the project tree
- When tab bar has focus: Left/Right arrows cycle tabs; Enter/Space activates the
  focused tab; Esc returns focus to the previous widget
- Tab labels expose `accessibleName` matching the visible text

### Motion

None. Tab switching is instant. The 200-250ms "panel slide" duration from DESIGN.md
applies to accordions and slide-out panels, not tab content swaps. Tab content replaces
the column content with no transition. Reasoning: tabs are navigation, not narrative.

### Anti-slop guardrails

- No icons on tabs. No "✨" anywhere.
- No pill-shaped tab backgrounds.
- No colored circles around the AI tab label.
- The AI tab label is plain text "AI". Not "✨ AI", not "AI ✨", not "AI Assistant".

### Accessibility notes

- Color contrast: Ink-on-Cotton is `#1C1B17` on `#F4EFE6` ≈ 14:1, WCAG AAA at body size.
  Plenty.
- Hooker's Green underline on Cotton: `#2C5F5D` on `#F4EFE6` ≈ 6.4:1, WCAG AA Large
  (which is what 13px qualifies as). Good.
- Keyboard reachability is non-negotiable. The shortcut Cmd/Ctrl+1..4 plus arrow-key nav
  inside the bar covers mouse-free operation.

---

## Component 2: Marginalia rail empty-state

### Why

The marginalia rail is the structural answer to "AI as marginalia, not chat" (DESIGN.md
Locked Decision #1). It must exist in S2 even though no AI features fire yet, so S3 can
ship the rewrite review pane without also building the rail primitive. The empty state
is what the user sees in S2.

### Geometry

The rail occupies the right column of the three-column layout. Width is fixed:
**280-320px** (DESIGN.md "Layout" section already locked this range). Use **300px** as
the S2 default.

```
+------------------+------------------------+-------------------+
| Project          | Manuscript             | Marginalia rail   |
| tree             | column                 | (this component)  |
|                  |                        |                   |
| (200-240px)      | (60ch enforced)        | (300px fixed)     |
|                  |                        |                   |
+------------------+------------------------+-------------------+
```

In the Manuscript tab: the rail is the live editor's-notes view, scroll-locked to the
manuscript column.

In the AI tab: the rail can be empty (S2) or can host filters/queue (S3+). For S2, the
rail in the AI tab renders the same empty state as elsewhere.

### Empty-state content

Three text blocks, vertically stacked, top-aligned (NOT centered — DESIGN.md anti-slop
forbids centered-everything).

**Block 1 (kind line):**

> EDITOR'S NOTES

- Font: IBM Plex Mono 10px uppercase
- Color: **Foxing `#7A6A4F`** (NOT vermilion — there is no AI activity yet, so the
  kind-line is in the metadata color, not the AI color)
- Letter-spacing: 0.1em
- Position: 24px from top of rail, 20px from left edge

**Block 2 (body):**

> No notes yet. When you ask the AI to review a passage, its observations land here as
> marginalia, alongside the manuscript, never on top of it.

- Font: Source Serif 4 14px / italic / 1.5 line-height
- Color: Ink `#1C1B17`
- Max-width: rail-width minus left padding (so it wraps naturally)
- 16px below the kind-line

**Block 3 (caption):**

> Inline rewrite arrives in the next release. Consistency check follows.

- Font: IBM Plex Mono 11px (matches DESIGN.md "Marginalia entry" reference role)
- Color: Foxing `#7A6A4F`
- 24px below the body

No other content. No illustration. No "Get Started" button. No "Learn more →" link. The
empty state is editorial copy, not a marketing surface.

### Color and surface

- Rail background: Vellum `#EDE3CF` (per DESIGN.md "Marginalia rail: surface elevation"
  pattern)
- Left edge: 1px Foxing vertical divider separating the rail from the manuscript column
- No border-radius (it's a full-height pane, not a card)
- No shadow

### When the rail later renders entries (S3+)

Already specified in DESIGN.md "Marginalia entry" component section:
- 2px Vermilion left-border per entry
- IBM Plex Mono 10px uppercase Vermilion kind-line
- Source Serif 4 14px italic body
- 16px gap between entries

The empty-state must not pre-bake any of that vermilion. When the first AI suggestion
lands in S3, the rail population is the user's first encounter with vermilion in
chrome (after the status bar pulse).

### States

| State | Visible | When |
|-------|---------|------|
| Empty (S2) | Three text blocks as above | No AI suggestions exist |
| Populated (S3+) | List of Marginalia entries per DESIGN.md component | At least one AI suggestion exists |
| Loading (S3+) | Thin 1px Hooker's Green progress strip at the very top of the rail, indeterminate | AI call in flight |
| Error (S3+) | Single entry with kind line "ERROR" in Error `#7A2222`, NOT vermilion | AI call failed |

S2 only ships the empty state. The other three are listed for completeness so the rail
widget is built with state-switching from day 1.

### Anti-slop guardrails

- No illustration, no empty-state cartoon, no "no items yet" icon.
- No call-to-action button. The user does not "create their first marginalia entry."
  Entries appear when the user asks the AI to review something.
- The kind line is **Foxing**, not Vermilion. Confirming: the empty state has zero
  vermilion. If a reviewer sees vermilion here, the build is wrong.

### Accessibility notes

- The rail has a landmark role (`role="complementary"` in HTML terms; Qt equivalent is
  `accessibleName="Editor's notes"` + `accessibleDescription`)
- Screen readers announce the kind line + body + caption as three separate items
- Keyboard reachable via Tab; arrow keys do not navigate inside the empty state (nothing
  to navigate to)

---

## Component 3: Auth-flow state machine (Gemini OAuth)

### Why

Gemini is the only v1 provider that supports OAuth ("Sign in with Google") alongside
API-key auth. This is the S2 release lede per the decision-brief Sprint 2 boundary:
the only desktop novel-writing tool with Gemini OAuth, free-tier in 30 seconds, no
credit card.

The OAuth UX must NOT borrow any vermilion or AI-magic styling. Authentication is
chrome, not AI activity.

### Location

`Preferences → AI → Gemini`. The Gemini provider row, when expanded, contains:

1. A radio group: `( ) API key` and `(•) Sign in with Google` (default to the radio
   the user previously selected; first-run default is "API key" because it's the
   safer guess about user intent)
2. Below the radio group, the content for the selected option appears.

### States (auth flow state machine)

```
              ┌────────────┐
              │   IDLE     │
              │ (signed-   │
              │   out)     │
              └─────┬──────┘
                    │ user clicks "Sign in with Google"
                    ▼
              ┌────────────┐         user cancels
              │  PENDING   │ ─────────────────────────┐
              │ (browser   │                          │
              │  opened)   │   browser callback       │
              └─────┬──────┘   returns code          │
                    │                                 │
                    ▼                                 ▼
              ┌────────────┐                    ┌──────────┐
              │ SIGNED IN  │                    │  ERROR   │
              │            │                    │          │
              └─────┬──────┘                    └─────┬────┘
                    │ user clicks "Sign out"          │
                    └──────────► IDLE ◄───────────────┘
```

### State 1: IDLE (signed out)

The Gemini row, with "Sign in with Google" radio selected, shows:

```
Gemini authentication
  ( ) API key
  (•) Sign in with Google

  [ Sign in with Google ]

  Opens your browser. We only request access to the Gemini generative API.
```

- "Sign in with Google" button: **Secondary** button per DESIGN.md "Buttons" component
  - Transparent background
  - 1px Foxing border, 2px radius
  - Ink label, IBM Plex Sans 13px / 500
  - Padding: 8px vertical / 18px horizontal
  - Hover: border darkens to Ink
- Helper line below: Foxing color, 11px, IBM Plex Sans
- **No Google branded artwork.** Plain text "Sign in with Google". DESIGN.md
  anti-slop rules out "colored icon circles" and "3-column icon grids"; we extend
  that to: no branded button artwork. Google's branding guidelines permit this if we
  use the official artwork unmodified, but the design system disallows it.

### State 2: PENDING (browser opened)

Button transforms in place (same width, same position):

```
Gemini authentication
  ( ) API key
  (•) Sign in with Google

  [ Waiting for browser... ]   Cancel

  ███████████░░░░░░░░░░░░  (animated)

  Approve access in your browser. We'll keep waiting.
  If you closed the tab, click here to retry.
```

- Button: same Secondary chrome but border thickens to Hooker's Green (`#2C5F5D`),
  label becomes "Waiting for browser..." in Ink
- "Cancel" appears to the right: text-only tertiary action, Foxing color, IBM Plex
  Sans 13px / 400
- Below the button: thin **1px Hooker's Green progress strip**, indeterminate
  animation (no spinner per DESIGN.md "Motion" rules), 200-250ms loop cycle,
  ease-in-out
- Helper text: same Foxing 11px IBM Plex Sans, but "click here to retry" is an inline
  Hooker's Green underlined link

**No vermilion.** No sparkle. No "we are signing you in! 🎉".

### State 3: SIGNED IN

```
Gemini authentication
  ( ) API key
  (•) Sign in with Google

  ● user@gmail.com                          [ Sign out ]

  Signed in. Token refreshes automatically.
```

- Green dot (Hooker's Green `#2C5F5D`) before the email, 8px diameter
- Email: **IBM Plex Mono 11px** in Foxing color (data role per DESIGN.md typography)
- "Sign out" button: Secondary chrome, right-aligned in the row
- Below: status line in Foxing 11px IBM Plex Sans
- The radio group ABOVE remains visible. If the user clicks "API key" radio, the
  signed-in row collapses to show the API-key field instead, **but credentials are
  NOT revoked on the server**. Clicking back to "Sign in with Google" radio shows
  the signed-in state again. Only clicking "Sign out" revokes.

### State 4: ERROR (three sub-cases)

Button reverts to IDLE chrome. Helper text below the button becomes **11px Error
`#7A2222`** (NOT vermilion — DESIGN.md "Semantic colors" deliberately specifies a
deeper red for errors to avoid AI confusion).

| Sub-case | Helper text |
|----------|-------------|
| Network error | "Couldn't reach Google. Check your connection and try again." |
| User cancelled | "Sign-in cancelled. Try again when you're ready." |
| Auth failed (Google returned `invalid_grant`, `access_denied`, etc.) | "Google declined the sign-in. Try again, or use an API key instead." |

No modal dialog. No toast. Errors live in the surface that caused them.

**Tone:** never scolding, never apologetic. "Sign-in cancelled" is a fact, not a
problem. No "Oh no!" or "Whoops!".

### Token refresh behavior (background, no UX surface in S2)

- Refresh when access token is within 60s of expiry, at call-start (never mid-call).
- Refresh failure (Google returns `invalid_grant` on refresh): treat as state-change
  to ERROR with sub-case "auth failed". Show the error in the AI Preferences pane
  AND set status bar to `AI: error (gemini)`.
- Refresh success: silent, no UX surface.

### State transitions

| From | To | Trigger |
|------|----|----|
| IDLE | PENDING | User clicks "Sign in with Google" |
| PENDING | SIGNED IN | Browser callback delivers valid auth code; code-to-token exchange succeeds |
| PENDING | ERROR | Browser callback delivers error; OR timeout (60s default); OR user clicks Cancel |
| PENDING | IDLE | User clicks Cancel (alternate path: ERROR sub-case "User cancelled") |
| SIGNED IN | IDLE | User clicks Sign out (revokes refresh token via Google's revoke endpoint) |
| SIGNED IN | ERROR | Background refresh fails with `invalid_grant` |
| ERROR | PENDING | User clicks "Sign in with Google" again (re-runs the flow) |

### Anti-slop guardrails

- No vermilion in any state. The OAuth flow is chrome, not AI activity.
- No sparkle, no wand, no "✨ Authenticating...".
- No spinner. The progress strip is the spinner substitute.
- No success modal. The signed-in row IS the confirmation. No "✅ Connected!".
- No Google branded button artwork. Plain text label only.
- No "We've sent you an email" copy. We don't send emails. The browser is the proof.

### Accessibility notes

- Tab order within the Gemini provider row:
  1. Radio "API key"
  2. Radio "Sign in with Google"
  3. (IDLE/ERROR) "Sign in with Google" button
  4. (PENDING) Cancel link
  5. (SIGNED IN) Sign out button
  6. (Any state) Helper-text links (e.g., "click here to retry")
- Focus ring: 1px Hooker's Green outline at 2px offset (matches DESIGN.md Inputs spec
  extended to buttons)
- Disabled state: when "API key" radio is selected, "Sign in with Google" button is
  **disabled, not hidden**. Disabled visual: Foxing text on Cotton, no border. Hidden
  buttons cause tab-order instability.
- Email address in SIGNED IN state: announces as "Signed in as user at gmail dot com"
  via `accessibleName`
- Progress strip in PENDING: `accessibleName="Waiting for browser sign-in"`,
  `accessibleRole="progress"` (Qt `Qt.AccessibleRole.ProgressBar`)
- Screen reader announcement on state change: "Status: signed in" / "Status: error,
  Google declined the sign-in"

---

## Status bar widget upgrade (already in DESIGN.md, S2 implements)

DESIGN.md "Status bar" component already specifies the four states:

- `● AI: off` (Foxing dot, Foxing label)
- `● AI: ready (local)` / `(cloud)` (Hooker's Green dot, Foxing label)
- `● AI: working...` (Vermilion dot pulsing 1Hz, Foxing label)

S2 implements:

- 1 Hz vermilion pulse on the working dot. Implementation: `QPropertyAnimation` on
  opacity, 0.4 ↔ 1.0, 500ms each direction, ease-in-out, loop infinitely. Stop
  animation on state change away from "working".
- Live provider name in the label parens: `AI: ready (ollama)`, `AI: ready
  (anthropic)`, `AI: ready (gemini)`. All lowercase.
- Multi-feature different-providers fallback: `AI: ready (mixed)`. Single word.
- New ERROR state (added in S2): `● AI: error (gemini)` with **Error `#7A2222`** dot
  (NOT vermilion — error semantic, not AI-activity semantic). Click opens AI
  Preferences with the failing provider's row expanded.
- Hover tooltip: Qt-default tooltip style (no custom popup).
  - When AI off: "AI features off. Click to configure."
  - When ready: "AI ready via {provider}. Click to configure."
  - When working: "Working..." (no token count in S2; S3 adds tokens)
  - When error: "{provider}: {error short text}. Click to retry."
- Keyboard: `setFocusPolicy(Qt.FocusPolicy.TabFocus)`, `accessibleName="AI status.
  Press Enter to configure."`, `keyPressEvent` on Enter/Space emits clicked.

### Anti-slop guardrails

- Provider name in label is lowercase only. No "AI: ready (Gemini)".
- No model name in the label. `(gemini)` not `(gemini-pro)` not `(gemini-1.5)`.
- No emoji, no Unicode logo glyph.
- The vermilion pulse is the only place vermilion appears in chrome.

---

## AI Preferences panel upgrade (already in DESIGN.md, S2 implements)

DESIGN.md does not currently have a panel-level component spec for `Preferences → AI`.
S2 implements:

### Structure

```
[Header]   AI features                                    [Off / Ready / Working]
           Off until you say otherwise.

[Section]  Per-project opt-in
           Master toggle:  Enable AI for this project   ( on/off )

[Section]  Features (disabled until Master is on)
           [ ] Inline rewrite          [Provider: ▾]
           [ ] Consistency check       [Provider: ▾]

[Section]  Providers
           ▸ Ollama  (collapsed)
           ▸ Anthropic  (collapsed)
           ▸ Gemini  (collapsed)
           [Anthropic and Gemini sections expand on click; show API-key field;
            Gemini additionally shows the OAuth radio + flow described above]

[Section]  Privacy
           Off until you say otherwise. Each feature is opt-in per project.
           Token estimates appear before every cloud call. No prompts or
           outputs are logged to disk unless you enable the debug log.
```

### Typography and spacing

- Section headers: IBM Plex Sans 14px / 600 / Ink. 8px below preceding content.
- Subhead under master toggle: Source Serif 4 14px italic Foxing.
- Body copy: IBM Plex Sans 13px / 1.5 / Ink.
- Section padding: 24px vertical between sections, 32px outer pane padding (DESIGN.md
  "Preferences: comfortable" density).
- Pane max-width: 720px (DESIGN.md "Max content width" rule).

### Vermilion appearance

**Zero.** The AI Preferences panel is chrome. None of it touches AI-generated content.
The only AI-related color is Hooker's Green (provider ready) and Error `#7A2222`
(provider error).

### Accessibility

- Per-feature toggles: `accessibleName` = "Enable inline rewrite feature" etc.
- Provider dropdowns: `accessibleName` = "Provider for inline rewrite"
- API-key fields: masked input (`QLineEdit.EchoMode.Password`), `accessibleName` =
  "Anthropic API key" / "Gemini API key"
- `setBuddy` wiring between each `QLabel` and its `QLineEdit` / `QComboBox` so
  clicking the label focuses the input
- All form fields are reachable in a sensible top-to-bottom tab order

---

## Open questions for build phase

Items the build can resolve without re-running `/design-consultation`:

- Tab bar height: implementation-dependent (Qt's default `QTabBar` height is roughly
  28-32px depending on platform; this is fine). If the implementation chooses to
  override, target 32px.
- Hover-state distinction between IDLE and HOVER tabs on Linux (where `QTabBar` mouse
  tracking is sometimes flaky): use `QObject.installEventFilter` to catch hover events
  if Qt's stylesheet `:hover` is unreliable.
- Sign in with Google "click here to retry" link target: this should re-trigger the
  OAuth flow without canceling the current pending state's listener. Implementation
  detail; design doesn't constrain.

Items that need user input if encountered:

- If Google requires app verification before users can grant the requested scope:
  what's the fallback copy in the OAuth consent screen warning? Design says:
  "Document in `docs/ai/privacy.md` and surface in the OAuth error helper text if
  Google returns the unverified-app code."
- If the user has an existing Anthropic key in keychain and switches to Gemini
  OAuth: do we delete the Anthropic key? Design says NO — keys persist until the
  user explicitly removes them via the API-key field's clear action.

---

## DESIGN.md Component Amendments

The following sections will be appended to `DESIGN.md` under `## Components`:

1. `### Tab bar (top-level IA)` — copy from "Component 1" above, condensed to fit
   DESIGN.md component-spec style (one paragraph + state table + spacing)
2. `### Marginalia rail empty-state` — copy from "Component 2", condensed
3. `### Auth flow (OAuth)` — copy from "Component 3", condensed; references the state
   machine without re-rendering it
4. `### AI Preferences panel` — copy from the panel section above, condensed
5. Update to `### Status bar` — add the new ERROR state with Error `#7A2222` dot
6. Update to `## Anti-Slop Rules` — append two rules:
   - "No Google (or any provider) branded button artwork. Plain text labels only."
   - "No success modals on auth flow completion. The signed-in row is the confirmation."

These amendments are applied to DESIGN.md in the same operation that signs off this
contract.

---

## Decisions log

| Decision | Rationale |
|----------|-----------|
| Tab bar uses underline, not pill backgrounds | Avoids "button-fight" feel; matches editorial aesthetic |
| Tab labels are plain words (no icons) | DESIGN.md anti-slop forbids "✨ AI" iconography; extends to category icons broadly |
| AI tab order: last | Writing flow is plan → write → reference → review; AI operates on the prior three |
| Tab switching: no motion | Tabs are navigation, not narrative; instant feels right per DESIGN.md "motion as decoration" prohibition |
| Marginalia rail empty-state uses Foxing kind line, not Vermilion | Empty state has no AI activity; vermilion would falsely advertise |
| OAuth uses Foxing/Hooker's Green/Error, never Vermilion | Authentication is chrome, not AI; preserves vermilion's "sacred for AI" status |
| No Google branded button artwork | DESIGN.md anti-slop rules out colored-icon decoration; plain text serves equally well |
| OAuth pending state uses progress strip, not spinner | DESIGN.md motion rule: "No spinners on the AI inspector"; extended to all chrome |
| Error state uses Error `#7A2222`, not Vermilion | DESIGN.md "Semantic colors" already specifies this distinction |
| Disabled "Sign in with Google" button is disabled, not hidden | Tab-order stability; matches DESIGN.md inputs pattern |
| Status bar error state added as `AI: error (provider)` | S2 introduces real network failures; needed for provider failure UX (open-Q #9) |

---

## Sign-off

This design contract resolves all three component specs called out in the
`design-intent.json` (`affected_surfaces`) for run-2026-05-12T01-45-20-695Z:

- ✓ `preferences-ai-panel` — full structure + accessibility spec
- ✓ `status-bar-ai-widget` — error state added; pulse animation specified
- ✓ `project-shell-tabs` — full spec (Component 1)
- ✓ `marginalia-rail-primitive` — full empty-state spec (Component 2)
- ✓ `ai-tab-empty-state` — covered under Component 2 (rail empty state IS the AI tab
  empty state in S2)
- ✓ `gemini-oauth-flow` — full state machine + per-state spec (Component 3)

`/handoff` transition rule satisfied: this file's line count exceeds 200 AND the
`## DESIGN.md Component Amendments` header is present.

DESIGN.md amendments applied in the same operation. Decisions Log updated.

Next stage: `/handoff` to package S2 for `/build`.
