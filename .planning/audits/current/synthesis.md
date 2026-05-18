# Review Synthesis — Sprint 2 foundation phase

**Run:** `run-2026-05-12T01-45-20-695Z`
**Review attempt:** review-2026-05-17 (Pass 1)
**Pass round:** 1
**Synthesizer:** claude (operator-attested)
**Discipline:** Nexus dual-audit per `/review` SKILL.md Iron Laws 1, 2, 3

## Law 1 — four required artifacts

### 1. Scope summary

Sprint 2 foundation phase build (46 files, +4707/-164 lines) delivers WS-0 fork branding (appName/appHandle → "plotwright" at `config.py:113-117`, About dialog at `dialogs/about.py:49,57`, `__init__.py` partial — see disagreement protocol below) and WS-1 AI substrate widening from S1 interface-only stubs to full S2 implementations: `auth.py` (203 lines, `Auth` ABC + `NoAuth`/`ApiKeyAuth`/`OAuthCreds` subclasses with 60s refresh window), `oauth.py` (486 lines, browser-loopback PKCE with cryptographic state CSRF, refresh, revoke), `transport.py` (single `httpx.Client` factory chokepoint), `tokenizers.py` (per-provider adapters with lazy tiktoken), `keychain.py` widened (228 lines, `OSKeyChainStore` via `keyring>=24.0`, OAuth JSON-blob round-trip), three cloud providers (`anthropic.py`, `gemini.py`, `ollama.py`), `provider/registry.py`, `staging_consumer.py`, `config.py` schema bump 1→2 with `provider_configs` dict, status bar (286 lines: 1Hz vermilion pulse via QPropertyAnimation, four states, ERROR with `#7A2222` not Vermilion, keyboard reachable), AI Preferences panel (770 lines: per-feature toggles unlocked, provider rows, Gemini API-key + OAuth radio with state machine, dry-run button). 99 new + extended tests across 10 modules; fixtures with token corpus (4 files) and FakeKeyStore. **WS-4 components (four-tab IA, marginalia rail) explicitly deferred** to follow-on /build per build-result.md. **Build provenance is operator-attested**: the spawned-claude path hung silently (Bash tool buffer constraint); operating Claude detected, terminated, authored artifacts directly. Test evidence is real and reproducible (run by controller in this review turn).

### 2. Fresh test evidence (run in this review turn)

Command: `QT_QPA_PLATFORM=offscreen python -m pytest tests/test_ai/ --tb=short`
Workspace: `/Users/henry/Documents/novelWriter/.nexus-worktrees/run-2026-05-12T01-45-20-695Z`
Python: `.venv/bin/python` (3.12.12)

```
============================== test session starts ==============================
platform darwin -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0
PyQt6 6.11.0 -- Qt runtime 6.11.0 -- Qt compiled 6.11.0
collected 99 items

tests/test_ai/test_auth_strategies.py ...........                        [ 11%]
tests/test_ai/test_config_persistence.py ...........                     [ 22%]
tests/test_ai/test_keychain_oauth.py ........                            [ 30%]
tests/test_ai/test_network_gating.py ......                              [ 36%]
tests/test_ai/test_oauth_flow.py ...........                             [ 47%]
tests/test_ai/test_privacy.py .....                                      [ 52%]
tests/test_ai/test_provider_construction_offline.py ..........           [ 62%]
tests/test_ai/test_provider_contract.py .............................    [ 91%]
tests/test_ai/test_tokens_accuracy.py ......                             [ 97%]
tests/test_ai/test_transport_isolation.py ..                             [100%]

============================== 99 passed in 0.90s ==============================
```

Exit code: 0. Re-verified independently in audit slot B's process.

### 3. Risk register

Both slots returned 21 findings total (10 from slot A, 11 from slot B). After Law 3 disagreement resolution (below), the consolidated register:

