# Decision Brief — novelWriter Fork: AI-Assisted Plotter's Workbench

## Nexus Execution Context

- Run ID: run-2026-04-26T08-32-35-381Z
- Stage: frame
- Predecessor: `docs/product/idea-brief.md`
- Execution mode: local_provider (claude, single_agent)
- Branch: codex/run-2026-04-26T08-32-35-381Z

## Positioning

A privately maintained fork of novelWriter, retargeted as an AI-assisted workbench for
**genre-fiction plotters** — novelists who outline before drafting and care about
internal consistency across long manuscripts.

The fork keeps novelWriter's strengths (plain-text storage, project metadata, offline-first,
Qt6 desktop) and adds two AI features designed to help plotters maintain craft control
rather than replace it: inline transformation of selected prose, and consistency checking
against the project's own notes. The product positioning is the opposite of "AI slop":
the AI assists with the parts of plotting that novelWriter already models (characters,
locations, scenes), not the parts where voice matters most (first-draft prose).

## Why now

novelWriter has the strongest plain-text + structured-metadata model in the niche. That
metadata (character notes, scene synopses, cross-references) is exactly what a consistency-
check feature needs as grounding context. Most AI writing tools start from a blank doc;
this fork starts from a structured project that already knows its own world.

## Scope (v1)

**In:**
- Two AI features:
  1. **Inline rewrite** — select prose, request transformation (rewrite, expand, contract,
     change tense/POV). Output is staged for review before replacing source text.
  2. **Consistency check** — scan a document or selection for character/place/timeline
     contradictions against the project's notes. Report inconsistencies inline.
- **Dual provider model** — local LLM (Ollama) and cloud BYO-API-key (Anthropic, OpenAI,
  Gemini). User picks per feature.
- **Privacy stance** — every AI feature is off by default; user opts in per feature, per
  project. No telemetry on prompts or outputs. Outbound network is explicit.
- **Full UI redesign** — new project shell, layout, and information architecture optimized
  for the plotter workflow (outline-first, scene cards, character-centric navigation).
- **i18n preserved** — new strings respect existing 16-locale translation pipeline.
- **Test coverage** — new modules have pytest coverage on parity with existing `tests/` suite.

**Out (post-MVP backlog, in priority order):**
1. Research helper (web/lookup Q&A with citations)
2. Outline/synopsis generation (auto-summarize chapters; auto-skeleton from synopsis)
3. Continuation drafting ("write next paragraph") — deliberately delayed until UX patterns
   for human-vs-AI authorship attribution are validated
4. Voice fine-tuning on the user's own corpus
5. Multi-document batch operations

## Non-goals (explicit)

- **Not** an upstream contribution. We do not propose these features to vkbo/novelWriter.
- **Not** a web app. PyQt6 desktop only. No browser shell, no Electron.
- **Not** a screenwriting tool. Fountain/screenplay format support is out of scope.
- **Not** a "ghostwriter." v1 will not generate prose continuation. Inline rewrite operates
  only on text the user has already written.
- **Not** opinionated about cloud providers. BYO-key, no proxy, no aggregation.
- **Not** a SaaS. No accounts, no server, no per-seat pricing. GPL-3.0 fork.
- **Not** chasing pantsers / discovery writers in v1. Plotter workflow first.

## Target persona (v1)

**Primary:** the genre-fiction plotter who already uses Scrivener, novelWriter, or Obsidian
for novel projects, has 2-5 manuscripts in flight, drafts in long sessions, and re-reads
chapters for continuity errors. Comfortable with desktop apps, willing to install local
LLMs or paste an API key.

**Anti-persona:** writers who want a one-click "draft my novel" tool. The product will
feel slow and constraining to them on purpose.

## Success criteria (v1)

Each is testable. We will not ship v1 until each is met or explicitly waived.

1. **Adoption signal:** at least 50 distinct users complete the AI-feature opt-in flow on
   a real project (not the sample) within 60 days of v1 release.
2. **Privacy guarantee verified:** with both AI features disabled, network traffic out of
   the app is zero across a recorded 1-hour session. (Tested via packet capture.)
3. **Consistency-check signal:** in a curated 3-novel test corpus with known continuity
   errors, the consistency-check feature flags at least 70% of the seeded errors with
   under 20% false-positive rate.
4. **Inline-rewrite quality bar:** of 100 sampled rewrite outputs (across rewrite/expand/
   contract), at least 80 are accepted or accepted-with-edit by the test panel.
5. **Provider parity:** every AI feature works on at least one local model (Ollama, e.g.
   llama3.1-8b) and one cloud model (Anthropic Claude 4.7), with output quality difference
   documented but not blocking.
6. **Redesign legibility:** new-user task completion (open project, draft first scene, run
   consistency check) under 8 minutes for a moderated test of 5 plotters with no prior
   novelWriter exposure.
7. **Existing-user migration:** users with existing upstream-novelWriter projects can open
   them in the fork without data loss or format conversion. (Carryover compatibility.)

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Upstream novelWriter codebase churn breaks the fork | Pin to a tagged upstream release for v1; document a periodic merge strategy as part of /retro. |
| Local LLM (Ollama) install friction blocks adoption | Ship a "Test with cloud first, switch to local later" onboarding; keep cloud-BYO-key as default opt-in. |
| Consistency-check false positives erode trust | Tunable strictness slider; require at least 2 corroborating signals before flagging. |
| Privacy regression slips in | Off-by-default + explicit per-feature opt-in + a network-activity indicator in the status bar; integration test verifies zero outbound traffic when AI is off. |
| AI feature drift in cost | BYO-key model means user pays own usage; ship per-feature token estimate before each call. |
| GPL-3 fork attribution issues | CONTRIBUTING / LICENSE updates clearly attribute upstream; product naming clearly differentiates from vkbo/novelWriter. |
| Maintainer relations | Keep the fork respectful: reference upstream, don't claim "novelWriter" name in branding, don't compete in upstream's distribution channels. |

## Distribution and fork stance

- New fork name TBD in `/plan` (suggestion: `plotwright` or `narrare` — names need check).
- GPL-3.0 maintained. License notice + attribution to vkbo/novelWriter retained.
- Distribution: GitHub releases, PyPI under new package name, no app stores in v1.
- Branding: explicitly *not* novelWriter. Different icon, different About dialog, different
  user-data directory to avoid colliding with upstream installs.

## Open items routed to `/plan`

- Final fork product name and repo location.
- Pinned upstream commit / release for v1 baseline.
- Concrete redesign scope: which screens, which IA changes, what stays.
- AI feature data flow: prompt templates, context assembly, output staging, undo model.
- Provider abstraction interface (so adding a future provider doesn't require core changes).
- Test plan for the privacy guarantee and consistency-check accuracy.

## Transition Rule

Advance to `/plan` only after Nexus writes the framing artifacts. Frame artifacts are
written. Open items above are planning concerns, not framing concerns.
