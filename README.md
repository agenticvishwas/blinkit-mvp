# blinkit-mvp

Part 4 deliverable: an AI-native MVP built on the problem definition and solution selection from
the parent grad project (`NLGradProject/docs/part3-problem-definition.md` and
`part4-mvp-proposal.md`).

**Chosen solution: Occasion Concierge** — a conversational agent that turns a stated occasion
("friends coming over tonight") into a curated, trust-signal-backed product collection, layered
onto the existing Blinkit home without touching the reorder flow (Buy Again, search, categories).

## Contents

- [`design/mockup.html`](design/mockup.html) — high-fidelity mobile mockup: baseline home →
  Concierge entry point → conversation → curated result, plus a differentiation table against
  the production app.
- [`docs/differentiation.md`](docs/differentiation.md) — the full write-up validating how this
  differs from what already ships, mapped back to the three hypotheses from Part 3.

## Status

Design pass complete. Not yet built — next step is scaffolding the actual agent (Claude tool-use
+ retrieval over the Part 1 review corpus), reusing the pattern already proven in
`NLGradProject/discovery_engine/chat_app.py`.

## Why a separate repo

This is scoped to ship independently to production (Part 4 requirement), separate from the
research/discovery-engine work in the parent project.
