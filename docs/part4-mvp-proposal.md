# Part 4: MVP Solution Proposal

Builds directly on [`part3-problem-definition.md`](part3-problem-definition.md): root cause (one
undifferentiated, trust-signal-free discovery mechanism serving fundamentally different user
intents), the three hypotheses (H1 occasion-based collections, H2 embedded trust signals, H3
mode-aware recommendations), and the primary target segment (**Trust-Ready Explorers** — Trust-
Seeking Category Expander + Social-Discovery Browser).

Per `docs/part4.md`, the MVP must be one of: a feature prototype within the existing product, an
AI-powered workflow, or an AI agent — and must ship to production, not stay a local demo.

**Scope constraint that shapes all three options below:** this is a student project without access
to Blinkit's real catalog, inventory, or session data. Any option has to be a standalone prototype
that stays grounded in *real* evidence (the scraped corpus and synthesized insights already built
in Part 1) rather than inventing a fake product catalog from scratch or pretending to have live
Blinkit data.

---

## Option A — Trust-Backed Discovery Widget

**What it is:** A single UI component simulating a storefront moment: given a cart that already
looks like a routine reorder (milk, eggs, bread), the widget surfaces one adjacent-category
suggestion with a trust rationale attached — rating, a real review snippet pulled from the
Part-1 corpus, and a "pairs with what you usually buy" line.

- **Hypotheses tested:** H2 directly; H3 partially (only triggers outside pure-reorder carts).
- **MVP type:** feature prototype within a simulated product.
- **Feasibility:** requires building a mock storefront UI (product grid, cart state) from
  scratch — the heaviest net-new frontend surface of the three options.
- **Risk:** easiest to build something that *looks* like a widget but doesn't actually prove
  the hypothesis, since a single static suggestion doesn't showcase the "different moments need
  different treatment" insight that's central to the root cause.

## Option B — Occasion Concierge Agent

**What it is:** A conversational agent (extends the chat pattern already proven in
`discovery_engine/chat_app.py`). User states a need in their own words — "friends are coming over
tonight," "going camping this weekend," "gift for a 5-year-old" — the agent asks at most one
clarifying question, then returns a curated multi-item collection where **every item carries a
trust rationale** (rating + real review snippet retrieved from the corpus + why it fits).

- **Hypotheses tested:** H1 directly (occasion-triggered collections); H2 built into every
  suggestion by construction, not bolted on; H3 satisfied structurally — the agent is only ever
  invoked for occasion/curiosity intent, so it never interrupts a reorder-mode session by design,
  no classifier needed.
- **MVP type:** AI agent — the type named explicitly in `part4.md`.
- **Feasibility:** reuses the exact stack already validated in Part 1 (Claude tool-use,
  `sentence-transformers` retrieval over `corpus.jsonl`, Streamlit deployment path). This is
  the option with the least net-new infrastructure risk.

## Option C — Mode-Aware Recommendation Classifier

**What it is:** A backend workflow that takes a simulated cart + session history and classifies
it as reorder-mode vs. occasion-mode vs. curiosity-mode, then decides whether/how to surface a
recommendation. Exposed via a small API plus a dashboard showing classification decisions on
sample sessions.

- **Hypotheses tested:** H3 directly; H1/H2 not addressed at all.
- **MVP type:** AI-powered workflow.
- **Feasibility:** buildable, but its output is a classification label, not a felt user
  experience — hard to demo persuasively without real behavioral session data we don't have, and
  it validates only one of the three hypotheses.

---

## Decision Matrix

