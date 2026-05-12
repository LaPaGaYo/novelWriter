# AI Substrate Architecture

This is the architecture sketch for the plotwright fork's AI substrate. The
substrate ships in Sprint 1; AI features (inline rewrite, consistency check)
build on top of it in Sprint 3 and Sprint 4.

## Goals

1. **Privacy by default.** Every feature off out of the box. With the master
   switch off, network egress is zero, enforced by a CI test.
2. **Provider abstraction.** Local Ollama and cloud BYO-key providers are
   indistinguishable to feature code. Adding a new provider does not require
   feature-side changes.
3. **Single egress point.** All cloud calls go through one module, so the
   privacy promise is statically auditable (`grep` for `httpx`/`requests`
   imports outside `novelwriter/ai/network.py` would catch a regression).
4. **Minimal merge surface.** Fork-specific code lives entirely under
   `novelwriter/ai/`, `tests/test_ai/`, and `docs/ai/`. Upstream merges
   touch only a handful of shared files (status bar, preferences dialog,
   config root).

## Module map

```
novelwriter/ai/
├── __init__.py              public surface for the rest of the app
├── config.py                AIConfig, AIFeature enum, project-scoped persistence
├── network.py               NetworkGate, PrivacyGatingError, AIError
├── keychain.py              KeyStore protocol + placeholder until Sprint 2
├── tokens.py                heuristic token estimator
├── staging.py               StagedRewrite dataclass (full widget in Sprint 3)
├── preferences_panel.py     AI Preferences > AI tab widget
└── provider/
    ├── __init__.py
    ├── base.py              Provider ABC, ProviderResponse, ProviderError
    └── mock.py              MockProvider (deterministic; only provider in Sprint 1)
```

## Privacy contract (the central invariant)

The substrate guarantees:

> **With `AIConfig.enabled` False, no code path in `novelwriter.ai.*` initiates
> a network connection. Period.**

This is enforced by three layers:

1. **Behavioral gate** — `NetworkGate.guard(feature)` raises
   `PrivacyGatingError` when either the master switch or the feature flag is
   False. Every cloud provider's `generate()` and `health_check()` MUST call
   this before any outbound request.
2. **Static check** (Sprint 2) — CI fails if any module outside
   `novelwriter/ai/network.py` imports `httpx` or `requests`. This catches a
   future contributor who tries to short-circuit the gate.
3. **Runtime regression test** — `tests/test_ai/test_privacy.py` monkey-patches
   `socket.socket.connect` to a fail-loud sentinel and exercises every Sprint
   1 surface with the master switch off. Any attempt to open a connection
   raises immediately.

The runtime test is the hard gate for Sprint 1 acceptance. If it fails, the
whole "100% NOT AI slop" positioning of the fork collapses.

## Lifecycle of a hypothetical cloud rewrite call (post-Sprint-2)

```
User selects prose, picks "Rewrite > Tighten"
    │
    ▼
Feature code (rewrite.py, Sprint 3) builds a prompt
    │
    ▼
Feature calls AnthropicProvider.generate(prompt, feature=REWRITE)
    │
    ▼
AnthropicProvider asks NetworkGate.guard(REWRITE)
    │  ├── master switch False?  → raise PrivacyGatingError
    │  ├── REWRITE feature flag False? → raise PrivacyGatingError
    │  └── both True?  → proceed
    ▼
AnthropicProvider asks default_keystore().get("anthropic")
    │  ├── no key? → raise ProviderError
    │  └── key present?  → use it
    ▼
AnthropicProvider issues a request via novelwriter/ai/network.py wrapper
    │  └── single-egress; logged to project debug log if enabled
    ▼
Response returns up through the same chain to feature code
    │
    ▼
Feature wraps the result in StagedRewrite and hands to the review pane widget
```

## Sprint 1 boundary

In Sprint 1 only the abstractions exist; the only concrete provider is
`MockProvider` (deterministic, never networks). The substrate is enough to:

- Construct an `AIConfig` and persist it.
- Refuse a network call attempt with `PrivacyGatingError`.
- Pass a uniform contract test against any future provider.
- Display an AI status indicator in the main-window status bar.
- Show an AI Preferences pane (with feature toggles disabled and labeled
  "available next sprint").

Sprint 2 adds the first real provider (Ollama local + Anthropic cloud BYO-key)
and the keystore backends. Sprint 3 builds inline rewrite on top. Sprint 4
builds consistency check.

## Why a project-scoped config (not user-global)

Opting in to AI for one project must never opt in another. A writer might
want the rewrite feature on for their fantasy series but off entirely for an
unfinished memoir. The privacy contract is naturally per-project, and the
config file living inside the project directory makes it impossible to
accidentally share an opt-in across projects via cloud sync of user
preferences.

## What lives outside the substrate (and why)

- **Status bar widget** (`novelwriter/gui/status_bar_ai.py`) — needs to live
  with the rest of the GUI status bar, but only consumes `AIConfig` and never
  knows about providers.
- **Preferences panel embed point** — eventually the AI Preferences pane
  embeds into `novelwriter/dialogs/preferences.py`. The widget itself lives
  under `novelwriter/ai/preferences_panel.py`; only the integration point is
  in the upstream-shared file.
- **`novelwriter/__init__.py` fork constants** — the fork name and
  user-data-directory rebrand have to live where the rest of the package
  identity lives.

These three "shared" files are exactly the ones flagged in `docs/fork.md` as
likely-conflict candidates during upstream merges.
