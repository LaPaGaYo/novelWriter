# Execution Readiness Packet — novelWriter Fork v1 (S2 amendment)

## Nexus Execution Context

- Run ID: run-2026-05-12T01-45-20-695Z (Sprint 2 plan amendment of v1 packet originally produced under run-2026-04-26T08-32-35-381Z)
- Stage: plan
- Predecessors: `docs/product/idea-brief.md`, `docs/product/decision-brief.md`, `docs/product/prd.md`, `.planning/current/frame/s2-scope.md`
- Execution mode: local_provider (claude, single_agent)
- Branch: main (S2 plan author commits onto the active sprint branch)

## Known plan-stage tooling gap (carried from v1)

The plan runtime inherited `design_impact: "none"` from `.planning/current/frame/status.json`,
which was committed before `.planning/current/frame/design-intent.json` was corrected to
`impact: "high"` for S2. The runtime did not regenerate the verification matrix from
design-intent on the first pass.

**Effect:** the bin-scaffolded `verification-matrix.json` came back with
`design_verification_required: false` and `design_review.suggested: false`. That is wrong
for S2. The framing decision ships three net-new design surfaces (four-tab IA, marginalia
rail primitive, OAuth-flow state machine) plus DESIGN.md amendments.

**Mitigation:**
- The verification matrix has been corrected in-place by the plan author. See "Verification
  matrix override notes" below.
- `/design-consultation` is the contract path (decided in /frame; not `/plan-design-review`).
- Real `design-contract.md` is required before `/handoff`. Plan kicks off
  `/design-consultation` in parallel with WS-1, not after.

## Reference artifacts

- `docs/product/idea-brief.md` — user intent and discovery context
- `docs/product/decision-brief.md` — positioning, scope, non-goals, 7 success criteria
- `docs/product/prd.md` — personas, two v1 features, cross-cutting requirements
- `.planning/current/frame/design-intent.json` — corrected design impact (high for S2)
- `.planning/current/frame/s2-scope.md` — locked S2 scope, non-goals, 18 success criteria
- `.fork-baseline.json` — pinned upstream baseline commit `10c8a186`

## Workstreams (v1, S2-amended)

Five workstreams with explicit dependencies. Sprint sequencing follows.

### WS-0 — Fork bootstrap (foundation)

Goal: a runnable fork with a distinct identity that can ingest upstream releases as needed.

- Pick fork name (Sprint 1 decision; **resolved: `plotwright`**).
- Rename PyPI package, app title, About dialog, default user-data directory.
- Pin upstream baseline to a tagged release (**resolved: `10c8a186` per
  `.fork-baseline.json`**).
- Update `pyproject.toml`, `MANIFEST.in`, `setup/`, and CI workflows.
- Update `README.md`, `CONTRIBUTING.md`, `CREDITS.md` to reflect fork status and attribute
  upstream.
- `.fork-baseline` file pointing to the upstream commit and rebase strategy notes.
- **S1 branding gap (S2 WS-0 carry-forward):** rename `appName` and `appHandle` at
  `novelwriter/config.py:113-114`, update About dialog at `novelwriter/dialogs/about.py:49,57`,
  refresh window title and any remaining UI strings, then `make i18n` to confirm clean
  string extraction. `appHandle` flows into the user-data directory path; deferring would
  cost a migration probe in S6.

Dependencies: none. Blocks every other workstream because branding/data-dir choices ripple.

### WS-1 — AI infrastructure (the substrate)

Goal: a clean abstraction every AI feature builds on. Privacy-gated by default.

Deliverables:

- `novelwriter/ai/` package:
  - `provider/` — abstract `Provider` base class, `OllamaProvider`, `AnthropicProvider`,
    `GeminiProvider`, plus `MockProvider` for tests. OpenAI provider deferred to S6.
  - `provider/registry.py` (new in S2) — maps provider name strings to factory callables;
    used by AIConfig deserialization.
  - `provider/base.py` (widened in S2) — adds `auth: Auth = NoAuth()` class attribute. No
    method signature changes; Mock + Ollama trivially compliant via default.
  - `auth.py` (new in S2) — `Auth` ABC with `mode: Literal["none", "api_key", "oauth"]`,
    `headers() -> dict[str, str]`, `refresh_if_needed() -> None`. Concrete: `NoAuth`,
    `ApiKeyAuth(api_key, header_name)`, `OAuthCreds(access_token, refresh_token, expiry,
    scope, refresher)`.
  - `oauth.py` (new in S2) — browser-loopback PKCE flow, `QDesktopServices.openUrl()` for
    system browser, `http.server` localhost listener on random free port, cryptographic
    state parameter, code-to-token exchange, returns `OAuthCreds` ready for keychain.
    Refresh policy: refresh when within 60s of expiry, at call-start (never mid-call);
    surfaces a re-auth modal on `invalid_grant`.
  - `transport.py` (new in S2) — single `httpx.Client` factory for every cloud provider.
    Lazy SDK imports live inside each `provider/<name>.py` module, never at package import
    time. CI lint rule: no `import httpx` / `import requests` in `provider/` modules.
  - `tokenizers.py` (new in S2) — per-provider adapters: tiktoken patterns for OpenAI-like
    models, Anthropic's offline tokenizer where available, Gemini heuristic where the
    offline tokenizer is not freely available. Module-level `estimate_tokens` from S1
    stays as the fallback path.
  - `config.py` (widened in S2) — feature flags (`ai.enabled`, per-feature opt-ins,
    per-feature provider choice) plus new `provider_configs: dict[str, dict]` for
    per-provider settings (Ollama base URL, Gemini auth_mode, etc.). `_SCHEMA_VERSION`
    bumped from 1 to 2.
  - `keychain.py` (widened in S2) — replaces `_MissingKeyStore` placeholder with
    `OSKeyChainStore` backed by `keyring>=24.0` (MIT). `KeyStore` Protocol gains
    `get_oauth(provider_id) -> dict | None` and `put_oauth(provider_id, blob)`. OAuth
    creds stored as JSON-encoded single-entry blob per provider (atomic refresh).
  - `tokens.py` — module-level fallback heuristic (S1).
  - `prompts/` — prompt template files, one per feature/transformation.
  - `staging.py` — output staging (proposed-vs-source diff model, undo-friendly).
    S2 widens `StagedRewrite` with cursor/range fields anticipating the S3 review pane and
    commits `staging_consumer.py` as the S3 boundary stub.
  - `network.py` — single egress point. Logs every request; asserts `ai.enabled == True`
    AND feature-specific opt-in before any call. Gating stays feature-level; providers
    stay dumb.
- `novelwriter/preferences/ai_panel.py` — un-greyed per-feature toggles, per-feature
  provider dropdown, per-provider config rows, per-provider auth UX (Ollama base URL,
  Anthropic masked API key, Gemini "API key / Sign in with Google" radio group),
  "Dry-run" smoke button. `setBuddy` and `accessibleName` wired per Design a11y notes.
- `novelwriter/gui/status_bar_ai.py` — 1 Hz vermilion pulse via `QPropertyAnimation` on
  opacity (0.4 ↔ 1.0, 500ms each direction, ease-in-out). Live provider name in the label.
  Hover tooltip uses Qt-default style (no custom popup). Click wired to
  `GuiPreferences.openAt("ai")`. `setFocusPolicy(Qt.FocusPolicy.TabFocus)`,
  `accessibleName`, Enter/Space activation.
- `tests/test_ai/test_privacy.py` (extended) — assert no SDK module in `sys.modules` after
  `import novelwriter.ai`.
- `tests/test_ai/test_provider_contract.py` (extended) — parametrize over MockProvider +
  Ollama + Anthropic + Gemini using `httpx.MockTransport`.
- New S2 tests: `test_oauth_flow.py`, `test_auth_strategies.py`, `test_keychain_oauth.py`,
  `test_provider_construction_offline.py`, `test_tokens_accuracy.py`.
- `tests/fixtures/cassettes/` — VCR cassettes for Anthropic + Gemini (Authorization /
  x-api-key headers redacted; cassettes committed).
- `tests/fixtures/token_corpus/` — ~10 public-domain prose excerpts + synthetic edge
  cases. Under 500KB.

Dependencies: WS-0.

### WS-2 — Feature: Inline rewrite

Goal: select prose, transform, review, accept.

Deliverables:

- `novelwriter/ai/features/rewrite.py` — orchestrates: collect selection, build context,
  call provider, parse output, hand to staging.
- `novelwriter/gui/ai_review_pane.py` — side-by-side review widget. Keyboard-driven.
- Editor integration: context-menu items, command palette entries, hotkey binding (gated
  by feature opt-in).
- Five transformation templates: rewrite, expand, contract, change tense, change POV.
- `tests/test_ai_rewrite_e2e.py` against `MockProvider`.
- Documentation: `docs/ai/rewrite.md`.

Dependencies: WS-1 (provider abstraction, staging, network gating).

### WS-3 — Feature: Consistency check

Goal: scan a doc/selection against the project's notes; flag inconsistencies inline.

Deliverables:

- `novelwriter/ai/features/consistency.py` — context assembly (characters, locations,
  synopses, timeline), prompt-driven inconsistency detection, structured-output parsing.
- `novelwriter/ai/schema/inconsistency.json` — JSON schema for inconsistency records.
- `novelwriter/gui/consistency_inline_markers.py` — inline marker rendering.
- `novelwriter/gui/consistency_panel.py` — side-panel with accept/dismiss/snooze.
- Strictness slider in Preferences > AI > Consistency.
- Corroboration logic: a finding requires `confidence == high` OR two or more supporting
  signals.
