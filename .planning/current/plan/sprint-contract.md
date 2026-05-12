# Sprint Contract — Sprint 2: Provider Implementations + UI Shell

This contract bounds Sprint 2 of v1. The full v1 plan lives in
`execution-readiness-packet.md`. Canonical framing is `.planning/current/frame/s2-scope.md`.
Nothing outside this contract is in scope for Sprint 2.

## Sprint goal

S2 ships three real providers (Ollama, Anthropic, Gemini) behind a widened `Auth`
strategy abstraction, full Gemini OAuth with "Sign in with Google" UX, the un-locked
AI Preferences panel, the animated status bar, the project shell IA (four tabs +
marginalia rail primitive rendering empty), the token-accuracy benchmark, the real
output staging implementation, and closes the S1 branding gap. No user-facing AI
features ship in Sprint 2. OpenAI is deferred to S6.

## In-scope deliverables

### Fork identity finish (WS-0 carry-forward)

S1 contract committed the rename to "plotwright"; the rename did not ship. S2 absorbs
the cleanup. Asymmetric vs. deferring: `appHandle` flows into the user-data directory
path, so renaming later would require a migration probe.

- Rename `appName` and `appHandle` at `novelwriter/config.py:113-114` from
  `"novelWriter"` / `"novelwriter"` to `"plotwright"` / `"plotwright"`.
- Update "About novelWriter" to "About plotwright" at `novelwriter/dialogs/about.py:49,57`,
  preserving GPL-3 upstream attribution text.
- Update the window title and any remaining UI strings that reference the upstream
  name. Refresh the `novelwriter/__init__.py` module docstring.
- Run `make i18n` and diff the generated `.pot` to confirm string extraction is clean
  (no orphan upstream strings, no stray fork strings missing extraction markers).

### AI substrate finish (WS-1)

Concrete files to create:

- `novelwriter/ai/auth.py` (new) — `Auth` ABC plus `NoAuth`, `ApiKeyAuth(api_key,
  header_name)`, and `OAuthCreds(access_token, refresh_token, expiry, scope, refresher)`
  subclasses. ABC contract: `mode: Literal["none", "api_key", "oauth"]`,
  `headers() -> dict[str, str]`, `refresh_if_needed() -> None`.
- `novelwriter/ai/oauth.py` (new) — Browser-loopback PKCE flow.
  `QDesktopServices.openUrl()` opens the system browser; `http.server` listens on a
  random free localhost port; cryptographic state parameter provides CSRF protection;
  code-to-token exchange returns `OAuthCreds` ready for keychain storage.
  `GEMINI_SCOPE` module constant pins
  `https://www.googleapis.com/auth/generative-language`. Refresh window: 60s before
  expiry, at call-start only, never mid-call. Refresh failure surfaces as a re-auth
  modal with an explicit button (no silent retry).
- `novelwriter/ai/provider/ollama.py` (new) — Local provider. HTTP to `/api/generate`;
  `/api/tags` for `health_check()`; uses `NoAuth`; no SDK dependency.
- `novelwriter/ai/provider/anthropic.py` (new) — Cloud provider. Uses the `anthropic`
  SDK with an injected `httpx.Client` from `transport.py`; `ApiKeyAuth` only.
- `novelwriter/ai/provider/gemini.py` (new) — Cloud provider. Uses
  `google-generativeai` with REST transport (`genai.configure(transport="rest")`);
  supports both `ApiKeyAuth` and `OAuthCreds`.
- `novelwriter/ai/provider/registry.py` (new) — Provider factory. Maps provider name
  strings to factory callables. Consumed by `AIConfig` deserialization.
- `novelwriter/ai/transport.py` (new) — Single `httpx.Client` factory used by every
  cloud provider. SDK imports stay inside their respective provider modules (lazy);
  no `httpx`/`requests` import at `novelwriter/ai/` package import time.
