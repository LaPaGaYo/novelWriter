# Sprint Contract — Sprint 1: Fork Bootstrap + AI Substrate

This contract bounds the *first* sprint of v1. The full v1 plan lives in
`execution-readiness-packet.md`. Nothing outside this contract is in scope for Sprint 1.

## Sprint goal

Stand up the fork as a runnable, branded application and put the AI substrate (provider
abstraction, privacy gating, MockProvider, network-zero regression test) in place. No real
AI feature ships in Sprint 1. No UI redesign ships in Sprint 1.

## In-scope deliverables

### Fork identity (WS-0)

- Rename:
  - `pyproject.toml` package name and console-entry-point.
  - `setup/` references that hardcode `novelwriter` paths.
  - User-data directory default in `novelwriter/config.py` (suggest: `<fork-name>/`).
  - App window title, About dialog text.
- Create `.fork-baseline.json` recording:
  - upstream commit hash
  - upstream tag (recommend `v26.2-alpha-0` or current `release` head)
  - rebase strategy notes
- Update `README.md` with fork-status, attribution to vkbo/novelWriter, GPL-3 notice.
- Update `CREDITS.md` to attribute upstream maintainer and contributors.
- Add `docs/fork.md` explaining the fork's purpose and stance on AI vs. upstream's anti-AI position.
- CI: ensure existing test suite still passes against the fork name.

### AI substrate (WS-1, partial)

Concrete files to create:

- `novelwriter/ai/__init__.py` — package init, public surface for the rest of the app.
- `novelwriter/ai/config.py`
  - `AIConfig` class: `enabled` (default False), `feature_flags` dict (rewrite/consistency
    each default False), per-feature provider choice.
  - Reads/writes from project config, *not* user-global config (per-project opt-in).
- `novelwriter/ai/network.py`
  - Single-egress wrapper around `httpx`/`requests`. Refuses to make a call unless:
    1. `AIConfig.enabled is True`
    2. The caller-supplied feature flag is True
    3. A non-empty cloud API key OR a local provider URL is configured
  - Logs every outbound call (metadata only — endpoint, byte count, no body) to a project-
    local debug log when enabled.
- `novelwriter/ai/provider/__init__.py`
- `novelwriter/ai/provider/base.py`
  - `Provider` ABC: `name`, `is_local`, `generate(prompt: str, **opts) -> str`,
    `estimate_tokens(text: str) -> int`, `health_check() -> bool`.
- `novelwriter/ai/provider/mock.py`
  - `MockProvider`: deterministic echo + fixed transformations. The only provider Sprint 1
    actually uses.
- `novelwriter/ai/keychain.py` — interface only. Real backends land in S2.
- `novelwriter/ai/tokens.py` — heuristic token-count helper (4 chars/token fallback).
- `novelwriter/ai/staging.py` — interface only. Real staging ships with rewrite in S3.
- `novelwriter/preferences/ai_panel.py`
  - Minimal Preferences > AI tab: `Enable AI features` checkbox; per-feature toggles disabled
    in S1 (greyed with "available in next sprint"); provider rows hidden until enabled.
- `novelwriter/gui/status_bar_ai.py`
  - Status-bar widget showing `AI: off` / `AI: ready (mock)`. Click opens AI Preferences.

### Tests

- `tests/test_ai_privacy.py`
  - With `AIConfig.enabled = False`, run a 60-second scripted session (open project, edit,
    save, close).
  - Assert: zero outbound TCP/UDP packets via `socket`-monkeypatch sentinel.
  - Failure here BLOCKS the sprint.
- `tests/test_ai_provider_contract.py`
  - Run the contract suite against `MockProvider`. Asserts every method on `Provider` ABC
    is implemented and returns expected types.
- `tests/test_ai_network_gating.py`
  - Direct unit tests on `network.py`: a call attempt with `enabled=False` raises
    `PrivacyGatingError`. A call attempt with `enabled=True` but feature-flag False also
    raises. Both errors must be subclasses of a new `AIError` base.
- `tests/test_ai_config_persistence.py`
  - Write AI config to a project, reopen, assert defaults intact, asserts opt-in survives.

### Documentation

- `docs/ai/architecture.md` — architecture sketch of the AI substrate.
- `docs/ai/privacy.md` — privacy guarantees, what's logged where, network-zero behavior.
- `docs/fork.md` — see fork identity above.

## Out of scope (Sprint 1)

- Real provider implementations (Ollama, Anthropic, OpenAI, Gemini). Land in S2.
- Inline rewrite feature. Lands in S3.
- Consistency check feature. Lands in S4.
- UI redesign of project shell, scene cards, character panel, AI inspector dock. Lands across S2-S5.
- Token-estimate accuracy benchmark. Belongs in S2.
- Migration testing. Belongs in S5.
- Translation strings for new UI beyond what already exists in upstream.

## Verification

This sprint is "done" when each of these is green:

1. Existing upstream test suite passes against the renamed package. (CI must show green.)
2. `tests/test_ai_privacy.py` passes — zero outbound traffic with AI off.
3. `tests/test_ai_provider_contract.py` passes against `MockProvider`.
4. `tests/test_ai_network_gating.py` passes — `PrivacyGatingError` raised on every disallowed
   call attempt.
5. `tests/test_ai_config_persistence.py` passes — AI config round-trips through project save/load.
6. App launches with the new fork name in window title and About dialog.
7. AI status-bar widget visible and shows `AI: off` by default.
8. AI Preferences tab visible with the master toggle; per-feature toggles correctly disabled.
9. `docs/fork.md`, `docs/ai/architecture.md`, `docs/ai/privacy.md` exist and pass markdown lint.
10. `.fork-baseline.json` exists and points at a reachable upstream commit/tag.

## Definition of "ready for /handoff"

All ten items above pass *and* a real `design-contract.md` exists for Sprint 1's UI surfaces.
The Sprint 1 design surface is small (Preferences > AI tab, status-bar widget). A
lightweight `/plan-design-review` is sufficient. /design-consultation is not required for
Sprint 1; defer to Sprint 2 when the project shell IA work begins.

## Estimated size

8-12 engineering days for one developer, less with parallelization on tests + docs.

## Sprint 1 risks

| Risk | Mitigation |
|------|------------|
| Privacy regression test is flaky on CI runners with background processes | Use a `socket.socket.connect` monkeypatch sentinel rather than packet capture; assert no calls reach the sentinel. |
| Renaming breaks i18n string extraction | Run i18n extraction script before/after rename; diff the `.pot`. |
| Fork name conflict on PyPI | Pre-check on PyPI before locking the name. Reserve placeholder if needed. |
| User-data directory rename breaks existing upstream-novelWriter installs on the same machine | Use a NEW directory; do not auto-migrate from the upstream one. Document as user-facing fork behavior. |

## Transition Rule

Advance to `/handoff` only after every verification item above is green AND a Sprint 1
design contract has been produced via `/plan-design-review`.
