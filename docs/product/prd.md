# PRD — novelWriter Fork v1

Companion to `docs/product/decision-brief.md`. The decision brief explains why and what
the v1 boundary is. This PRD specifies what gets built.

## Personas

### Plotter Pat (primary)

Genre-fiction novelist (urban fantasy, SFF, mystery). Outlines first, drafts in scenes,
maintains a project bible. Has 2-5 manuscripts going. Re-reads chapters for continuity.
Already uses one of: Scrivener, novelWriter, Obsidian, plain Markdown.

**Top jobs to be done:**
- "Help me check this chapter doesn't contradict what's in my project bible."
- "I wrote this paragraph too sparse / too purple — give me 3 alternatives."
- "Switch this scene from past to present tense" (or POV shift).
- "Tighten this dialogue without losing voice."

### Migrator Mira (secondary)

Existing upstream-novelWriter user evaluating the fork. Already has projects on disk in
the upstream `.nwx` format. Will not adopt the fork if migration risks her work.

**Top jobs to be done:**
- "Open my existing project in the fork without breaking it."
- "Try AI features without making any network call I didn't authorize."
- "Switch back to upstream novelWriter at any time."

## v1 features

### Feature 1 — Inline rewrite

**User story.** As Plotter Pat, I select a paragraph, choose "Rewrite," pick a transformation
(rewrite / expand / contract / change tense / change POV), and review the result before
it replaces my source text.

**Behavior.**

- Selection-driven. No selection means no action.
- Transformations:
  - Rewrite (preserve meaning, vary phrasing)
  - Expand (add detail, max 1.5× length)
  - Contract (compress, max 0.5× length)
  - Change tense (past ↔ present)
  - Change POV (1st ↔ 3rd limited)
- Output appears in a side-by-side review pane (original | proposed). User accepts,
  rejects, or accepts-with-edit. Rejection is a single keystroke.
- Accepted output replaces selection in a single undo-step. Original stays in undo history.
- Provider chosen per-feature in settings (local Ollama or cloud BYO key). Token estimate
  shown before each call when using a metered provider.
- No automatic submission. The user clicks "Generate" each time. No streaming auto-replace.

**Acceptance criteria.**

1. Selection of zero characters disables the menu item.
2. The review pane is reachable by keyboard alone (no mouse required).
3. Rejecting a proposal leaves the document unchanged in *every* respect (cursor position,
   undo stack, scroll). Verifiable by a regression test that diffs the document state.
4. Token estimate displayed before any cloud-provider call. The number is within 20% of
   actual usage on a 95% sample.
5. With AI off in settings, the "Rewrite" menu items are hidden, not greyed.
6. All transformation prompts ship with both an English (default) and a Chinese template
   for v1; other locales use the English template until translated.

**Out of scope for v1.**
- "Continue writing from here" / draft-generation transformation.
- Whole-document rewrites.
- Voice-tuning to author's prior chapters.

### Feature 2 — Consistency check

**User story.** As Plotter Pat, I run "Check consistency" on a chapter or selection. The
fork compares the text against character notes, location notes, and prior chapters, and
flags inconsistencies inline.

**Behavior.**

- Trigger from the document menu, command palette, or hotkey. No background scan.
- Build context from the project's existing structured notes:
  - All character notes (name, aliases, attributes the user has recorded)
  - All location notes
  - Synopses of all prior scenes/chapters in the project's reading order
  - Project-level metadata (timeline if present)
- For each candidate inconsistency, the AI must output a structured record:
  - kind: `character_attribute` | `location_attribute` | `timeline` | `cross_reference` | `other`
  - target span in the source text (line + offset)
  - referenced project note (path)
  - confidence: low/medium/high
  - explanation: one sentence
- Display: inline marker in the editor; click to open a side panel with the full record
  and accept/dismiss/snooze controls.
- Strictness slider: low (high-confidence only) / medium / high (low-confidence too).
  Default medium.
- A flagged inconsistency requires at least 2 corroborating signals OR confidence=high
  before display. (Mitigates false-positive risk from decision brief.)

**Acceptance criteria.**

1. Running on the bundled sample project produces zero "phantom" inconsistencies (false
   positives) at default strictness on a clean run.
2. Test corpus accuracy: ≥70% recall on seeded errors, ≤20% false-positive rate at
   default strictness. (Test corpus: 3 novels, 30 seeded errors total.)
3. Output records validate against the JSON schema before display. Malformed model output
   is surfaced as an error, never as silent loss.
4. Cancelling a check mid-run leaves the document untouched and the inline markers in
   their pre-run state.
