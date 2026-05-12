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

---

## Sprint 2 boundary (added 2026-05-12, run-2026-05-12T01-45-20-695Z)

Sprint 2 is being framed against the v1 decisions above. Decisions specific to S2 that
adjust scope without changing v1 boundaries:

### Provider lineup adjustments

The v1 PRD lists **Ollama + Anthropic + OpenAI + Gemini** as v1 providers. Sprint 2
ships only **Ollama + Anthropic + Gemini**. **OpenAI is deferred to Sprint 6 hardening.**

Rationale: two cloud providers (Anthropic + Gemini) stress-test the Provider
abstraction enough for v1 confidence. OpenAI adds zero unique positioning (no OAuth
value, no "easiest setup" story) and consumes 2-3 dev-days that better serve Gemini
OAuth completeness. The v1 PRD's provider list remains correct as a v1-totality
statement; the cut is sprint-level, not v1-level.

### Gemini OAuth pulled forward

Gemini supports both **API key (BYO from ai.google.dev) AND OAuth ("Sign in with
Google")** in S2. The OAuth UX is an explicit button in `Preferences → AI → Gemini`,
not auto-detection of gcloud ADC, not lazy auth on first call.

**Positioning rationale:** plotwright becomes the only desktop novel-writing tool
with Gemini OAuth. Sudowrite, NovelCrafter, Plottr-with-AI, Squibler all require a
paid account or BYO API key. The free-tier Gemini + OAuth combination gives a user
working AI in under 30 seconds with no credit card and no key management. This is
the S2 release lede.

**Engineering rationale:** OAuth is the first non-API-key auth path in the system.
Implementing it now forces the `Provider` ABC and `keychain.py` to widen for
multi-auth at v1 time rather than v2 retrofit. The Auth strategy class (composition)
is the recommended shape (sibling Auth ABC, not polymorphic credential blob).

### Sprint 2 visual differentiation

S2 starts WS-4 (UI redesign) with the four-tab top-level IA: **Outline / Manuscript /
Notes / AI**. This is the first sprint where a returning upstream-novelWriter user
sees that plotwright is a different product.

S2 also lands the **marginalia rail primitive** (three-column geometry, empty rail
rendering). This is structural, not feature: the AI-as-marginalia design decision
(DESIGN.md locked decision #1) is the architectural answer to "AI as editor, not
author." Without the rail primitive in S2, S3 would have to ship rail + rewrite +
review pane + keyboard nav in one sprint.

Out of scope for S2: scene-card view (S5), character panel restructure (S4/S5),
outline tree restructure (S4/S5), marginalia rail content (S3+).

### S1 branding gap closed in S2

Sprint 1 contract said `appName`, `appHandle`, window title, and About dialog would
be renamed from "novelWriter" to "plotwright". The rename did not ship. S2 WS-0
absorbs the cleanup. Cost is 0.5 dev-day. Asymmetric vs. deferring: `appHandle` flows
into the user-data directory path, so renaming later would require a migration probe
for users whose project directories were created with the wrong handle.

### Privacy contract extension

S1's network-zero regression test (`tests/test_ai/test_privacy.py`) extends in S2 to
also assert no provider SDK is in `sys.modules` after `import novelwriter.ai`. Reason:
some cloud SDKs do eager network discovery on import. Lazy SDK import inside each
provider module is the rule. CI lint enforces no `import httpx` / `import requests`
outside `novelwriter/ai/transport.py`.

### Sprint 2 success criteria (added to v1)

S2 ships when each of these is green. Full numbered list lives in
`.planning/current/frame/s2-scope.md` ("Success criteria" section). Headline gates:

- `test_privacy.py` (S1) still passes with three providers registered.
- Auth strategy class with `NoAuth` / `ApiKeyAuth` / `OAuthCreds` subclasses.
- Ollama + Anthropic + Gemini all pass `test_provider_contract.py`.
- Gemini OAuth works end-to-end: button → browser → callback → keychain → status bar.
- Token-accuracy benchmark: 20% bound on committed corpus.
- Four-tab IA + marginalia rail primitive visible. AI tab shows "EDITOR'S NOTES"
  empty state.
- Window title says "plotwright"; `appHandle` renamed.
- Real `design-contract.md` exists for WS-4. DESIGN.md extended.

### Sprint 2 risks accepted

The S2 estimate is 22-27 dev-days (vs. S1's 8-12). The risk lead recommended cutting
OAuth to S6 (R1 score 20/25). The product owner rejected that cut in favor of
positioning value. Mitigations:

- **OAuth has a hard day-4 cut-line.** If `test_oauth_flow.py` is not green by end of
  dev-day 4, OAuth defers to S6 and Gemini ships API-key only.
- **OpenAI is the primary scope-cut lever** (already locked).
- **WS-4 has a "tabs + empty rail" scope ceiling.** No marginalia rendering, no
  character panel, no scene cards.
- **`/design-consultation` runs in parallel with WS-1 finish**, not sequentially.
- **Slip indicators tracked daily.** Day-4 (OAuth), day-7 (design contract), day-10
  (token accuracy), day-12 (WS-4 file footprint), day-14 (smoke test), day-16 (final).

### Marketing/positioning impact

The S2 release notes lede: "The fastest privacy-respecting setup in the category.
Sign in with Google, AI works. Network-zero by default if you don't." README.md
updates land at end of S2, not S6.

The S2 release explicitly does NOT market the rewrite or consistency-check features
(they don't exist yet). The S2 story is "AI plumbing you can trust, with one-click
sign-in." Not "AI features."
