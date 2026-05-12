# Closeout Record

## Overview

Nexus-owned closeout guidance for archive verification, provenance consistency, and final readiness.

## Nexus Execution Context

- Run ID: run-2026-04-26T08-32-35-381Z
- Command: closeout
- Stage: closeout
- Continuation mode: project_reset
- Execution mode: local_provider
- Primary provider: claude
- Provider topology: single_agent

### Predecessor Artifacts

- .planning/current/review/status.json
- .planning/current/qa/status.json
- .planning/current/ship/status.json
- .planning/audits/current/meta.json

## Closeout Checklist

- verify audit completeness
- verify archive state
- verify legal transition history

## Canonical Artifact Contract

Writes `.planning/current/closeout/CLOSEOUT-RECORD.md`, `.planning/current/closeout/FOLLOW-ON-SUMMARY.md`, `.planning/current/closeout/follow-on-summary.json`, `.planning/current/closeout/NEXT-RUN.md`, `.planning/current/closeout/next-run-bootstrap.json`, and `.planning/current/closeout/status.json`.

When `/review`, `/qa`, or `/ship` leave valid learning-candidates artifacts behind, `/closeout` assembles the canonical run learnings and writes `.planning/current/closeout/LEARNINGS.md` and `.planning/current/closeout/learnings.json` alongside the other closeout outputs. If no valid candidates are available on rerun, closeout removes any stale learnings artifacts and ledger references instead of leaving them behind.

Follow-on support workflows may attach additional closeout evidence without
changing canonical closeout state, including
`.planning/current/closeout/documentation-sync.md` from
`/document-release`. `/closeout` assembles the currently attached QA/ship/closeout
follow-on evidence into `.planning/current/closeout/FOLLOW-ON-SUMMARY.md` and
`.planning/current/closeout/follow-on-summary.json` so fresh discover, retro,
and learn flows can consume one stable index instead of rediscovering each raw
artifact separately.

## Final Gate

Closeout is the final governed conclusion of the work unit and must remain blocked if archive or provenance checks are inconsistent.
