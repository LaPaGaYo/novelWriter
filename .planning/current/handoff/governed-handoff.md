# Governed Handoff — Sprint 1

`/handoff` froze the routing intent for Sprint 1 of the novelWriter fork v1. `/build` now
has explicit permission to proceed against the bounded sprint scope.

## Approval

| Field | Value |
|-------|-------|
| Approved at | 2026-04-26T16:54:47Z |
| Approved by | Nexus runtime (via `bin/nexus.ts handoff`) |
| Approval reason | "Nexus approved the requested local provider route" |
| Sprint | Sprint 1 — Fork Bootstrap + AI Substrate |
| Run ID | `run-2026-04-26T08-32-35-381Z` |
| Branch | `codex/run-2026-04-26T08-32-35-381Z` |

Routing detail and rationale: `governed-execution-routing.md`.

## Execution Contract — what `/build` is permitted to do

The complete, bounded sprint scope is in:

- **`.planning/current/plan/sprint-contract.md`** — Sprint 1 deliverables, files to create,
  out-of-scope list, 10 verification items. **This is the canonical contract.**
- **`.planning/current/plan/execution-readiness-packet.md`** — broader v1 plan for context.

Sprint 1 in one sentence: *stand up the fork as a runnable, branded application, and put
the AI substrate (provider abstraction, privacy gating, MockProvider, network-zero
regression test) in place. No real AI feature ships in Sprint 1.*

## Design contract

**`DESIGN.md`** is authoritative for every visual or UI decision in Sprint 1. The two Sprint-1
UI surfaces are:

- AI Preferences pane (Preferences > AI tab — master toggle, per-feature toggles disabled
  with "available in next sprint" copy, provider rows hidden until enabled)
- Status-bar AI widget (`AI: off` / `AI: ready (mock)` indicator, click opens AI Preferences)

The other six surfaces (project shell, scene-card view, character panel, AI inspector
dock, AI review pane, consistency-check inline markers) are explicitly out of Sprint 1
scope. The visual language is locked in DESIGN.md, but per-surface implementation defers
to Sprint 2-5.

## Review scope (what `/review` will assess)

| Field | Value |
|-------|-------|
| Mode | `full_acceptance` |
| Source stage | `plan` |
| Blocking items | (none in advance — all 10 sprint-1 verification items are gate-affecting) |
| Advisory policy | `out_of_scope_advisory` (findings outside Sprint 1 scope downgrade to advisory, do not block) |

Full acceptance means `/review` audits the entire Sprint 1 diff against the sprint contract.
Out-of-scope findings (e.g., "the project shell still looks upstream") are recorded as
advisory, not blocking, because those surfaces belong to later sprints.

## Verification gates that block Sprint 1 acceptance

From `verification-matrix.json` and `sprint-contract.md`:

1. Existing upstream test suite passes against the renamed package.
2. `tests/test_ai_privacy.py` passes (zero outbound traffic with AI off). **Hard gate.**
3. `tests/test_ai_provider_contract.py` passes against MockProvider.
4. `tests/test_ai_network_gating.py` passes (PrivacyGatingError on disallowed call).
5. `tests/test_ai_config_persistence.py` passes (AI config round-trips).
6. App launches with the new fork name in window title and About dialog.
7. AI status-bar widget visible, default `AI: off`.
8. AI Preferences tab visible, master toggle present, per-feature toggles correctly disabled.
9. `docs/fork.md`, `docs/ai/architecture.md`, `docs/ai/privacy.md` exist and pass markdown lint.
10. `.fork-baseline.json` exists and points at a reachable upstream commit/tag.

Plus from this handoff:

11. **Static-check gate:** no `httpx` / `requests` imports outside `novelwriter/ai/network.py`.
12. **DESIGN.md adherence:** AI Preferences pane and status-bar widget match the spec in
    `DESIGN.md` (typography, color tokens, component specs).

## Provenance for downstream stages

- `/build` should reference this handoff in build-result metadata.
- `/review` should reference both `governed-execution-routing.md` and the full
  `verification-matrix.json` in audit findings.
- `/qa` should treat the privacy regression test as a hard gate (any failure is `BLOCKED`,
  not a finding).
- `/ship` should reject if any of items 2, 3, or 11 are red.

## Risks at handoff

- **Single-agent audit weakness.** A/B audit voices share a Claude prior; findings have
  lower independence guarantee than governed dual-audit. Mitigation: tighter human review
  on Sprint 1 outputs since this is the foundational sprint.
- **Local provider unavailability mid-build.** Fallback is disabled; the run halts
  cleanly if Claude becomes unreachable. Recoverable via `/handoff` re-run.
- **Renaming surface area.** Sprint 1 touches `pyproject.toml`, `setup/`, app titles,
  user-data dirs. PyPI name conflict on the fork name (`plotwright`) would force a rename.
  Mitigation in sprint-contract.md: pre-check PyPI before locking.

## Done state for handoff

Three artifacts written, one approval recorded, route validated and approved.

- `.planning/current/handoff/governed-execution-routing.md`
- `.planning/current/handoff/governed-handoff.md` (this file)
- `.planning/current/handoff/status.json` (machine-readable)

`/build` may proceed.