- Test corpus: 3 short novels with seeded errors. Stored in `tests/corpus/consistency/`.
- `tests/test_ai_consistency_corpus.py` — recall/precision against the corpus.
- Documentation: `docs/ai/consistency.md`.

Dependencies: WS-1. Independent of WS-2 (can run in parallel).

### WS-4 — UI redesign

Goal: new project shell, IA optimized for plotters.

Deliverables (eight surfaces from `design-intent.json`):

1. Project shell — top-level navigation reorganized: Outline / Manuscript / Notes / AI.
   Cmd/Ctrl+1..4 shortcuts wired. **S2 ships this surface.**
2. Scene-card view — corkboard alternative to the document tree, drag to reorder.
3. Character panel — pull all references to a character into one view.
4. AI inspector dock — host for review pane and consistency results.
5. Status bar — provider state, network indicator, token-usage estimate. **S2 ships the
   pulse animation and provider-name label.**
6. Preferences > AI section — feature opt-ins, provider config, key entry. **S2 ships
   the full panel including the dry-run button.**
7. AI review pane — covered in WS-2.
8. Consistency-check inline markers — covered in WS-3.

S2 also ships the three-column geometry primitive (project tree 200-240px / main column
60ch enforced in Manuscript view / marginalia rail 280-320px fixed) and the marginalia
rail primitive (empty rendering in S2; populated S3+). Cream-paper theme is the default
boot per DESIGN.md.

Dependencies: WS-0 (branding); WS-2 and WS-3 supply two of the surfaces. Real design
contract via `/design-consultation` required before `/handoff`.

### WS-5 — Migration & fork polish

Goal: existing upstream-novelWriter users can migrate without data loss.

Deliverables:

- Migration probe: open an upstream `.nwx` project; assert no schema changes when
  read-only.
- Round-trip integration test: open in fork, save, reopen in upstream novelWriter, diff.
- Fork-only metadata stored under namespaced extension (e.g., `nwx:ext:plotwright`).
- New default user-data dir: `~/.config/<fork-name>/` (Linux), platform equivalents.
- Branding: new icon set in `setup/`, About dialog rewrite, splash screen update.
- `docs/migration.md` for users coming from upstream.

Dependencies: WS-0. Final polish runs concurrent with hardening sprint.

## Sprint sequencing

