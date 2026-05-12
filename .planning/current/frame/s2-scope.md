# Sprint 2 Scope — Frame Artifact

Canonical S2 scope, non-goals, and success criteria. This is the framing output of
`run-2026-05-12T01-45-20-695Z`. `/plan` reads this and writes
`.planning/current/plan/sprint-contract.md`.

## Sprint 2 boundary in one sentence

S2 ships three real providers behind a widened Auth-strategy ABC, full Gemini OAuth
with "Sign in with Google" UX, the un-locked AI Preferences panel + animated status
bar, the project shell IA (four tabs + marginalia rail primitive), the token-accuracy
benchmark, the real output staging implementation, and closes the S1 branding gap. No
features ship.

## In-scope deliverables

### WS-0 carry-forward (S1 branding gap)

- Rename `appName` and `appHandle` at `novelwriter/config.py:113-114` from `"novelWriter"`
  / `"novelwriter"` to `"plotwright"` / `"plotwright"`.
- Update "About novelWriter" → "About plotwright" in `novelwriter/dialogs/about.py:49,57`,
  preserving GPL-3 upstream attribution.
- Update window title and any remaining UI strings.
- Run `make i18n` and diff the `.pot` to confirm string extraction is clean.
- Rationale: `appHandle` flows into user-data directory path; deferring the rename
  means writing a migration probe in S6. Cost asymmetry too large.

### WS-1 finish — real providers + OAuth substrate

**Auth strategy abstraction (decided):**

- New file `novelwriter/ai/auth.py`:
  - `Auth` ABC with `mode: Literal["none", "api_key", "oauth"]`, `headers() -> dict[str, str]`,
    `refresh_if_needed() -> None`
  - `NoAuth`, `ApiKeyAuth(api_key, header_name)`, `OAuthCreds(access_token, refresh_token,
    expiry, scope, refresher)`
- Widen `Provider` ABC at `novelwriter/ai/provider/base.py`: add `auth: Auth = NoAuth()`
  class attribute. **No method signature changes.** Mock + Ollama trivially compliant via
  default.

**OAuth flow (decided to keep in S2):**

- New file `novelwriter/ai/oauth.py`:
  - Browser-loopback PKCE flow
  - `QDesktopServices.openUrl()` to open system browser
  - `http.server`-based localhost listener on random free port
  - Cryptographic state parameter (CSRF protection)
  - Code → token exchange
  - Returns `OAuthCreds` ready for keychain storage
- Refresh-token lifecycle: refresh when access token is within 60s of expiry, at
  call-start (never mid-call). Refresh failure surfaces as re-auth modal with explicit
  button.
- **Time-box waiver:** if `test_oauth_flow.py` is not green by **end of dev-day 4**, cut
  OAuth from S2 to S6 and ship Gemini API-key only.

**Keychain widening:**

- Replace `_MissingKeyStore` placeholder in `novelwriter/ai/keychain.py` with
  `OSKeyChainStore` backed by `keyring>=24.0` (MIT, GPL-3 compatible).
- `KeyStore` Protocol gains `get_oauth(provider_id) -> dict | None` and
  `put_oauth(provider_id, blob)` methods. Protocol is structural; widening doesn't
  break existing call sites.
- OAuth credentials stored as JSON-encoded blob in a single keychain entry per
  provider (atomic refresh; no partial-write inconsistency).
- `FakeKeyStore` in `tests/fixtures/` (in-memory dict) so CI never touches real
  keychain.

**Three real provider implementations:**

- `novelwriter/ai/provider/ollama.py` — local; HTTP to `/api/generate`, `/api/tags` for
  health; no auth.
- `novelwriter/ai/provider/anthropic.py` — cloud; `anthropic` SDK with injected
  `httpx.Client`; `ApiKeyAuth` only.
- `novelwriter/ai/provider/gemini.py` — cloud; `google-generativeai` REST transport
  (`genai.configure(transport="rest")`); supports both `ApiKeyAuth` and `OAuthCreds`.

**Per-provider tokenizer adapters:**

- New file `novelwriter/ai/tokenizers.py`. Adapters using `tiktoken` (OpenAI patterns
  applicable to other models as approximation), Anthropic's offline tokenizer where
  available, Gemini's heuristic where the offline tokenizer is not freely available.
  Fallback to `tokens.estimate_tokens` (S1 heuristic).