- `novelwriter/ai/tokenizers.py` (new) — Per-provider tokenizer adapters. Uses
  `tiktoken` where applicable, Anthropic's offline tokenizer where available, Gemini
  heuristic where no offline tokenizer is freely available. Falls back to
  `tokens.estimate_tokens` (S1 heuristic).

Widening (no method-signature break):

- `novelwriter/ai/provider/base.py` — add `auth: Auth = NoAuth()` class attribute on
  the `Provider` ABC. `MockProvider` and `OllamaProvider` are trivially compliant via
  default. No method signature changes.
- `novelwriter/ai/keychain.py` — replace `_MissingKeyStore` placeholder with
  `OSKeyChainStore` backed by `keyring>=24.0` (MIT, GPL-3 compatible). `KeyStore`
  Protocol gains `get_oauth(provider_id) -> dict | None` and
  `put_oauth(provider_id, blob)`. Protocol is structural; widening does not break
  S1 call sites. OAuth credentials stored as a single JSON-encoded blob per provider
  (atomic refresh; no partial-write inconsistency).
- `novelwriter/ai/config.py` — add `provider_configs: dict[str, dict]` to `AIConfig`
  for per-provider settings (Ollama base URL, Gemini `auth_mode`, etc.). Bump
  `_SCHEMA_VERSION` from 1 to 2 at `config.py:39`. `from_dict` already ignores unknown
  keys (forward-compat tested in S1 at `test_config_persistence.py:50`).
- `novelwriter/ai/staging.py` — widen `StagedRewrite` with cursor/range fields
  anticipating the S3 review pane. Expose `stage(prompt, provider) -> StagedRewrite`
  orchestration. Stub `staging_consumer.py` (the S3 review-pane interface) so the
  boundary is committed even though S3 fills it. No UI rendering in S2; the dry-run
  button is the S2 surface.
- `novelwriter/ai/tokens.py` — keep S1 heuristic as the fallback path behind
  `Provider.estimate_tokens()`.

### AI Preferences panel (WS-1)

- Un-grey the per-feature toggles that S1 locked.
- Expose provider rows: per-feature dropdown (Ollama / Anthropic / Gemini) with a
  per-provider configuration block rendered below.
- Per-provider auth UX:
  - Ollama: base URL field.
  - Anthropic: masked API key field, keychain-backed.
  - Gemini: radio group "API key" / "Sign in with Google" with the relevant input or
    button rendered below.
- "Dry-run" button per feature: sends a fixed test prompt through the staging
  mechanic, displays the staged result and the token estimate. This is the S2
  smoke-test surface.
- Accessibility: `setBuddy` wiring for label-to-input keyboard activation;
  `accessibleName` set on every `QComboBox` and `QPushButton` per Design's a11y notes.

### Status bar widget upgrade (WS-1)

- `novelwriter/gui/status_bar_ai.py`:
  - 1 Hz vermilion pulse via `QPropertyAnimation` on opacity (0.4 to 1.0, 500ms each
    direction, ease-in-out).
  - Live provider name in status text: `AI: ready (ollama)`, `AI: ready (anthropic)`,
    `AI: ready (gemini)`.
  - "mixed" label when multiple features use different providers.
  - Hover tooltip (Qt-default style, no custom popup); content varies by state.
  - Click wired to `GuiPreferences.openAt("ai")` (S1 emitted the signal but the
    receiver was a no-op).
  - Keyboard reachable: `setFocusPolicy(Qt.FocusPolicy.TabFocus)`, `accessibleName`,
    `keyPressEvent` handles Enter and Space activation per Design's a11y spec.

### Project shell IA (WS-4 start)

- Four-tab top-level IA: **Outline / Manuscript / Notes / AI**. Cmd/Ctrl+1..4
  shortcuts wired.
- Three-column geometry primitive:
  - Project tree (left): 200-240px.
  - Main content column (center): 60ch enforced in the Manuscript view.
  - Marginalia rail (right): 280-320px fixed.
- Cream-paper theme (Cotton `#F4EFE6` / Ink `#1C1B17`) as the default boot. Dark-mode
  toggle exists but defaults to cream per DESIGN.md "Two Locked Risk Decisions" #2.
