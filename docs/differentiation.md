# Differentiation: Occasion Concierge vs. Production Blinkit

This expands on the comparison table embedded in [`design/mockup.html`](../design/mockup.html).
It exists to answer one question honestly before any code gets written: **is this actually new,
or a reskin of something that already ships?**

**Revision note (2026-08-01):** the first pass of this document was built entirely from the
scraped-review corpus and 6 interviews, with an explicit caveat that it hadn't been checked
against a live screenshot of the app. That check has now been done, against a real screenshot of
the production home screen. It changed the argument in one important way — see
[§2](#2-what-the-live-audit-changed) — and the claim below is now the corrected, sharper version.

## 1. Live audit: what's actually in the production app today (2026-08-01)

Source: [`../assets/WhatsApp Image 2026-08-01 at 2.51.11 PM.jpeg`](../assets/WhatsApp%20Image%202026-08-01%20at%202.51.11%20PM.jpeg)
— a real screenshot of the production Blinkit home screen, timestamped 2:51 PM. Confirmed
directly from that screenshot, not inferred from reviews:

- **Dynamic status header** — the top of the home screen shows real-time operational state
  ("Due to excess demand / Currently unavailable"), not a fixed ETA. This mockup uses the normal
  "Delivery in 8 mins" state as the representative baseline, since that's the typical case, not
  the surge edge case.
- **Address row** — bold "HOME -" label + address + dropdown chevron, with a wallet/cashback
  pill (₹0) and a profile icon top-right.
- **Search bar** — large pill, rotating example placeholder text (e.g. `Search "bouquet"`), mic
  icon.
- **Category icon-tab row**, directly under search — All / Rakhi (with a "New" badge) /
  Electronics / Beauty / Pharmacy / Decor. This *is* the category browse entry point; there's no
  separate category-icon grid further down the page.
- **A "Powered by" sponsor ribbon** — a decorative brand-placement strip below the category tabs.
- **A merchandising grid** dominating the fold: a tall offer tile (Bands, Cards & Flowers —
  ₹199 struck through to ₹49) plus four square tiles — **Gifting Corner, Party With Friends,
  Chocolates & Cakes, and an occasion-specific tile** (e.g. a date-night edit tied to a calendar
  date).
- **A full-width IP/brand store banner** below the grid (a licensed-merchandise shop-in-shop).
- **"Frequently bought"** (not "Buy it again") — shown as small clustered collections
  (**Favourites**, **Vegetables & Fruits**) with a `+N more` badge, not a scrollable row of
  individual product-add cards.
- **Bottom tab bar**: Home / Order Again / Categories / Print — no visible Cart or Account tab —
  plus a separate floating cross-app promotional pill (a partner service, e.g. "district ↗")
  sitting outside the tab bar.

## 2. What the live audit changed

The first draft of this document claimed occasion-based merchandising was mostly absent from the
app, with only "occasional static promo banners." **That was wrong, or at least understated.** The
real app already runs Gifting Corner, Party With Friends, a date-night tile, a seasonal
Rakhi category, and a full IP-branded store — that's five occasion-shaped merchandising surfaces
on the home screen simultaneously. If the differentiation argument had rested on "Blinkit doesn't
do occasion collections," it would not survive contact with the real product.

**What the argument actually rests on, corrected:**

1. **These tiles are curated by a merchandising calendar, not by the user.** Gifting Corner and
   Party With Friends exist because someone on a merchandising team decided this week's push;
   they don't exist because a specific user said "my cousin's kids are visiting" (Interview 2) or
   "friends coming over tonight." The set of occasions covered is whatever marketing picked, not
   whatever the user actually has.
2. **None of the tiles are personalized to specifics.** "Party With Friends" shows the same
   contents regardless of whether the party is for 2 people or 20, snacks-only or a full spread.
   There is no clarifying question anywhere in this flow.
3. **None of the tiles carry a trust signal.** Not one of the five merchandising surfaces —
   Gifting Corner, Party With Friends, Chocolates & Cakes, the date-night tile, or the IP store —
   shows a rating, a review, or any "why this" reasoning on the tile itself or its landing
   preview. This was the strongest AI-engine finding (moderate strength) and the most consistent
   interview finding (Interviews 1, 4, 6), and it remains completely unaddressed by what already
   ships, even where occasion merchandising exists.

So the corrected claim is narrower and more defensible than the original: **the gap isn't
"occasion collections don't exist," it's "occasion collections aren't personalized to a stated
need, and none of them carry a trust signal at the decision moment."**

## 3. Full comparison, corrected

| | Existing surfaces (verified) | Occasion Concierge |
|---|---|---|
| Occasion coverage | Fixed set the merchandising calendar picked this week (Rakhi, Gifting Corner, Party With Friends, date-night, IP store) | Any occasion the user states, not limited to a campaign calendar |
| Personalization | None — same tile contents for every user who taps it | Built from what the user says, sharpened by one clarifying question |
| Trust signal placement | Absent from all five merchandising surfaces audited | Rating + review snippet + "why this" inline, at the point of suggestion |
| Trigger | Always visible on home, algorithmic elsewhere (Buy Again / cross-sell) | User states an explicit need; never shown to users who don't ask |
| Timing | Passive (home tile) or reactive (checkout upsell, per Interview 1) | Before cart-building, shaped by the stated need |
| Effect on reorder-mode sessions | N/A — one homepage serves every session identically | None — Concierge is a separate, opt-in screen; Buy Again, search, categories, and every merchandising tile are pixel-identical to today |

## 4. What is deliberately *not* changing

This matters as much as what's new, because the root-cause diagnosis in
`docs/part3-problem-definition.md` explicitly warns against forcing browsing onto users for whom
browsing itself is the friction (the Efficiency Reorderer and Mission-Driven Household Manager
segments). So the MVP:

- Does **not** modify the home screen layout, merchandising grid, IP store banner, or Frequently
  Bought section in any way — Screens 01 and 02 in the mockup are pixel-identical except for one
  added prompt card.
- Does **not** inject recommendations into a reorder-mode session — Concierge is reached only by
  tapping the prompt card or invoking it directly; it never interrupts.
- Does **not** replace search or the existing category tabs — a user who knows what they want
  still types it and moves on, same as today.

## 5. Mapping back to the three hypotheses

- **H1 (occasion-based collections increase exploration):** the live audit shows this mechanism
  already exists in production — the differentiation is *personalized, user-triggered* occasion
  collections vs. the *fixed, campaign-curated* ones that already ship.
- **H2 (embedded trust signals reduce perceived risk):** unaffected by the audit — confirmed as
  the sharpest gap, since zero of the audited merchandising surfaces carry a trust signal.
- **H3 (mode-aware recommendations outperform generic cross-sell):** unaffected by the audit —
  validated structurally by Concierge existing as an isolated, opt-in flow.

## 6. Open question for the next design pass

The mockup assumes users are willing to type a free-text occasion description. Interview 3's
request was for pre-built collections ("Study Night Essentials," "Movie Marathon Kit") rather than
a blank chat box — and the live audit shows Blinkit's own merchandising team already thinks in
exactly that format (Gifting Corner, Party With Friends). Worth testing whether a hybrid entry
(tap a suggested occasion chip, seeded from real merchandising categories, *or* type freely)
converts better than free text alone before finalizing the built agent's UI.
