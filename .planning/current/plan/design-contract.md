# Design Contract Scheduling — Sprint 2

## Status

Placeholder. The substantive design contract is produced by `/design-consultation`,
scheduled to run in parallel with WS-1 finish (days 1-7 of Sprint 2). This file
captures the scope and inputs that `/design-consultation` will consume, and the
expected output structure.

> **NOTE:** All component-spec details below are FRAME-STAGE INPUTS (harvested from
> `s2-scope.md` and `design-intent.json`), not locked design decisions.
> `/design-consultation` may revise any of them. The only locked rules
> (per `DESIGN.md` "Two Locked Risk Decisions") are:
>
> 1. Vermilion `#9B2C2C` reserved exclusively for AI-touched regions
> 2. Cream paper default (Cotton `#F4EFE6` / Ink `#1C1B17`)
> 3. AI as marginalia, never chat sidebar, never sparkle/wand button
>
> Everything else (typography sizes, exact spacing, motion timing, copy) is open
> for `/design-consultation` to resolve.

## Scope: three component specs needed

Sprint 2 introduces three net-new component categories not yet in DESIGN.md:

### 1. Four-tab top-level IA (tab-bar component)

What needs spec'ing:
- Tab bar visual: spacing, divider, active-state indicator (Hooker's Green 2px underline per agent guidance)
- Type: tab label font, weight, size (likely IBM Plex Sans 13/500 per existing button spec)
- Keyboard nav: Cmd/Ctrl+1..4 shortcuts; arrow-key navigation within bar
- Focus indicator
- Three-column geometry: tree (200-240px) | manuscript (60ch) | rail (280-320px)
- Tab dispatch logic: what content lives in each tab (Outline, Manuscript, Notes, AI)

### 2. Marginalia-rail empty-state component

What needs spec'ing:
- Empty rail visual (S2 state), width, background, what (if anything) appears
- "EDITOR'S NOTES" kind line styling (Foxing, NOT vermilion, IBM Plex Mono 10px uppercase per existing Marginalia entry spec)
- Empty body copy: "No notes yet. When you ask the AI to review a passage, its observations land here as marginalia, alongside the manuscript, never on top of it."
- Caption copy: "Inline rewrite arrives in the next release. Consistency check follows."
- Layout: left-aligned (DESIGN.md anti-slop: "No centered everything")
- Future state: how rail looks when populated (deferred to S3, just sketch the layout)

### 3. Auth-flow state machine component (OAuth)

What needs spec'ing:
- Idle (signed out): radio group + "Sign in with Google" Secondary button + helper copy
- Pending: button transforms to "Waiting for browser..." + thin Hooker's Green 1px progress strip (no spinner per DESIGN.md motion); Cancel tertiary action
- Error: button reverts; helper text becomes Error `#7A2222`; three sub-cases (network error, user cancelled, auth failed)
- Signed in: row with Hooker's Green dot + email (IBM Plex Mono Foxing) + "Sign out" Secondary button
- **Vermilion does NOT appear in any OAuth state** (vermilion = AI-touched regions only)
- Plain text "Sign in with Google", no Google branded button artwork

## Inputs to `/design-consultation`

- `DESIGN.md` (current state)
- `docs/product/decision-brief.md` "Sprint 2 boundary" section
- `docs/product/idea-brief.md` open questions #6 (AI tab placeholder) and #10 (WS-4 depth)
- `.planning/current/frame/design-intent.json`
- `.planning/current/frame/s2-scope.md` "Project shell IA + marginalia rail primitive" section
- `novelwriter/ai/preferences_panel.py` (S1 panel, extends in S2)
- `novelwriter/gui/status_bar_ai.py` (S1 widget, extends in S2)

## Expected output

After `/design-consultation` runs, this file is replaced with substantive design
contract content. The replacement should include:

- Updated DESIGN.md with the three new component sections
- Wireframes or ASCII layouts for each component state
- Token usage table (per component, which DESIGN.md color/type/spacing tokens are used)
- A11y notes per component
- Motion specifications (animations, transitions, durations)
- Anti-slop confirmations (vermilion-only-for-AI, no chat affordance, no sparkle, no spinner)

## Schedule and dependency

- **Start:** day 1 of Sprint 2 (in parallel with WS-1 substrate work)
- **Target completion:** day 7 of Sprint 2
- **Slip indicator (per sprint-contract):** if `.planning/current/plan/design-contract.md`
  is still this placeholder text at end of day 7, escalate. `/design-consultation`
  blocks `/handoff` per v1 packet transition rule
- **Critical path:** the design contract is the gate for `/handoff`. Without it, the
  build cannot start.

## Accessibility expectations

The `/design-consultation` must address:
- Keyboard reachability for all OAuth flow states (Sign in button, Cancel, Sign out)
- Tab order for the new four-tab IA
- Focus ring color and width
- Color contrast check on Foxing-on-Cotton (Design agent flagged this as borderline 4.2:1 AA at body text size)
- `accessibleName` requirements for new Qt widgets

## Transition rule

`.planning/current/plan/design-contract.md` advances from "scheduling placeholder" to
"substantive contract" when `/design-consultation` completes. `/handoff` gate REQUIRES
the substantive contract, not the placeholder. Detection: this file's line count
exceeds 200 OR a section header `## DESIGN.md Component Amendments` exists.
