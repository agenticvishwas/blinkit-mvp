# Phase 1 — Agent Core (Tool-Use Loop)

**Status:** not started. **Depends on:** [Phase 0](../phase-0-data-foundation/architecture.md).
**Blocks:** [Phase 2](../phase-2-ui-screens/architecture.md) screens 03/04, [Phase 3](../phase-3-guardrails-eval/architecture.md).
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

## Problem this phase solves

The root-cause diagnosis this whole MVP answers (`part3-problem-definition.md` in the parent repo,
summarized in [`part4-mvp-proposal.md`](../../part4-mvp-proposal.md)) is that Blinkit runs one
undifferentiated, trust-signal-free discovery mechanism for fundamentally different user intents.
Phase 1 is where that diagnosis becomes executable logic: the three hypotheses (H1 occasion
collections, H2 embedded trust signals, H3 mode-aware recommendations) all live in this phase's
tool contracts and system prompt, not in the UI. Get this phase wrong and no amount of UI polish
in Phase 2 fixes it, because the UI only renders what this loop returns.

## Scope

In scope: the Claude tool-use loop itself, its three tools, the system prompt encoding the three
structural rules, and a non-UI scripted test harness to validate it before any screen exists.

Out of scope: rendering ([Phase 2](../phase-2-ui-screens/architecture.md)), the formal regression
eval suite ([Phase 3](../phase-3-guardrails-eval/architecture.md) — this phase's harness is a
build-time sanity check, not the committed regression gate).

## Repo layout produced by this phase

```
blinkit-mvp/
  agent/
    retrieval.py          # from Phase 0
    tools.py               # this phase: the three tool implementations
    loop.py                 # this phase: the Claude tool-use orchestration
    prompts.py              # this phase: system prompt text
  tests/
    test_agent_loop.py       # scripted harness, 5-6 occasion prompts
```

## Tool contracts

Each tool's job is narrower than it sounds — narrow on purpose, because each narrowness is what
enforces one of the three structural rules below.

### `retrieve_evidence(query: str) -> list[Evidence]`