- `Provider.estimate_tokens()` per-provider plugs into the adapter; module-level
  function stays as the fallback path.

**Transport factory:**

- New file `novelwriter/ai/transport.py`. Single `httpx.Client` factory used by every
  cloud provider. Lazy import of provider SDKs only inside their respective modules
  (never at `novelwriter/ai/` package import time — guards the privacy regression test).
- CI lint rule: no `import httpx` / `import requests` in `provider/` modules; clients
  must come from `transport.py`.

**Network gate wiring:**

- Gating remains feature-level. Features call `NetworkGate.guard(feature)` before
  invoking `provider.generate(...)`. Providers stay dumb.
- `test_privacy.py` (S1) extends: import `novelwriter.ai` and assert no SDK module is
  in `sys.modules` afterward. Catches eager SDK network discovery on import.

**AIConfig schema bump:**

- Add `provider_configs: dict[str, dict]` to `AIConfig` for per-provider settings
  (Ollama base URL, Gemini auth_mode, etc.).
- Bump `_SCHEMA_VERSION` from 1 to 2 in `config.py:39`. `from_dict` path already ignores
  unknown keys (forward-compat tested in S1 at `test_config_persistence.py:50`), so the
  bump is safe before user files exist on disk.

**Provider registry:**

- New file `novelwriter/ai/provider/registry.py`. Maps provider name strings to factory
  callables. Used by AIConfig deserialization.

### WS-1 finish — AI Preferences panel

- Un-grey the per-feature toggles (locked in S1).
- Expose provider rows: per-feature dropdown (Ollama / Anthropic / Gemini), per-provider
  config below.
- Per-provider auth UX:
  - Ollama: base URL field
  - Anthropic: masked API key field (keychain-backed)
  - Gemini: radio group "API key" / "Sign in with Google" → respective input below
- "Dry-run" button per feature: send a fixed test prompt through the staging
  mechanic; show staged result + token estimate. This is the smoke test surface.
- Add `setBuddy` wiring for label-to-input keyboard activation; set `accessibleName`
  per `QComboBox` and `QPushButton` per Design's a11y notes.

### WS-1 finish — Status bar widget upgrade

- `novelwriter/gui/status_bar_ai.py`:
  - 1 Hz vermilion pulse via `QPropertyAnimation` on opacity (0.4 ↔ 1.0, 500ms each
    direction, ease-in-out)
  - Live provider name in status: `AI: ready (ollama)`, `AI: ready (anthropic)`,
    `AI: ready (gemini)`
  - "mixed" label when multiple features use different providers
  - Hover tooltip (Qt-default style, NO custom popup) — content varies by state
  - Click wired to `GuiPreferences.openAt("ai")` (S1 emitted but receiver was no-op)
  - `setFocusPolicy(Qt.FocusPolicy.TabFocus)`, `accessibleName`, `keyPressEvent`
    Enter/Space activation per Design's a11y spec

### WS-1 finish — Output staging real implementation

- `novelwriter/ai/staging.py`:
  - Widen `StagedRewrite` with cursor/range fields anticipating S3 review pane
  - Expose `stage(prompt, provider) -> StagedRewrite` orchestration function
  - Stub `staging_consumer.py` (S3 review pane interface) so the boundary is committed
    even though S3 fills it
- No UI rendering in S2 (S3 owns the review pane). The dry-run button output is the
  S2 surface.

### WS-4 start — Project shell IA + marginalia rail primitive (decided)

- Four-tab top-level IA: **Outline / Manuscript / Notes / AI**. Cmd/Ctrl+1..4
  shortcuts wired.
- Three-column geometry primitive:
  - Project tree (left): 200-240px
  - Main content column (center): 60ch enforced in Manuscript view
  - Marginalia rail (right): 280-320px fixed
- Cream-paper theme (Cotton `#F4EFE6` / Ink `#1C1B17`) as default boot. Dark mode
  toggle exists but defaults to cream per DESIGN.md "Two Locked Risk Decisions" #2.
- AI tab content: empty state with "EDITOR'S NOTES" kind line (Foxing, NOT vermilion),
  body copy: "No notes yet. When you ask the AI to review a passage, its observations
  land here as marginalia — alongside the manuscript, never on top of it." Caption:
  "Inline rewrite arrives in the next release. Consistency check follows." Layout
  left-aligned per DESIGN.md anti-slop.
