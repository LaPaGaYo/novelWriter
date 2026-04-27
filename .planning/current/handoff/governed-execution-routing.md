# Governed Execution Routing — Sprint 1

## Route summary

| Field | Value |
|-------|-------|
| Command | `/build` |
| Sprint | Sprint 1 (Fork Bootstrap + AI Substrate) |
| Execution mode | `local_provider` |
| Primary provider | `claude` |
| Provider topology | `single_agent` |
| Execution path | `claude-local-single_agent` |
| Planner | `claude+pm-gsd` |
| Generator | `claude-local-single_agent` |
| Evaluator A | `claude-local-single_agent-audit-a` |
| Evaluator B | `claude-local-single_agent-audit-b` |
| Synthesizer | `claude` |
| Substrate | `superpowers-core` |
| Transport | `local` |
| Fallback policy | `disabled` |
| Transport availability | available |
| Nexus approval | **approved** (recorded by `bun run bin/nexus.ts handoff`, 2026-04-26T16:54:47Z) |

## Workspace

| Field | Value |
|-------|-------|
| Path | `/Users/henry/Documents/novelWriter/.nexus-worktrees/run-2026-04-26T08-32-35-381Z` |
| Kind | git worktree |
| Branch | `codex/run-2026-04-26T08-32-35-381Z` |
| Source | `allocated:fresh_run` |
| Retirement state | active |

The worktree branch name retains the legacy `codex/` prefix because it was allocated under
Nexus v1.0.45 (before v1.0.46 introduced provider-neutral `branch/run-*` naming). The worktree
remains valid; new runs after this one will use the new naming.

## Routing rationale

Local provider was the persisted execution-mode preference at handoff time, set during
`/nexus` Phase 0 because governed CCB had no providers mounted in this session. The route
is *not* the standard governed-CCB dual-audit path (codex + gemini); it is single-agent
Claude with an internal A/B audit split.

Implication for `/review`:

- Audit will run as one Claude pass that emits two separate audit voices (`audit-a`,
  `audit-b`), then a synthesizer pass.
- This is weaker than the governed dual-provider audit because both voices share a model
  prior. Findings have lower independence guarantee.
- The user accepted this tradeoff explicitly when persisting `local_provider` during
  `/nexus` Phase 0.

To upgrade to governed dual-audit later: mount CCB providers (`tmux` then
`ccb codex gemini claude`), set `execution_mode=governed_ccb` via
`~/.claude/skills/nexus/bin/nexus-config set execution_mode governed_ccb`, and re-run
`/handoff` for the next sprint.

## Fallback policy

Fallback is **disabled**. If the local Claude provider becomes unavailable mid-build,
the run halts and emits a `BLOCKED` status. There is no silent escalation to another
route. This is the right policy for Sprint 1 because:

- The sprint goal is to verify the privacy-first AI substrate. A silent provider switch
  during build would invalidate the privacy regression test.
- Single-agent runs already have weaker audit guarantees; layered fallback would erode
  that further.

## Boundary with `/build`

`/build` consumes:
- `.planning/current/plan/sprint-contract.md` (Sprint 1 bounded scope)
- `.planning/current/plan/execution-readiness-packet.md` (broader v1 plan, for context)
- `.planning/current/plan/verification-matrix.json` (gate criteria)
- `DESIGN.md` (system spec, required for any UI work in Sprint 1)
- `.planning/current/plan/design-contract.md` (8-surface coverage map; only 2 surfaces
  in scope for Sprint 1: status bar + AI Preferences)

`/build` writes:
- Source files per `sprint-contract.md` "In-scope deliverables" list
- `.planning/current/build/build-result.md`
- `.planning/current/build/status.json`

`/build` must NOT:
- Modify any of the 6 surfaces deferred to Sprint 2-5 (project shell, scene-card view,
  character panel, AI inspector dock, AI review pane, consistency-check inline markers)
- Implement real provider backends beyond MockProvider (Sprint 2 scope)
- Implement either AI feature (Sprint 3 / Sprint 4 scope)
- Touch font bundling beyond a TODO marker (deferred to a Sprint-1 task is fine if
  scope-bounded; full bundling can land in Sprint 2 with the real providers)

## Privacy as a routing constraint

The privacy regression test (`tests/test_ai_privacy.py`) is a gate. The `/review` audits
must verify:

1. Static check: no `httpx`/`requests` imports outside `novelwriter/ai/network.py`.
2. Runtime check: 60-second scripted session with AI off produces zero outbound packets.
3. Default check: `AIConfig.enabled` defaults to `False` and persists `False` on a fresh
   project.

Failing any of the three blocks the gate, regardless of audit voice agreement.
