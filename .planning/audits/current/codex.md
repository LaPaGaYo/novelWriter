# Local Audit A (codex slot) — Code + Architecture

**Run:** `run-2026-05-12T01-45-20-695Z` Sprint 2 foundation phase
**Review attempt:** review-2026-05-17 (Pass 1)
**Slot route:** `claude-local-single_agent-audit-a`
**Focus:** code quality, architecture, abstraction correctness, test sufficiency

## Result: fail

Two block-grade findings: provider-gating gap (A-F1) and SC-12 contract-honesty gap (A-F2). All other findings are advisory or nit.

## Scope

Sprint 2 foundation phase delivers the AI substrate finish per `sprint-contract.md`: tight `Auth` ABC (`NoAuth`/`ApiKeyAuth`/`OAuthCreds`) with 60s pre-expiry refresh; three real providers (Ollama/Anthropic/Gemini) constructed lazily without socket activity; single-egress `transport.make_client` chokepoint plus AST-based CI lint test verifying SC-8; full browser-loopback PKCE OAuth with S256, cryptographic state nonce, random-port loopback, refresh, revoke, JSON-blob keychain persistence; `OSKeyChainStore` wrapping `keyring>=24.0` with `FakeKeyStore` fixture; `AIConfig` bumped to `_SCHEMA_VERSION=2` with `provider_configs` dict and v1→v2 forward-compat; per-provider tokenizer adapters with lazy `tiktoken` import; AI Preferences panel un-locked; animated status-bar widget with QPropertyAnimation pulse, four states, keyboard activation; WS-0 branding rename at `config.py:116-117` and About dialog. **99/99 tests pass** (verified by controller in this review turn).

## Findings

### [A-F1] Cloud providers don't invoke NetworkGate.guard() despite ABC contract requiring it

- **Severity: block**
- **Files:** `novelwriter/ai/provider/anthropic.py:85-107`, `novelwriter/ai/provider/gemini.py:88-121`
- `provider/base.py:91-95` declares the contract verbatim: "Cloud providers MUST call `NetworkGate.guard(feature)` before issuing any outbound request." Neither cloud provider accepts or invokes a `NetworkGate`. Preferences "Dry-run" path (`preferences_panel.py:253-292`) → `staging.stage()` (which `staging.py:67` declares "does no gating") → `provider.generate()` → direct network call. The privacy lede ("AI off → network silent") is unenforced for the only S2 user-facing call path. `test_privacy.py` doesn't catch this because it exercises `NetworkGate.guard()` directly, not via staging → provider.generate(). Slip-indicator day-8 ("STOP. Do not add a new provider until isolated and fixed") was the early-warning that fired silently.
- **Fix:** Inject a `(AIConfig, AIFeature)` or `NetworkGate` into cloud provider constructors. Call `gate.guard(feature)` at the top of `generate()` before any `_make_client()`. Add a regression test exercising gate-via-provider with master off.

### [A-F2] SC-12 evidence does not match the stated 20% bound

- **Severity: block**
- **File:** `tests/test_ai/test_tokens_accuracy.py:53-74`
- SC-12 says "20% accuracy bound on the committed corpus." Test asserts per-file `0.4 ≤ ratio ≤ 2.5` (-60%/+150%) and corpus-avg `0.5 ≤ avg ≤ 1.5` (±50%). Docstring acknowledges: "S6 will tighten to 0.8..1.2." That's a known-gap waiver, not a satisfied contract. Corpus has 4 files; contract called for ~10. Day-10 slip indicator authorizes a documented waiver, but the waiver was not formally invoked in build-result.md.
- **Fix:** Tighten the bound to ±20% OR explicitly invoke the documented-waiver lane (update verification-matrix SC-12 wording AND record waiver in build-result.md before /qa).

### [A-F3] Gemini provider drops cached client on every generate() call

- **Severity: advisory**
- `novelwriter/ai/provider/gemini.py:98-102` — `self._client = None` set unconditionally; defeats lazy-cache for `ApiKeyAuth` path.
- **Fix:** `if isinstance(self.auth, OAuthCreds): self._client = None`.

