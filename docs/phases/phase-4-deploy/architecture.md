# Phase 4 — Deploy to Production

**Status:** not started. **Depends on:** [Phase 1](../phase-1-agent-core/architecture.md),
[Phase 2](../phase-2-ui-screens/architecture.md), [Phase 3](../phase-3-guardrails-eval/architecture.md)
all complete. **Blocks:** [Phase 5](../phase-5-stretch-hybrid-entry/architecture.md).
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

**Revision (2026-08-01):** originally scoped as a single Streamlit Community Cloud deploy. Since
[Phase 2](../phase-2-ui-screens/architecture.md) switched to a React SPA + FastAPI split, this
phase now ships **two independently deployed services** instead of one app, which changes secrets
handling, CORS, and the post-deploy smoke test.

## Problem this phase solves

[`part4.md`](../../part4.md) states the requirement plainly: "You need to deploy this MVP to
production." Everything through Phase 3 can be fully correct and still not satisfy Part 4 if it
never leaves a local machine. This phase closes that gap, and is also the phase that turns
Phase 3's guardrails from "checks that exist" into "checks that actually gate what ships."

## Scope

In scope: choosing and executing the deploy path for both services, secrets handling, CORS
configuration between them, a post-deploy smoke test that re-runs Phase 3's checks against the
*live* API (not just local), and updating the repo's status docs to reflect reality.

Out of scope: any further feature work — this phase ships what Phases 1–3 already built, it does
not add scope.

## Deploy targets

| Service | What it is | Target | Holds `ANTHROPIC_API_KEY`? |
|---|---|---|---|
| `web/` | Static Vite/React build | Vercel or Netlify | No |
| `api/` | FastAPI wrapping Phase 1's agent loop | Render, Fly.io, or Railway | Yes |

Two services instead of Streamlit's one app-server model, because the frontend is now a static
bundle with no Python runtime, and the backend is the only place `ANTHROPIC_API_KEY` and
`agent.loop` are allowed to run (see [Phase 2](../phase-2-ui-screens/architecture.md)'s note on why
that split exists — the key must never reach the browser).

## Secrets and CORS

- `ANTHROPIC_API_KEY` goes into the `api/` host's secrets manager (Render/Fly/Railway env vars),
  never committed, never sent to the frontend build.
- `api/main.py`'s CORS `allow_origins` must be set to the exact deployed `web/` origin, not `*` —
  this is a hard requirement carried over from Phase 2, not optional hardening.
- `web/`'s build needs one non-secret env var: the deployed API's base URL (e.g.
  `VITE_API_BASE_URL`), consumed by `web/src/api/client.ts`.
- **Deploy ordering to avoid a chicken-and-egg CORS gap:** deploy `api/` first with a placeholder
  or wildcard-free but temporary CORS origin, deploy `web/` second now that the API's real URL is
  known, then immediately update `api/`'s CORS origin to the frontend's real URL and redeploy the
  backend once. Do not leave CORS open during this gap longer than necessary.

## Build steps

1. Add `api/requirements.txt` (fastapi, uvicorn, the embedding/Claude SDK deps from Phases 0–1)
   and `web/package.json`'s build script (`vite build`).
2. Run [Phase 3](../phase-3-guardrails-eval/architecture.md)'s `scripts/pre_deploy_gate.py`
   locally, against the local `agent.loop`, immediately before deploying `api/` — nothing with a
   known fabrication or redirect failure should ship.
3. Deploy `api/` to the chosen host; set `ANTHROPIC_API_KEY`.
4. Deploy `web/` to the chosen host; set `VITE_API_BASE_URL` to the `api/` deployment's URL.
5. Update `api/`'s CORS `allow_origins` to the real `web/` URL and redeploy `api/` once more.
6. Post-deploy smoke test, two parts:
   - Re-run Phase 3's eval prompt set as raw HTTP calls against the **live** `/api/converse`
     endpoint (not local) — a deploy can succeed while still misbehaving due to environment
     differences (missing secret, dependency version drift), so the local pre-deploy gate passing
     is necessary but not sufficient.
   - Load the live `web/` URL in a browser and walk Screen 01 → 04 once, confirming the
     cross-origin call to `api/` actually succeeds (this is the check that catches a CORS
     misconfiguration the HTTP-only smoke test above wouldn't).
7. Update [`../../../README.md`](../../../README.md) §"Status" from "Design pass complete. Not yet
   built" to both live URLs plus a short usage note.

## Exit criteria

- Both URLs (`web/`, `api/`) are live and reachable.
- Phase 3's eval prompt set, re-run as HTTP calls against the live `api/` URL, passes at the same
  standard it passed locally.
- A manual walkthrough of the live `web/` URL completes Screen 01 → 04 with a real cross-origin API
  call succeeding.
- `README.md` reflects reality: both live URLs present, "Not yet built" language removed.

## Risks specific to this phase

- **Two services to keep in sync instead of one:** an API contract change now requires
  redeploying both `web/` and `api/` in the right order, versus Streamlit's single-deploy model —
  a partial deploy (only one side updated) is a new failure mode this split introduces.
- **CORS misconfiguration:** either too permissive (security risk, see Phase 2) or too restrictive
  (frontend silently fails every request with no visible error unless the browser console is
  checked) — the manual browser walkthrough in step 6 is what catches the latter.
- **Free-tier cold starts:** Render/Fly/Railway free tiers commonly sleep an idle backend after a
  period of inactivity, adding several seconds of latency to the first request after idle time —
  acceptable for a student-project demo, but worth a one-line warning in the README so a first-time
  visitor doesn't assume the demo is broken.
- **Silent cost/rate-limit exposure:** a public API calling the Claude API on every conversation
  turn has no built-in request ceiling — decide before going live whether a basic rate limit or
  usage cap is needed, given this is a student project without production-grade infra to absorb
  unexpected traffic.