| ID | Severity | Slot | One-line | File |
|---|---|---|---|---|
| **S-1** | **block** | A-F1 | Cloud providers don't invoke NetworkGate.guard(); Dry-run path bypasses privacy contract | `provider/anthropic.py:85-107`, `provider/gemini.py:88-121` |
| **S-2** | advisory (must-fix-before-/qa) | B-F1 | OAuthCreds + ApiKeyAuth dataclass `__repr__` leaks secrets to logs/tracebacks | `ai/auth.py:108-115, 138-159` |
| **S-3** | advisory | A-F2 + B-F8 | SC-12 contract claims 20% bound; test asserts ±50%; waiver authorized but not invoked in build-result | `tests/test_ai/test_tokens_accuracy.py:53-74` + build-result.md |
| **S-4** | advisory | B-F2 | Sign-out deletes keychain blob but does NOT call Google's /o/oauth2/revoke endpoint | `preferences_panel.py:752-760` |
| **S-5** | advisory | B-F3 + A-F9 | OAuth client_id not wired; sign-in handler is a stub; SC-2 cannot fire end-to-end | `preferences_panel.py:738-750` |
| **S-6** | advisory | B-F4 | Design contract PENDING state visual UX (progress strip, Cancel link) not implemented | `preferences_panel.py:738-750` |
| **S-7** | advisory | B-F5 | Privacy regression test forbidden list omits httpx; AST scan doesn't cover oauth/staging/keychain/auth/tokenizers | `test_privacy.py:39-45`, `test_transport_isolation.py` |
| **S-8** | advisory | B-F6 | docs/ai/security.md is a sprint deliverable but is missing | `docs/ai/` |
| **S-9** | advisory | A-F7 + B-F10 | WS-0 branding incomplete — 6+ user-visible "novelWriter" strings remain (version, help, splash, error dialog, macOS CFBundleName, AppUserModelID) | `novelwriter/__init__.py:130,183,224,251,270,276,295` |
| **S-10** | advisory | B-F9 | OAuth refresh has no concurrency lock; refresh-during-call race possible (low probability in PyQt6 main-thread model) | `auth.py:177-191` |
| **S-11** | advisory | B-F11 | adapter-output.json provenance fields are placeholders; future audit reading only the JSON would misclassify the operator-attested run as a normal spawn | `.planning/current/build/adapter-output.json:22-24, 41-47` |
| **S-12** | advisory | A-F3 | Gemini provider drops cached client on every generate() call; defeats lazy-cache for ApiKeyAuth path | `provider/gemini.py:98-102` |
| **S-13** | advisory | A-F4 | Status-bar pulse uses LoopCount(-1) + manual swap instead of native ping-pong; subtle race window | `gui/status_bar_ai.py:230-258` |
| **S-14** | advisory | A-F5 | Per-feature provider dropdown exposes test-only `mock` to end users | `preferences_panel.py:161`, `registry.py:101-106` |
| **S-15** | advisory | B-F7 | Exception logging in keychain/preferences may indirect-leak secrets if library messages echo argument values | `preferences_panel.py:614,732`, `keychain.py:127` |
| **S-16** | nit | A-F6 | test_transport_isolation.py error message references nonexistent `build_cloud_client` (actual: `make_client`) | `tests/test_ai/test_transport_isolation.py:121` |
| **S-17** | nit | A-F8 | available_providers() ordering is dict-iteration order, not a defined contract | `registry.py:109-111` |
| **S-18** | nit | A-F10 | Token corpus is 4 files; sprint contract specified ~10 | `tests/fixtures/token_corpus/` |

### 4. Explicit gate verdict

**fail** (Pass 1)

Per Iron Law 2: any Pass-1 block-grade advisory forbids `pass` / `pass_with_advisories`. S-1 is block-grade. Pass 1 verdict is **fail**; Pass 2 protocol required after S-1 is addressed.

`pass_round: 1`

## Law 3 — disagreement protocol

The two slots disagreed on multiple findings. Per Law 3, every disagreement is enumerated explicitly. No silent averaging.

### Disagreement 1: Provider not enforcing NetworkGate (synthesis ID S-1)

| Slot | Verdict on this finding | Reasoning |
|---|---|---|
| local_a (A-F1) | **block** | Traced the code path: `preferences_panel.py:253-292` (Dry-run) → `staging.stage()` (line 67 declares "no gating") → `provider.generate()` → cloud network call. ABC contract documented but unenforced. |
| local_b | not surfaced | Slot B verified `NetworkGate.guard()` correctness directly at `network.py` and ran `test_privacy.py` which passed. Did not trace the staging → provider.generate() path that bypasses the gate. |

**Accepted verdict:** **block**. Synthesis takes local_a's call.

**Rationale for trusting local_a on this finding:** local_a inspected the actual user-facing call path (Preferences → Dry-run → staging → provider.generate). The privacy lede ("AI off → network silent") is the load-bearing positioning of the entire fork. The ABC documents the gating contract at `provider/base.py:91-95` but the concrete cloud providers don't implement it. Day-8 slip-indicator ("STOP. Do not add a new provider until isolated and fixed") was the early warning that fired silently because `test_privacy.py` doesn't exercise the staging→provider path.

