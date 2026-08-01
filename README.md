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
- [`docs/part4-architecture.md`](docs/part4-architecture.md) — phase-wise build plan, with a
  detailed architecture doc per phase under [`docs/phases/`](docs/phases/).
- `agent/` — retrieval + the Claude tool-use loop (Phases 0–1), framework-agnostic.
- `api/` — thin FastAPI service wrapping `agent/` over HTTP (Phase 2 backend). The only process
  that holds `ANTHROPIC_API_KEY`.
- `web/` — React + Vite + TypeScript + Tailwind SPA (Phase 2 frontend), talks to `api/` only.
- `data/corpus.jsonl` — vendored, read-only Part 1 review corpus (588 tagged items). Real App
  Store / Play Store review text about the Blinkit *app* experience, not a per-product catalog —
  see `agent/retrieval.py`'s docstring for what that does and doesn't support.
- `tests/` — retrieval smoke test, API contract tests (mocked), and a live agent-loop test
  (skipped unless `ANTHROPIC_API_KEY` is set).

## Status

Built and verified locally end to end (agent loop, API, and SPA all running together, real
Claude API calls, real corpus-grounded evidence) and QA/PO-reviewed — see the review notes below.
Deploy configs are ready (`render.yaml`, `web/vercel.json`) but nothing is live yet: that step
needs hosting accounts (Vercel, Render/Fly/Railway) this session doesn't have access to. See
[`docs/phases/phase-4-deploy/architecture.md`](docs/phases/phase-4-deploy/architecture.md) for the
full deploy plan.

### Run it locally

```bash
# Backend (needs ANTHROPIC_API_KEY in the environment or a .env file, see .env.example)
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m uvicorn api.main:app --reload --port 8000

# Frontend, in a second terminal
cd web && npm install && npm run dev   # http://localhost:5173
```

### Tests

```bash
.venv/Scripts/python -m pytest tests/test_retrieval_smoke.py tests/test_api.py -v   # no API key needed
.venv/Scripts/python -m pytest tests/test_agent_loop.py -v -s                        # needs ANTHROPIC_API_KEY, real API calls
cd web && npm test                                                                    # Vitest + React Testing Library
```

### QA/PO review (2026-08-01)

A full pass against the real API and a real browser found and fixed: an unhandled 500 on blank
messages (now a clean 422), evidence quotes rendering as full untruncated reviews instead of
short snippets, and reorder+occasion mixed-intent messages (e.g. "add milk for my party") being
fully redirected instead of helped. All three have regression tests. Open items: no automated
frontend tests existed before this pass (now 11, covering the skip/undo and chip flows); H3's
reorder-redirect is prompt-enforced only, with no deterministic backstop like the fabrication
guard has.

## Why a separate repo

This is scoped to ship independently to production (Part 4 requirement), separate from the
research/discovery-engine work in the parent project.
