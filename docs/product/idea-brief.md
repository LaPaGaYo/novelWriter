# Idea Brief — Sprint 2

Sprint 2 of the novelWriter AI fork v1. Companion to `docs/product/decision-brief.md`
(v1 boundary) and `docs/product/prd.md` (feature spec). This brief captures what S2
needs to discover before `/frame` locks scope.

## Run context

- Run: `run-2026-05-12T01-45-20-695Z` (sprint 2)
- Continuation mode: phase
- Predecessor run: `run-2026-04-26T08-32-35-381Z` (sprint 1, closed 2026-04-27)
- Carry-forward artifacts: `docs/product/prd.md`, `docs/product/decision-brief.md`, S1 closeout record
- Scoping decision from session 2026-05-06: pull Gemini OAuth forward into S2

## Where S1 left off

S1 closeout passed all ten verification items. Substrate state ready for S2 to build on:

- `novelwriter/ai/` package shipped: `provider/base.py` ABC, `MockProvider`, `AIConfig`,
  `NetworkGate`, `keychain.py` (interface only), `tokens.py` (3.5 chars/token heuristic),
  `staging.py` (interface only).
- UI surfaces shipped: `novelwriter/ai/preferences_panel.py` (master toggle live;
  per-feature toggles locked with "available next sprint"; provider rows hidden),
  `novelwriter/gui/status_bar_ai.py` (off / ready / working states, static color in S1).
- Tests shipped and green: `test_privacy.py` (socket-sentinel zero-egress with AI off),
  `test_provider_contract.py` (against MockProvider), `test_network_gating.py`,
  `test_config_persistence.py`.
- Docs shipped: `docs/ai/architecture.md`, `docs/ai/privacy.md`, `docs/fork.md`.
- Fork identity: `pyproject.toml` package renamed to `plotwright`, `.fork-baseline.json`
  pinned to upstream commit `10c8a186`, README + CREDITS attribute upstream.

S1 also left a known gap: `appName`, `appHandle`, window title, and About dialog still
read `"novelWriter"` in `novelwriter/config.py:113-114` and `novelwriter/dialogs/about.py`.
The S1 contract said these would be renamed; they were not. This must be resolved in
S2 or formally deferred to S6.

## Goals — what S2 must deliver

### Provider implementations (WS-1 finish)

Four real providers ship in S2, all behind the existing `Provider` ABC and
`NetworkGate`:

1. **OllamaProvider** (`novelwriter/ai/provider/ollama.py`). Local. Default model
   `llama3.1-8b`. No auth. Healthcheck via `GET /api/tags` on the configured base URL.
2. **AnthropicProvider** (`novelwriter/ai/provider/anthropic.py`). Cloud, API key only.
3. **OpenAIProvider** (`novelwriter/ai/provider/openai.py`). Cloud, API key only.
4. **GeminiProvider** (`novelwriter/ai/provider/gemini.py`). Cloud, **two auth modes**:
   - API key (BYO from ai.google.dev)
   - OAuth ("Sign in with Google"), explicit button in `Preferences → AI → Gemini`

### OAuth substrate (net-new for S2)

- `novelwriter/ai/auth.py` (new file). Browser-loopback OAuth flow with PKCE. Spins up
  a localhost HTTP listener on a random free port; pops system browser via Qt's
  `QDesktopServices.openUrl()`; exchanges auth code for refresh + access token;
  stores credentials via the widened keychain.
- `novelwriter/ai/keychain.py` (widen). KeyStore now handles both single-secret API
  keys (current shape) and OAuth credential blobs (`access_token`, `refresh_token`,
  `expiry`, `scope`). Backward-compatible for Anthropic/OpenAI which stay API-key.
- Token refresh loop. When access token is within 60s of expiry, refresh transparently
  before the next provider call. Refresh failure surfaces as a re-auth prompt.

### Provider ABC widening (S1 → S2 retrofit)

- Add `auth_mode: Literal["none", "api_key", "oauth"]` to `Provider` ABC.
- Add opaque `credential` field passed at provider construction. MockProvider gets
  `auth_mode = "none"`. OllamaProvider gets `auth_mode = "none"`. Cloud providers get
  `api_key` or (for Gemini) `oauth`.
- Must not break the S1 `test_provider_contract.py` against MockProvider.