- AI tab content: empty state with "EDITOR'S NOTES" kind line (Foxing, not vermilion),
  body copy: "No notes yet. When you ask the AI to review a passage, its observations
  land here as marginalia, alongside the manuscript, never on top of it." Caption:
  "Inline rewrite arrives in the next release. Consistency check follows." Layout
  left-aligned per DESIGN.md anti-slop.
- Marginalia rail renders empty in S2 (placeholder rail; content lands S3+).
- Active tab indicator: Hooker's Green 2px underline.

### Tests

- `tests/test_ai/test_oauth_flow.py` (new) — PKCE handshake against a localhost stub;
  refresh-token round-trip; revoke-on-disable; state-parameter CSRF check.
- `tests/test_ai/test_tokens_accuracy.py` (new) — 20% accuracy bound on the committed
  corpus, parametrized per provider.
- `tests/test_ai/test_auth_strategies.py` (new) — `Auth` subclass behavior in
  isolation (`NoAuth`, `ApiKeyAuth`, `OAuthCreds` including refresh path).
- `tests/test_ai/test_keychain_oauth.py` (new) — JSON-blob round-trip through
  `OSKeyChainStore` using `FakeKeyStore`.
- `tests/test_ai/test_provider_construction_offline.py` (new) — every cloud provider
  can be constructed inside `network_sentinel()` without socket activity.
- `tests/test_ai/test_privacy.py` (extended) — import `novelwriter.ai`; assert no
  provider SDK module appears in `sys.modules`. Guards against eager SDK network
  discovery on import.
- `tests/test_ai/test_provider_contract.py` (extended) — parametrized over
  `MockProvider`, `OllamaProvider`, `AnthropicProvider`, `GeminiProvider` using
  `httpx.MockTransport` for the cloud providers.
- `tests/fixtures/cassettes/` (new) — VCR cassettes for Anthropic and Gemini.
  Authorization and `x-api-key` headers redacted at record time; cassettes committed.
- `tests/fixtures/token_corpus/` (new) — about 10 public-domain prose excerpts plus
  synthetic edge cases (heavy dialogue, em-dashes, non-Latin text). Under 500KB total.
- `tests/fixtures/FakeKeyStore` (new) — in-memory dict implementation of the
  `KeyStore` Protocol so CI never touches the real OS keychain.

CI lint rule lands with this sprint: no `import httpx` or `import requests` in any
file under `novelwriter/ai/provider/`; clients must come from `transport.py`.

### Documentation

- `docs/ai/security.md` (new) — secret-handling model; how contributors obtain keys
  for local smoke tests; cassette redaction policy.
- Update `docs/ai/architecture.md` — Auth strategy abstraction, transport factory,
  OAuth lifecycle diagram.
- Update `docs/ai/privacy.md` — OAuth refresh-token storage, revoke-on-disable
  behavior, the lazy-SDK-import rule, the extended `test_privacy.py` assertion.
- Update `README.md` at the end of S2 — "easiest privacy-respecting setup in the
  category" positioning per the decision-brief lede.

### Design contract (parallel to WS-1)

- `/design-consultation` is the contract path (decided; not `/plan-design-review`).
- Output: `.planning/current/plan/design-contract.md`.
- New DESIGN.md component specs to land via design-consultation:
  - Four-tab top-level IA component.
  - Marginalia-rail empty-state component.
  - Auth-flow state machine component (idle / pending / error / signed-in).
- Hard deadline: **day 7**. Must run in parallel with WS-1 finish, not sequentially.
  Designer turnaround is a slip risk and `/handoff` must not gate on a design
  contract started on day 7.

## Out of scope (Sprint 2)

Things that might look like they belong but do not:

