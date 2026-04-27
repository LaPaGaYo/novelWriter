# Idea Brief — AI-Assisted Writing & UX Redesign for novelWriter

## Nexus Execution Context

- Run ID: run-2026-04-26T08-32-35-381Z
- Stage: discover
- Continuation mode: project_reset
- Execution mode: local_provider (claude, single_agent)
- Branch: main (worktree: codex/run-2026-04-26T08-32-35-381Z)

## Stated Intent

> "I want to involve AI writer into this existing project. We can use AI to gather all kinds of information that we need, redesign the UI/UX."

User wants to add AI assistance to novelWriter, in two directions:
1. AI as a research/information-gathering helper for the writer.
2. AI involved in drafting (an "AI writer" inside the app).
3. A UI/UX redesign, presumably to surface these new capabilities.

## Project Context

novelWriter is an established, production-stable, offline-first PyQt6 desktop app for novelists.

- **Stack:** Python 3.11+, PyQt6, pyenchant for spellcheck. Cross-platform (Linux, Windows, macOS).
- **Storage:** Plain-text-on-disk per document, version-control friendly.
- **Format:** Minimal Markdown-inspired syntax with metadata for synopsis/comments/cross-references.
- **Maintainer:** Veronica Berglyd Olsen. Upstream repo: vkbo/novelWriter.
- **License:** GPL-3.0-or-later (with Apache-2.0 and CC-BY-4.0 components).
- **Maturity:** Development Status 5 - Production/Stable. Currently 26.2 Alpha 0.

## Goals (captured)

1. Let writers use AI to gather background information (research) without leaving the app.
2. Let writers use AI to draft, suggest, or transform prose inline.
3. Refresh the UI/UX so AI features feel native rather than bolted on.

## Constraints (captured)

### CRITICAL — Upstream policy conflict

The upstream `README.md` states verbatim:
> "This project is developed with care, and is 100% free of AI slop."

Adding AI writing/research features to *upstream* novelWriter would directly contradict
the maintainer's stated position. This is the single biggest discovery finding and must
be resolved before any framing work begins.

### Technical constraints (likely)

- **Desktop, offline-first.** AI features must reconcile with users who expect the app
  to work without a network. Options: bring-your-own-key cloud LLM, local LLM (Ollama,
  llama.cpp), or both.
- **Plain-text-on-disk storage.** AI-generated content needs to fit the existing file
  layout cleanly, ideally distinguishable from human-authored content.
- **Privacy/copyright.** Sending novel manuscripts to a third-party LLM has obvious
  IP implications. Many users will refuse. Local-only option likely required.
- **PyQt6 UI.** Redesign must stay in Qt6, not a web reskin.
- **i18n.** Existing translations cover ~16 locales (see `i18n/`). New UI must respect this.
- **Test coverage.** Existing test suite in `tests/` — additions should keep it green.

## Decisions (answered)

| # | Question | Answer |
|---|----------|--------|
| 1 | Fork vs upstream | **(a) personal/private fork** — diverges from vkbo/novelWriter |
| 2 | AI provider model | **(c) Both** — local LLM and cloud BYO-key, user chooses per-feature |
| 3 | AI feature scope | **all five** — research, inline rewrite, outline/synopsis, consistency checking, continuation drafting |
| 4 | UI/UX redesign scope | **(c) Full redesign** — new project shell, layout, information architecture |
| 5 | Target user | new sub-segment (specific persona TBD) |
| 6 | Privacy default | off by default, explicit opt-in per feature |

### Implications and unresolved tensions for `/frame`

These answers are workable, but two of them set up scope tension that `/frame` must resolve:

- **#3 says all five AI features for MVP.** Each one is a real engineering surface (UI,
  prompt design, provider plumbing, evaluation). Five of them at once + a full UI redesign
  + dual provider model is several quarters of work for a small team. Frame stage should
  either bound MVP to ~2 features and slate the rest as post-MVP, or accept a much longer
  v1 timeline. Flag this explicitly in the framing artifact.

- **#5 says new sub-segment but not which one.** Genre fiction (plotters), screenwriters,
  technical writers, world-builders for TTRPG, and academic-adjacent writers all have
  different needs and would shape the redesign differently. Framing must pick one before
  the IA work starts, or the redesign will sprawl.

- **#1 + #4 + #6 combination is consistent and clean.** A private fork with full redesign
  and opt-in privacy is the lowest-risk product position — no upstream coordination
  needed, full design freedom, conservative privacy stance.

## Open questions (originally captured, now answered)

These are the decisions only you can make. Pick answers, then we move to `/frame`.

1. **Fork vs upstream.** Is this work for:
   x (a) a personal/private fork that diverges from vkbo/novelWriter, or

   - (b) a proposed upstream contribution (will require maintainer buy-in, currently appears
         opposed), or
   - (c) a derivative product built on novelWriter's codebase under GPL?

2. **AI provider model.** Which is in-scope?
   - (a) Local-only (Ollama / llama.cpp) — privacy-safe, slower, larger install footprint.
   - (b) Cloud-only with bring-your-own-key (OpenAI/Anthropic/Gemini).
   x (c) Both, user chooses per-feature.

3. **AI feature scope (pick what's in MVP).**
   x (a) Research helper — answer factual/world-building questions with citations.
   x (b) Inline rewrite/expand/contract — select prose, request transformation.
   x (c) Outline/synopsis generation from existing text.
   x (d) Character/setting consistency checking against project notes.
   x (e) Continuation drafting ("write next paragraph").

4. **UI/UX redesign scope.**
   - (a) Surgical — add AI panel/sidebar, leave existing UI alone.
   - (b) Modernize the existing chrome (icons, density, theme) without restructuring.
   x (c) Full redesign — new project shell, layout, and information architecture.

5. **Target user.** Same novelist persona as upstream, or a new sub-segment (e.g., genre
   writers who want plotting help, technical writers, screenwriters)? new sub-segment

6. **Privacy default.** Off by default with explicit opt-in per feature, or on with clear
   redaction options?Off by default with explicit opt-in per feature

## Next step

All six questions answered. Discovery is ready to advance.

`/frame` will need to:
1. Pick the target sub-segment for question #5 (genre fiction, screenwriters, TTRPG
   world-builders, academic, technical, etc.).
2. Bound MVP for question #3 — recommend 2 features for v1, slate the other 3 as
   post-MVP.
3. Define success criteria, non-goals, and named milestones.

Run `/frame` to begin scope definition.

## Canonical Artifact Contract

Writes `docs/product/idea-brief.md` (this file) and `.planning/current/discover/status.json`.

## Transition Rule

Advance to `/frame` only after the six open questions have answers and the upstream-policy
conflict is resolved.

**Status: all six answered. Upstream conflict resolved by choosing fork (1a). Ready to advance.**
