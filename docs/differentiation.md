# Differentiation: Occasion Concierge vs. Production Blinkit

This expands on the comparison table embedded in [`design/mockup.html`](../design/mockup.html).
It exists to answer one question honestly before any code gets written: **is this actually new,
or a reskin of something that already ships?**

## What already exists in the production app today

Based on the research corpus (`discovery_engine/data/processed/corpus.jsonl`, 588 items scraped
from Play Store, App Store, Reddit, and MouthShut) and the 6 primary interviews
(`docs/part2.md` in the parent project), the current app's discovery surfaces are:

1. **Homepage banners** — static, promotional, identical for every user in a given campaign
   window (e.g. discount banners). Not personalized to an individual's stated need.
2. **Category grid** — a fixed taxonomy (Fruits & Vegetables, Dairy & Breakfast, Munchies,
   Household, etc.) the user must already know to browse into.
3. **Search** — works only if the user already knows what they want to type.
4. **"Buy it again"** — reorder shortcut from purchase history; the AI insight rated *strong*
   confirms this is the dominant repeat-purchase driver (Part 1, research question 1).
5. **Checkout-time upsells** — the one discovery moment Interview 1 describes ("only when
   something appeared during checkout with a discount") — reactive, discount-triggered, and
   arrives after the cart is already built, not before.
6. **Occasional static "collections" banners** (e.g. seasonal promos) — exist in some
   quick-commerce apps as merchandising banners, but are campaign-driven and non-conversational:
   the same banner for every user, not built from a need the user actually stated.

None of these six surfaces do three things at once: (a) start from a user-stated need, (b) ask a
clarifying question to sharpen relevance, and (c) attach a trust signal (rating + review) to each
suggested item at the moment of suggestion. That combination is what's new.

**Caveat, stated plainly:** this assessment is built from scraped reviews, Reddit discussion, and
6 interviews — not a direct current-state audit of the live Blinkit app. Before implementation,
a 10-minute screenshot walkthrough of the actual app should confirm none of these six surfaces
have since added conversational or occasion-based personalization; the research evidence above
is the best available proxy but isn't a substitute for looking at the live app.

## What is genuinely new

| | Existing surfaces | Occasion Concierge |
|---|---|---|
| Trigger | Always visible / algorithmic | User states an explicit need |
| Personalization mechanism | Purchase history pattern-matching | Stated occasion + one clarifying question |
| Trust signal placement | Buried on the product detail page | Inline, at the point of suggestion |
| Timing | Before browsing (banner) or after cart-building (checkout upsell) | Before cart-building, shaped by the stated need |
| Effect on reorder-mode sessions | N/A — there's only one mode | None — Concierge is a separate, opt-in screen; Buy Again / search / categories are pixel-for-pixel unchanged |

## What is deliberately *not* changing

This matters as much as what's new, because the root-cause diagnosis in
`docs/part3-problem-definition.md` explicitly warns against forcing browsing onto users for whom
browsing itself is the friction (the Efficiency Reorderer and Mission-Driven Household Manager
segments). So the MVP:

- Does **not** modify the homepage layout, banner, category grid, or Buy Again section in any way.
- Does **not** inject recommendations into a reorder-mode session — Concierge is reached only by
  tapping the prompt card or invoking it directly; it never interrupts.
- Does **not** replace search — a user who knows what they want still types it and moves on in
  three taps, same as today.

## Mapping back to the three hypotheses

- **H1 (occasion-based collections increase exploration):** validated by Screens 02→04 —
  collection is built from a stated occasion, not shown generically.
- **H2 (embedded trust signals reduce perceived risk):** validated by Screen 04 — every item
  carries a rating and a review-style snippet inline, addressing the "I don't know whether I'll
  like it, I don't want to waste money" blocker from Interview 1.
- **H3 (mode-aware recommendations outperform generic cross-sell):** validated structurally —
  Concierge exists as an isolated flow the reorder-mode majority never sees, rather than a
  classifier bolted onto the existing homepage.

## Open question for the next design pass

The mockup assumes users are willing to type a free-text occasion description. Interview 3's
request was for pre-built collections ("Study Night Essentials," "Movie Marathon Kit") rather than
a blank chat box — worth testing whether a hybrid entry (tap a suggested occasion chip *or* type
freely) converts better than free text alone before finalizing the built agent's UI.
