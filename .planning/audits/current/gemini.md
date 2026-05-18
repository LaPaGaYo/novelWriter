# Local Audit B (gemini slot) — Privacy + Security + Design-contract + Governance

**Run:** `run-2026-05-12T01-45-20-695Z` Sprint 2 foundation phase
**Review attempt:** review-2026-05-17 (Pass 1)
**Slot route:** `claude-local-single_agent-audit-b`
**Focus:** privacy contract, security holes, design-contract compliance, license compatibility, governance provenance

## Result: pass_with_advisories (with one block self-promoted to advisory)

One latent block-grade finding (B-F1, dataclass `__repr__` secret leak) self-promoted to advisory because no current call site triggers it. Slot recommends synthesis treat B-F1 as must-fix-before-/qa to remove the regression risk.

## Scope

This audit covers Sprint 2's privacy contract (SC-6/7/8), Gemini OAuth security (SC-11), license compatibility, design-contract compliance on the 3 newly-specified components (tabs, marginalia, OAuth flow), branding finish-up gap, token-estimate accuracy contract (SC-12), SDK eager-import gate (SC-7/SC-16), and the operator-attested provenance disclosure. Read AI substrate (auth, oauth, network, transport, keychain, preferences_panel, status_bar_ai, 4 providers, registry, tokenizers), every `tests/test_ai/*`, design-contract, sprint-contract, and build provenance (`adapter-output.json`). Re-ran privacy probe in slot process: `import novelwriter.ai` leaves zero forbidden SDKs in `sys.modules`. **99/99 tests pass.**

## Findings

### [B-F1] OAuthCreds and ApiKeyAuth dataclass __repr__ leak secrets to logs

- **Severity: block (self-demoted to advisory due to no current call site)**
- `novelwriter/ai/auth.py:108-115` (ApiKeyAuth), `novelwriter/ai/auth.py:138-159` (OAuthCreds)
- Both classes are `@dataclass` with default `__repr__`. Verified: `repr(OAuthCreds(access_token="SECRET", refresh_token="SECRET", ...))` returns the full tokens. Same for ApiKeyAuth.api_key. `refresher` field is correctly excluded (`field(repr=False)`); actual secrets are not. Any `logger.exception("...", creds)`, `f"failed: {auth}"`, or unhandled exception traceback involving the dataclass writes bearer/refresh token / API key to stderr (and to disk if debug log is on). Contradicts the AI Preferences promise. No current call site triggers it (grep across `novelwriter/ai/` confirms zero `logger.X("...", auth)` or `f"{creds}"`), but the fix is one line and protects against future regressions.
- **Fix:** Add `field(repr=False)` to `access_token`, `refresh_token` on `OAuthCreds` and `api_key` on `ApiKeyAuth`. Optionally define `__repr__` emitting `OAuthCreds(access_token=<redacted sha256:...>, expiry=...)`. Add a unit test `test_auth_repr_does_not_leak_secret`.

### [B-F2] Sign-out path deletes local OAuth blob but does NOT call Google's revoke endpoint

- **Severity: advisory**
- `novelwriter/ai/preferences_panel.py:752-760` (`_GeminiConfigRow._on_signout_clicked`)
- SC-11 demands "revoke-on-disable." Sprint contract: "Revoke: explicit revoke-on-sign-out via Google's `/o/oauth2/revoke` endpoint." `oauth.revoke()` exists and is tested (`test_oauth_flow.py::test_revoke_posts_refresh_token`), but the sign-out button only calls `self._keystore.delete_oauth("gemini")`. Refresh token stays valid on Google's side until rotation.
- **Fix:** In `_on_signout_clicked`, before keychain delete, build `OAuthFlowConfig` (or accept injected) and call `oauth.revoke(creds, config)`. Best-effort fine (revoke returns bool, never raises).

### [B-F3] OAuth client_id has no production wiring path; SC-2 not reachable end-to-end

- **Severity: advisory**
- `novelwriter/ai/preferences_panel.py:738-750` — `_on_signin_clicked` only changes button text; never invokes `oauth.authorize`. `OAuthFlowConfig.client_id` has no source — no env var read, no config file path, no user-facing input field. SC-2 ("Click Sign in with Google, browser opens, user approves") cannot fire. SC-11 ("PKCE handshake + refresh + revoke + CSRF") is claimed green via unit tests against `httpx.MockTransport`, but does not exercise the real end-to-end path. Day-4 slip indicator ("Cut Gemini OAuth from S2") was not declared but in practice the OAuth lane has unit-level evidence only.
- **Fix:** Declare the deferral explicitly in build-result.md ("SC-11 satisfied at unit level; SC-2 deferred to follow-on /build"), OR wire the client_id loader + sign-in button to `oauth.authorize` before /qa.

