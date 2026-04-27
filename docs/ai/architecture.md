# AI Substrate — Architecture

This document describes the AI substrate that ships in Sprint 1 of
Plotwright. It is the foundation every later AI feature builds on. No
end-user-visible AI feature ships in Sprint 1 — the substrate exists so
that Sprints 2–5 can layer features on without re-deriving the privacy
or provider contracts.

## Goals

1. **One way to talk to a model.** Every AI feature uses the same
   provider abstraction so swapping providers is a configuration change,
   never a code change.
2. **One place that talks to the network.** All real outbound calls
   route through `novelwriter/ai/network.py`. CI fails if any other
   module imports `httpx` or `requests`.
3. **Off by default, every time.** Defaults err toward not contacting
   anything. A freshly opened project has zero capability to make a
   network request until a human flips the master toggle *and* the
   feature flag.
4. **Faithful skeleton, no premature concretion.** Sprint 1 ships
   interfaces for keychain, staging, and real providers — the actual
   implementations land in Sprints 2–3 alongside the features that need
   them.

## Module map

```
novelwriter/ai/
├── __init__.py        Public surface for the rest of the app
├── config.py          AIConfig dataclass (per-project settings)
├── error.py           AIError, PrivacyGatingError, ProviderError
├── network.py         Single egress point + privacy gate
├── persistence.py     AIConfig <-> ai-config.json round-trip
├── keychain.py        Keychain ABC (Sprint 2 backends)
├── staging.py         Staging ABC + StagedProposal (Sprint 3 features)
├── tokens.py          estimate_tokens() — heuristic placeholder
└── provider/
    ├── __init__.py
    ├── base.py        Provider ABC
    └── mock.py        MockProvider — Sprint 1's only working backend
```

## Data flow (Sprint 2 onwards)

```
GUI feature  →  AIConfig.is_feature_enabled(...)
            →  Provider.generate(prompt, **opts)
            →  network.gated_request(config, EgressRequest)   ← refuses if off
            →  (Sprint 2 transport — out of scope for this sprint)
            ←  Provider returns text
            ←  Staging.stage(StagedProposal)                  ← user accept/reject
            ←  Editor undo stack
```

In Sprint 1 the dotted path stops after `gated_request` returns. The
real transport call ships in Sprint 2 with the Anthropic / OpenAI /
Ollama / Gemini provider implementations.

## Configuration

`AIConfig` is per-project, not user-global. Privacy posture is a
per-manuscript decision and we never want a "once enabled everywhere,
enabled forever" mode. The serialised form is JSON (`ai-config.json` in
the project directory) for Sprint 1; Sprint 2 will move it inside the
upstream XML project format without changing the dict schema.

| Field | Default | Purpose |
|-------|---------|---------|
| `enabled` | `False` | Master toggle. Off = no AI capability anywhere. |
| `feature_flags` | `{rewrite: False, consistency: False}` | Per-feature opt-in. |
| `feature_providers` | `{rewrite: "mock", consistency: "mock"}` | Which provider backs each feature. |

`AIConfig.is_feature_enabled(feature)` is the canonical predicate for
"may this feature do anything?" It returns `True` only when the master
toggle and the per-feature flag are both on.

## Privacy gate

`gated_request(config, EgressRequest)` is the choke point. It refuses
the call (raises `PrivacyGatingError`, a subclass of `AIError`) unless
**all** of these are true at the moment of the call:

1. `config.enabled is True`
2. `config.feature_flags[request.feature] is True`
3. `request.endpoint` is non-empty
4. `request.has_credential` is `True` (cloud providers) or the endpoint
   is a local URL (Sprint 2 will refine the local-vs-cloud split)

When the gate allows the call, it logs a metadata-only line
(`endpoint`, `byte_count`, `feature`). The body is never read or logged
by this module — it goes straight to the transport layer.

## Provider contract

`Provider` is an ABC. Every concrete provider implements:

- `name: str` — stable identifier (`"mock"`, `"ollama"`, ...).
- `is_local: bool` — drives privacy UX and gate decisions.
- `generate(prompt: str, **opts) -> str` — synchronous completion.
  Streaming arrives in Sprint 2 as a separate `stream()` method without
  changing the synchronous contract.
- `estimate_tokens(text: str) -> int` — defaults to a 4-chars/token
  heuristic; real providers override with their tokenizer.
- `health_check() -> bool` — cheap, side-effect-free.

The contract test (`tests/test_ai_provider_contract.py`) is parametrised
over `PROVIDERS_UNDER_TEST`. New providers register themselves there and
inherit the full contract suite without writing new test bodies.

## What Sprint 1 deliberately does *not* ship

- Real provider implementations (Anthropic / OpenAI / Ollama / Gemini).
- Real transport in `network.py` — only the gate.
- Real keychain backends. The ABC exists; OS-native backends ship in S2.
- Real staging behaviour. Both ABCs exist; concrete implementation ships
  in Sprint 3 alongside the inline-rewrite feature that first stages
  output.
- Streaming. Sprint 2 adds it as an additional method on the provider
  ABC.

These are intentional gaps, not omissions. Each one is owned by a later
sprint with its own verification criteria.

## How to extend

When adding a new provider in Sprint 2:

1. Create `novelwriter/ai/provider/<name>.py` subclassing `Provider`.
2. Register it in `PROVIDERS_UNDER_TEST` in
   `tests/test_ai_provider_contract.py` — that picks up the full
   contract suite.
3. Add the provider id to `KNOWN_PROVIDERS` in `config.py`.
4. **Do not** import `httpx` / `requests` in the provider module. Route
   real calls through `network.py`. CI will catch you.

When adding a new AI feature in Sprint 3+:

1. Add the feature name to `KNOWN_FEATURES` and to the `feature_flags`
   default in `AIConfig`.
2. Use `AIConfig.is_feature_enabled(...)` as the only predicate for "is
   this allowed?".
3. Build EgressRequests through `network.gated_request(...)` so the
   single-egress contract holds.
4. Stage outputs through `Staging` so undo and accept/reject are
   uniform across features.

---

*Maintained as part of the Sprint 1 fork bootstrap. Updated whenever
the substrate evolves. Last updated: 2026-04-26.*
