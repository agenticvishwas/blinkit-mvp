# Phase 5 — Stretch: Hybrid Entry (Post-MVP)

**Status:** not started. **Depends on:** [Phase 4](../phase-4-deploy/architecture.md) shipped and
live — this phase needs a real deployed agent to A/B against, it is not buildable in isolation.
**Sequenced deliberately after Phase 4**, not before: it's a UX experiment, not a blocker for
shipping the core MVP.
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

## Problem this phase solves

[`differentiation.md`](../../differentiation.md) §6 leaves an open question rather than a settled
one: the mockup assumes users will type a free-text occasion description, but Interview 3 (parent
repo, `part2.md`) asked for pre-built collections ("Study Night Essentials," "Movie Marathon Kit")
instead of a blank chat box — and the live production audit in `differentiation.md` §1-2 shows
Blinkit's own merchandising team already thinks in exactly that tile format (Gifting Corner, Party
With Friends). Phase 5 exists to test, not assume, whether a hybrid entry point converts better
than free text alone.

## Scope

In scope: adding occasion chips (seeded from real merchandising categories already observed in the
live audit — Gifting Corner, Party With Friends, and similar) as an alternative entry alongside the
existing free-text box on Screen 03, and a simple comparison of engagement between the two entry
modes.

Out of scope: anything that changes Phase 1's agent contract — chips are an *input* affordance
only; once a chip is tapped, it should resolve to the same occasion text pipeline
`agent.loop` already handles, not a separate code path.

## Design

Occasion chips are seeded only from categories with real precedent — either merchandising tiles
confirmed in the `differentiation.md` §1 live audit (Gifting Corner, Party With Friends) or
occasion language that actually appeared in interview transcripts (`part2.md`). No invented chip
categories, for the same evidence-grounding reason Phase 0 vendors real corpus data instead of a
fabricated catalog.

Chip tap behavior: selecting a chip populates the same free-text input Screen 03 already has (from
[Phase 2](../phase-2-ui-screens/architecture.md)) with the chip's associated occasion phrase, then
submits it through the existing `agent.loop` exactly as if the user had typed it. This keeps
Phase 1's tool contracts and guardrails untouched — chips are a UI convenience, not a new intent
path requiring its own testing surface.

## Build steps

1. Extract the confirmed merchandising categories from `differentiation.md` §1 (Gifting Corner,
   Party With Friends, Chocolates & Cakes, date-night) plus any additional occasion phrases from
   `part2.md` interviews not already covered, as the fixed chip set.
2. Add a chip row to Screen 03 above or alongside the free-text input, wired to populate-and-submit
   as described above.
3. Instrument both entry paths (chip tap vs. free-text submit) with a simple counter/log — this
   project has no production analytics stack, so a lightweight logged event (timestamp, entry
   mode, occasion text) written to a local log or a simple append-only file is sufficient; do not
   over-build this into a full analytics pipeline for a stretch phase.
4. Run an informal comparison after a period of real usage (or a moderated usability pass with
   people matching the Trust-Ready Explorer profile, per the same proxy-signal approach
   `part4-mvp-proposal.md` uses for the core MVP): which entry mode gets used more, and does either
   one correlate with higher rubric scores on the resulting collection (reusing
   [Phase 3](../phase-3-guardrails-eval/architecture.md)'s rubric).

## Exit criteria

- Chip row live on the deployed Screen 03, chips resolve through the unmodified `agent.loop`.
- At least an informal read on chip-tap vs. free-text usage share, documented (even qualitatively)
  rather than left as an unanswered open question.

## Risks specific to this phase

- **Treating a stretch result as validated fact:** given the small scale of usage this project can
  realistically generate, any chip-vs-free-text signal here is directional at best — do not
  overstate it as a settled finding the way `part4-mvp-proposal.md` is careful not to overstate the
  core MVP's own eval-rubric proxy signal.
- **Chip set going stale:** the chip set is seeded from a live audit taken on 2026-08-01
  (`differentiation.md` §1) — Blinkit's actual merchandising calendar rotates, so a chip set frozen
  at build time may reference categories no longer live in production; this is an acceptable
  known limitation for a stretch phase, not something to solve with a live-scraping dependency.
