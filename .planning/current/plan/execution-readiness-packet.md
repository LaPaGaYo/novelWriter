# Execution Readiness Packet — novelWriter Fork v1

## Nexus Execution Context

- Run ID: run-2026-04-26T08-32-35-381Z
- Stage: plan
- Predecessors: `docs/product/idea-brief.md`, `docs/product/decision-brief.md`, `docs/product/prd.md`
- Execution mode: local_provider (claude, single_agent)
- Branch: codex/run-2026-04-26T08-32-35-381Z

## Known plan-stage tooling gap

The plan runtime inherited `design_impact: "none"` from `.planning/current/frame/status.json`,
which was committed before `.planning/current/frame/design-intent.json` was corrected to
`impact: "major"`. The runtime did not regenerate the verification matrix from design-intent.

**Effect:** the `verification-matrix.json` here was scaffolded with
`design_verification_required: false` and `design_review.suggested: false`. That is wrong.
The framing decision was a full UI redesign with eight named surfaces.

**Mitigation:**
- This packet treats design as a major work surface anyway.
- `.planning/current/plan/design-contract.md` is authored here as a placeholder that
  records what we know and surfaces the gap.
- Before `/handoff`, run `/plan-design-review` or `/design-consultation` to produce a real
  design contract. `/handoff` should not freeze routing without one for an MVP this design-heavy.

## Reference artifacts

- `docs/product/idea-brief.md` — user intent and discovery context
- `docs/product/decision-brief.md` — positioning, scope, non-goals, 7 success criteria
- `docs/product/prd.md` — personas, two v1 features, cross-cutting requirements
- `.planning/current/frame/design-intent.json` — corrected design impact (major, 8 surfaces)

## Workstreams (v1)

Five workstreams with explicit dependencies. Sprint sequencing follows.

### WS-0 — Fork bootstrap (foundation)

Goal: a runnable fork with a distinct identity that can ingest upstream releases as needed.

- Pick fork name (Sprint 1 decision; placeholder `plotwright`).
- Rename PyPI package, app title, About dialog, default user-data directory.
- Pin upstream baseline to a tagged release (recommended: `26.2 Alpha 0` per current branch state).
- Update `pyproject.toml`, `MANIFEST.in`, `setup/`, and CI workflows.
- Update `README.md`, `CONTRIBUTING.md`, `CREDITS.md` to reflect fork status and attribute upstream.
- Add `.fork-baseline` file pointing to the upstream commit and rebase strategy notes.

Dependencies: none. Blocks every other workstream because branding/data-dir choices ripple.

### WS-1 — AI infrastructure (the substrate)

Goal: a clean abstraction every AI feature builds on. Privacy-gated by default.

Deliverables:

- `novelwriter/ai/` package (new):
  - `provider/` — abstract `Provider` base class, `OllamaProvider`, `AnthropicProvider`,
    `OpenAIProvider`, `GeminiProvider`, plus `MockProvider` for tests.
  - `config.py` — feature flags (`ai.enabled`, per-feature opt-ins, per-feature provider choice).
  - `keychain.py` — OS-keychain wrapper for cloud API keys (extends existing keychain pattern).
  - `tokens.py` — token estimation (tiktoken-compatible, fallback heuristic for local).
  - `prompts/` — prompt template files, one per feature/transformation.
  - `staging.py` — output staging (proposed-vs-source diff model, undo-friendly).
  - `network.py` — single egress point for all cloud calls. Logs every request, asserts
    `ai.enabled == True` AND feature-specific opt-in == True before making the call.
- `novelwriter/preferences/ai_panel.py` — Preferences > AI section UI.
- `novelwriter/gui/status_bar_ai.py` — status-bar provider/state indicator.
- `tests/test_ai_privacy.py` — network-zero regression test.
- `tests/test_ai_provider_contract.py` — every provider passes the same contract.

Dependencies: WS-0.

### WS-2 — Feature: Inline rewrite

Goal: select prose, transform, review, accept.

Deliverables:

- `novelwriter/ai/features/rewrite.py` — orchestrates: collect selection, build context,
  call provider, parse output, hand to staging.
- `novelwriter/gui/ai_review_pane.py` — side-by-side review widget. Keyboard-driven.
- Editor integration: context-menu items, command palette entries, hotkey binding (gated
  by feature opt-in).
- Five transformation templates: rewrite, expand, contract, change tense, change POV.
- `tests/test_ai_rewrite_e2e.py` against `MockProvider`.
- Documentation: `docs/ai/rewrite.md`.

Dependencies: WS-1 (provider abstraction, staging, network gating).

### WS-3 — Feature: Consistency check

Goal: scan a doc/selection against the project's notes; flag inconsistencies inline.

Deliverables:

- `novelwriter/ai/features/consistency.py` — context assembly (characters, locations,
  synopses, timeline), prompt-driven inconsistency detection, structured-output parsing.
- `novelwriter/ai/schema/inconsistency.json` — JSON schema for inconsistency records.
- `novelwriter/gui/consistency_inline_markers.py` — inline marker rendering.
- `novelwriter/gui/consistency_panel.py` — side-panel with accept/dismiss/snooze.
- Strictness slider in Preferences > AI > Consistency.
- Corroboration logic: a finding requires `confidence == high` OR `≥2 supporting signals`.
- Test corpus: 3 short novels with seeded errors. Stored in `tests/corpus/consistency/`.
- `tests/test_ai_consistency_corpus.py` — recall/precision against the corpus.
- Documentation: `docs/ai/consistency.md`.

Dependencies: WS-1. Independent of WS-2 (can run in parallel).

### WS-4 — UI redesign

Goal: new project shell, IA optimized for plotters.

