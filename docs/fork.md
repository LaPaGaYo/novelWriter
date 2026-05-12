# Fork: plotwright

This document records why `plotwright` exists, what it changes, and how it relates to
upstream `novelWriter`.

## Status

- **Type:** private GPL-3 fork
- **Upstream:** [vkbo/novelWriter](https://github.com/vkbo/novelWriter) by Veronica Berglyd Olsen
- **Pinned baseline:** see `.fork-baseline.json` at the repo root
- **Working name:** `plotwright` (subject to a final naming pass before public release)
- **Audience:** genre-fiction plotters (novelists who outline before drafting)
- **Not seeking upstream merge.** This fork's positioning is incompatible with upstream's
  stated stance, and we respect that boundary.

## Why a fork?

Upstream's `README.md` includes the line:

> _This project is developed with care, and is 100% free of AI slop._

We agree with the *spirit* of that line. We also believe it forecloses a useful version
of the product: AI as **editor**, not AI as **author**. `plotwright` takes the opposite
position with great care:

- The two MVP AI features (**inline rewrite** of text the user wrote, and **consistency
  check** against the user's own project notes) only operate on user-authored content.
- The AI is rendered as **marginalia** in the editor (vermilion underlines + right-side
  rail of editor's notes), never as a chat sidebar, never with sparkle/wand iconography.
  The visual language is editorial review, not pair programming.
- Privacy is the default: every AI feature is off out of the box, opt-in per feature per
  project. With AI off, network traffic out of the app is zero. This is enforced by a
  CI regression test (`tests/test_ai/test_privacy.py`).

This is, deliberately, a *craft tool* that uses AI rather than an *AI product*.

## Differences from upstream

### Visual identity

- Branding deliberately differs from upstream so installs don't collide on the same
  machine. Different application name (`plotwright`), different default user-data
  directory, different About dialog, eventually a different icon set.
- New design system: see `DESIGN.md` ("Manuscript" — Cartographic Modernism). Upstream's
  visual language is preserved as a code reference but not as a target.

### Code surfaces

Fork-specific code is concentrated in three areas to minimize merge conflicts when
syncing with upstream:

- `novelwriter/ai/` — the AI substrate (provider abstraction, privacy gating, feature
  modules)
- `tests/test_ai/` — fork-specific test suite
- `docs/ai/` — fork-specific documentation

Shared files (notably `__init__.py`, `config.py`, `gui/statusbar.py`, `dialogs/preferences.py`,
`README.md`, `CREDITS.md`, `pyproject.toml`) carry small additive patches that should be
straightforward to rebase against upstream changes.

### Distribution

- New PyPI distribution name (`plotwright`). The Python package directory remains
  `novelwriter/` to avoid hundreds of import-rewrite ripples through the codebase.
- New console entry point (`plotwright`). Upstream's `novelwriter` entry point is
  retired in this fork.

## Upstream credit and respect

- All upstream copyright headers, license texts, and contributor credits are preserved.
- `CREDITS.md` records the fork status and points to upstream.
- We do not use the `novelWriter` name in fork branding.
- We do not compete with upstream in upstream's own distribution channels (the upstream
  PyPI project, novelwriter.io, the upstream PPA, etc.).
- Bug reports for behaviors inherited from upstream go upstream first when the fix would
  be useful to all users; fork-specific reports stay in the fork.

## Sync policy

See `.fork-baseline.json` for the pinned upstream commit and the rebase strategy. In
short: we merge upstream `main` into the fork quarterly, and we pin to a tagged upstream
release before each fork `v*` release. Fork-specific files were chosen to minimize
conflicts during these merges.

## How to switch back to upstream

If `plotwright` doesn't fit your workflow:

```bash
pip uninstall plotwright
pip install novelWriter
```

Your existing project files are forward and backward compatible (`plotwright` reads
upstream projects without modification, and round-trips them cleanly back to upstream
because fork-only metadata is kept under a clearly-namespaced extension that upstream
ignores). The default user-data directory is different, so neither install touches the
other's preferences.