### [B-F4] Design-contract Component 3 State 2 (PENDING) visual UX not implemented

- **Severity: advisory**
- `novelwriter/ai/preferences_panel.py:738-750` — no progress strip, no Cancel link, no retry inline link.
- Design contract specifies for PENDING: button label "Waiting for browser...", border thickens to Hooker's Green, 1px Hooker's Green progress strip (indeterminate 200-250ms ease-in-out), Cancel text-only tertiary action, "click here to retry" inline link. Current implementation: only `setText("Waiting for browser...")` and `setDisabled(True)`. SC-18 BUILD-compliance gap.
- **Fix:** When OAuth wiring lands (B-F3), construct progress strip (`QProgressBar` indeterminate with 1px Hooker's Green stylesheet) and Cancel link.

### [B-F5] Privacy regression test forbidden list omits httpx

- **Severity: advisory (defense-in-depth)**
- `tests/test_ai/test_privacy.py:39-45` `_FORBIDDEN_SDK_MODULES` includes anthropic, google, google.generativeai, openai, tiktoken — but NOT httpx. AST scan (`test_transport_isolation.py`) only covers `novelwriter/ai/provider/*.py` + `__init__.py`. Future contributor adding `import httpx` to `oauth.py`, `staging.py`, `keychain.py`, `auth.py`, or `tokenizers.py` would pass both checks.
- **Fix:** Add `httpx` to `_FORBIDDEN_SDK_MODULES` AND widen AST scan to include all `.py` under `novelwriter/ai/**`, allowing only `transport.py`.

### [B-F6] docs/ai/security.md is a sprint deliverable but is missing

- **Severity: advisory**
- Sprint contract Documentation section lists `docs/ai/security.md` as new ("secret-handling model, cassette redaction policy, OAuth consent screen verification path"). File doesn't exist. Cassettes directory present but redaction policy undocumented.
- **Fix:** Write `docs/ai/security.md` before /qa hits OAuth consent verification.

### [B-F7] Exception logging in keychain/preferences may indirect-leak secrets

- **Severity: nit**
- `novelwriter/ai/preferences_panel.py:614, 732`, `novelwriter/ai/keychain.py:127` — `logger.warning("...: %s", exc)`. If underlying library exception message echoes the value passed in (rare but possible), API key could land in log.
- **Fix:** `logger.warning("Storing key failed", exc_info=False)` or sanitize: `logger.warning("Keychain write failed for provider=%s (type=%s)", provider_id, type(exc).__name__)`.

### [B-F8] Token-accuracy bound widened from 20% (SC-12) to 50% without recorded waiver

- **Severity: advisory** (parallel to A-F2; local_b grades softer)
- `tests/test_ai/test_tokens_accuracy.py:66-73` asserts `0.5 ≤ avg ≤ 1.5` (±50%) and per-file `0.4 ≤ ratio ≤ 2.5` (-60%/+150%). Docstring acknowledges S6 tightens. Day-10 slip indicator authorizes the waiver but build-result.md doesn't record it.
- **Fix:** Update build-result.md SC-12 entry: "PASS at S2-relaxed bound. 20% bound deferred to S6 per day-10 slip indicator. Waiver invoked."

### [B-F9] OAuth refresh has no concurrency lock (refresh-during-call race)

- **Severity: advisory**
- `novelwriter/ai/auth.py:177-191` `OAuthCreds.refresh_if_needed` mutates fields without a lock. PyQt6 keeps most code on main thread (so unlikely in practice), but design intent ("never mid-call, single refresh") deserves a lock for safety.
- **Fix:** Add `_refresh_lock = threading.Lock()` to `OAuthCreds`; wrap refresh body; re-check `is_expiring_soon()` inside lock.

### [B-F10] Branding finish-up leaves user-visible "novelWriter" strings (parallel to A-F7)

- **Severity: advisory**
- `novelwriter/__init__.py:130,183,224,251,270,276,295`, `novelwriter/error.py:149`, `novelwriter/guimain.py:312-313,345,428,435` — startup banner, version flag, splash, "ready" status, error dialog, macOS CFBundleName, Windows AppUserModelID, more strings. SC-9 technically green (window title + About are correct); spirit of SC-9 ("not novelWriter") not satisfied.
- **Fix:** Replace literal "novelWriter" with `CONFIG.appName` throughout user-visible sites; upstream copyright header strings stay verbatim per GPL-3.

### [B-F11] Governance: adapter-output.json provenance fields are placeholders not real

- **Severity: advisory (transparency, not security)**
- `.planning/current/build/adapter-output.json:22-24, 41-47` — `transport.raw_output.dispatch_command` is `"claude -p --output-format text --dangerously-skip-permissions"` and `actual_route.receipt_path` claims success. `build-result.md:18-29` discloses no real spawn happened. Future audit reading only `adapter-output.json` (without the markdown disclosure) treats this as a normal spawn.
- **Fix:** Add explicit `provenance.kind` field with values `"spawned_provider" | "operator_attested"`, populated honestly. Until Nexus ships that schema, ensure reviewers always read `build-result.md`.

## Coverage check

| SC | Verdict | Evidence |
|---|---|---|
| SC-6 (AI off → network silent) | ✓ at code level (QA-owned for full walkthrough) | `network.py` gate + `test_privacy.py::test_no_network_with_master_off` |
| SC-7 (no SDK in sys.modules) | ✓ | 5 privacy tests + manual verification; caveat B-F5 (httpx not in forbidden list) |
| SC-8 (no httpx outside transport.py) | ✓ at source-scan level | AST scan in `test_transport_isolation.py`; caveat B-F5 (scan scope) |
| SC-9 (window title + About say plotwright) | ✓ (with B-F10 advisory) | `config.py:113-117` + `dialogs/about.py:57`; 6 other strings still say "novelWriter" |
| SC-10 (Migrator Mira 4-tab walkthrough) | ⛔ deferred | Four-tab IA + marginalia rail are follow-on /build per build-result.md |
| SC-11 (PKCE + refresh + revoke + CSRF) | ✓ at unit level | `test_oauth_flow.py` 11 tests. B-F2 (revoke not wired to sign-out), B-F3 (E2E not wired) |
| SC-12 (token accuracy 20% bound) | ⚠ partial | Test passes at ±50%; waiver authorized but not invoked (B-F8) |
| SC-15 (keychain OAuth round-trip) | ✓ | 8 tests; atomic-replace contract enforced |
| SC-18 (design contract honored in build) | ⚠ mixed | Status-bar OK (1Hz vermilion only on working state; Error #7A2222 not vermilion). Preferences panel: ZERO vermilion in any state (verified by grep), but `preferences_panel.py:807` hides whole `_oauth_container` on radio toggle — design rule says "disabled, not hidden, for tab-order stability." PENDING state not implemented per spec (B-F4). Components 1 & 2 deferred. |

## License audit

`pyproject.toml` new deps:
- `httpx>=0.27` (BSD-3) ✓
- `keyring>=24.0` (MIT) ✓ — backends: pywin32 (PSF-2), SecretStorage (BSD-3)
- `anthropic>=0.40` (MIT) ✓ (optional)
- `google-generativeai>=0.8` (Apache-2) ✓ (optional)
- `tiktoken>=0.7` (MIT) ✓ (optional)

All GPL-3 compatible.

## Verdict (slot only)

**pass_with_advisories**

Privacy contract is substantively honored: master switch / per-feature gating in `network.py` correct; lazy-SDK rule honored at call sites that matter; `transport.py` is single httpx owner; keychain stores OAuth as single atomic JSON blob; PKCE uses S256 with cryptographic randomness; loopback listener binds 127.0.0.1 on random free port; `state` validated for CSRF; test suite green; Vermilion rule observed in chrome (grep returns zero non-status-bar vermilion in `preferences_panel.py`).

B-F1 (repr leak) is a latent block: no current call site triggers it, but the fix is 1-line. Recommend synthesis treat as **must-fix-before-/qa**, not block.

B-F2 + B-F3 (revoke + sign-in wiring) are honest deferrals; record explicitly in build-result.

B-F8 (SC-12 waiver) — parallel to local_a's A-F2, but slot B grades softer because day-10 indicator authorizes the path; the gap is documentation, not safety.

Slot recommends synthesis verdict: pass_with_advisories with the must-fix list above. Synthesis may promote B-F1 to block if a callable path triggering leak is found.