**Pushed-back verdict:** local_b's verbal silence on the provider-gating gap is NOT followed. Slot B's `pass_with_advisories` would have shipped a privacy-contract gap into /qa.

### Disagreement 2: SC-12 token-accuracy bound widening (synthesis ID S-3)

| Slot | Verdict | Reasoning |
|---|---|---|
| local_a (A-F2) | block | Strict reading: SC-12 contract says 20%; test asserts ±50%; waiver path not invoked. |
| local_b (B-F8) | advisory | Day-10 slip-indicator authorizes the waiver path; gap is documentation, not safety. |

**Accepted verdict:** **advisory**. Synthesis takes local_b's call.

**Rationale for trusting local_b on this finding:** The day-10 slip-indicator table in `sprint-contract.md` explicitly authorizes "waive to 'best-effort, documented gap'; do not slip sprint." The waiver path exists; the build invoked the relaxed bound without formally recording the waiver in build-result.md. That's a documentation hygiene issue, not a safety issue. Tightening the bound is also acceptable but not required by the contract's authorized waiver.

**Pushed-back verdict:** local_a's block grade on S-3 is NOT followed. Slot A's strict reading would block a finding the sprint contract already provides an authorized resolution for.

### Disagreement 3: OAuthCreds __repr__ secrets leak (synthesis ID S-2)

| Slot | Verdict | Reasoning |
|---|---|---|
| local_a | not surfaced | Slot A's auth review focused on refresh semantics (60s window, mid-call retry); didn't audit log surface. |
| local_b (B-F1) | block → self-demoted to advisory | Verified the leak by repl execution. No current call site triggers it (`grep` across `novelwriter/ai/` returns zero `f"{auth}"` or `logger.X("...", auth)`). Fix is one line. Self-demoted because no current trigger. |

**Accepted verdict:** **advisory (must-fix-before-/qa)**. Synthesis confirms local_b's self-demotion but tightens the must-fix-by milestone.

**Rationale for trusting local_b on this finding:** local_b's verification by direct repl + call-site grep is correct. The leak is latent — no current code triggers it. Self-demotion from block to advisory is defensible because (a) no exfiltration path exists today, (b) fix is `field(repr=False)` (literally one line per field). However, /qa will exercise exception paths (provider errors, OAuth failures) where a credential object COULD end up in a traceback. So must-fix-before-/qa is the right milestone, not must-fix-before-/ship.

**Pushed-back verdict:** none. local_a missing this finding is excused — different focus area. The slot disagreement is resolved by integrating both perspectives into S-2.

### Disagreement 4: WS-0 branding rename completeness (synthesis ID S-9)

Both slots found this (A-F7, B-F10). Same severity (advisory). No disagreement. Aggregated to S-9 directly.

### Other findings without disagreement

S-4 through S-8, S-10 through S-18: Each was found by only one slot. Each was rated advisory or nit by that slot. No disagreement to resolve.

## Pass 1 conclusion

**Gate verdict: fail.** One block-grade finding (S-1) plus 17 advisories/nits.

Per Law 2, Pass 2 protocol applies. Required path:

1. S-1 (provider NetworkGate enforcement) MUST be addressed in a follow-on `/build` before `/qa` can proceed.
2. S-2 (`__repr__` secret leak) SHOULD be addressed in the same follow-on `/build` because /qa will exercise exception paths that could trigger the leak.
3. S-3 (SC-12 waiver) SHOULD be invoked formally in build-result.md before /qa or /ship; verification-matrix wording for SC-12 should be amended to reflect the waiver.
4. S-4 (revoke wiring), S-5 (sign-in wiring), S-6 (PENDING UX) are honest deferrals from the follow-on /build that also ships WS-4. Record explicitly.
5. S-7 (privacy test scope expansion) is a defense-in-depth hygiene improvement; recommend including in the S-1 fix-build.
6. S-8 through S-18 are advisories/nits eligible for normal address-or-dispute disposition.

**Disposition options per Law 2 Step 5 and the Completion Advisor:**