- Marginalia rail renders empty in S2 (placeholder rail; populated in S3+).
- Active tab indicator: Hooker's Green 2px underline.

### Tests

- `tests/test_ai/test_oauth_flow.py` — PKCE handshake against localhost stub;
  refresh-token round-trip; revoke-on-disable; state-parameter CSRF check.
- `tests/test_ai/test_tokens_accuracy.py` — 20% accuracy bound on corpus.
- `tests/test_ai/test_auth_strategies.py` — `Auth` subclass behavior in isolation.
- `tests/test_ai/test_keychain_oauth.py` — JSON-blob round-trip through `OSKeyChainStore`
  using `FakeKeyStore`.
- `tests/test_ai/test_provider_construction_offline.py` — every cloud provider can be
  constructed inside `network_sentinel()` without socket activity.
- `tests/test_ai/test_privacy.py` (extended) — assert no SDK in `sys.modules` after
  `import novelwriter.ai`.
- `tests/test_ai/test_provider_contract.py` (extended) — parametrize over MockProvider +
  Ollama + Anthropic + Gemini using `httpx.MockTransport`.
- `tests/fixtures/cassettes/` — VCR cassettes for Anthropic + Gemini (Authorization /
  x-api-key headers redacted; cassettes committed).
- `tests/fixtures/token_corpus/` — ~10 public-domain prose excerpts + synthetic edge
  cases (heavy dialogue, em-dashes, non-Latin text). <500KB.

### Documentation

- `docs/ai/security.md` (new) — secret-handling model, how contributors get keys for
  local smoke tests, cassette redaction policy.
- Update `docs/ai/architecture.md` — Auth strategy abstraction, transport factory,
  OAuth lifecycle diagram.
- Update `docs/ai/privacy.md` — OAuth refresh-token storage, revoke-on-disable
  behavior, the "lazy SDK import" rule.
- Update `README.md` at end of S2 — "easiest privacy-respecting setup in the category"
  positioning per CEO recommendation.

### Design contract

- `/design-consultation` is the contract path (decided; not `/plan-design-review`).
- New DESIGN.md component specs (added via design-consultation):
  - Four-tab top-level IA component
  - Marginalia-rail empty-state component
  - Auth-flow state machine component (idle / pending / error / signed-in)
- Output: `.planning/current/plan/design-contract.md`
- **Must run in parallel with WS-1 finish, not sequentially.** Designer turnaround is a
  slip-risk; don't gate /handoff on a design contract that started on day 7.

## Non-goals for S2 (explicit)

Things that might look like they belong but DO NOT:

