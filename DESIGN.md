# Design System — Manuscript (novelWriter Fork)

The visual identity for the novelWriter fork (working name: `plotwright`). Read this
before any UI work. If you change a value here, update CLAUDE.md and the plan-stage
design contract.

## Product Context

- **What this is:** a private GPL-3 fork of novelWriter, retargeted as an AI-assisted
  workbench for genre-fiction plotters.
- **Who it's for:** novelists who outline before drafting, re-read for continuity,
  and want craft control. Anti-persona: writers seeking one-click drafting.
- **Space:** desktop creative-writing apps. Peers: Scrivener, novelWriter upstream,
  iA Writer, Ulysses, Plottr, Obsidian.
- **Project type:** PyQt6 cross-platform desktop application. No web shell.
- **Positioning:** the opposite of "AI slop." AI features only operate on text the
  user wrote and metadata the user authored.

## Aesthetic Direction

- **Direction:** Cartographic Modernism / Editorial.
- **Mood:** an editor's desk, not a SaaS dashboard. Mid-century Penguin Classics meets
  Tufte planning notebooks. Quiet, slightly bookish, deeply respectful of craft.
- **Decoration level:** minimal. Typography and paper texture do the work. No icons in
  colored circles, no decorative blobs, no gradients.
- **Reference designers/studios:** Massimo Vignelli (grid discipline), Jonathan Hoefler
  (typographic moralism), Irma Boom (book-object sensibility), Edward Tufte (information
  density in planning views).
- **Reference research:** screenshots of Scrivener, Obsidian, iA Writer, Ulysses,
  novelWriter upstream, and Plottr captured at
  `~/.nexus/projects/LaPaGaYo-novelWriter/designs/design-system-20260426/research/`.

## The Two Locked Risk Decisions

These shape every other choice. Do not silently override.

1. **AI as marginalia, not chat.** AI-generated rewrites and consistency findings appear
   as vermilion editorial markup in the manuscript and as editor's notes in a right-side
   marginalia rail. Never as a chat sidebar. Never as a sparkle/wand button.
2. **Manuscript theme as canonical, not dark.** The app opens to cream paper on dark ink
   by default. Dark mode exists but is secondary, not a peer. This is the immediate
   one-second visual differentiator from Obsidian / iA Writer / upstream.

## Typography

All four typefaces are open-licensed (OFL) and bundle as TTF/OTF with the application.
No CDN, no runtime download.

| Role | Font | License | Where it appears |
|------|------|---------|------------------|
| Display | **Spectral** (Production Type) | OFL | Project titles, chapter headers, dialog headers, marketing copy |
| Body / manuscript | **Source Serif 4** (Adobe) | OFL | Manuscript text, long-form descriptions, marginalia content |
| UI / chrome / sidebar | **IBM Plex Sans** | OFL | Project tree, menus, buttons, labels, preferences, status bar |
| Data / counts / IDs | **IBM Plex Mono** | OFL | Word counts, scene IDs, timestamps, terminal-style metadata |

**Optional paid upgrade:** Tiempos Headline (Klim) for display. Higher contrast and more
editorial backbone. Defer until budget is approved and license redistribution is sorted.

**Loading:** font files live in `novelwriter/assets/fonts/` (or fork-rebranded equivalent).
Loaded into Qt via `QFontDatabase.addApplicationFont` at startup. No system-font fallback
for the four roles above (consistency over portability).

**Scale (manuscript view):**
- Display 1: 32px / 1.2 / 600
- Display 2: 24px / 1.25 / 600
- Body: 17px / 1.75 (manuscript prose, max 60ch column)
- Body small: 14px / 1.5 (marginalia content)
- Caption: 11px / 1.4 (mono metadata, 0.06em letter-spacing)

**Scale (UI/chrome):**
- H3: 14px / 1.3 / 600
- Body: 13px / 1.5
- Small: 11px / 1.3
- Mono: 11-13px / 1.5 (tabular-nums always on)

## Color

**Approach:** restrained. Six palette tokens for the canonical theme, one mode-shift
token for dark.