- (A) `/build --review-advisory-disposition fix_before_qa` — address S-1 (block) + S-2 (must-fix) + S-7 (hygiene); re-enter `/review` Pass 2 to verify; **recommended for the privacy block**.
- (B) `/qa --review-advisory-disposition continue_to_qa` — accept the privacy block and proceed; **NOT recommended for S-1**.
- (C) `/qa --review-advisory-disposition defer_to_follow_on` — fold S-1 into the same follow-on /build that ships WS-4 + remaining S2 scope; **acceptable if WS-4 build is starting next**.

The synthesis recommends (A) for clean Pass 2 verification of the privacy contract; (C) is also acceptable if the follow-on build is imminent and would naturally absorb both fixes.

---

## Pass 2 — 2026-05-17

**Pass round:** 2
**Trigger:** Pass 1 verdict was `fail` (one block-grade S-1). Disposition (A) selected: `/build --review-advisory-disposition fix_before_qa`.

### Verification

Per Iron Law 2: "Pass 2 verifies the specific advisory has been closed AND no regression was introduced. Re-running the same audit set is the minimum; spot-checking the changed area is the recommended."

Spot-check applied to each of S-1, S-2, S-3 plus full test-suite regression run.

### S-1 closure verification (block → closed)

**Fix applied:**
- `provider/base.py:74-101` — added `_enforce_privacy_gate()` helper to the ABC. Reads `self._gate` and `self._feature`; calls `gate.guard(feature)` when both set; raises `ProviderError` if half-configured.
- `provider/anthropic.py:48-72` — added `gate` + `feature` kwargs to `__init__`. `generate():85-90` now calls `self._enforce_privacy_gate()` before any client work.
- `provider/gemini.py:48-73` — same pattern; gate at top of generate.
- `provider/ollama.py:37-55` — same pattern; gate at top of generate (parity: local providers also honor master switch).
- `provider/registry.py:31-141` — every factory and `make_provider` accept and thread `gate` + `feature`.
- `staging.py:58-100` — `stage()` accepts optional `gate` + `feature`; gates at orchestration layer (belt-and-suspenders).
- `preferences_panel.py:253-336` (`_run_dry_run`) — production Dry-run path builds `NetworkGate(self._config)` and threads `(gate, feature)` through both the provider factory AND `staging.stage()`. Catches `PrivacyGatingError` separately from generic provider errors so the UI message is precise.

