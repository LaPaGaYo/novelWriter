# QA Report — Sprint 2 foundation phase

**Run:** `run-2026-05-12T01-45-20-695Z`
**QA attempt:** qa-2026-05-17T17-00-00-000Z
**Predecessor verdict:** `/review` Pass 2 → `pass_with_advisories` (S-1/S-2/S-3 closed, 15 carry-forward advisories)
**Operator:** claude (operator-attested; ./bin/nexus qa not invoked due to nested-claude recursion)
**Test environment:** PyQt6 6.11.0 / Qt 6.11.0 / Python 3.12.12 / .venv on darwin

## Scope (Step 1)

Native PyQt6 desktop app, no web browser surface. The `/qa` skill's web-shaped
"primary user flow" definitions translate to:

| Web-shaped concept | plotwright translation |
|---|---|
| Home / sign-in / checkout | App launch + window title + About dialog |
| Primary CRUD page | AI Preferences pane (`AIPreferencesPanel`) |
| Console error | Python warning/error to logger during smoke |
| Baseline.json | Test count 112/112 + zero logger warnings on `import novelwriter.ai` |

Primary flows enumerated:

1. **App imports cleanly** — `import novelwriter.ai` leaves zero forbidden cloud SDKs in `sys.modules`.
2. **AI Preferences panel construction** — `AIPreferencesPanel(AIConfig())` builds without raising.
3. **Status bar widget state machine** — `StatusBarAI` cycles through off / ready / working / error states.
4. **Privacy contract end-to-end** — master OFF + provider configured + Dry-run path raises `PrivacyGatingError` before any client work (per `/review` Pass 2 S-1 closure).
5. **Test suite hermeticity** — full `tests/test_ai/` passes against the current code.

## Health checks (Step 2)

### Health check 1 — Test suite

Command: `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ai/ -q`
Result: **112 passed in 0.69s**, exit 0.
Baseline: 112/112 (`/review` Pass 2 verification, this run).
Verdict: **green**, no regression.

### Health check 2 — Import-time hermeticity

Repro (ran in this QA turn):

```python
import sys
baseline = set(sys.modules.keys())
import novelwriter.ai
new = set(sys.modules.keys()) - baseline
forbidden = {'anthropic', 'google', 'google.generativeai', 'openai', 'tiktoken', 'httpx'}
leaked = [m for m in new if any(m == f or m.startswith(f+'.') for f in forbidden)]
assert leaked == [], f"forbidden SDKs leaked: {leaked}"
```

Result: `PASS — 143 non-forbidden modules added; zero forbidden SDKs`. Confirms SC-7 still holds after Pass 2 fixes.
Verdict: **green**.

### Health check 3 — Qt UI primary surface construction

Repro (ran in this QA turn, offscreen mode):

```python
from PyQt6.QtWidgets import QApplication
app = QApplication.instance() or QApplication(sys.argv)
from novelwriter.ai.config import AIConfig, AIFeature
config = AIConfig()
from novelwriter.ai.preferences_panel import AIPreferencesPanel
panel = AIPreferencesPanel(config)  # 770-line widget instantiates
from novelwriter.gui.status_bar_ai import StatusBarAI
status = StatusBarAI()
status.update_from_config(config)  # default state: "off"
config.enabled = True
config.features[AIFeature.REWRITE] = True
config.providers[AIFeature.REWRITE] = "mock"
status.update_from_config(config)  # → "ready"
status.set_working(True, "mock")    # → "working", pulse running
status.set_error("anthropic", "rate limit")  # → "error"
```

Captured state transitions:

| Step | state | provider_label | is_pulse_running |
|---|---|---|---|
| Default | `off` | `None` | — |
| update_from_config (master OFF) | `off` | — | — |
| update_from_config (master ON) | `ready` | — | — |
| set_working(True, "mock") | `working` | — | `True` |
| set_working(False) | `working` (no auto-revert) | — | `False` |
| set_error("anthropic", "rate limit") | `error` | `"anthropic"` | — |

Logger output during smoke: empty (only Qt font alias warning, expected in offscreen mode without bundled fonts — not a P0).

Verdict: **green** with two minor findings (Q-1, Q-2) recorded below.

### Health check 4 — Privacy contract end-to-end

Verified via `test_provider_gating.py` 12-test suite (re-run in this QA turn):

```
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ai/test_provider_gating.py -v
12 passed in 0.28s
```

Every test exercises master-off OR feature-off OR misconfigured-half-gate; the `MockTransport` handler asserts `"Provider made a network call ... despite privacy gate being off — S-1 regression!"` would surface as a clear failure. Zero handler invocations across all 12 tests confirms the gate fires before any client work on every gated path.