| Criterion | A: Trust Widget | B: Occasion Concierge | C: Mode Classifier |
|---|:-:|:-:|:-:|
| Hypothesis coverage (of H1/H2/H3) | 1.5 / 3 | **3 / 3** | 1 / 3 |
| Fit to primary segment (Trust-Ready Explorers) | Good | **Best** | Fair |
| Technical feasibility with existing stack | Fair (new frontend) | **Best** (reuses Part-1 stack) | Fair |
| Demoability / production deployability | Good | **Best** | Weak (infra, not experience) |
| Grounded in real corpus data (not invented) | Partial | **Full** (retrieval-grounded) | Partial |
| Novelty vs. what Part 1 already built | Low | **High** (agent vs. Part 1's Q&A chat) | Medium |

**Recommendation: Option B — Occasion Concierge Agent.**

It's the only option that operationalizes all three hypotheses at once, fits the primary segment
most directly (Trust-Ready Explorers are, by definition, people who'll act once given relevance +
trust signal — this *is* that moment), and carries the lowest infrastructure risk because it
extends a stack already proven to work in this repo rather than starting a new frontend from
scratch. It also avoids the trap Option A falls into — a single generic widget doesn't actually
demonstrate mode-awareness, which is the core of the root-cause diagnosis in Part 3.

---

## Implementation Plan for the Occasion Concierge Agent

**Revision note (2026-08-01):** the Streamlit-based architecture and deployment path below is the
*original* plan, kept as-is for the historical record of why Option B was chosen (it was, at the
time, the option with the least net-new infrastructure risk). That has since changed: Streamlit
was replaced with a React SPA + FastAPI split because Streamlit's widget-based rendering couldn't
hit the pixel-parity bar `differentiation.md` §4 commits to. The current, authoritative build plan
is [`part4-architecture.md`](part4-architecture.md) and its `phases/` folder — treat everything
below this note as superseded on tech-stack specifics, still valid on scope, data-grounding
principles, and the eval approach.

**Architecture (superseded — see revision note above)**

```
User occasion prompt
   -> Claude agent (tool-use loop)
        tool: retrieve_evidence(query)      -- embeds query, cosine-search over corpus.jsonl
                                                (same sentence-transformers index as chat_app.py)
        tool: suggest_items(occasion, evidence) -- grounds item picks in real corpus mentions,
                                                    not invented products
        tool: build_collection(items)        -- assembles the final curated list + trust rationale
   -> Streamlit UI: collection card per item (name, rating badge, review snippet, "why this"),
                     mock "add all to cart" action
```

**Data**

- Reuse `discovery_engine/data/processed/corpus.jsonl` (588 cleaned items) and
  `data/insights/insights.json` as the grounding source for trust rationale — every review
  snippet shown to the user must be a real quote from Part 1's corpus, not fabricated, to keep
  the MVP honest (same principle the Part-1 pipeline already applies).
- Product/category universe is derived from categories actually mentioned in the corpus
  (groceries, produce, gym essentials, electronics, plants, gifting items, etc.) rather than an
  invented catalog — keeps the demo evidence-grounded end to end.

**Build steps**

1. Extend the existing embedding index (already built for `chat_app.py`) with a
   `retrieve_evidence(query)` tool callable by the agent.
2. Write the agent system prompt to (a) ask at most one clarifying question, (b) never fabricate
   a rating or review — retrieval miss should fall back to "no direct evidence, general
   suggestion" rather than inventing a quote, (c) stay occasion/curiosity-scoped and refuse
   reorder-mode requests ("I need milk") by redirecting to the normal storefront, which is the
   structural enforcement of H3.
3. Build the Streamlit collection-card UI (rating badge, snippet, rationale, mock add-to-cart).
4. Add a small fixed eval set of occasion prompts drawn straight from the interview language
   (`docs/part2.md`: "guests coming over," "travelling," "gift for a 5-year-old," "gym
   essentials") and hand-score each response against a short rubric: relevance, trust-signal
   presence, would-a-Trust-Ready-Explorer-act-on-this.
5. Deploy to Streamlit Community Cloud (the path already flagged as a known next step in
   `discovery_engine/README.md`), satisfying the "deploy to production" requirement.

**Success signal (given no real production traffic available)**

Since a live conversion-rate test isn't possible in this scope, treat the eval-set rubric score
plus a short informal usability pass with a few people matching the Trust-Ready-Explorer profile
as the leading indicator — explicitly a proxy, not a substitute for the real H1/H2/H3 tests
defined in Part 3, which would require production instrumentation this project doesn't have.

---

Ready to move into building this once you confirm — next step would be scaffolding the agent
inside `discovery_engine/` (new `concierge_app.py` alongside the existing `chat_app.py`) and
wiring the retrieval tool into the corpus that's already indexed.
