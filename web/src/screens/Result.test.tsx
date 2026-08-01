import { useEffect } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";
import { ConciergeProvider, useConcierge } from "../state/ConciergeContext";
import Result from "./Result";
import type { Collection } from "../types";

const fixtureCollection: Collection = {
  occasion_summary: "Snacks for a party",
  note: null,
  items: [
    {
      label: "Chips & namkeen",
      rationale: "Crowd-pleaser",
      has_evidence: true,
      evidence_quote: "great snacks, arrived fast",
      evidence_rating: 5,
      evidence_source: "app_store",
    },
    { label: "Soft drinks", rationale: "General suggestion", has_evidence: false, evidence_quote: null, evidence_rating: null, evidence_source: null },
    { label: "Dips", rationale: "General suggestion", has_evidence: false, evidence_quote: null, evidence_rating: null, evidence_source: null },
  ],
};

function Seed({ collection }: { collection: Collection }) {
  const { dispatch } = useConcierge();
  useEffect(() => {
    dispatch({ type: "SET_COLLECTION", collection });
  }, [collection, dispatch]);
  return null;
}

function renderResult(collection: Collection = fixtureCollection) {
  return render(
    <ConciergeProvider>
      <Seed collection={collection} />
      <Result />
    </ConciergeProvider>
  );
}

describe("Result screen skip/undo -- regression coverage for the flow verified manually during QA review", () => {
  it("renders every item and a cart button counting all of them initially", () => {
    renderResult();
    expect(screen.getByText("Chips & namkeen")).toBeInTheDocument();
    expect(screen.getByText("Soft drinks")).toBeInTheDocument();
    expect(screen.getByText("Dips")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Add 3 to cart" })).toBeInTheDocument();
  });

  it("shows evidence quote + rating only for items that actually have evidence", () => {
    renderResult();
    expect(screen.getByText(/great snacks, arrived fast/)).toBeInTheDocument();
    expect(screen.getAllByText("No direct review evidence -- general suggestion.")).toHaveLength(2);
  });

  it("decrements the cart count when an item is skipped, and updates the pill", async () => {
    const user = userEvent.setup();
    renderResult();
    await user.click(screen.getAllByRole("button", { name: "Skip" })[0]);
    expect(screen.getByRole("button", { name: "Add 2 to cart" })).toBeInTheDocument();
    expect(screen.getByText("2 of 3 items")).toBeInTheDocument();
  });

  it("disables the cart button and reads 'Nothing selected' once every item is skipped", async () => {
    const user = userEvent.setup();
    renderResult();
    for (const btn of screen.getAllByRole("button", { name: "Skip" })) {
      await user.click(btn);
    }
    const cartButton = screen.getByRole("button", { name: "Nothing selected" });
    expect(cartButton).toBeDisabled();
  });

  it("re-enables the cart button when a skipped item is added back", async () => {
    const user = userEvent.setup();
    renderResult();
    for (const btn of screen.getAllByRole("button", { name: "Skip" })) {
      await user.click(btn);
    }
    await user.click(screen.getAllByRole("button", { name: "Add back" })[0]);
    const cartButton = screen.getByRole("button", { name: "Add 1 to cart" });
    expect(cartButton).not.toBeDisabled();
  });

  it("renders the mixed-intent note when present", () => {
    renderResult({ ...fixtureCollection, note: "Also grab milk via search -- not something I curate." });
    expect(screen.getByText(/Also grab milk via search/)).toBeInTheDocument();
  });

  it("does not render a note element when note is null", () => {
    renderResult();
    expect(screen.queryByText(/Also grab/)).not.toBeInTheDocument();
  });
});
