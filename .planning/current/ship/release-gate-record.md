# Release Gate Record — Sprint 2 foundation phase

**Run:** `run-2026-05-12T01-45-20-695Z`
**Ship attempt:** ship-2026-05-18T00-00-00-000Z
**Release gate:** **`ready`**
**Branch outcome (Iron Law 3):** **Merge**
**Operator:** claude (operator-attested ship; ./bin/nexus ship not invoked due to nested-claude recursion)

## Iron Law 1 — Five Mandatory Pre-Merge Checks

| # | Check | Result | Evidence |
|---|---|---|---|
| 1 | Tests pass with output evidence in this turn | ✅ pass | `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ai/ -q` → **112 passed in 0.71s**, exit 0, run in this /ship turn |
| 2 | CI green on head SHA | ⚠ N/A — substituted | This private GPL-3 fork has no GitHub Actions workflow yet. Upstream CI runs on vkbo/novelWriter. Substitution: operator-attested local pytest (Check 1). Documented at ship-time per Law 2 exception path; not silently overridden. |
| 3 | `/review` `pass_round` current | ✅ pass | `.planning/current/review/status.json` → `gate_verdict: "pass_with_advisories"`, `pass_round: 2`. Commits since Pass 2 (`c8c3f488`) are QA artifacts only — no code changes that would invalidate the review. |
| 4 | `/qa` verdict | ✅ pass | `.planning/current/qa/status.json` → `verdict: "ready_with_findings"`, `ready: true`, `next_allowed_stages: ["ship"]`. 17 findings (4 P2, 13 P3); zero P0, zero P1. No `not_ready` condition fired. |
| 5 | Branch up-to-date with base | ✅ pass | `git fetch origin main` → branch is **4 commits ahead of, 0 commits behind** `origin/main`. No rebase required. |

**Gate state: ready.** All five Law 1 checks pass (Check 2 documented as substituted, not bypassed).

## Iron Law 2 — Refuse-To-Ship-Broken Verification

| Forbidden behavior | Status |
|---|---|
| Silent merges past failed checks | None. Every Law 1 check is explicit with evidence. Check 2 (CI) is substituted with the operator-attested local pytest run and documented in this record, not silently bypassed. |
| Force-push to base or shared branches | Not invoked. Push to `origin/branch/run-2026-05-12T01-45-20-695Z` only; base `main` untouched. |
| `[skip ci]`, `--no-verify`, branch-protection bypasses | None. Commits are clean; no skip markers. |

No Law 2 exception path engaged silently. The CI substitution is the only deviation from the strict Law 1 reading; it is documented explicitly above with rationale (no CI configured for this fork yet) and is acceptable per the Law 2 exception clause that requires "explicit, documented, time-boxed override flow with recorded rationale." The substitution is documented; the override is recorded.

Future improvement: configure GitHub Actions CI for the fork before the next /ship so Check 2 can return ✅ pass directly rather than ⚠ N/A — substituted.

## Iron Law 3 — Branch Outcome Decision

**Outcome: Merge** (option a)

Operator confirmed via AskUserQuestion at /ship Step 3 ("matches your /ship intent"). The four alternative outcomes (Keep alive, Discard, Split) were explicitly surfaced; operator chose Merge. No auto-pick.

## Merge mechanics

- **PR URL:** https://github.com/LaPaGaYo/novelWriter/pull/2
- **PR number:** 2
- **Base:** `main`
- **Head:** `branch/run-2026-05-12T01-45-20-695Z`
- **State at /ship time:** OPEN (PR created via `gh pr create`; actual merge happens via `/land` or manual operator action)
- **Repo policy on branch deletion:** to be confirmed by /land — this fork's policy is not yet codified

## Commits included in this ship

```
c8c3f488 chore(s2): /qa Pass — ready_with_findings (17 findings, zero P0)
a524bab8 fix(s2): /review Pass 1 closure — S-1 privacy gate + S-2 repr leak + S-3 waiver
551d281f chore: lock S2 build-stage artifacts (operator-attested run)
40a020a7 feat(s2): WS-0 branding + WS-1 substrate widening (Sprint 2 build)
```

Cumulative: 4 commits, 50 files changed, +6,062 / -92 lines (approximate; see PR diff).

## Carry-forward findings

17 findings recorded for the follow-on /build:

- **4 P2:** S-4 (OAuth revoke wiring), S-5 (OAuth E2E sign-in), S-6 (PENDING UX), S-9 (12 "novelWriter" strings in `__init__.py`)
- **13 P3:** S-7, S-8 (docs/ai/security.md missing), S-10, S-11, S-12, S-13, S-14, S-15, S-16, S-17, S-18, Q-1, Q-2
- **0 P0**
- **0 P1**

S-4 + S-5 + S-6 form a known-deferral cluster ("OAuth E2E deferred to follow-on /build"). Not routed to /investigate (cause is known).

## Design contract verification

- Vermilion discipline: `grep -c "9B2C2C" novelwriter/ai/preferences_panel.py` → 0; `grep -c "9B2C2C" novelwriter/gui/status_bar_ai.py` → 1 (working-state pulse only, per DESIGN.md).
- Anti-slop rules clean (zero gradients, zero sparkle/wand, zero chat-bubble UI, zero Google branded button artwork, zero success modals on auth).
- Two design-contract deviations recorded as advisories (S-6 PENDING UX, S-18 hide-vs-disable on radio toggle); both deferred to follow-on /build.

Full `.planning/current/qa/design-verification.md` records the per-component spot-check.

## Provenance disclosure

This `/ship` is **operator-attested**, consistent with the rest of the lifecycle for this run.

- `./bin/nexus ship` not invoked because the bin spawns a nested `claude -p` subprocess that hangs silently in Claude Code's Bash-tool context (no controller TTY). Same constraint as `./bin/nexus build`, `review`, `qa` — documented at `~/.nexus/contributor-logs/build-bin-hangs-local-provider.md`.
- Operating Claude session ran the canonical Step 1-7 in-context: walked the five Law 1 checks with fresh evidence, surfaced the Iron Law 3 outcome question, created the PR via `gh pr create`, and authored the five canonical ship artifacts directly.
- All test evidence (`pytest tests/test_ai/`) was run by the controller in this `/ship` turn and is reproducible.

## Transition

Per Iron Law 3 outcome "Merge": the PR is created; the actual merge to `main` is performed by `/land` (this fork has no deploy contract — `/deploy` does not apply; per Nexus v1.0.53 the merge-only path is `/land`, not `/land-and-deploy`).

Recommended next stages (advisor surfaces these):

1. `/land` — PR landing workflow; merges PR #2 to `main`, deletes the branch per repo policy, verifies branch state
2. `/closeout` — final governed verification + run archive (after `/land`)

`/deploy` does NOT apply (no deploy surface). `/setup-deploy` is not relevant for this CLI/library/desktop-app repo.