- Inline rewrite feature itself. S3.
- Consistency check feature. S4.
- Rewrite review pane UI. S3.
- OpenAI provider. S6 (decided cut).
- Character panel restructure. S4/S5.
- Outline tree restructure. S4/S5.
- Scene-card / corkboard view. S5.
- Marginalia rail content (real editor's notes). S3+.
- Streaming / async response handling. Not in v1 per `prd.md:52`.
- Background consistency scanning, auto-fix, whole-document rewrite. Out of v1
  per `prd.md:178-188`.
- Telemetry / usage analytics. Privacy positioning forbids.
- GitHub Actions CI secrets for cloud-API smoke tests. S6.
- `brand-spec.md` / logos / icon set. Deferred per DESIGN.md.
- i18n for new S2 strings. English-only in S2; translation pipeline owned by S6.
- Google's branded "Sign in with Google" button artwork. Plain-text secondary button
  per Design's spec; DESIGN.md anti-slop rules out branded icon circles.

## Verification

This sprint is "done" when each of the 18 items below is green. Items mirror the
success criteria in `.planning/current/frame/s2-scope.md`.

### Functional gate

1. Plotter Pat opens Preferences then AI; sees the master toggle off and sees Ollama
   / Anthropic / Gemini provider options.
2. Click "Sign in with Google" in `Preferences → AI → Gemini`. Browser opens, user
   approves, control returns to plotwright. Status bar shows `AI: ready (gemini)`.
3. Toggle AI on for "rewrite" (feature will not fire until S3; this only enables the
   flag).
4. Click "dry-run". A staged result returns from Gemini through the staging
   interface. Token estimate is displayed before the call; the 20% accuracy bound
   holds.
5. Open the AI tab. The "EDITOR'S NOTES" empty state renders with Design-specified
   copy and left-aligned layout.
6. Toggle AI off. Status bar returns to `AI: off`. Network goes silent.

### Trust gate

7. `tests/test_ai/test_privacy.py` passes with three providers registered and AI
   off; no SDK modules appear in `sys.modules` after `import novelwriter.ai`.
8. CI privacy assertion: no `import httpx` or `import requests` outside
   `novelwriter/ai/transport.py`.

### Narrative gate

9. Window title says **plotwright**, not novelWriter. About dialog says "About
   plotwright" with upstream attribution preserved.
10. Migrator Mira opens her existing project. Four tabs visible. AI off by default.
    `appHandle` already renamed so no migration burden.

### Verification and sign-off

11. `tests/test_ai/test_oauth_flow.py` passes (PKCE + refresh + revoke).
12. `tests/test_ai/test_tokens_accuracy.py` passes (20% bound on committed corpus).
13. `tests/test_ai/test_provider_contract.py` passes for all four providers
    (Mock + Ollama + Anthropic + Gemini).
14. `tests/test_ai/test_auth_strategies.py` passes.
15. `tests/test_ai/test_keychain_oauth.py` passes.
16. `tests/test_ai/test_provider_construction_offline.py` passes.
17. Smoke test (manual gate): real Anthropic and Gemini calls work end-to-end with
    real keys. Output staging produces a usable `StagedRewrite`.
18. Real `design-contract.md` exists for WS-4 surfaces. DESIGN.md extended with the
    three new component specs.

## Definition of "ready for /handoff"

All 18 verification items above pass **and** a real `design-contract.md` exists for
WS-4 surfaces, where "real" means the file's line count is greater than 200 or the
file contains a `## DESIGN.md Component Amendments` header. Placeholder contracts
do not satisfy the gate (per the v1 packet transition rule).

## Estimated size

22-27 engineering days for one developer.

## Sprint 2 slip indicators (day-by-day)

| Day | Indicator | Action if triggered |
|-----|-----------|---------------------|
| Day 2 | `auth_mode` field not on Provider ABC; `test_provider_contract.py` not green against widened MockProvider | Pause and audit abstraction; do not start cloud providers |
| Day 4 | `test_oauth_flow.py` not green against localhost stub | **Cut Gemini OAuth from S2, defer to S6**; ship Gemini API-key only |
| Day 6 | AnthropicProvider not passing contract suite against VCR cassettes | Investigate; verify cassette redaction; if still red day 7, escalate |
| Day 7 | `design-contract.md` still placeholder (line count <200) | Run `/design-consultation` THIS DAY (it should have been started day 1) |
| Day 8 | `test_privacy.py` failed even once | **STOP. Do not add a new provider until isolated and fixed.** |
| Day 10 | Token-accuracy benchmark cannot hit 20% bound on Gemini | Waive to "best-effort, documented gap"; do not slip sprint |
| Day 12 | WS-4 touched >6 files outside `novelwriter/gui/` | Revert WS-4 commits; ship just AI substrate; defer IA to mini-sprint |
| Day 14 | Smoke test (real keys) not demonstrated manually | Declare "manual-gate-only, no CI"; ship without automated smoke |
| Day 16 | Anything still red | Ship what's green; carry forward to S6 |

## Sprint 2 risks

| Risk | Mitigation |
|------|------------|
| OAuth implementation slips past the day-4 cut-line | Hard day-4 gate on `test_oauth_flow.py`. If red, cut OAuth to S6 and ship Gemini API-key only. The contract permits this without a re-plan. |
| Privacy regression (SDK eager-imports network, or `httpx` leaks into a provider) | Extended `test_privacy.py` asserts no SDK in `sys.modules`; CI lint rule blocks `import httpx`/`import requests` outside `transport.py`; day-8 indicator stops new providers if `test_privacy.py` fails. |
| Token-accuracy benchmark cannot hit 20% bound, especially on Gemini (no freely available offline tokenizer) | Per-provider tokenizer adapters with documented fallback to heuristic; day-10 waiver path documents the gap rather than slipping the sprint. |
| WS-4 sprawls beyond the "tabs + empty rail" scope ceiling | Day-12 indicator: revert WS-4 commits if footprint exceeds 6 files outside `novelwriter/gui/`. Marginalia rail content explicitly out of scope. |
| Keychain library breaks on one of macOS / Linux / Windows | `keyring>=24.0` MIT, GPL-3 compatible; `FakeKeyStore` covers CI; manual smoke on all three platforms before day 14; OAuth blob is a single JSON entry per provider (atomic refresh, no partial-write inconsistency). |
| OAuth refresh-token rotation fails silently (token revoked, expired, or rotated by provider) | Refresh checked 60s before expiry at call-start only, never mid-call. Refresh failure surfaces as a re-auth modal with an explicit button; no silent retry. `test_oauth_flow.py` includes a refresh round-trip case. |
| Loopback listener conflicts with host firewall or another process on the chosen port | Random free port via `socket.socket.bind(("", 0))`; bind to `127.0.0.1` only (not `0.0.0.0`); cryptographic state parameter prevents cross-origin replay; documented manual fallback in `docs/ai/security.md`. |
| Google OAuth consent screen verification status (unverified app warning, scope review) | Use the broad `https://www.googleapis.com/auth/generative-language` scope pinned as `GEMINI_SCOPE` module constant; document the consent-screen path in `docs/ai/security.md`; surface unverified-app warning to the user rather than hiding it. |
| VCR cassettes go stale as providers ship breaking API changes | Cassettes record full request/response with redacted auth headers; manual re-record path documented in `docs/ai/security.md`; cassette mismatch fails the contract suite loudly rather than silently passing. |
| Provider SDK version pins conflict (e.g., `anthropic` and `google-generativeai` both pinning `httpx` ranges) | Lazy SDK import inside each provider module; single `httpx.Client` factory in `transport.py` is the only allowed client; pin `httpx` ourselves in `pyproject.toml` and let SDK ranges flex around it. |

## Transition Rule

Advance to `/handoff` only after every verification item above is green AND a real
`design-contract.md` exists for WS-4 surfaces (per the v1 packet transition rule).

---

**Next step:** kick off `/design-consultation` in parallel with the WS-1 finish work
on day 1 so the design contract is mature before the day-7 hard deadline. The build
agent should treat the slip-indicator table as a live checklist, not a retrospective
artifact.