| Token | Hex | Role |
|-------|-----|------|
| Cotton | `#F4EFE6` | Canvas (warm paper, not pure white) |
| Ink | `#1C1B17` | Body text (near-black, green undertone, never `#000`) |
| Foxing | `#7A6A4F` | Muted text, dividers, secondary metadata |
| Vellum | `#EDE3CF` | Surface elevation (sidebars, marginalia rail, cards) |
| Hooker's Green | `#2C5F5D` | Selection, active focus, primary accent |
| **Vermilion** | `#9B2C2C` | **AI-touched regions ONLY. Sacred.** Inline underlines on AI selections; left-border on marginalia entries; flagged-scene edge on scene cards |
| Slate | `#3A3530` | Dark-mode primary surface (warm slate, never blue-black) |

**Dark-mode tokens** (when active):
- bg → Slate `#3A3530`
- surface → `#2A2520`
- text → `#E6E0D2`
- muted → `#8A7C5F`
- accent → `#6FA9A6` (lifted Hooker's Green)
- ai → `#C26B65` (lifted Vermilion, still readable)

**Rules:**
- Vermilion never used outside AI semantics. Errors use a different red? No. Errors don't
  exist in the manuscript view; they live in dialogs and use OS-native error coloring.
  In the manuscript view, vermilion = AI. Period.
- Hooker's Green is the only "active" color in the canonical theme. Buttons, focus rings,
  selection highlights all use it.
- No alpha-blended accents on the manuscript canvas. The cream paper is the canvas; do
  not lay translucent panels over it.

**Semantic colors (dialogs only, not in manuscript view):**
- Success: `#2C5F5D` (Hooker's Green, reused)
- Warning: `#B58A2E` (mustard, never seen in manuscript)
- Error: `#7A2222` (deeper than Vermilion to avoid AI-confusion)
- Info: `#3A6F8C` (storm blue)

## Spacing

- **Base unit:** 4px.
- **Scale:** 2 / 4 / 8 / 12 / 16 / 24 / 32 / 48 / 64.
- **Density per surface:**
  - Manuscript view: comfortable. 48-64px outer padding. 60ch enforced measure on the
    text column. Line-height 1.75.
  - Marginalia rail: medium. 20-24px padding. Compact but readable.
  - Project tree / chrome / status bar: compact. 4-8px padding per row. 1.4 line-height.
  - Scene-card view: dense. 8px gap between cards, 12px card padding, 140px min-height.
  - Dialogs / Preferences: comfortable. 24-32px padding, 1.5 line-height.

## Layout

- **Approach:** asymmetric two-column with marginalia rail. Project tree | manuscript
  column | marginalia rail.
- **Manuscript column:** 60ch enforced measure, left-aligned to a baseline grid.
  Generous outer padding.
- **Marginalia rail:** 280-320px fixed width, scrolls in lockstep with the manuscript
  column when possible.
- **Project tree:** 200-240px fixed width, collapsible.
- **Scene-card view:** 4-column grid at desktop, dense Tufte-style.
- **Character panel:** asymmetric — character portrait/metadata on the left, all
  references-across-scenes on the right.
- **Border radius:** 2px on every surface. We do not round into "friendly app" territory.
  Sharp corners read as serious tool.
- **Max content width (Preferences, dialogs):** 720px.

## Motion

- **Approach:** minimal-functional. No hero animations. No motion as decoration.
- **Easing:** ease-out for enter, ease-in for exit, ease-in-out for sustained moves.
- **Duration:**
  - Micro (hover, focus): 100ms
  - Short (panel slides, accordion): 200-250ms
  - AI marginalia fade-in: 150ms (signals "this just appeared," gives the user a beat to
    register it)
  - Long (rare): 400ms only for cross-screen transitions
- **No spinners on the AI inspector.** Use a thin progress bar at the top of the
  marginalia rail.

## Components

### Buttons

- **Primary:** Hooker's Green background, Cotton text. 8px vertical / 18px horizontal
  padding. 13px IBM Plex Sans 500.
- **Secondary:** transparent, 1px Foxing border, Ink text. Border darkens to Ink on hover.
- **AI action:** transparent, 1px Vermilion border, Vermilion text. ONLY for actions that
  trigger AI calls (e.g., "Mark for AI review", "Run consistency check").
- **Destructive:** OS-native error coloring; do not invent a red.

### Inputs

- 1px Foxing border, 2px radius. Cotton background. Focus state: Hooker's Green border +
  1px box-shadow. No animation on focus other than border-color (instant is fine).

### Dividers

- 1px Foxing for primary dividers (between panes).
- 0.5px (where supported) or `rgba(28,27,23,0.08)` for inline dividers.

### Status bar

- Always visible at the bottom of the main window.
- Left: project name (IBM Plex Sans, 11px).
- Right: chapter/scene location, word counts, AI state.
- AI state pattern: dot + label.
  - `● AI: off` (Foxing color, dot Foxing)
  - `● AI: ready (provider)` (Hooker's Green dot, label Foxing) — provider name is
    lowercase, no model name, no version: `(ollama)`, `(anthropic)`, `(gemini)`. When
    multiple features use different providers: `(mixed)`.
  - `● AI: working...` (Vermilion dot pulsing 1Hz via `QPropertyAnimation` on opacity
    0.4 ↔ 1.0 ease-in-out, label Foxing)
  - `● AI: error (provider)` (Error `#7A2222` dot — NOT Vermilion; error semantic, not
    AI-activity semantic; label Foxing)
- Click on the AI state opens the AI Preferences pane focused on the relevant section.
- Hover tooltip uses Qt-default style (no custom popup). Content varies by state.
- Keyboard reachable: `setFocusPolicy(Qt.FocusPolicy.TabFocus)`, Enter/Space activates,
  `accessibleName="AI status. Press Enter to configure."`

### Marginalia entry

- Border-left 2px Vermilion.
- 8px vertical / 12px left padding.
- 16px gap between entries.
- Kind line: IBM Plex Mono 10px, uppercase, Vermilion, 0.1em tracking.
- Body: Source Serif 4 14px italic, Ink.
- Reference: IBM Plex Mono 11px, Foxing.

### Scene card (corkboard view)

- Vellum background, 1px subtle border, 2px radius.
- 12px padding, 140px min-height.
- Number: IBM Plex Mono 10px Foxing.
- Title: Spectral 14px 600.
- Synopsis: Source Serif 4 12px Foxing.
- POV: IBM Plex Mono 10px Foxing.
- Flagged-by-AI variant: 2px Vermilion left border, number color shifts to Vermilion.

### Selection / inline AI marker

- Selection: Hooker's Green background, Cotton text.
- AI inline marker: wavy Vermilion underline 1.5px, 4px underline-offset, cursor pointer.
  Click opens the corresponding marginalia entry.

### Tab bar (top-level IA, S2)

- Four tabs at the top of the main window, below menu, above content: **Outline /
  Manuscript / Notes / AI**. Cmd/Ctrl+1..4 shortcuts wired.
- Plain-text labels only. No icons, no badges, no "✨ AI". Title case.
- Type: IBM Plex Sans 13px / 500 / Ink.
- Cells: 8px vertical / 16px horizontal padding, abutting (no gap).
- Active-tab indicator: **2px Hooker's Green underline** 2px below the baseline. The
  underline does the whole job. No background-color change between states.
- Hover: 1px Foxing underline at the same baseline.
- Focus (keyboard): 1px Hooker's Green outline at 2px offset around the cell.
- Bottom border of the tab bar: 1px Foxing across full width, broken by the active
  underline.
- No motion on tab switch. Tabs are navigation, not narrative.

### Marginalia rail empty-state (S2)

- The 280-320px right column (use 300px) on Vellum surface, 1px Foxing left divider.
- Empty state has three top-aligned text blocks, left-aligned (NEVER centered):
  1. Kind line: `EDITOR'S NOTES` — IBM Plex Mono 10px uppercase, **Foxing** (NOT
     Vermilion — empty state has no AI activity). 0.1em tracking. 24px from top, 20px
     left padding.
  2. Body: Source Serif 4 14px italic Ink, copy = "No notes yet. When you ask the AI
     to review a passage, its observations land here as marginalia, alongside the
     manuscript, never on top of it." 16px below kind line.
  3. Caption: IBM Plex Mono 11px Foxing, copy = "Inline rewrite arrives in the next
     release. Consistency check follows." 24px below body.
- No illustration, no CTA button, no "create your first entry" affordance.
- When populated (S3+), the rail renders Marginalia entries per the existing component
  spec, which IS where Vermilion appears.

### Auth flow (Gemini OAuth, S2)

Lives in `Preferences → AI → Gemini` when "Sign in with Google" radio is selected.
Four states. **Vermilion never appears in this flow.** Authentication is chrome, not
AI activity.

- **IDLE (signed out):** Secondary button "Sign in with Google" (transparent, 1px
  Foxing border, Ink label, 2px radius). Helper text below in Foxing 11px. Plain text
  label only — no Google branded artwork.
- **PENDING (browser opened):** Button transforms in place to "Waiting for browser..."
  with Hooker's Green border. Below: 1px Hooker's Green progress strip, indeterminate
  animation (no spinner per the motion rule). "Cancel" tertiary action right of the
  button. Helper text becomes "Approve access in your browser. We'll keep waiting. If
  you closed the tab, click here to retry."
- **SIGNED IN:** Replace button with row: `● user@gmail.com [ Sign out ]`. Green dot
  (Hooker's Green) before the email. Email in IBM Plex Mono 11px Foxing (data role).
  Sign out is Secondary chrome, right-aligned. Status line below: "Signed in. Token
  refreshes automatically."
- **ERROR:** Button reverts to IDLE chrome. Helper text becomes 11px Error `#7A2222`
  (NOT Vermilion). Three sub-cases: network error, user cancelled, auth failed. Tone
  is matter-of-fact. No modal. No toast.

State transitions: IDLE → PENDING (user clicks Sign in); PENDING → SIGNED IN (callback
delivers valid code); PENDING → ERROR or IDLE (cancel or failure); SIGNED IN → IDLE
(user clicks Sign out, which revokes); SIGNED IN → ERROR (background refresh fails);
ERROR → PENDING (user retries).

Disabled state when "API key" radio is selected: button disabled (NOT hidden) — Foxing
text on Cotton, no border.

### AI Preferences panel (S2)

`Preferences → AI` pane. Comfortable density (24-32px padding, 1.5 line-height). Max
720px wide.

Structure (top to bottom):

1. Header — "AI features" (IBM Plex Sans 14px / 600 / Ink). Subhead: "Off until you
   say otherwise." (Source Serif 4 14px italic Foxing).
2. Per-project opt-in — master toggle "Enable AI for this project".
3. Features — per-feature toggles ("Inline rewrite", "Consistency check"). Disabled
   until master is on. Each feature has a provider dropdown next to it.
4. Providers — collapsible rows for Ollama, Anthropic, Gemini. Expand on click to
   reveal per-provider auth fields. Gemini additionally shows the OAuth radio + flow
   described above.
5. Privacy — copy block restating the privacy posture: "Off until you say otherwise.
   Each feature is opt-in per project. Token estimates appear before every cloud
   call. No prompts or outputs are logged to disk unless you enable the debug log."

Zero vermilion in the pane. Provider-ready uses Hooker's Green. Provider-error uses
Error `#7A2222`.

`setBuddy` wires every QLabel to its QLineEdit / QComboBox for click-to-focus.
Every input sets `accessibleName` matching the visible label.

## i18n

- All UI strings use the existing `nwTr.tr()` pattern from upstream.
- Spectral, Source Serif 4, IBM Plex Sans, IBM Plex Mono all have Latin Extended +
  Cyrillic. Plex Sans/Mono have CJK variants we can wire in for zh / ja / ko later.
- v1 ships English + Chinese as gated locales; other locales fall back to English until
  translated.
- Avoid centered text in headers — left-aligned reads better in RTL fallback.

## Privacy as Visual Language

The privacy posture is a visible part of the design system, not just a setting.

- The status bar AI indicator is *always* visible. The user never has to wonder whether
  AI is on.
- "AI: off" is the default and reads as steady gray. "AI: ready" introduces the
  Hooker's Green dot. "AI: working" introduces a pulsing Vermilion dot — the only place
  Vermilion appears in chrome (still semantically "AI is touching things").
- Token estimates appear before any cloud call, in IBM Plex Mono with explicit numerals.
  No rounded marketing-y "About 500 tokens" — show the number.
- The AI Preferences pane uses the strongest type ("Off until you say otherwise") as the
  pane's leading line. Privacy default is design copy, not a footnote.

## Anti-Slop Rules (do not break)

These came from competitive research. Each is a category convention we deliberately
break.

- No purple/violet anywhere.
- No gradient buttons. No gradient hero. No gradient anything.
- No 3-column icon grids in colored circles.
- No "✨ AI" sparkle iconography. No wands. No stars. No magic.
- No chat-bubble UI for AI output. Marginalia only.
- No "Generated by AI" badges on accepted content. The user's edits make it the user's.
- No stock-photo hero shots in marketing surfaces (About dialog, README hero).
- No decorative blobs, waves, or "abstract shapes" for visual padding.
- No centered everything. Asymmetry is the default.
- No Google (or any provider) branded button artwork. Plain text labels only on auth
  affordances. Google's branding guidelines permit unmodified artwork; the design
  system disallows it.
- No success modals on auth flow completion. The signed-in row IS the confirmation.
  No "✅ Connected!", no celebratory toast.

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-26 | Initial design system created | /design-consultation; subagent + competitive research converged on Cartographic Modernism / Manuscript direction |
| 2026-04-26 | Spectral chosen over Tiempos Headline | OFL license fits GPL-3 fork redistribution; Tiempos noted as paid upgrade path |
| 2026-04-26 | IBM Plex Sans/Mono chosen over National 2 / MD IO | OFL license; Plex family coheres internally |
| 2026-04-26 | Vermilion locked as AI-exclusive | Justifies the fork's "opposite of AI slop" positioning at first glance |
| 2026-04-26 | Manuscript theme canonical, dark secondary | One-second visual differentiation from Obsidian/iA Writer/upstream novelWriter |
| 2026-04-26 | Codex outside voice unavailable | `gpt-5.5 requires newer Codex CLI`; proposal proceeded with Claude main + Claude subagent only, tagged `[single-model]` |
| 2026-05-12 | Tab bar uses underline indicator, not pill backgrounds | Editorial aesthetic; avoids "button-fight" feel; matches DESIGN.md asymmetry/density rules. S2 WS-4. |
| 2026-05-12 | Marginalia rail empty-state uses Foxing kind line, not Vermilion | Empty state has no AI activity; Vermilion in empty state would falsely advertise. S2 WS-4. |
| 2026-05-12 | OAuth flow uses Foxing/Hooker's Green/Error palette only | Authentication is chrome, not AI activity. Preserves Vermilion's "sacred for AI" status. S2 WS-1. |
| 2026-05-12 | No Google branded button artwork for Sign in with Google | Anti-slop rule extension. Plain text label serves equally. S2 WS-1. |
| 2026-05-12 | OAuth pending state uses 1px Hooker's Green progress strip, not spinner | DESIGN.md motion rule "no spinners" extended to all chrome auth surfaces. S2 WS-1. |
| 2026-05-12 | Status bar gains `AI: error (provider)` state in Error `#7A2222` | S2 introduces real network failures; provider failure UX needs a status-bar surface. S2 WS-1. |
| 2026-05-12 | Codex outside voice skipped per local_provider policy | `_PRIMARY_PROVIDER=claude` policy disallows Codex; component-spec work is low-ROI for outside voice; proceeded single-agent with explicit DESIGN.md anchor adherence. |

## Implementation pointers

- Font bundling: write a `novelwriter/gui/theme/fonts.py` (or fork equivalent) that
  registers all four families on `QApplication` startup via `QFontDatabase.addApplicationFont`.
- Theme tokens: keep palette + spacing in `novelwriter/gui/theme/tokens.py`, exported as
  Qt-stylesheet template strings. Light/dark mode swaps a small token map.
- Marginalia rail widget: `novelwriter/gui/marginalia.py`. Implements scroll-lock with
  the manuscript view, click-to-jump from inline marker to marginalia entry.
- AI inline marker rendering: subclass `QSyntaxHighlighter` to apply the wavy underline
  format on AI-marked spans.

## What this file is not

- Not a brand-spec. The fork doesn't have brand-frozen assets yet (logo, icon set, About
  imagery). When those land, write a separate `brand-spec.md`.
- Not the implementation plan. That lives in `.planning/current/plan/`.
- Not enforcement. CI doesn't validate this file. Reviewers do.