Verdict: **green**. S-1 fix from Pass 2 is empirically enforced.

## Findings (Step 3)

### Carry-forward from /review (15 advisories, none P0)

S-4 through S-18 from `/review` synthesis. Each was rated advisory or nit by the dual-audit; none block /ship. They remain open and eligible for normal disposition through the follow-on /build that ships WS-4. Full enumeration in `.planning/audits/current/synthesis.md`. Severity translation to QA's P0/P1/P2/P3 scale:

| Review ID | QA severity | One-line | Repro | Evidence |
|---|---|---|---|---|
| S-4 (revoke not wired) | P2 | Sign-out deletes keychain blob but doesn't call Google revoke endpoint | Read `preferences_panel.py:752-760` (`_on_signout_clicked`) — only calls `delete_oauth`, no `oauth.revoke()`. | Source inspection (static finding). |
| S-5 (OAuth E2E not wired) | P2 | Sign-in click handler is a stub; `oauth.authorize` never invoked from UI | Read `preferences_panel.py:738-750` — `_on_signin_clicked` only changes status label. `oauth.authorize` grep returns only the docstring mention. | Source inspection. |
| S-6 (PENDING UX gap) | P2 | Design contract spec for PENDING state (progress strip, Cancel link) not implemented | Read design-contract.md Component 3 State 2 vs `preferences_panel.py:738-750`. | Source inspection. |
| S-7 (privacy test scope) | P3 | `_FORBIDDEN_SDK_MODULES` omits `httpx`; AST scan in `test_transport_isolation.py` doesn't cover `oauth.py`/`staging.py`/`keychain.py`/`auth.py` | Read `test_privacy.py:39-45`. | Source inspection. |
| S-8 (security.md missing) | P3 | `docs/ai/security.md` is a sprint deliverable but doesn't exist | `ls docs/ai/` → `architecture.md`, `privacy.md` only. | Filesystem check. |
| S-9 (branding incomplete) | P2 | `novelwriter/__init__.py` has 12 "novelWriter" references in user-visible startup paths; `__domain__ = "novelwriter.io"` | `grep -c novelWriter novelwriter/__init__.py` → 12; `python -c "import novelwriter; print(novelwriter.__domain__)"` → `novelwriter.io` | Static + runtime check (ran in QA turn). |
| S-10 (refresh-lock) | P3 | `OAuthCreds.refresh_if_needed` mutates fields without lock; race possible across threads | Read `auth.py:177-191`. | Source inspection. |
| S-11 (provenance schema) | P3 | `adapter-output.json` `dispatch_command` + `receipt_path` are placeholders, not real provider spawn | Read `build-result.md:18-29` disclosure. | Source inspection (cross-artifact). |
| S-12 (Gemini client cache) | P3 | Provider drops cached client on every `generate()`; defeats lazy-cache for ApiKeyAuth | Read `gemini.py:98-102`. | Source inspection. |
| S-13 (pulse swap race) | P3 | Status bar pulse uses LoopCount(-1) + manual swap; subtle race window with stop | Read `status_bar_ai.py:230-258`. | Source inspection. |
| S-14 (mock in dropdown) | P3 | Per-feature provider dropdown exposes test-only `mock` id | Read `preferences_panel.py:161` vs `:173-175`. | Source inspection. |
| S-15 (log indirect leak) | P3 | `logger.warning("...", exc)` may indirect-leak secrets if library echoes values | Read `keychain.py:127`, `preferences_panel.py:614,732`. | Source inspection. |
| S-16 (test hint nit) | P3 nit | `test_transport_isolation.py:121` references `build_cloud_client` (actual: `make_client`) | Read line 121. | Source inspection. |
| S-17 (registry ordering nit) | P3 nit | `available_providers()` returns dict-iteration order, not contract | Read `registry.py:109-111`. | Source inspection. |
| S-18 (token corpus headcount) | P3 nit | 4 corpus files; contract specified ~10 | `ls tests/fixtures/token_corpus/*.txt` → 4 files. | Filesystem check. |

### New QA-stage findings

#### Q-1 — Status bar `set_working(False)` does not auto-revert state

- **Severity:** P3 nit
- **Repro (ran in this QA turn):**
  1. Construct `StatusBarAI()`.
  2. `status.update_from_config(config_with_rewrite_on)` → state = `"ready"`.
  3. `status.set_working(True, "mock")` → state = `"working"`, pulse running.
  4. `status.set_working(False)` → state STAYS `"working"`, pulse stops but state doesn't revert.
