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
  - `● AI: ready (local)` (Hooker's Green dot, label Foxing)
  - `● AI: ready (cloud)` (Hooker's Green dot, label Foxing)
  - `● AI: working...` (Vermilion dot pulsing 1Hz, label Foxing)
- Click on the AI state opens the AI Preferences pane.

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

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-04-26 | Initial design system created | /design-consultation; subagent + competitive research converged on Cartographic Modernism / Manuscript direction |
| 2026-04-26 | Spectral chosen over Tiempos Headline | OFL license fits GPL-3 fork redistribution; Tiempos noted as paid upgrade path |
| 2026-04-26 | IBM Plex Sans/Mono chosen over National 2 / MD IO | OFL license; Plex family coheres internally |
| 2026-04-26 | Vermilion locked as AI-exclusive | Justifies the fork's "opposite of AI slop" positioning at first glance |
| 2026-04-26 | Manuscript theme canonical, dark secondary | One-second visual differentiation from Obsidian/iA Writer/upstream novelWriter |
| 2026-04-26 | Codex outside voice unavailable | `gpt-5.5 requires newer Codex CLI`; proposal proceeded with Claude main + Claude subagent only, tagged `[single-model]` |

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
