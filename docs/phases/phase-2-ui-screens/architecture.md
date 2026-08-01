# Phase 2 — Frontend SPA + API Layer

**Status:** not started. **Depends on:** [Phase 1](../phase-1-agent-core/architecture.md) for the
`/api/converse` endpoint and screens 03/04 (screens 01/02 are static and can be built in parallel).
**Blocks:** [Phase 3](../phase-3-guardrails-eval/architecture.md) end-to-end checks, [Phase 4](../phase-4-deploy/architecture.md).
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

**Revision (2026-08-01):** originally scoped as a single Streamlit app. Switched to a React SPA
because Streamlit's widget-based rendering can't hit the pixel parity
[`differentiation.md`](../../differentiation.md) §4 commits to for Screens 01/02 — a coral card,
chat bubbles, and a mobile tab bar need real CSS control. This phase now produces **two**
deployables: a static SPA and a thin API wrapping [Phase 1](../phase-1-agent-core/architecture.md)'s
agent loop, which did not exist as a separate concern under the Streamlit design (Streamlit could
import `agent.loop` in-process; a browser SPA cannot).

## Problem this phase solves

Same claim as before the revision: [`differentiation.md`](../../differentiation.md) §4 states
Screens 01/02 are pixel-identical to the live production app except one added prompt card, and the
Concierge never interrupts a reorder-mode session. This phase's job is to build exactly what
[`../../../design/mockup.html`](../../../design/mockup.html) already specified — now as real,
componentized, pixel-controlled UI instead of a data-app framework's approximation of it — wired to
real Phase 1 output instead of mockup placeholder text.

## Scope

In scope: a Vite + React + TypeScript SPA implementing the four screens, a thin FastAPI service
exposing [Phase 1](../phase-1-agent-core/architecture.md)'s agent loop over HTTP, and the contract
between them.

Out of scope: the eval harness that verifies output against the corpus
([Phase 3](../phase-3-guardrails-eval/architecture.md)), deployment itself
([Phase 4](../phase-4-deploy/architecture.md)).

**Why Vite + React over Next.js:** this is a pure client-rendered app with no SEO or
server-rendering requirement — a "full SPA" per the direction chosen — so Vite's plain
build-a-static-bundle model is less tooling than a hybrid meta-framework needs to carry. **Why a
separate FastAPI service over, say, embedding Python in the frontend:** Phase 1's agent loop and
its `ANTHROPIC_API_KEY` must never run in the browser — the key would be exposed to anyone who
opens dev tools.

## Repo layout produced by this phase

```
blinkit-mvp/
  agent/                        # from Phase 0 + Phase 1, untouched by this phase
    retrieval.py
    tools.py
    loop.py
    prompts.py
  api/
    main.py                       # FastAPI app: CORS config, /api/converse route
    schemas.py                     # pydantic models mirroring Phase 1's dataclasses
  web/
    index.html
    package.json
    vite.config.ts
    tailwind.config.ts              # coral palette + spacing tokens ported from mockup.html
    src/
      main.tsx
      screens/
        Home.tsx                    # Screen 01
        Entry.tsx                    # Screen 02
        Conversation.tsx              # Screen 03
        Result.tsx                     # Screen 04
      components/
        PromptCard.tsx
        ChatBubble.tsx
        CollectionCard.tsx
      state/
        ConciergeContext.tsx           # React Context + useReducer
      api/
        client.ts                       # fetch wrapper calling /api/converse
  tests/
    test_api.py                        # this phase: API contract tests
```

`api/` and `web/` do not exist yet — both are created fresh by this phase. `agent/` already exists
from Phases 0–1 and is consumed, not modified, here.

## API contract (`api/main.py`)

The SPA is stateless on the server side by design — no session store, no database. Each request
carries the full conversation so far; the backend has nothing to remember between calls. This
matches the project's "no production-grade infra" scope constraint and avoids needing to solve
session persistence for a demo-scale MVP.

```
POST /api/converse
Request:
  { "message": string, "chat_history": ChatTurn[] }

Response (one of):
  { "type": "clarifying_question", "question": string }
  { "type": "collection", "collection": Collection }        # Phase 1's Collection dataclass
  { "type": "redirect", "message": string }                  # reorder-mode request, H3 guarantee
```

`schemas.py` pydantic models must mirror Phase 1's `Evidence` / `CandidateItem` / `Collection` /
`CollectionCardItem` dataclasses field-for-field. There is no shared codegen between the Python
dataclasses and the TypeScript types on the frontend at this project's scale — keeping
`schemas.py` and `web/src/state/ConciergeContext.tsx`'s types in sync is a manual discipline, not
an automated guarantee (see Risks).

CORS: `api/main.py` must restrict `allow_origins` to the frontend's actual deployed origin, never
`*` — an open CORS policy on an endpoint that spends a real `ANTHROPIC_API_KEY` per call is an
easy way to let unrelated sites burn the key through a user's browser.

## Frontend state

```ts
interface ConciergeState {
  screen: "home" | "entry" | "conversation" | "result";
  chatHistory: ChatTurn[];
  clarifyingQuestionPending: boolean;
  collection: Collection | null;
}
```

