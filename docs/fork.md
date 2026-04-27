# Plotwright — Fork Notes

Plotwright is a fork of [novelWriter](https://github.com/vkbo/novelWriter)
maintained by Veronica Berglyd Olsen and the novelWriter contributors. Both
projects are licensed under [GPL-3.0-or-later](../LICENSE.md). This document
records why the fork exists, how it relates to upstream, and how we intend
to keep it healthy over time.

## Why fork

novelWriter is, by deliberate design and policy, **AI-free**. It is one of
the cleanest plain-text long-form editors available, and that minimalism is
core to its identity. Plotwright takes a different position: we believe AI
assistance — done with a privacy-first, locally-runnable, opt-in posture —
materially helps a specific class of writer (genre-fiction plotters working
across many scenes and characters). We did not want to ask upstream to host
work that conflicts with their stated stance. So we forked.

The two projects share editor DNA but have *opposing positions on AI*. Both
positions are defensible; we owe upstream attribution and respect, not
disagreement.

## What's different in Plotwright

| Area | Upstream novelWriter | Plotwright |
|------|----------------------|------------|
| AI assistance | Out of scope by policy | Optional, off by default, network-zero unless enabled |
| Network behaviour | None outside update checks | None unless an AI feature is opted in *and* a provider is configured |
| Project shell | Tree + document + details | Asymmetric tree / manuscript / marginalia (Sprint 2+) |
| Privacy contract | Not codified | `network.py` single egress + CI static check + regression test |

Sprint 1 only covers the foundation: branding, AI substrate, MockProvider,
and the privacy regression test. Real AI features (inline rewrite,
consistency check) and the redesigned shell ship in Sprints 2–5.

## Upstream baseline and rebase policy

The current upstream baseline is recorded in
[`.fork-baseline.json`](../.fork-baseline.json). The pinned commit is
`10c8a186` (subject: "Merge release fixes into 26.2 Alpha 0"). It will be
promoted to a tag once upstream signs `26.2-alpha-0`.

Rebase policy: **scheduled quarterly**, performed as a merge (not a rebase
of the fork branch onto upstream). Branding deltas are re-applied after each
merge. Fork-specific paths are stable and listed in `.fork-baseline.json`:

- `novelwriter/ai/`
- `novelwriter/preferences/ai_panel.py`
- `novelwriter/gui/status_bar_ai.py`
- `tests/test_ai_*.py`
- `docs/ai/`
- `docs/fork.md`
- `DESIGN.md`
- `.fork-baseline.json`

## Privacy stance

We treat privacy as a hard product requirement, not a marketing item. The
contract is:

1. AI is **off by default** for every project, every install.
2. With AI off, the fork performs **zero outbound TCP/UDP traffic**. Tests
   enforce this (see [`docs/ai/privacy.md`](ai/privacy.md)).
3. The single egress point is `novelwriter/ai/network.py`. CI fails if any
   other module imports `httpx` or `requests`.
4. Cloud API keys live in the OS keychain when real cloud providers ship in
   Sprint 2; they are never written to disk in plaintext.
5. Per-project opt-in. Enabling AI in one project does not enable it in
   another.

If you find a way to bypass this contract, please open a security advisory
on the fork's repository before disclosing publicly.

## Attribution

Every editor, document-format, and project-tree improvement in this fork
originated upstream in novelWriter. Maintainer: Veronica Berglyd Olsen.
Contributors: see [`CREDITS.md`](../CREDITS.md). The AI substrate, fork
branding, plotter-focused redesign, and the privacy contract are
fork-specific work and are not the responsibility of the upstream
maintainer.

## Compatibility

Plotwright reads upstream novelWriter projects without schema changes. The
round-trip migration test (Sprint 5) will assert *zero diff* when an
upstream project is opened in Plotwright, saved, and reopened in upstream
novelWriter. Fork-specific metadata is namespaced so it cannot collide with
the upstream schema.

## Reporting issues

- Bugs and behaviour reports for the fork: open an issue on the Plotwright
  repository.
- Bugs in the upstream editor that are *not* introduced by the fork: please
  report them upstream at <https://github.com/vkbo/novelWriter/issues>. We
  will help triage if it isn't clear which side a regression came from.

---

*This document is updated whenever the upstream baseline shifts or the
fork's stance on AI changes. Last updated: Sprint 1, 2026-04-26.*
