# AI Privacy

This document is the user-facing privacy promise for the plotwright fork's AI
features. It is also the contract the implementation is held to in CI.

## The promise (in one sentence)

**Every AI feature is off by default. With AI off, the app makes no outbound
network calls. You opt in per feature, per project, every time.**

## What "off" means

When `AIConfig.enabled` is False:

- No prompt leaves your machine.
- No metadata about your project leaves your machine.
- No telemetry leaves your machine.
- No outbound TCP/UDP connection is opened from inside `novelwriter.ai.*`.

This is enforced by `tests/test_ai/test_privacy.py`, which monkey-patches
`socket.socket.connect` to a fail-loud sentinel and runs the substrate's
surface with the master switch off. The test is part of the CI gate for
every change to the AI substrate.

## What "on" means

When `AIConfig.enabled` is True AND a feature flag is True:

- That feature is permitted to make a call to the provider you configured for it.
- The call goes to your selected provider only — local Ollama if local, or the
  cloud BYO-API-key endpoint you set.
- A token-count estimate is shown before any cloud call, so you know what the
  call will cost before it happens. (Sprint 2.)
- Nothing else can make a call. Other features remain individually gated.

## Per-project, not user-global

Opt-in is recorded inside each project (in an `ai-config.json` file in the
project directory), not in your user-global preferences. Turning on the
rewrite feature for one project does not turn it on for any other.

## What gets logged where

- **Default:** nothing. No prompts, no responses, no metadata.
- **If you enable the project-local debug log:** every outbound call records
  endpoint hostname and byte counts (no body content) to a file inside the
  project directory. The debug log is gitignored by default and is the only
  place AI-related metadata lands on disk.

## Cloud API keys

- API keys for cloud providers are stored in your OS keychain (macOS Keychain,
  Windows Credential Manager, libsecret on Linux). Sprint 2 wires this up.
- API keys are NEVER written to disk in plaintext, NEVER printed in logs,
  NEVER included in a project file.
- A static check verifies key strings don't leak via grep across the repo
  during development.

## Local providers

If you configure a local provider (e.g. Ollama with `llama3.1-8b`):

- No outbound TCP traffic leaves your machine for that feature's calls.
- The "AI: ready" indicator shows the local provider's name to make the local
  status visible at a glance.
- The privacy regression test still runs with local providers in scope, so
  even a misconfigured local backend can't accidentally fall through to a
  cloud call.

## Indicators in the UI

The status bar AI indicator is **always visible**. You can never be uncertain
whether AI is on. The states:

- `AI: off` (Foxing color) — master switch is False.
- `AI: ready (provider name)` (Hooker's Green dot) — master switch True; the
  named provider is selected.
- `AI: working...` (Vermilion dot) — a call is in flight. Sprint 2.

Vermilion is reserved app-wide for AI-touched regions, so seeing it lets you
know unambiguously that AI is doing something *right now*.

## What we will not do

- Aggregate user prompts to train a model. We don't host any model and don't
  proxy your requests through our servers.
- Run a server. The fork is desktop-only.
- Phone home for telemetry, analytics, or "anonymous usage stats."
- Auto-update the application's AI prompts based on a remote source. Prompts
  ship with the binary and only change when you update the app.
- Default any AI feature to on after an upgrade. Defaults stay off; existing
  user opt-ins persist across upgrades.

## Reporting a privacy concern

If you believe an AI-related code path violates this contract:

1. File an issue in the fork repository titled `[privacy]: ...`.
2. If you have a reproduction, attach packet capture or a `socket.connect`
   sentinel test that demonstrates the leak.
3. Privacy bugs are highest priority and block any open release.