Thin wrapper around `agent.retrieval.RetrievalIndex.search()` from Phase 0. Takes the user's
occasion text (or the agent's own reformulation of it) and returns ranked `Evidence` objects, or
an empty list if nothing clears the similarity floor. This is the only tool that touches
`corpus.jsonl` — every fact the agent can cite about a product originates here.

### `suggest_items(occasion: str, evidence: list[Evidence]) -> list[CandidateItem]`

```python
@dataclass
class CandidateItem:
    item_name: str
    category: str
    evidence_source_id: str   # must equal an Evidence.source_id from retrieve_evidence's output
```

Constraint that matters more than anything else in this file: **`evidence_source_id` must trace to
an actual `Evidence` object returned by `retrieve_evidence` in the same turn.** This tool proposes
which retrieved items to include and in what quantity/mix — it does not invent new items. If
`evidence` is empty (retrieval miss), this tool returns an empty list rather than falling back to
invented items; the loop-level prompt (below) is what turns that into the honest "no direct
evidence, general suggestion" copy instead of silently degrading.

### `build_collection(items: list[CandidateItem]) -> Collection`

```python
@dataclass
class CollectionCardItem:
    item_name: str
    rating: float
    review_snippet: str     # copied verbatim from the sourced Evidence, never reworded
    rationale: str            # e.g. "pairs with what you usually buy" / "why this fits {occasion}"

@dataclass
class Collection:
    occasion_summary: str
    items: list[CollectionCardItem]
```

Assembles the final response. The verbatim-snippet constraint is the one Phase 3's automated
fabrication check (substring match against `corpus.jsonl`) is built to enforce — if
`build_collection` ever paraphrases a snippet instead of quoting it, that check should fail the
build, which is by design.

## Loop orchestration (`agent/loop.py`)

```
User occasion text
   │
   ▼
Claude (system prompt below, tools registered)
   │
   ├─ optionally emits ≤1 clarifying question → returned to UI, loop pauses for user reply
   │
   ├─ calls retrieve_evidence(query) ──► agent/retrieval.py ──► corpus.jsonl (Phase 0)
   ├─ calls suggest_items(occasion, evidence)
   ├─ calls build_collection(items)
   │
   ▼
Collection object returned to caller (Phase 2's UI, or Phase 1's own test harness)
```

## System prompt — the three structural rules

These are not style preferences; each one is the mechanism by which a specific hypothesis or
constraint from `part4-mvp-proposal.md` gets enforced in code rather than left as an aspiration:

1. **Ask at most one clarifying question, then answer.** Prevents the interaction from turning
   into an open-ended chat, which the eval rubric in Phase 3 explicitly scores against.
2. **Never fabricate a rating or review.** A `retrieve_evidence` miss (empty list) must produce
   "no direct evidence, general suggestion" copy, not an invented quote. This is H2's
   trust-signal claim made falsifiable — a trust signal that can be fabricated isn't a trust
   signal.
3. **Stay occasion/curiosity-scoped; redirect reorder-mode requests.** A prompt like "I need milk"
   or "add eggs" must be redirected back to normal search, not answered by the agent. This is the
   structural enforcement of H3 (mode-aware recommendations) — there is no separate classifier
   because the agent is simply never invoked for, and never engages with, reorder-mode intent.
   This also protects the "nothing existing was touched" claim in
   [`differentiation.md`](../../differentiation.md) §4: the agent must never make it look like the
   Buy Again flow is going through it.

## Build steps

1. Implement `CandidateItem`, `Collection`, `CollectionCardItem` dataclasses and the three tool
   functions in `agent/tools.py`, calling into Phase 0's `agent/retrieval.py`.
2. Write the system prompt in `agent/prompts.py` encoding the three rules above; include 2-3
   worked examples in the prompt itself (a full occasion → clarifying question → collection
   transcript, and one reorder-mode redirect transcript) since few-shot examples are the most
   reliable way to keep a tool-use loop on-contract.
3. Implement `agent/loop.py`: register the three tools with the Claude API, drive the turn loop,
   surface the clarifying-question pause as an explicit return value (not swallowed internally) so
   Phase 2 can render it as a chat turn.
4. Write `tests/test_agent_loop.py`: send the same fixed occasion-prompt set used in Phase 0's
   smoke test (plus at least one reorder-mode prompt) through the full loop; for every returned
   `CollectionCardItem`, assert `review_snippet` is a substring of some record in `corpus.jsonl`
   (a first pass at the check Phase 3 formalizes) and assert the reorder-mode prompt produces a
   redirect, not a collection.

## Exit criteria

- `tests/test_agent_loop.py` passes for the fixed occasion-prompt set: every card traces to a real
  corpus snippet, no card is returned for a reorder-mode prompt, and no turn asks more than one
  clarifying question.
- The loop is callable with no UI dependency — [Phase 2](../phase-2-ui-screens/architecture.md)'s
  FastAPI service imports `agent.loop` directly and wraps it in an HTTP endpoint; it does not
  reimplement any part of the orchestration logic.

**Revision (2026-08-01):** Phase 2 originally called this module in-process from a Streamlit app;
it now calls it in-process from a FastAPI route instead (`api/main.py`). The distinction doesn't
change anything here — `agent.loop` was already designed to be UI-framework-agnostic — but it does
mean `ANTHROPIC_API_KEY` now lives only on the `api/` service's host, never in a browser-reachable
process; see [Phase 4](../phase-4-deploy/architecture.md)'s secrets section.

## Risks specific to this phase

- **Prompt drift under load:** a system prompt that holds for 5 hand-picked test prompts can still
  leak on a prompt worded unusually — Phase 3's larger eval set is what catches this at scale, but
  if this phase's 5-6 prompt harness already shows inconsistent rule-following, do not proceed to
  Phase 2 until the prompt is tightened.
- **Tool-contract violation slipping through:** if `build_collection` is ever allowed to accept
  items whose `evidence_source_id` doesn't trace back to a real `retrieve_evidence` call in the
  same turn, the "never fabricate" guarantee silently breaks at the orchestration layer instead of
  the prompt layer — enforce this in code (assert/raise), not just by prompting nicely.
