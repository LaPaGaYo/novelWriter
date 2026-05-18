# Gate Decision

Gate: **pass_with_advisories**

Pass round: 2
Updated: 2026-05-17 (Pass 2 closure)

## Pass 1 → Pass 2 trajectory

Pass 1 verdict was **fail** with one block-grade advisory (S-1: cloud
providers did not invoke `NetworkGate.guard()`, allowing the Preferences
Dry-run path to bypass the privacy contract). Operator selected disposition
(A): `/build --review-advisory-disposition fix_before_qa`. Fix-build landed
the privacy-gate plumbing, dataclass repr redaction, and SC-12 waiver
disclosure. Pass 2 verifies closure of S-1, S-2, S-3 with no regression.

## Pass 2 closures

| ID | Status | Evidence |
|---|---|---|
| **S-1** (block) | **closed** | `_enforce_privacy_gate()` added to Provider ABC; cloud + Ollama providers gate at top of `generate()`; staging.stage() gates at orchestration layer; `tests/test_ai/test_provider_gating.py` 12/12 PASS exercising master-off, feature-off, misconfigured-half, backward-compat, staging-layer, both-layers, registry-threading. |
| **S-2** (must-fix-before-/qa) | **closed** | `field(repr=False)` on ApiKeyAuth.api_key, OAuthCreds.access_token + refresh_token, RefreshedCreds.access_token + refresh_token. `test_repr_redacts_secrets` PASS. |
| **S-3** (must-fix-before-/qa) | **closed** | build-result.md Pass 2 addendum invokes day-10 SC-12 waiver. verification-matrix.json SC-12 carries `waiver_invoked: "day-10"` and `waiver_notes`. |

## Full-suite regression verification

`QT_QPA_PLATFORM=offscreen python -m pytest tests/test_ai/` →
**112 passed in 0.74s**, exit 0. Pass 1 was 99 tests; +13 new from Pass 2
fixes (12 gating + 1 repr-redaction). No regressions in privacy / oauth /
contract / network-gating / config / keychain / tokens / transport /
construction-offline suites.

## Open advisories (eligible for normal disposition through /qa)

S-4 through S-18 (15 items). None block /qa. Recommended disposition
when /qa runs: `continue_to_qa` with the list noted. The follow-on /build
that ships WS-4 (four-tab IA, marginalia rail) will naturally absorb
S-4 (revoke wiring), S-5 (sign-in E2E), S-6 (PENDING UX), S-9 (branding
finish-up), and other UI advisories.

## Pass 2 verdict

**pass_with_advisories** (`pass_round: 2`)

The build is ready to advance to `/qa`. The privacy contract — the
load-bearing positioning of the entire fork — is now enforced at two
independent layers on the Preferences Dry-run path. Dataclass repr
redaction protects future exception paths. SC-12 waiver is formally
invoked. No regression on the 99 prior tests; 13 new tests added with
explicit regression markers ("ProvideR made a network call ... despite
privacy gate being off" assertion in MockTransport handler).

Recommended next stage: `/qa --review-advisory-disposition continue_to_qa`.
