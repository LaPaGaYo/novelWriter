
## Nexus Skill Routing

When the user's request matches a canonical Nexus command, invoke that command first.
This guidance helps command discovery only.
Contracts, transitions, governed artifacts, and lifecycle truth are owned by `lib/nexus/`
and canonical `.planning/` artifacts.

Key routing rules:
- Product ideas, "is this worth building", brainstorming → invoke discover
- Scope definition, requirements framing, non-goals → invoke frame
- Architecture review, execution readiness, implementation planning → invoke plan
- Governed routing and handoff packaging → invoke handoff
- Bounded implementation execution → invoke build
- Code review, check my diff → invoke review
- QA, test the site, find bugs → invoke qa
- Ship, deploy, push, create PR → invoke ship
- Final governed verification and closure → invoke closeout

## Design System

Always read `DESIGN.md` at the repo root before making any visual or UI decision.
It defines the system-level rules for typography, color, spacing, layout, motion, and
component conventions for the Manuscript design system. Two locked decisions to never
silently override:

1. **AI as marginalia, not chat.** AI output appears as vermilion editorial markup in
   the manuscript and as editor's notes in a right-side marginalia rail. Never as a
   chat sidebar, never as a sparkle/wand button.
2. **Manuscript theme is canonical.** The app opens to cream paper on dark ink by
   default. Dark mode is secondary, not a peer.

Vermilion (`#9B2C2C`) is reserved exclusively for AI-touched regions. Do not use it for
errors, warnings, or any non-AI semantic.

In QA mode, flag any code that doesn't match `DESIGN.md`. When `brand-spec.md` later
exists, treat it as the frozen source of truth for logos, brand assets, and approved
palette constraints.