Same shape as the Streamlit-era `ConciergeState`, now held in a React Context + `useReducer`
instead of `st.session_state` — the state machine itself didn't change with the framework switch,
only where it lives.

## Screen-by-screen detail

Build order matches the mockup's own sequencing; each screen is gated on the previous being wired
to real data, not mocked, before moving on.

### Screen 01 — Home (`Home.tsx`, static)

No API calls. Port the markup and CSS from `design/mockup.html` directly into JSX + Tailwind
classes (or scoped CSS ported near-verbatim) — this is the screen the pixel-parity claim depends
on, so treat the mockup as the literal spec, not inspiration. Screenshot it and diff against
[`../../../assets/WhatsApp Image 2026-08-01 at 2.51.11 PM.jpeg`](../../../assets/WhatsApp%20Image%202026-08-01%20at%202.51.11%20PM.jpeg),
the real production screenshot cited in `differentiation.md` §1.

### Screen 02 — Entry (`Entry.tsx`, static + one prompt card)

Screen 01 plus the single coral `PromptCard.tsx` slotted below search, per `design/mockup.html`
("One coral prompt card slotted below search... nothing existing was touched to add this").
Clicking it dispatches `screen: "conversation"`. No API call on this screen — pure navigation.

### Screen 03 — Conversation (`Conversation.tsx`)

First screen that calls `POST /api/converse` via `api/client.ts`. Each user message is sent with
the current `chatHistory`; the response is either:
- `clarifying_question` → append to `chatHistory`, set `clarifyingQuestionPending = true`, stay on
  this screen, or
- `collection` → store in `state.collection`, dispatch `screen: "result"`, or
- `redirect` → render the redirect message inline, stay on this screen (this is the visible,
  by-eye check for Phase 1's H3 guarantee).

If a `clarifying_question` response arrives while `clarifyingQuestionPending` is already `true`,
that's a Phase 1 prompt regression, not something this screen should silently absorb — surface it
(console warning at minimum) rather than just rendering a second question as if it were normal.

### Screen 04 — Curated result (`Result.tsx`)

Renders `state.collection.items` as `CollectionCard.tsx` instances: item name, rating badge,
review snippet (verbatim, per Phase 1's contract — the frontend must not reformat or truncate it
in a way that changes its meaning), rationale line, and a mock "add all to cart" action that
updates local state only — no real cart/checkout integration, per the standalone-prototype scoping
in `part4-mvp-proposal.md`.

## Build steps

1. Scaffold `web/` with Vite's React-TS template; port `tailwind.config.ts` tokens (coral palette,
   spacing, font stack) from `design/mockup.html`'s inline styles.
2. Scaffold `api/` with FastAPI; implement `schemas.py`, then `main.py`'s `/api/converse` route
   calling into `agent.loop` (Phase 1) — this route should be a thin translation layer, not new
   business logic.
3. Build `Home.tsx` and `Entry.tsx` directly from the mockup markup.
4. Build `Conversation.tsx` against a stubbed `api/client.ts` response (fixed clarifying question
   / collection) to unblock UI work without waiting on Phase 1 or a running `api/` service — then
   point it at the real local FastAPI instance once both exist.
5. Build `Result.tsx` and `CollectionCard.tsx` against real API responses.
6. Write `tests/test_api.py`: contract tests against `api/main.py` using FastAPI's `TestClient` —
   assert response shapes match the documented union type, and that a reorder-mode message
   produces `"type": "redirect"`.
7. Manual pass: run `web/` and `api/` together locally, walk Screen 01 → 02 → 03 (one clarifying
   exchange) → 04 end to end, compare every screen against `design/mockup.html` side by side.

## Exit criteria

- A user can go Screen 01 → 02 → 03 (one clarifying exchange) → 04 with real Phase 1 agent output
  end to end, matching the mockup's visual spec, running `web/` and `api/` locally together.
- Screen 01 visually matches the production screenshot audit in `differentiation.md` §1 (modulo
  the documented "8 min delivery" baseline-state exception already called out there).
- Reorder-mode prompts typed into Screen 03 visibly redirect rather than producing a collection.
- `tests/test_api.py` passes.

## Risks specific to this phase

- **Schema drift between `api/schemas.py` and the TypeScript types:** nothing enforces these stay
  in sync automatically at this project's scale — a field renamed on one side silently breaks the
  other at runtime, not at build time. Treat any change to Phase 1's dataclasses as requiring a
  matching edit on both sides of this phase, checked by hand.
- **CORS misconfiguration:** an overly permissive `allow_origins` doesn't just risk XSS-style
  abuse in the abstract — it directly risks unrelated sites spending the project's real
  `ANTHROPIC_API_KEY` through a victim's browser session.
- **Mockup drift:** a "close enough" React port of static HTML/CSS can quietly diverge from the
  mockup on spacing, iconography, or copy — same risk the Streamlit-era doc flagged, still true
  under React, mitigated the same way (treat `design/mockup.html` as the spec for Screens 01/02).