**Regression test:** `tests/test_ai/test_provider_gating.py` (new, 12 tests):
- `test_anthropic_generate_refuses_when_master_off` — PASS
- `test_gemini_generate_refuses_when_master_off` — PASS
- `test_ollama_generate_refuses_when_master_off` — PASS (verifies local providers gate too)
- `test_anthropic_generate_refuses_when_feature_off` — PASS
- `test_gemini_generate_refuses_when_feature_off` — PASS
- `test_anthropic_misconfigured_gate_without_feature_raises` — PASS (catches half-configuration)
- `test_anthropic_misconfigured_feature_without_gate_raises` — PASS
- `test_anthropic_without_gate_does_not_enforce` — PASS (backward compat for test-only paths)
- `test_staging_stage_refuses_with_master_off` — PASS (belt-and-suspenders fires even for MockProvider)
- `test_staging_stage_misconfigured_gate_or_feature_raises` — PASS
- `test_both_layers_gate_independently` — PASS (provider's own gate fires when stage has no gate)
- `test_make_provider_threads_gate_to_cloud_provider` — PASS (registry routing verified)

Each "refuses" test uses `httpx.MockTransport` with a handler that raises `AssertionError("Provider made a network call ... despite privacy gate being off")` — if the gate ever fails to fire and a provider reaches transport, the test fails with a clear regression message instead of a silent network call.

**S-1 verdict: closed.** The block-grade finding is resolved; the Preferences Dry-run path now enforces the privacy contract at two independent layers (provider + staging) before any client / network work runs.

### S-2 closure verification (advisory must-fix-before-/qa → closed)

**Fix applied:**
- `auth.py:108-118` — `ApiKeyAuth.api_key` annotated `field(repr=False)`.
- `auth.py:131-138` — `RefreshedCreds.access_token` + `refresh_token` annotated `field(repr=False)`.
- `auth.py:155-159` — `OAuthCreds.access_token` + `refresh_token` annotated `field(repr=False)`. (`refresher` was already excluded.)

**Regression test:** `tests/test_ai/test_auth_strategies.py::test_repr_redacts_secrets` — PASS. Verifies that:
- `repr(ApiKeyAuth(api_key="sk-SECRET..."))` does NOT contain the secret string OR the field name `api_key`.
- `repr(OAuthCreds(access_token="SECRET_ACCESS...", refresh_token="SECRET_REFRESH..."))` does NOT contain either secret OR either field name.
- `repr(RefreshedCreds(...))` same redaction.
- Sanity assertions confirm the secrets ARE still present in `headers()` — the test is not accidentally asserting against a constructor that silently dropped the values.

**S-2 verdict: closed.** Future logger/exception paths cannot accidentally serialize bearer tokens or API keys to stderr/disk via the default dataclass `__repr__`.

### S-3 closure verification (advisory must-fix-before-/qa → closed)

**Fix applied:**
- `.planning/current/build/build-result.md` Pass 2 addendum (lines 39+) explicitly invokes the day-10 SC-12 waiver: "Waiver invoked: SC-12 passes at S2-relaxed bound; 20% bound deferred to S6 hardening when Anthropic ships an offline tokenizer and a Gemini-supplied counter lands."
- `.planning/current/plan/verification-matrix.json` SC-12 entry now carries `waiver_invoked: "day-10"` and `waiver_notes` recording the S6 deferral path.

**S-3 verdict: closed.** The verification matrix wording reflects the authorized waiver; the build-result documents the formal invocation. `/qa` and `/ship` can read the waiver from either artifact and treat SC-12 as "pass at S2-relaxed bound, S6 tightens."

### Regression check — full test suite

Command (run in this review turn, fresh process):

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ai/ --tb=short
```

Result: **112 passed in 0.74s** (99 prior + 12 new gating + 1 new repr-redaction). Exit code 0. No regressions in privacy / oauth / contract / network-gating / config / keychain / tokens / transport / construction-offline suites.

### Other advisories (not-block, eligible for normal disposition)

| ID | Status | Note |
|---|---|---|
| S-4 (revoke not wired to sign-out) | open advisory | Defer to follow-on /build that ships WS-4. Recommended fix: in `_GeminiConfigRow._on_signout_clicked`, call `oauth.revoke(creds, config)` before keychain delete. |
| S-5 (OAuth E2E not wired) | open advisory | Defer to follow-on /build. SC-2 cannot fire E2E until client_id loader + sign-in handler land. |
| S-6 (PENDING UX spec gap) | open advisory | Defer to follow-on /build (paired with S-5). |
| S-7 (privacy test scope) | open advisory | Hygiene improvement: add `httpx` to `_FORBIDDEN_SDK_MODULES` + widen AST scan to all `novelwriter/ai/**`. Low-priority. |
| S-8 (docs/ai/security.md missing) | open advisory | Hygiene: write `docs/ai/security.md` before /qa hits OAuth consent verification questions. |
| S-9 (WS-0 branding incomplete) | open advisory | 6+ user-visible "novelWriter" strings remain in `__init__.py`. Recommended for follow-on /build (cheap mechanical change). |
| S-10 (OAuth refresh no lock) | open advisory | PyQt6 main-thread model makes race unlikely in practice. Add `threading.Lock` in S6. |
| S-11 (adapter-output.json provenance kind) | open advisory | Nexus schema improvement; out-of-band of this run. |
| S-12 (Gemini client cache invalidation) | open advisory | Minor perf optimization. |
| S-13 (status-bar pulse swap race) | open advisory | Switch to QSequentialAnimationGroup in cleanup pass. |
| S-14 (mock provider in user dropdown) | open advisory | Add `user_facing_providers()` filter. |
| S-15 (exception logging may indirect-leak) | open advisory | Use `exc_info=False` or sanitize. |
| S-16 (test_transport_isolation hint nit) | open nit | One-line string fix. |
| S-17 (registry ordering nit) | open nit | Optional sorted tuple. |
| S-18 (token corpus headcount nit) | open nit | Add 4-6 more excerpts when SC-12 tightens in S6. |

### Pass 2 verdict

**pass_with_advisories** — `pass_round: 2`.

Block-grade S-1 is closed (test_provider_gating.py: 12/12 PASS). Must-fix S-2 is closed (test_repr_redacts_secrets: PASS). Must-fix S-3 is closed (waiver invoked in build-result.md + verification-matrix.json updated). Full suite passes 112/112. No regressions. The 15 remaining advisories/nits are eligible for normal address-or-dispute disposition through `/qa`.

Recommended next stage: `/qa --review-advisory-disposition continue_to_qa` (the advisor naming for "proceed with advisories noted, none are blocking").