### Token estimation accuracy benchmark (PRD criterion)

- The S1 `tokens.py` heuristic is a 3.5 chars/token fallback. S2 owner of WS-1's
  benchmark per `execution-readiness-packet.md:189`.
- PRD requires "within 20% of actual usage on a 95% sample" for cloud-provider runs
  (`prd.md:60`). Apply this to all three cloud providers.
- Provider-specific tokenizers where available: `tiktoken` for OpenAI, Anthropic's
  `count_tokens` API for Anthropic, Google's Vertex `count_tokens` for Gemini. Fallback
  to the heuristic for unknown models.
- `tests/test_ai/test_tokens_accuracy.py` (new). Asserts the 20% bound on a corpus of
  fixed sample texts.

### Output staging real implementation

- `novelwriter/ai/staging.py` widens from interface-only to a working staging area.
- The pattern: provider call returns `StagedRewrite`, UI presents it (S3's review pane
  will consume this), no source-text mutation until explicit accept.
- S2 lands the staging mechanic without the review-pane UI (that's S3). The Preferences
  panel can include a "dry-run" button that produces a staged result for inspection.

### Full AI Preferences panel

- Un-grey the per-feature toggles in `preferences_panel.py`. They were locked in S1.
- Expose provider rows: per-feature dropdown (Ollama / Anthropic / OpenAI / Gemini),
  per-provider config (model name, base URL where applicable).
- Per-provider auth UX:
  - Ollama: base URL field
  - Anthropic: API key field (masked, stored via keychain)
  - OpenAI: API key field (masked, stored via keychain)
  - Gemini: radio group "API key" / "Sign in with Google" → respective input below

### Status bar widget upgrade

- `novelwriter/gui/status_bar_ai.py` gains the "working..." pulse animation that was
  static in S1 (per S1 audit). New states: `AI: ready (ollama)`, `AI: ready
  (anthropic)`, etc.

### Project shell IA (WS-4 start)

- Top-level tab structure changes from upstream's layout to: **Outline / Manuscript /
  Notes / AI**.
- Honor `DESIGN.md`: cream-paper default theme, vermilion reserved for AI-touched
  regions only. The "AI" tab is *not* a chat sidebar — it is a marginalia rail per the
  locked design decision.
- S2 ships the IA scaffold only. AI tab content is empty until S3 (rewrite) and S4
  (consistency check).
- Requires a real `design-contract.md` before `/handoff` (already noted as required
  in the v1 packet's transition rule).

### Verification

S2 done when each of these is green:

1. All four providers pass `tests/test_ai/test_provider_contract.py`. The contract
   suite from S1 runs unchanged against MockProvider, OllamaProvider (with local mock
   server), AnthropicProvider (with VCR cassette), OpenAIProvider (with VCR cassette),
   GeminiProvider (with VCR cassette).
2. `tests/test_ai/test_oauth_flow.py` (new). PKCE handshake against a localhost OAuth
   stub. Refresh-token round-trip. Revoke-on-disable.
3. `tests/test_ai/test_tokens_accuracy.py` (new). 20% accuracy bound on corpus.
4. `tests/test_ai/test_privacy.py` (S1) **still passes** — network-zero regression
   holds with all four providers registered but AI off.
5. Smoke test: real AI call works end-to-end through each cloud provider (manual gate
   with real keys, opt-in CI job with stored secrets).
6. AI Preferences panel: per-feature toggles enabled, provider dropdowns populated,
   Gemini "Sign in with Google" launches browser flow and completes.
7. Project shell shows new top-level IA. `DESIGN.md` audit clean.
8. AI status-bar widget shows live provider name and animated working state.
9. S1 branding gap (appName/appHandle/About dialog) resolved or formally deferred.
10. Sprint 2 design contract exists and was reviewed via `/plan-design-review` or
    `/design-consultation` before `/handoff`.

## Constraints

- **Privacy contract is non-negotiable.** S1's `test_privacy.py` socket-sentinel must
  continue to pass with all four providers loaded but AI off. OAuth refresh-token
  network calls only happen when at least one Gemini-using feature is opted in.
- **Backward compatibility with S1 substrate.** MockProvider must continue to work
  unchanged. The S1 keychain interface widens without breaking. The S1 `Provider` ABC
  gains fields, not breaking method signatures.
- **Design system is canonical.** `DESIGN.md` rules: cream-paper default, vermilion
  reserved for AI-touched regions, AI as marginalia (not chat). WS-4 implementation
  must honor this; `/plan-design-review` is the enforcement gate.
- **Sprint 2 size is ~2× S1.** Estimated 16-27 dev-days. Risk of slipping if any one
  provider implementation goes sideways. Scope-control lever: defer OpenAI to S6
  hardening (only Gemini and Anthropic are strictly required for the abstraction
  stress-test that motivates this sprint).
- **No new files outside the `novelwriter/ai/` package and `novelwriter/gui/` for
  status bar.** Provider implementations stay in `novelwriter/ai/provider/`. OAuth
  flow stays in `novelwriter/ai/auth.py`. UI changes to existing files only for
  Preferences and status bar.
- **GPL-3 license preserved.** Any provider SDK dependency must be license-compatible.
  Anthropic SDK (MIT), OpenAI SDK (Apache-2), Google generative-ai (Apache-2), Ollama
  (no SDK needed, plain HTTP). All compatible.
- **No prompt or output written to disk by default.** Debug log is opt-in,
  project-local, git-ignored (per `prd.md:133`).

## Open questions for `/frame`

1. **Provider abstraction shape for OAuth.** Polymorphic `provider.credential` blob
   on the ABC, or sibling `Auth` strategy class that providers reference? First is
   simpler for two auth modes; second scales to Azure AD / Bedrock IAM in v2. Decide
   in `/frame`.
2. **OpenAI scope for S2.** Ship API-key only and design OAuth-readiness for later,
   or skip OpenAI entirely in S2 and add it in S6 along with any extra cloud providers?
3. **S1 branding gap resolution.** Fold appName/appHandle/window title rename into
   S2 WS-0 cleanup (cheap, 0.5 dev-day), or formally defer to S6 with a recorded
   waiver? Recommend folding into S2.
4. **Gemini OAuth scope value.** Which exact Google API scope does the Gemini OAuth
   flow request? `https://www.googleapis.com/auth/generative-language.retriever` is
   one candidate; confirm against current ai.google.dev OAuth documentation during
   `/plan` research.
5. **OAuth token storage location.** macOS Keychain, Linux libsecret, Windows
   Credential Manager — the keychain wrapper has to handle three platforms. Which
   library? Recommend `keyring` (Python, cross-platform, MIT licensed).
6. **AI tab content placeholder.** When the new project shell shows the AI tab in
   S2, what does it display while rewrite (S3) and consistency check (S4) haven't
   shipped? Empty state, "available next sprint" copy, or hidden until first feature
   ships?
7. **Test corpus for token-accuracy benchmark.** Where do the 95% sample texts come
   from? Synthetic generated text, public-domain prose excerpts (Project Gutenberg),
   or a curated corpus committed to `tests/fixtures/`?
8. **Smoke test secret management.** Real cloud API keys for CI need to be stored
   somewhere. GitHub Actions secrets work for CI but require a repo-level decision.
   Local-only smoke test (skip on CI without keys) is simpler but weaker.
9. **Provider failure UX.** When a cloud provider returns a safety refusal, rate
   limit, or quota error, what does the user see? S2 needs a baseline error-surfacing
   pattern that S3's review pane will plug into.
10. **Project shell IA — depth of redesign in S2.** The v1 plan's sequencing table
    lists "project shell skeleton" for S2 and "review pane surface" for S3. What
    counts as "skeleton"? Just the four-tab structure, or also character-panel /
    outline tree restructuring? Recommend strict scope: tabs only.

## Plan / handoff transition

Advance to `/frame` when this brief is reviewed. `/frame` produces the S2 scope
contract, non-goals, and success criteria. `/plan` then writes
`.planning/current/plan/sprint-contract.md` for S2 and amends the sprint-sequencing
table in `execution-readiness-packet.md:147-154` to reflect the four-provider scope.

A real `design-contract.md` for the WS-4 project shell skeleton is required before
`/handoff` per the v1 packet transition rule (`execution-readiness-packet.md:194`).
The S1 design contract used `/plan-design-review` for a small surface; S2's WS-4
surface justifies `/design-consultation` per memory #S632.