5. With AI off, the menu item is hidden, not greyed.
6. Cloud-provider runs disclose token estimate before sending, like Feature 1.

**Out of scope for v1.**
- Auto-fix suggestions for flagged inconsistencies.
- Whole-project background scanning.
- Cross-project consistency.

## Cross-cutting requirements

### Provider model

- Provider categories in v1: **local** (Ollama, default model `llama3.1-8b` or user's choice)
  and **cloud** (Anthropic, OpenAI, Gemini).
- Auth modes in v1:
  - Ollama: no auth (local HTTP)
  - Anthropic: BYO API key
  - OpenAI: BYO API key
  - Gemini: **BYO API key OR OAuth ("Sign in with Google")**. OAuth uses a browser-
    loopback PKCE flow; refresh tokens are stored in the OS keychain.
- Provider chosen per feature in Preferences. A feature can have local and cloud configured
  but only one active at a time.
- Provider abstraction layer hides the difference from feature code. New providers added
  later do not require feature changes. The Auth strategy is a sibling abstraction
  (composition), so new auth modes (e.g., enterprise IAM in v2) do not require changes
  to provider implementations.
- Sprint sequencing within v1: S2 ships Ollama + Anthropic + Gemini (with OAuth).
  OpenAI is deferred to S6 hardening. See `docs/product/decision-brief.md` "Sprint 2
  boundary" for rationale.

### Privacy

- AI features off by default. Each must be explicitly enabled per project.
- Status bar indicator: "AI: off" / "AI: local" / "AI: cloud (provider name)" — always visible.
- A regression test asserts zero outbound TCP/UDP traffic with AI fully off across a
  scripted 60-second session covering open project, edit, save, close.
- No prompt or output is logged to disk unless the user explicitly enables a debug log.
  The debug log lives only in the project directory and is git-ignored by default.
- Cloud API keys stored in OS keychain via existing PyQt6 conventions, never in plaintext.

### UI redesign

Full redesign per discovery #4. Targets the genre-fiction-plotter workflow.

**v1 redesign surfaces (informational; concrete IA in `/plan`):**
- Project shell: navigation reorganized around "Outline / Manuscript / Notes / AI" instead
  of upstream's tree-only model.
- Scene-card view: a corkboard-style alternative to the document tree, drag to reorder.
- Character-centric panel: pull all references to a character across scenes into one view.
- AI inspector: dedicated dock for the rewrite review pane and consistency-check results.
- Status bar: AI provider state, token-usage estimate, network indicator.

**i18n.** All new strings use the existing `nwTr.tr()` pattern. Translations gated to
English + Chinese for v1 ship; other locales use English fallback until translated.

### Migration / compatibility

- The fork reads upstream novelWriter project files in their existing format without
  modification.
- A migrated project remains readable by upstream novelWriter (round-trip safe). Any
  fork-only metadata is stored under a clearly-namespaced extension that upstream ignores.
- Different user-data directory (e.g. `~/.config/<fork-name>/`) so installs do not clobber
  each other.

### Performance

- Inline rewrite must initiate within 200 ms of click on a local provider (model already
  warm). Time-to-first-token target depends on provider.
- Consistency check on a 50,000-word manuscript with default settings completes within
  60 seconds on a local model and 30 seconds on a cloud model. (Tests measure both.)
- Idle CPU/memory cost of having AI features installed-but-off is below the 5%
  regression threshold against upstream baseline.

### Testing

- Unit tests for provider abstraction, prompt templating, output parsing, privacy gating.
- Integration tests for the two features against a deterministic mock provider.
- Privacy regression test (network-zero with AI off).
- Manual test panel of 5 plotters for redesign legibility (success criterion #6 in
  decision brief).

## Post-MVP backlog (out of v1)

In priority order. Each becomes a future framing input.

1. Research helper (web search Q&A with citations).
2. Outline / synopsis generation.
3. Continuation drafting.
4. Voice fine-tuning on user's own corpus.
5. Multi-document batch operations.
6. Pantser-mode UX adjustments.
7. Screenwriting / Fountain support (if at all).

## Open items handed to `/plan`

- Concrete IA for the redesign (which screens, which interactions stay vs change).
- Provider abstraction interface signature.
- Prompt templates for both features (rewrite variants, consistency-check schema prompt).
- Output staging / undo model details (especially Feature 1's review pane semantics).
- Test corpus assembly for consistency-check accuracy measurement.
- Fork product name + repo location.
- Pinned upstream baseline commit.

## Transition rule

Advance to `/plan` only after Nexus writes the framing artifacts. Decision brief and PRD
are written; design intent flagged as `major` (full redesign).