### [A-F4] Status-bar pulse uses Forward + manual swap instead of native ping-pong

- **Severity: advisory**
- `novelwriter/gui/status_bar_ai.py:230-258` — `LoopCount(-1)` + `finished` signal handler `_pulse_swap`. Subtle race with `_stop_pulse`.
- **Fix:** Replace with `QSequentialAnimationGroup` containing two chained `QPropertyAnimation`s.

### [A-F5] Per-feature provider dropdown exposes `mock` to end users

- **Severity: advisory**
- `novelwriter/ai/preferences_panel.py:161`, `registry.py:101-106` — `available_providers()` returns `(mock, ollama, anthropic, gemini)`. Feature dropdown shows all four; config rows filter out mock. Asymmetric leak of test-only id.
- **Fix:** Add `user_facing_providers()` in registry excluding test-only ids.

### [A-F6] Recovery hint in test_transport_isolation.py references nonexistent function

- **Severity: nit**
- `tests/test_ai/test_transport_isolation.py:121` references `build_cloud_client`. Actual factory is `make_client`.

### [A-F7] WS-0 branding rename incomplete — six "novelWriter" strings remain

- **Severity: advisory**
- `novelwriter/__init__.py:130,183,224,251,270,295` and `:63` (`__domain__`). User running `plotwright --version` sees "novelWriter Version". macOS CFBundleName = "novelWriter". Windows AppUserModelID `io.novelwriter`. `__domain__ = "novelwriter.io"`.
- **Fix:** Replace literal "novelWriter" with `CONFIG.appName` in user-visible sites, or carve out which surfaces stay branded for upstream attribution.

### [A-F8] available_providers() ordering is dict-iteration, not contract

- **Severity: nit**
- `registry.py:109-111` — returns `tuple(_FACTORIES.keys())`. CPython preserves insertion order today; future reorder silently changes UI.

### [A-F9] Sign-in click handler doesn't run the actual OAuth flow

- **Severity: advisory**
- `novelwriter/ai/preferences_panel.py:738-750` — `_on_signin_clicked` only changes status label and disables button. Never calls `oauth.authorize()`. SC-2 (end-to-end demo path) cannot fire.
- **Fix:** Record the gap explicitly in build-result.md OR wire `oauth.authorize` before /qa.

### [A-F10] Token corpus is 4 files, contract specified ~10

- **Severity: nit**
- `tests/fixtures/token_corpus/` has austen, dialogue, dickens, nonlatin. Sprint contract: "about 10 public-domain prose excerpts." Couples with A-F2.

## Coverage check

| SC | Verdict | Evidence |
|---|---|---|
| SC-3 (schema 1→2) | ✓ | `config.py:47` `_SCHEMA_VERSION=2`; `test_config_persistence.py:118-121, 152-163` |
| SC-7 (no SDK in sys.modules) | ✓ | `test_privacy.py:129-157` subprocess hermetic check |
| SC-8 (no httpx/requests outside transport.py) | ✓ | `test_transport_isolation.py` AST scan; grep confirms zero hits outside transport.py |
| SC-11 (PKCE + refresh + revoke + CSRF) | ✓ | `test_oauth_flow.py:44-52, 167-172, 183-199, 229-253` |
| SC-12 (token accuracy 20% bound) | ⚠ partial | Test passes at ±50%, not ±20% (A-F2) |
| SC-13 (provider contract over 4 providers) | ✓ | `test_provider_contract.py:88-106, 150-159` |
| SC-14 (auth strategies isolated) | ✓ | `test_auth_strategies.py` 10 tests |
| SC-15 (keychain OAuth round-trip) | ✓ | `test_keychain_oauth.py` 8 tests |
| SC-16 (offline cloud-provider construction) | ✓ | `test_provider_construction_offline.py` 10 tests |

## Verdict (slot only)

**fail** — two block-grade findings (A-F1 privacy contract enforcement gap; A-F2 SC-12 bound undocumented widening).

If A-F1 is resolved (gate calls + regression test) and A-F2 is resolved (tighten or invoke waiver), this becomes pass_with_advisories.
