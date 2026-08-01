# Phase 3 — Guardrails & Eval Harness

**Status:** not started. **Depends on:** [Phase 1](../phase-1-agent-core/architecture.md)'s agent
loop (does not need the UI, so can start as soon as Phase 1's exit criteria are met, in parallel
with [Phase 2](../phase-2-ui-screens/architecture.md)).
**Blocks:** [Phase 4](../phase-4-deploy/architecture.md).
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

## Problem this phase solves

Phase 1's system prompt *states* three structural rules; nothing so far *proves* the running agent
still follows them after a prompt tweak, a model swap, or six months of drift. Phase 3 turns the
one-off scripted checks from Phase 1's build step into a committed, repeatable regression suite —
the difference between "we tested this once" and "this cannot regress silently before a deploy."
It also produces the honest success signal this MVP settles for in place of a real production
conversion test, per `part4-mvp-proposal.md`'s closing section: since no live traffic exists,
the eval-set rubric score is the leading indicator, explicitly flagged there as a proxy, not a
substitute.

## Scope

In scope: a fixed eval prompt set drawn from real interview language, a hand-scored rubric, an
automated fabrication check, an automated reorder-mode redirect check, and wiring both automated
checks as a gate that runs before every deploy.

Out of scope: the deploy mechanics themselves ([Phase 4](../phase-4-deploy/architecture.md) runs
this phase's checks against the deployed instance as a post-deploy smoke test, but building the
deploy pipeline is Phase 4's job).

## Repo layout produced by this phase

```
blinkit-mvp/
  eval/
    prompts.py               # fixed occasion-prompt set, sourced from interview language
    rubric.md                  # hand-scoring criteria
    results.md                  # committed hand-scored results, updated per run
    fabrication_check.py         # automated: every shown snippet traces to corpus.jsonl
    redirect_check.py             # automated: reorder-mode prompts get redirected, not answered
  scripts/
    pre_deploy_gate.py            # runs fabrication_check + redirect_check, exits non-zero on failure
```

## Eval prompt set

Pulled verbatim (not paraphrased) from `NLGradProject/docs/part2.md` interview language, per the
existing proposal — at minimum: "guests coming over," "travelling" / camping, "gift for a
5-year-old," "gym essentials." Extend this set as more interview language becomes available, but
never invent synthetic prompts as a substitute for real interview phrasing — the whole point of
sourcing from `part2.md` is that these are things a real interviewee actually said, which is as
close to real user language as this project can get without production traffic.

## Rubric (`eval/rubric.md`)

Per response, hand-score three dimensions (since no production conversion data exists to automate
this):

| Dimension | Question | Scale |
|---|---|---|
| Relevance | Does the collection actually fit the stated occasion? | 1-5 |
| Trust-signal presence | Does every card carry a real rating + review snippet + rationale? | 1-5 |
| Would-a-Trust-Ready-Explorer-act-on-this | Judged against the primary segment profile in `part4-mvp-proposal.md` | 1-5 |

Record scores and a one-line justification per prompt in `eval/results.md`, committed to the repo
so scores are diffable across runs, not just a local artifact someone forgets to re-run.

## Automated checks

### `fabrication_check.py`

For every `CollectionCardItem.review_snippet` in every eval prompt's response, assert it is a
substring of some record in `data/corpus.jsonl` (Phase 0's vendored file). This is the
mechanical, non-negotiable version of Phase 1's "never fabricate" rule — a prompt can drift, code
cannot silently pass this check while fabricating.

### `redirect_check.py`

Fire reorder-mode prompts ("I need milk," "add eggs," "order bread") through `agent.loop` and
assert each one produces a redirect response, never a `Collection`. This is the regression test
for H3's structural guarantee (Phase 1 §"Stay occasion/curiosity-scoped") — without this check,
nothing stops a future prompt edit from quietly making the agent start answering reorder requests,
which would silently violate the "Concierge never interrupts a reorder-mode session" claim in
[`differentiation.md`](../../differentiation.md) §4.

### `scripts/pre_deploy_gate.py`

Runs both checks, exits non-zero on any failure. [Phase 4](../phase-4-deploy/architecture.md) is
expected to call this before every deploy — a failing gate blocks the deploy, it doesn't just log
a warning.

**Revision (2026-08-01):** since [Phase 2](../phase-2-ui-screens/architecture.md) now wraps
`agent.loop` in a FastAPI service instead of a Streamlit process, both checks need two modes: one
that calls `agent.loop` in-process (used locally, and by `pre_deploy_gate.py` before anything is
deployed), and one that calls the same prompts over HTTP against a running `api/` instance's
`/api/converse` endpoint (used by [Phase 4](../phase-4-deploy/architecture.md)'s post-deploy smoke
test against the live URL). Implement this as a swappable transport (a small interface with an
in-process implementation and an HTTP-client implementation), not two copies of the check logic —
the assertions themselves (substring match against `corpus.jsonl`, redirect-not-collection) must
stay identical between modes, only how the response is fetched differs.

## Build steps

1. Write `eval/prompts.py` with the fixed prompt set + source citation (which interview, which
   line) for each prompt.
2. Write `eval/rubric.md` per the table above.
3. Run the eval set through the real `agent.loop` (Phase 1), hand-score each response, commit to
   `eval/results.md`.
4. Implement `fabrication_check.py` and `redirect_check.py` as pytest-style assertions runnable
   both individually and via `pre_deploy_gate.py`.
5. Wire `pre_deploy_gate.py` into whatever deploy trigger Phase 4 ends up using (manual step or CI
   — Phase 4 decides the mechanism, this phase just needs to expose a single callable/script
   entry point).

## Exit criteria

- Eval set + rubric scores committed to `eval/results.md`.
- `fabrication_check.py` and `redirect_check.py` both pass against the current `agent.loop`, and
  both are runnable as part of the same test pass used before deploy.
- `scripts/pre_deploy_gate.py` exists and exits non-zero on a deliberately-broken agent (verify
  this by temporarily breaking a rule and confirming the gate catches it, then reverting).

## Risks specific to this phase

- **Rubric subjectivity:** hand-scored rubrics drift between scoring sessions if the scorer
  changes or time passes — keep the one-line justification per score, since that's what makes a
  score re-checkable later, not just a number with no reasoning attached.
- **Eval set too small to catch edge cases:** 4-6 fixed prompts catch gross regressions, not
  subtle ones — treat a passing eval run as "no known regression," not "proven correct for all
  inputs."