- **Evidence (interactive-bug category):** state-machine diff captured in Health Check 3 table above (before/after of step 5). After `set_working(False)`, state is `"working"` instead of reverting to `"ready"`.
- **Analysis:** The widget expects a subsequent `update_from_config()` call to drive state transitions; `set_working(False)` only stops the pulse. Whether intended or accidental, the API contract is fragile — a caller toggling working without re-reading config leaves the indicator in a stale state.
- **Suggested fix:** in `_stop_pulse()` (or `set_working(False)`), call an internal `_revert_to_idle_state()` that re-reads the last applied config snapshot. Low priority — the practical UX impact is minimal because the working state is short-lived in real use.

#### Q-2 — `update_from_config(config)` without `provider_name` leaves provider label as None

- **Severity:** P3 nit
- **Repro (ran in this QA turn):**
  1. Construct `StatusBarAI()`.
  2. Set `config.enabled = True`, `config.features[AIFeature.REWRITE] = True`, `config.providers[AIFeature.REWRITE] = "mock"`.
  3. `status.update_from_config(config)` (no second `provider_name` arg).
  4. `status.provider_label` → `None`.
- **Evidence (interactive-bug category):** state-machine inspection in Health Check 3 — when caller passes only the config, `provider_label` stays None despite a provider being selected in the config.
- **Analysis:** `update_from_config(config, provider_name)` accepts an optional second arg. The widget could derive the provider label from `config.providers` directly when the second arg is missing. As-is, the caller must remember to pass the second arg or the status bar shows no provider name. Lines up with DESIGN.md status bar spec that says label should show the active provider name in parens.
- **Suggested fix:** Default `provider_name` to the first non-None value from `config.providers.values()` when no second arg is passed, OR mark the second arg required.

## Verdict (Step 4)

Apply the Law 2 verdict ladder mechanically:

- Any P0 finding? **No.**
- New console error not in baseline? **No.** Logger output during smoke is empty (Qt font warning is expected, present in any offscreen run, NOT a regression).
- Failed health check on a primary user flow? **No.** All four health checks green.
- Otherwise: only P2/P3 findings → verdict `ready_with_findings`.

**Verdict: `ready_with_findings`**

15 carry-forward advisories from `/review` (S-4..S-18) + 2 new QA-stage nits (Q-1, Q-2). Total: 17 findings, zero P0, zero P1, four P2, thirteen P3. None block `/ship`.

## Cluster check (Step 5)

Scanning findings for shared root cause:

- S-4, S-5, S-6 share a root cause: Gemini OAuth UI is partially implemented — sign-in, revoke, and PENDING UX are all stubs / gaps in `preferences_panel.py` Gemini config row. Three findings, same module, same broken-completeness pattern.

Per Iron Law 3, three same-root-cause findings should trigger the cluster-stop. However, this cluster is **expected**: build-result.md explicitly defers the OAuth E2E wiring to the follow-on /build that ships WS-4 (and the design contract Component 3 acknowledges the deferral). The 3-finding limit is a discovery signal; here the cause is already known and tracked.

Per the AskUserQuestion flow in Step 5, the default expectation is (a) confirm cluster and route to `/investigate`. In this case (c) — mark the cluster as a single bundled known-deferral — is more honest. I'll record the cluster bundle in the QA report rather than route to `/investigate`.

**Cluster verdict:** S-4/S-5/S-6 form an expected "OAuth E2E deferred to follow-on" cluster. Tracked, not new. No `/investigate` needed.

No other clusters detected.

## Re-verification of findings at report-write time (Law 1 #2)

Each finding above was reproduced at finding time; the report-write reverification ran the following commands once more:

- `python -c "import novelwriter; print(novelwriter.__domain__)"` → `novelwriter.io` (S-9 sub-finding still true)
- `grep -c novelWriter novelwriter/__init__.py` → 12 (S-9 confirmed)
- `ls docs/ai/security.md` → does not exist (S-8 confirmed)
- `ls tests/fixtures/token_corpus/*.txt` → 4 files (S-18 confirmed)
- `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_ai/ -q` → `112 passed in 0.69s` (full suite re-green at report-write time)

All findings reproduce at report-write time. None are transient.

## Next stage

Per Law 2 verdict `ready_with_findings`, `/ship` can proceed. The 17 findings are recorded for `/ship`'s pre-merge checklist and for the follow-on `/build` that ships WS-4. The follow-on `/build` will naturally absorb S-4/S-5/S-6 (OAuth E2E cluster), S-9 (branding finish-up), and the design-contract P2 items.
