# Phase 0 — Data Foundation

**Status:** complete. **Blocks:** [Phase 1](../phase-1-agent-core/architecture.md).
**Parent plan:** [`part4-architecture.md`](../../part4-architecture.md).

**Revision (2026-08-01):** this doc's retrieval design below describes the original
embedding-based approach (`sentence-transformers` + cosine similarity). That was replaced with
BM25 keyword search after the embedding model's `torch` dependency proved too heavy for a
free-tier deploy host's memory — see the root [`README.md`](../../../README.md)'s "Retrieval
strategy" section for the full decision writeup. The actual, current implementation is
`agent/retrieval.py`; treat the embedding-specific detail below as historical context for *why*
Phase 0 exists, not as a description of what's running today.

## Problem this phase solves

Every downstream phase depends on one non-negotiable constraint from
[`part4-mvp-proposal.md`](../../part4-mvp-proposal.md) (the "Scope constraint" note that opens the
options section): this is a student project with no access to Blinkit's real catalog or session
data, so the MVP
must stay grounded in the *real* evidence already collected in Part 1 (the scraped review corpus)
rather than inventing a fake product catalog. Phase 0 is the phase that makes that constraint
possible to honor — every later phase (agent tool calls, UI cards, eval checks) assumes real
corpus data already exists locally in this repo.

This repo is deliberately separate from the parent `NLGradProject` repo that holds
`discovery_engine/chat_app.py` and `corpus.jsonl` (see [`../../../README.md`](../../../README.md)
§"Why a separate repo"), so nothing here can silently import from that repo at runtime — Phase 0
is a one-time, one-directional vendoring step, not a live dependency.

## Scope

In scope:
- Copying `corpus.jsonl` and `insights.json` from `NLGradProject` into this repo as static,
  read-only files.
- Porting the embedding/retrieval pattern from `discovery_engine/chat_app.py` into a standalone
  module in this repo, with zero runtime import from the parent repo.
- Verifying the ported retrieval returns the same neighbors the original does, for a fixed set of
  sanity queries.

Out of scope (deferred to later phases):
- The Claude tool-use loop that calls this retrieval module — [Phase 1](../phase-1-agent-core/architecture.md).
- Any UI — [Phase 2](../phase-2-ui-screens/architecture.md).
- Automated fabrication checking against the corpus — [Phase 3](../phase-3-guardrails-eval/architecture.md).

## Repo layout produced by this phase

```
blinkit-mvp/
  data/
    corpus.jsonl        # vendored, read-only, 588 cleaned review-backed items
    insights.json        # vendored, read-only, Part-1 synthesized insights
  agent/
    __init__.py
    retrieval.py          # this phase's only code artifact
  tests/
    test_retrieval_smoke.py
```

`data/` and `agent/` do not exist yet in this repo (confirmed: current tree is only
`design/`, `docs/`, `assets/`) — both are created fresh by this phase.

## Data contract

`corpus.jsonl` — one JSON object per line. Exact field names must be confirmed against the source
file at vendoring time (do not assume without checking `NLGradProject/discovery_engine/data/processed/corpus.jsonl`
directly), but every record is expected to carry at minimum:

| Field | Type | Used by |
|---|---|---|
| `item_name` | str | `suggest_items()` in Phase 1, card title in Phase 2 |
| `category` | str | occasion → category matching in Phase 1 |
| `review_snippet` | str | the trust rationale shown verbatim in Phase 2 — **never paraphrased** |
| `rating` | float | rating badge in Phase 2 |
| `source_id` | str | the substring-match key Phase 3's fabrication check uses to prove a shown snippet traces back to this file |

`insights.json` is read-only reference context (not embedded/searched) — used for occasion
vocabulary and category framing, not per-item retrieval.

If the real file's schema differs from this table, update this table to match reality before
writing `retrieval.py` — the table is a contract for Phase 1, and Phase 1 breaks if it's wrong.

## `agent/retrieval.py` interface

```python
@dataclass
class Evidence:
    item_name: str
    category: str
    review_snippet: str
    rating: float
    source_id: str
    similarity: float

def build_index(corpus_path: str = "data/corpus.jsonl") -> "RetrievalIndex":
    """Embeds every corpus record once, at process start. Same embedding model
    discovery_engine/chat_app.py uses — confirm the exact model name against that
    file during vendoring rather than assuming one, since a mismatched model
    silently produces different neighbors for the same query."""

class RetrievalIndex:
    def search(self, query: str, top_k: int = 5, min_similarity: float = ...) -> list[Evidence]:
        """Returns [] (not a forced low-similarity match) when nothing clears
        min_similarity — this is the retrieval-level enforcement of the
        'never fabricate' rule that Phase 1's system prompt also states."""
```

The `min_similarity` floor is the single most important number in this file: it's what turns "no
good match" into an honest empty result instead of a plausible-looking bad one. Pick it
empirically during the smoke test below, not arbitrarily.

## Build steps

1. Locate and copy `corpus.jsonl` and `insights.json` from the `NLGradProject` checkout into
   `data/` here. Copy only — do not re-scrape or regenerate; the whole point is that this is the
   same evidence Part 1 already validated.
2. Open `discovery_engine/chat_app.py` in the parent repo and note: the exact embedding model
   name, the similarity metric (cosine, expected), and any preprocessing applied to query text
   before embedding (lowercasing, stopword handling, etc.). Port these exactly — silent drift here
   is the kind of bug that only shows up as "the agent's suggestions got worse" three phases later.
3. Write `agent/retrieval.py` implementing `build_index()` and `RetrievalIndex.search()` per the
   interface above.
4. Write `tests/test_retrieval_smoke.py`: run a fixed set of known queries (e.g. "camping trip,"
   "gift for a 5-year-old," "friends coming over," "gym essentials" — reuse language straight from
   `NLGradProject/docs/part2.md` interviews) through both the original `chat_app.py` retrieval and
   the new `agent/retrieval.py`, and assert the top-3 neighbors match (or are a reasonable
   near-match if the port isn't byte-for-byte identical — document any intentional divergence).

## Exit criteria

- `agent/retrieval.py` returns real corpus snippets for a query with **no runtime dependency on
  `NLGradProject` being present on disk** — this repo must be cloneable and runnable standalone.
- `tests/test_retrieval_smoke.py` passes: ported retrieval's top results match the original
  `chat_app.py` behavior for the fixed query set.
- `min_similarity` floor is set and documented (not left at a placeholder), with a note on how it
  was chosen (e.g. "lowest similarity score observed among true-positive matches in the smoke
  set, minus a margin").

## Risks specific to this phase

- **Schema drift:** if `corpus.jsonl`'s real fields don't match the table above, every downstream
  phase's assumptions need re-checking, not just this one — flag this loudly if it happens rather
  than quietly adapting only `retrieval.py`.
- **Model mismatch:** using a different embedding model than `chat_app.py` (even a similar one)
  changes which neighbors come back for the same query, silently invalidating the Part-1
  validation this MVP is supposed to inherit.
