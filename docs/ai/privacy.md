# AI Privacy — What Plotwright Promises and How It's Enforced

Plotwright integrates optional AI assistance. We treat privacy as a hard
product requirement, not a marketing line. This document is the
human-readable form of the contract; the machine-readable form lives in
`novelwriter/ai/network.py` and the test suite.

## TL;DR

- AI is **off by default**. Every install. Every project. Every time.
- With AI off, Plotwright performs **zero outbound TCP/UDP traffic** —
  same network behaviour as upstream novelWriter.
- Enabling AI is a deliberate, per-project, two-step decision.
- All real network calls route through one file. Everything else is
  prevented from importing `httpx` or `requests` at all.
- Cloud API keys live in the OS keychain (Sprint 2) and are never
  written to disk in plaintext.

## The default posture

A freshly opened project has:

- `AIConfig.enabled = False`
- `AIConfig.feature_flags = {rewrite: False, consistency: False}`
- `AIConfig.feature_providers = {rewrite: "mock", consistency: "mock"}`

The `is_feature_enabled(feature)` predicate returns `True` only when
**both** the master toggle and the per-feature flag are on. Every AI
feature uses this single predicate as its gate.

## What it takes to enable AI for a project

1. Open Preferences > AI.
2. Turn on the master toggle ("Enable AI features").
3. (Sprint 2+) Pick a provider and supply the credential or local URL.
4. (Sprint 2+) Turn on the specific feature you want (Inline rewrite,
   Consistency check).

Step 1 alone produces no network traffic. Steps 2–3 are needed before
any real call can be made. Step 4 is the per-feature opt-in that
distinguishes "I'm OK with rewrite" from "I'm OK with consistency
check".

## What is logged, where, and why

| Surface | Logged? | Where | Notes |
|---------|---------|-------|-------|
| Request body (your text) | **No** | — | The privacy gate never reads it. |
| Endpoint URL | Yes | Process log when AI is enabled | Metadata only. |
| Byte count | Yes | Process log when AI is enabled | For local debugging of token use. |
| Feature name | Yes | Process log | Distinguishes rewrite from consistency calls. |
| Cloud API keys | Never logged | OS keychain (Sprint 2) | Never on disk in plaintext. |
| Provider responses | **No** | — | Returned to staging/editor in memory only. |

The privacy log is process-local. It goes to the standard Python
logging machinery and is never sent anywhere by Plotwright itself.

## How the contract is enforced

Three independent mechanisms enforce the contract. Each one is
sufficient on its own; together they form a defence-in-depth posture.

### 1. The privacy gate (`novelwriter/ai/network.py`)

`gated_request(config, request)` raises `PrivacyGatingError` *before*
any I/O is attempted, unless **all** of these are true at the moment of
the call:

1. `config.enabled is True`
2. `config.feature_flags[request.feature] is True`
3. `request.endpoint` is non-empty
4. `request.has_credential` is `True`

Catching this error in calling code is allowed only for surface-level
UX feedback — never to retry the call without flipping the gate first.

### 2. The single-egress static check
(`tests/test_ai_no_external_imports.py`)

Walks every Python module under `novelwriter/` with `ast` and asserts
no module other than `novelwriter/ai/network.py` imports `httpx` or
`requests`. CI fails on any violation. This makes "just bypass the
gate" mechanically impossible — you can't even import the transport
library outside the gate file.

### 3. The privacy regression test
(`tests/test_ai_privacy.py`)

Monkeypatches `socket.socket.connect`, `socket.create_connection`, and
`socket.getaddrinfo` with tripwires. Exercises the AI substrate
(import, default config, mock provider, config round-trip, gate
evaluation) with AI off. Any tripwire firing is a fatal failure.

This is the **hard gate** of Sprint 1 — failure here blocks the sprint
even if every other test passes.

## Differences from upstream novelWriter

Upstream novelWriter is AI-free by design. With AI off, Plotwright
behaves identically to upstream from a network perspective: no AI
modules talk to the outside world, and the rest of the app retains
upstream's network behaviour (which is to say, near-zero).

When AI is on, only the modules under `novelwriter/ai/` and only the
`network.py` egress point are involved in real network traffic. The
editor, project tree, document loader, and exporters are untouched.

## What this contract does NOT cover

- Operating system telemetry (Qt, the Python interpreter, the OS
  itself). Out of scope.
- Update checks. Plotwright does not currently perform them; if and
  when it does, they will be off by default and surfaced in
  Preferences.
- Crash reports. None today; future work will be opt-in.

## Bug reports

If you find a way to make the AI substrate produce traffic with AI off,
or to bypass the gate, please open a security advisory on the fork's
repository before disclosing publicly. This contract is foundational —
we treat regressions against it as P0.

---

*Maintained as part of the Sprint 1 fork bootstrap. Last updated:
2026-04-26.*