- **Inline rewrite feature itself.** S3.
- **Consistency check feature.** S4.
- **Rewrite review pane UI.** S3.
- **OpenAI provider.** S6 (decided cut).
- **Character panel restructure.** S4/S5.
- **Outline tree restructure.** S4/S5.
- **Scene-card / corkboard view.** S5.
- **Marginalia rail content (real editor's notes).** S3+.
- **Streaming / async response handling.** Not in v1 per `prd.md:52`.
- **Background consistency scanning, auto-fix, whole-document rewrite.** Out of v1
  per `prd.md:178-188`.
- **Telemetry / usage analytics.** Privacy positioning forbids.
- **GitHub Actions CI secrets for cloud-API smoke tests.** S6.
- **`brand-spec.md` / logos / icon set.** Deferred per DESIGN.md.
- **i18n for new S2 strings.** English-only in S2; translation pipeline owned by S6.
- **Google's branded "Sign in with Google" button artwork.** Plain-text secondary
  button per Design's spec; DESIGN.md anti-slop rules out branded icon circles.

## Success criteria — S2 ships when each of these is green

### Functional gate

1. Plotter Pat opens Preferences → AI, sees master toggle off, sees Ollama / Anthropic /
   Gemini provider options.
2. Click "Sign in with Google" in `Preferences → AI → Gemini`. Browser opens. User
   approves. Returns to plotwright. Status bar shows `AI: ready (gemini)`.
3. Toggle AI on for "rewrite" feature (feature won't fire until S3; just enables flag).
4. Click "dry-run" button. See staged result come back from Gemini through the staging
   interface. Token estimate displayed before the call. The 20% accuracy bound holds.
5. Open the AI tab. See "EDITOR'S NOTES" empty state with Design-specified copy and
   left-aligned layout.
6. Toggle AI off. Status bar returns to `AI: off`. Network goes silent.

### Trust gate

7. `tests/test_ai/test_privacy.py` (S1) passes with three providers registered and AI
   off. No SDK modules in `sys.modules` after `import novelwriter.ai`.
8. CI privacy assertion: no `import httpx` / `import requests` outside
   `novelwriter/ai/transport.py`.

### Narrative gate

9. Window title says **plotwright**, not novelWriter. About dialog says "About
   plotwright" with upstream attribution preserved.
10. Migrator Mira opens her existing project. Four tabs visible. AI off by default.
    `appHandle` already renamed so no migration burden.

### Verification & sign-off

11. `tests/test_ai/test_oauth_flow.py` passes (PKCE + refresh + revoke).
12. `tests/test_ai/test_tokens_accuracy.py` passes (20% bound on committed corpus).
13. `tests/test_ai/test_provider_contract.py` passes for all 4 providers (Mock + Ollama
    + Anthropic + Gemini).
14. `tests/test_ai/test_auth_strategies.py` passes.
15. `tests/test_ai/test_keychain_oauth.py` passes.
16. `tests/test_ai/test_provider_construction_offline.py` passes.
17. Smoke test (manual gate): real Anthropic + Gemini calls work end-to-end with real
    keys. Output staging produces a usable `StagedRewrite`.
18. Real `design-contract.md` exists for WS-4 surfaces. DESIGN.md extended with the
    three new component specs.

## Risks accepted

The user chose ambitious scope. Risk's #1 mitigation (cut OAuth) was rejected. The
sprint is on a knife's edge. Mitigations:

- **OpenAI is cut** (Risk's third-favorite lever). Largest single scope reduction.
- **OAuth has a hard day-4 cut-line.** If `test_oauth_flow.py` isn't green by end of
  dev-day 4, OAuth defers to S6 and Gemini ships API-key only.
- **WS-4 has a "tabs + empty rail" scope ceiling.** No marginalia rendering, no
  character panel, no scene cards, no outline tree restructure.
- **`/design-consultation` runs in parallel with WS-1.** Not after.
- **Slip indicators tracked daily.** Full table in the sprint contract (`/plan` writes
  it).

## Required decisions captured (the 10 open questions)

| Q | Decision | Source |
|---|---|---|
| Q1 | Sibling `Auth` strategy class (composition) | User chose B-style |
| Q2 | OpenAI deferred to S6 | Cross-agent consensus |
| Q3 | S1 branding gap folded into S2 WS-0 | Cross-agent consensus |
| Q4 | OAuth scope: `https://www.googleapis.com/auth/generative-language` (broad). Verify via WebFetch during `/plan`. Pin as `GEMINI_SCOPE` module constant. | Eng research with fallback strategy |
| Q5 | `keyring>=24.0` (MIT). JSON-blob single entry per provider. `FakeKeyStore` in fixtures. | Cross-agent consensus |
| Q6 | "EDITOR'S NOTES" empty state with Design-specified copy. Visible tab, not hidden. | Design recommendation |
| Q7 | Curated corpus in `tests/fixtures/token_corpus/`: ~10 public-domain prose excerpts + synthetic edge cases. <500KB. | Cross-agent consensus |
| Q8 | Local-only smoke test, skip on CI without keys. VCR cassettes for CI. CI secret governance deferred to S6. | Cross-agent consensus |
| Q9 | Error envelope shape: typed dataclass `ProviderError` with `kind: Literal["safety_refusal", "rate_limit", "quota", "network", "auth"]` + `message` + `provider`. Status bar shows `AI: error ({provider})`. | Synthesis (Eng + Design + Risk) |
| Q10 | Tabs + marginalia rail primitive (empty rendering). No character panel, no scene cards, no outline tree restructure. | User chose Design recommendation |

## Transition rule

Advance to `/plan` to write `.planning/current/plan/sprint-contract.md` for S2, amend
`execution-readiness-packet.md:147-154` (the sprint-sequencing table) to reflect
OpenAI deferral, and produce a fresh `verification-matrix.json` covering the 18
success criteria above.

Real `design-contract.md` is required before `/handoff` (not before `/plan`). Plan
should kick off `/design-consultation` work in parallel.
