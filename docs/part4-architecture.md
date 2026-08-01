# Part 4 Architecture: Occasion Concierge Agent

High-level system architecture and phase index for the AI agent chosen in
[`part4-mvp-proposal.md`](part4-mvp-proposal.md) (Option B), constrained by what's already locked
in [`differentiation.md`](differentiation.md) and the four screens already designed in
[`../design/mockup.html`](../design/mockup.html). Per [`part4.md`](part4.md) this must ship to
production, not stay a local demo.

**Where things stand:** design pass is done (mockup + differentiation write-up). Nothing has been
built yet. This repo (`blinkit-mvp`) is deliberately separate from the parent `NLGradProject` repo
that holds `discovery_engine/chat_app.py` and `corpus.jsonl` — so [Phase 0](phases/phase-0-data-foundation/architecture.md)
is about vendoring what's needed from that stack into this repo, not assuming it's already here.

Each phase below has its own detailed architecture doc — problem framing, data/interface
contracts, build steps, exit criteria, and phase-specific risks — in `phases/<phase>/architecture.md`.
This document stays the system-level overview and the sequencing map between them.

---

## System overview

**Revision (2026-08-01):** switched from a single Streamlit app to a React SPA + FastAPI split —
Streamlit's widget-based rendering couldn't hit the pixel parity `differentiation.md` §4 commits
to. See the revision notes in [Phase 2](phases/phase-2-ui-screens/architecture.md) and
[Phase 4](phases/phase-4-deploy/architecture.md) for the full reasoning.

```
┌───────────────────────────────┐        ┌─────────────────────────────────────┐
│ web/ — React SPA (static)     │        │ api/ — FastAPI (this repo)           │
│                                │  HTTP  │                                     │
│  Screen 01/02      Screen 03  │ ─────► │  POST /api/converse                  │
│  Home + entry ──►  Conversa-  │ ◄───── │      │                               │
│  (static)          tion (chat,│        │      ▼                               │
│                     ≤1        │        │  ┌──────────────────────┐           │
│                     clarifying│        │  │ Claude tool-use loop │           │
│                     Q)        │        │  │  retrieve_evidence() │──► sentence-│
│         │                     │        │  │  suggest_items()     │    transformers│
│         ▼                     │        │  │  build_collection()  │    cosine search│
│  Screen 04                    │        │  └──────────────────────┘    over corpus.jsonl│
│  Curated result (collection   │        └─────────────────────────────────────┘
│  cards: rating + review +     │                          │
│  "why this")                  │                          ▼
└───────────────────────────────┘             corpus.jsonl (588 items) + insights.json
                                               vendored from Part 1, read-only ground truth
```

`api/` is the only process that ever holds `ANTHROPIC_API_KEY`; `web/` is a static bundle with no
server-side secrets. The constraint from `differentiation.md` §4 governs everything above: Screens
01/02 stay pixel-identical to production except one added prompt card, and the agent never fires
inside a reorder-mode session.

---

## Phase index

| Phase | Folder | Goal | Depends on |
|---|---|---|---|
| 0 | [`phases/phase-0-data-foundation/`](phases/phase-0-data-foundation/architecture.md) | Vendor `corpus.jsonl` + `insights.json`; port the retrieval pattern into this repo, no runtime dependency on `NLGradProject` | — |
| 1 | [`phases/phase-1-agent-core/`](phases/phase-1-agent-core/architecture.md) | The three-tool Claude tool-use loop; system prompt encoding the three structural rules (≤1 clarifying question, never fabricate, stay occasion-scoped) | Phase 0 |
| 2 | [`phases/phase-2-ui-screens/`](phases/phase-2-ui-screens/architecture.md) | The four screens as a React/Vite SPA (`web/`), plus a thin FastAPI service (`api/`) wrapping the agent loop over HTTP | Phase 1 (screens 03/04 and `api/` only — 01/02 are static, parallelizable) |
| 3 | [`phases/phase-3-guardrails-eval/`](phases/phase-3-guardrails-eval/architecture.md) | Fixed eval set + rubric, automated fabrication check, automated reorder-redirect check, pre-deploy gate (runs in-process locally, over HTTP against the deployed API) | Phase 1 (doesn't need the UI) |
| 4 | [`phases/phase-4-deploy/`](phases/phase-4-deploy/architecture.md) | Ship `web/` (Vercel/Netlify) and `api/` (Render/Fly/Railway) as two services; post-deploy smoke test against both live URLs; update README status | Phases 1–3 complete |
| 5 | [`phases/phase-5-stretch-hybrid-entry/`](phases/phase-5-stretch-hybrid-entry/architecture.md) | Post-MVP: occasion chips (seeded from real merchandising categories) alongside free text, per the open question in `differentiation.md` §6 | Phase 4 live |

## Sequencing

Phase 0 blocks Phase 1 (no retrieval, no agent). Phase 1 blocks Phase 2 screens 03/04 (screens
01/02 can be built in parallel, they're static). Phase 3 can start as soon as Phase 1's agent loop
exists — it doesn't need the UI. Phase 4 requires Phases 1–3 complete. Phase 5 is explicitly
after Phase 4, not before.

```
Phase 0 ──► Phase 1 ──┬──► Phase 2 (screens 03/04) ──┐
                       │                               ├──► Phase 4 ──► Phase 5
         Phase 2       └──► Phase 3 ───────────────────┘
      (screens 01/02,
       parallel, static)
```