| Sprint | Workstreams | Concrete focus | Exit criterion |
|--------|-------------|----------------|----------------|
| **S1** | WS-0 + WS-1 (start) | Fork bootstrap, provider abstraction interface, MockProvider, privacy config skeleton, network-zero test scaffolding | App launches with fork branding; `tests/test_ai_privacy.py` runs and asserts zero outbound traffic with AI off; provider contract tests pass against MockProvider. |
| **S2** | WS-0 (carry-forward branding) + WS-1 (finish) + WS-4 (start) | Ollama + Anthropic + Gemini (with OAuth) providers, Auth strategy class, token estimation, output staging, full AI Preferences panel, four-tab IA + marginalia rail primitive, status-bar pulse animation, S1 branding gap closed | Three providers pass contract suite; Gemini OAuth works end-to-end; project shell shows new IA + marginalia rail primitive; `test_privacy.py` still passes; design-contract.md exists for WS-4 surfaces |
| **S3** | WS-2 (full) + WS-4 (review pane surface) | Inline rewrite end-to-end on five transformations; review pane keyboard-driven | Rewrite acceptance test panel passes 80/100 sample bar (or documents what didn't and why). |
| **S4** | WS-3 (full) + WS-4 (consistency markers + character panel) | Consistency check end-to-end; corroboration logic; test corpus assembled; strictness slider | Test-corpus recall >= 70%, FPR <= 20% at default strictness. |
| **S5** | WS-4 (finish) + WS-5 | Scene-card view, AI inspector dock polish, character-panel polish, migration probe + round-trip test, branding | Moderated 5-plotter legibility test <= 8min task completion; round-trip migration zero-diff. |
| **S6** | Hardening + OpenAI provider | OpenAI provider, cross-platform smoke (Linux/Win/macOS), translation pipeline check, packaging, release notes, success-criteria measurement | All seven `decision-brief.md` success criteria measured and either met or formally waived; OpenAI provider passes contract suite. |

Footnote: OpenAI provider deferred from S2 to S6 hardening per /frame decisions
(run-2026-05-12T01-45-20-695Z). OpenAI ships in S6 alongside cross-platform packaging.

Each sprint runs its own `/plan` -> `/handoff` -> `/build` -> `/review` -> `/qa` -> `/ship` -> `/closeout` cycle.

## Risks (planning-stage)

| Risk | Owner sprint | Mitigation |
|------|--------------|------------|
| Provider abstraction over-fits to one provider, painful to add a second | S1 | Implement two providers in S1 (Mock + one real) before features start. |
| Privacy gating bypassed by a future contributor | S1 | Single-egress `network.py`; CI test asserts no `httpx`/`requests` import outside that module. |
| UI redesign sprawls and slips MVP | S2-S5 | Design contract before /handoff; budget per surface; cut scope on individual surfaces, not on the privacy/AI core. |
| Consistency-check accuracy regresses with model updates | S4 + S6 | Test corpus is a hard CI gate. New model versions must clear it before they ship as defaults. |
| Upstream merge becomes unmaintainable | S6 | Document a quarterly upstream-merge runbook in WS-5; tag fork-specific files explicitly. |
| Local Ollama install friction kills adoption | S2 + S5 | Cloud-first onboarding flow; "switch to local later" guide; ship a known-good Ollama config. |
| GPL-3 attribution slip in fork branding | WS-0 + WS-5 | Legal review checkpoint in S6; CREDITS.md and About dialog explicitly attribute upstream. |
| OAuth refresh-token rotation failure mid-session | S2 | Surface as blocking modal with re-auth button; log to status bar. Test `invalid_grant` handling. |
| Random-port loopback listener conflicts with corporate firewalls | S2 | Detect listener bind failure; fall back to manual code copy/paste OR API key. |
| Google Cloud Console OAuth consent screen verification status | S2 | Document in docs/ai/privacy.md; use least-permissive scope. |
| VCR cassette staleness (Anthropic/Gemini APIs evolve) | S2-S6 | Quarterly cassette regeneration cadence; CI clearly marks "cassette mode" in output. |
| Provider SDK version pin conflicts (httpx/pydantic across SDKs) | S2 | Pin SDKs in pyproject.toml; run `pip check` in CI. |
| Token-refresh-during-call race | S2 | Refresh at call-start when within 60s window; never mid-call; document retry behavior. |
| OAuth state-parameter CSRF risk | S2 | Generate cryptographic state per attempt; reject mismatched state on callback. |
| Designer / design-contract turnaround slippage | S2 | Run /design-consultation in parallel with WS-1, not sequentially. |
| Sprint-2 review pane plug points unspecified | S2-S3 | Stub the S3 consumer interface in S2; commit it as `staging_consumer.py` even if unimplemented. |
| Eager SDK network discovery on import breaks privacy test | S2 | Lazy import every SDK inside provider/<name>.py module functions; CI assertion: no SDK in sys.modules after `import novelwriter.ai`. |

## Verification matrix override notes

S2 reshapes the verification matrix away from the bin-scaffolded defaults. The corrected
expectations are:

- `design_review.suggested: true` — S2 ships first multi-surface design work (four-tab IA,
  marginalia rail primitive, status-bar pulse animation, AI Preferences panel layout,
  OAuth-flow state machine).
- `design_verification_required: true` — four-tab IA + marginalia rail primitive + OAuth
  flow are net-new design surfaces. DESIGN.md gets three new component specs.
- `accessibility.applies: true` — OAuth browser handoff plus keyboard activation across
  the AI Preferences panel and the four-tab IA (Cmd/Ctrl+1..4) require accessibility
  coverage.
- `/design-consultation` artifact REQUIRED before `/handoff` (matches what's now in
  `design-intent.json`). `/design-consultation` is the contract path, not
  `/plan-design-review`.

The plan stage author has updated `verification-matrix.json` accordingly; the
`s2_success_criteria` array lists all 18 gates from `s2-scope.md` with owner stage,
evidence artifact, slip-indicator day, and gate-blocking flag.

## Open items (to resolve in sprint plans)

These move from this v1 packet into individual sprint contracts.

- Final fork product name — **RESOLVED: `plotwright`** (per S1 + S2 WS-0 cleanup)
- Pinned upstream baseline commit — **RESOLVED: `10c8a186`** per `.fork-baseline.json`
- S1 branding gap (`appName` / `appHandle` / window title / About dialog) —
  **RESOLVED: folded into S2 WS-0 carry-forward** per `/frame` Q3 decision.
  Closes before first fork release so no user-data-dir migration probe needed.
- Token-estimate accuracy benchmark — **S2 owner with corpus in
  `tests/fixtures/token_corpus/`**
- Test-corpus assembly approach — **still open, S4 owner**
- Migration round-trip schema diff tool — **still open, S5 owner**
- OpenAI provider scope — **new open, S6 owner** (deferred from S2)

## Transition Rule

Advance to `/handoff` only after Nexus declares execution ready and a real design contract
exists.

## Sprint contract pointer

Each sprint's bounded contract lives in `.planning/current/plan/sprint-contract.md`.
Sprint 2's contract is governed by the locked decisions in
`.planning/current/frame/s2-scope.md`.
