# Design Contract — Manuscript

`/design-consultation` produced this contract on 2026-04-26 for the novelWriter fork v1.
Replaces the prior placeholder. Pointers below are authoritative.

## Source of truth

- **`DESIGN.md`** at the repo root — full system spec (typography, color, spacing,
  layout, motion, components, anti-slop rules, decisions log).
- **`CLAUDE.md`** — routing rule that requires reading `DESIGN.md` before any UI work.
- **HTML preview** — `~/.nexus/projects/LaPaGaYo-novelWriter/designs/design-system-20260426/manuscript-preview.html`
  (generated 2026-04-26). Visual reference for tone and density. Open in any browser
  to see fonts, palette, writing surface mock, scene-card view, AI Preferences mock.
- **Competitive research screenshots** —
  `~/.nexus/projects/LaPaGaYo-novelWriter/designs/design-system-20260426/research/`.

## Direction (one-line)

**Manuscript** — an editor's desk for genre-fiction plotters. Cartographic Modernism.
Cream paper, dark ink, library-binding green, foxed-page foxing. Vermilion appears
only where the AI has touched the page.

## Locked decisions

1. AI as marginalia (vermilion underlines + right-side marginalia rail), never chat.
2. Manuscript theme canonical; dark mode is secondary.
3. Open-licensed fonts only: Spectral / Source Serif 4 / IBM Plex Sans / IBM Plex Mono.
4. Palette: Cotton / Ink / Foxing / Vellum / Hooker's Green / Vermilion (AI only) / Slate (dark only).
5. Border radius 2px globally. No rounded "friendly app" forms.
6. Vermilion is sacred — AI-touched regions only.

## Coverage of the 8 frame surfaces

| # | Surface | Status | Notes |
|---|---------|--------|-------|
| 1 | `project_shell` | Designed | Asymmetric tree-manuscript-marginalia layout; see DESIGN.md "Layout" |
| 2 | `scene_card_view` | Designed | Dense Tufte-style cards, vermilion edge for AI-flagged scenes |
| 3 | `character_panel` | Sketched | Asymmetric portrait/metadata + cross-reference list. Detail design owned by Sprint 4 (consistency check builds character context first). |
| 4 | `ai_inspector_dock` | Designed | Realized as the marginalia rail; not a separate dock |
| 5 | `status_bar` | Designed | AI state pattern (dot + label) specified in DESIGN.md "Components" |
| 6 | `preferences_ai_section` | Designed | Layout + copy locked; see HTML preview |
| 7 | `ai_review_pane` | Designed | Side-by-side via marginalia entry expansion; full interaction model owned by Sprint 3 |
| 8 | `consistency_check_inline_markers` | Designed | Wavy vermilion underline 1.5px, 4px offset, click-to-marginalia |

Two surfaces (3 and 7) carry "owned by Sprint X" notes — the visual language is locked,
but per-surface interaction details get refined during the relevant sprint when the
feature implementation reveals the corner cases.

## Verification expectations downstream

- **`/qa`** must verify `design_verification_required: true`. Inspect each surface against
  DESIGN.md.
- **`/review`** auditors should treat any deviation from DESIGN.md as a finding.
- **`/build`** for any UI work must reference DESIGN.md in commit messages.

## Replaces

- `/plan/design-contract.md` placeholder (2026-04-26 morning).
- `verification-matrix.json.blocking_gaps[design-contract-missing]` — should be removed.

## Outside-voice provenance

- Claude main: synthesized direction from competitive research + subagent.
- Claude subagent: independent proposal converged on the same direction (
  "Plotter's Drafting Table"). Strong signal of coherence.
- Codex: unavailable (`gpt-5.5 requires newer Codex CLI`). Tagged `[single-model]`. Not
  blocking.

## Outstanding follow-ons (NOT blocking handoff)

- Final fork product name. `plotwright` is the working placeholder. Lock during Sprint 5
  branding work.
- Bundle the four font files into `novelwriter/assets/fonts/` (or fork equivalent).
  Sprint 1 task.
- Icon set and About-dialog imagery — write `brand-spec.md` when those are commissioned.
- Tiempos Headline upgrade evaluation — defer until budget approval.

## What this contract does not cover

- Implementation file paths and module structure (lives in
  `execution-readiness-packet.md` and `sprint-contract.md`).
- Test plan for visual regression (gets defined in Sprint 4-5 when more surfaces are live).
- Localized font rendering for CJK locales (Plex family supports it; concrete pairing
  decisions deferred to localization sprint).
