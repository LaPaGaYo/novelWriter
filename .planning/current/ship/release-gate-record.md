# Release Gate Record

## Overview

Nexus-owned ship guidance for governed release gating and explicit merge readiness.

## Gate Checklist

- require completed review artifacts
- require ready QA when QA was run
- keep merge and release readiness explicit in canonical gate artifacts

## Canonical Artifact Contract

Writes `.planning/current/ship/release-gate-record.md`,
`.planning/current/ship/checklist.json`,
`.planning/current/ship/deploy-readiness.json`,
`.planning/current/ship/pull-request.json`,
`.planning/current/ship/status.json`, and optionally
`.planning/current/ship/learning-candidates.json` when ship raw output contains
valid reusable learning candidates. `/closeout` may consume that optional
artifact when assembling run learnings.
Requires QA design verification for design-bearing runs before recording a ready ship state.

Follow-on support workflows may attach additional ship evidence without
changing canonical ship state, including
`.planning/current/ship/canary-status.json` from `/canary` and
`.planning/current/ship/deploy-result.json` from `/land-and-deploy`.

## Routing and Governance

Ship content starts only after completed review and optional ready QA. It must not imply any bypass of review, audit persistence, or closeout. Superpowers ship discipline informs the release gate, but Nexus-owned ship artifacts remain the only release authority.

Result: merge ready
## Design Verification

- Design impact: none
- Design contract: none
- QA design verification: verified
- Design verification artifact: .planning/current/qa/design-verification.md