Deliverables (eight surfaces from `design-intent.json`):

1. Project shell — top-level navigation reorganized: Outline / Manuscript / Notes / AI.
2. Scene-card view — corkboard alternative to the document tree, drag to reorder.
3. Character panel — pull all references to a character into one view.
4. AI inspector dock — host for review pane and consistency results.
5. Status bar — provider state, network indicator, token-usage estimate.
6. Preferences > AI section — feature opt-ins, provider config, key entry.
7. AI review pane — covered in WS-2.
8. Consistency-check inline markers — covered in WS-3.

Dependencies: WS-0 (branding); WS-2 and WS-3 supply two of the surfaces. Other six can land
incrementally. Real design contract needed before locking IA — see "Known plan-stage tooling
gap" above.

### WS-5 — Migration & fork polish

Goal: existing upstream-novelWriter users can migrate without data loss.

Deliverables:

- Migration probe: open an upstream `.nwx` project; assert no schema changes when read-only.
- Round-trip integration test: open in fork, save, reopen in upstream novelWriter, diff.
- Fork-only metadata stored under namespaced extension (e.g., `nwx:ext:plotwright`).
- New default user-data dir: `~/.config/<fork-name>/` (Linux), platform equivalents.
- Branding: new icon set in `setup/`, About dialog rewrite, splash screen update.
- `docs/migration.md` for users coming from upstream.

Dependencies: WS-0. Final polish runs concurrent with hardening sprint.

## Sprint sequencing

| Sprint | Workstreams | Concrete focus | Exit criterion |
|--------|-------------|----------------|----------------|
| **S1** | WS-0 + WS-1 (start) | Fork bootstrap, provider abstraction interface, MockProvider, privacy config skeleton, network-zero test scaffolding | App launches with fork branding; `tests/test_ai_privacy.py` runs and asserts zero outbound traffic with AI off; provider contract tests pass against MockProvider. |
| **S2** | WS-1 (finish) + WS-4 (start: project shell skeleton) | Ollama + Anthropic providers, token estimation, output staging, AI Preferences panel, project-shell IA (Outline/Manuscript/Notes/AI tabs) | Real AI call works end-to-end through both providers in a smoke test; project shell shows new top-level IA; AI status-bar indicator is live. |
| **S3** | WS-2 (full) + WS-4 (review pane surface) | Inline rewrite end-to-end on five transformations; review pane keyboard-driven | Rewrite acceptance test panel passes 80/100 sample bar (or documents what didn't and why). |
| **S4** | WS-3 (full) + WS-4 (consistency markers + character panel) | Consistency check end-to-end; corroboration logic; test corpus assembled; strictness slider | Test-corpus recall ≥70%, FPR ≤20% at default strictness. |
| **S5** | WS-4 (finish) + WS-5 | Scene-card view, AI inspector dock polish, character-panel polish, migration probe + round-trip test, branding | Moderated 5-plotter legibility test ≤8min task completion; round-trip migration zero-diff. |
| **S6** | Hardening | Cross-platform smoke (Linux/Win/macOS), translation pipeline check, packaging, release notes, success-criteria measurement | All seven `decision-brief.md` success criteria measured and either met or formally waived. |

Each sprint will run its own `/plan` -> `/handoff` -> `/build` -> `/review` -> `/qa` -> `/ship` -> `/closeout` cycle.

## Risks (planning-stage)

| Risk | Owner sprint | Mitigation |
|------|--------------|------------|
| Provider abstraction over-fits to one provider, painful to add a second | S1 | Implement two providers in S1 (Mock + one real) before features start. |
| Privacy gating bypassed by a future contributor | S1 | Single-egress `network.py`; CI test asserts no `httpx`/`requests` import outside that module. |
| UI redesign sprawls and slips MVP | S2-S5 | Design contract before /handoff; budget per surface; cut scope on individual surfaces, not on the privacy/AI core. |
| Consistency-check accuracy regresses with model updates | S4 + S6 | Test corpus is a hard CI gate. New model versions must clear it before they ship as defaults. |
| Upstream merge becomes unmaintainable | S6 | Document a quarterly upstream-merge runbook in WS-5; tag fork-specific files explicitly. |
| Local Ollama install friction kills adoption | S2 + S5 | Cloud-first onboarding flow; "switch to local later" guide; ship a known-good Ollama config. |
| GPL-3 attribution slip in fork branding | WS-0 + WS-5 | Legal review checkpoint in S6; CREDITS.md and About dialog explicitly attribute upstream. |

## Verification matrix override notes

The `verification-matrix.json` scaffolded by the bin understates design verification.
The corrected expectations are:

- `design_review.suggested: true` — full UI redesign per frame design-intent.
- `design_verification_required: true` — at least 4 of the 8 surfaces are net-new.
- A `/plan-design-review` or `/design-consultation` artifact is **required** before `/handoff`.

The plan stage author has updated `verification-matrix.json` accordingly. The corrections
are clearly marked.

## Open items (to resolve in sprint plans)

These move from this v1 packet into individual sprint contracts.

- Final fork product name (placeholder: `plotwright`)
- Pinned upstream baseline commit (recommended: tag `v26.2-alpha-0` head)
- Test-corpus assembly approach (S4 owner)
- Token-estimate accuracy benchmark (S2 owner)
- Migration round-trip schema diff tool (S5 owner)

## Transition Rule

Advance to `/handoff` only after Nexus declares execution ready *and* a real design contract
exists. The current `design-contract.md` is a placeholder; replace it via
`/plan-design-review` or `/design-consultation` before handoff.

## Sprint contract pointer

Sprint 1's bounded scope lives in `.planning/current/plan/sprint-contract.md`. That is the
file `/handoff` and `/build` will execute against.
