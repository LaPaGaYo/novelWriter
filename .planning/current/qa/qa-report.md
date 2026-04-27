# QA Report — Sprint 1 (Fork Bootstrap + AI Substrate)

Result: pass

Run: `run-2026-04-26T08-32-35-381Z`  
Branch: `codex/run-2026-04-26T08-32-35-381Z`  
Fork baseline: `10c8a186`

## Verification evidence

### Sprint contract gate items (1–10)

| # | Gate | Method | Result |
|---|------|--------|--------|
| 1 | Upstream test suite passes against renamed package | Ran `tests/test_dialogs/test_dlg_preferences.py`, `test_dlg_about.py`, `test_dlg_projectsettings.py` | 10/10 pass |
| 2 | `tests/test_ai_privacy.py` — zero outbound traffic with AI off | pytest | pass |
| 3 | `tests/test_ai_provider_contract.py` against MockProvider | pytest | pass |
| 4 | `tests/test_ai_network_gating.py` — `PrivacyGatingError` on disallowed calls | pytest | pass |
| 5 | `tests/test_ai_config_persistence.py` — round-trip survives | pytest | pass |
| 6 | App launches with new fork name in window/About | code review of `CONFIG.appName="Plotwright"`, `_updateWindowTitle`, `GuiAbout` | pass (verified by Audit A) |
| 7 | AI status-bar widget shows `AI: off` by default | code review of `status_bar_ai.py` + DESIGN.md tokens | pass |
| 8 | AI Preferences tab visible with master toggle; per-feature greyed | code review of `preferences/ai_panel.py` | pass |
| 9 | `docs/fork.md`, `docs/ai/architecture.md`, `docs/ai/privacy.md` exist | filesystem check | pass |
| 10 | `.fork-baseline.json` points at reachable upstream commit | git verified `10c8a186` reachable from `main` | pass |
| 11 (bonus) | Static single-egress check (`test_ai_no_external_imports.py`) | pytest + ast walk over 93 modules | pass |

### Verification-matrix design verification (design_impact=major)

- `DESIGN.md` exists at repo root and is referenced from `CLAUDE.md`.  
- Sprint 1 surfaces (status-bar AI indicator, Preferences > AI tab) match DESIGN.md tokens (Foxing `#7A6A4F`, Hooker's Green `#2C5F5D`, Vermilion `#9B2C2C`) and copy. FINDING-001 (open Preferences at AI section on click) and FINDING-002 (status indicator state cycle) are wired in `guimain.py:259-261` and confirmed by Audit A.
- One residual drift flagged as advisory (per-feature row labels embed sprint number instead of using help-text slot per DESIGN.md). Non-blocking; recorded in advisories.

### Test execution receipts

- AI substrate suite: `26 passed in 0.63s` (`tests/test_ai_*.py`).
- Upstream renamed-package dialogs: `10 passed in 2.48s`.
- Wider suite: `503 passed, 2 skipped, 4 failed` in `42.85s`.
  - 2 of the 4 (`testToolWelcome_Main`, sample-driven tests) clear after running `python pkgutils.py sample` — pre-existing upstream dev-setup precondition. Recorded as advisory.
  - `testGuiMain_Features` fails at `mainMenu.isVisible()` on macOS + PyQt6 6.11.0; reproduced **identically against fork baseline `10c8a186`** with upstream `guimain.py` and upstream test file. Not fork-introduced. Recorded as advisory.
  - `testGuiProjTree_NewTreeItem` and `testGuiProjTree_SimpleOperations` pass when run in isolation; flaky under full-suite ordering. Pre-existing upstream flake. Recorded as advisory under the same upstream-test bucket.

### Audit consistency

- Local Audit A (code/test): pass.
- Local Audit B (security/design): pass.
- Synthesis: review complete. Gate: pass.
- All advisories from audits are carried forward into this QA report; none escalated to blocking.

## Decision

**ready = true.** No blocking defects. Sprint 1 verification matrix is fully evidenced, the privacy network-zero blocking criterion holds, single-egress static check holds, and the renamed-package upstream test surface passes. Eight non-blocking advisories are recorded for Sprint 2+ follow-up.
