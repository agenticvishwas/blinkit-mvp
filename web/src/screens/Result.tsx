import { useState } from "react";
import CollectionCard from "../components/CollectionCard";
import { useConcierge } from "../state/ConciergeContext";

// Screen 04 -- renders agent.loop's real Collection output, not placeholder
// data. Mock "add all to cart" only touches local state, per
// docs/phases/phase-2-ui-screens/architecture.md (no real cart integration --
// this is a standalone prototype layered onto, not replacing, the storefront).
export default function Result() {
  const { state, dispatch } = useConcierge();
  const collection = state.collection;

  // Which items the user has skipped -- local to this screen (not global
  // ConciergeState) since it's just cart-inclusion UI state, reset naturally
  // whenever a fresh collection is set.
  const [skipped, setSkipped] = useState<Set<number>>(new Set());

  if (!collection) {
    return (
      <div className="flex items-center justify-center h-full text-sm text-ink-500">
        No collection yet -- go back and describe an occasion.
      </div>
    );
  }

  function toggleSkip(index: number) {
    setSkipped((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  const includedCount = collection.items.length - skipped.size;

  return (
    <div className="flex flex-col h-full bg-app-bg">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-canvas-line">
        <button onClick={() => dispatch({ type: "GO_TO", screen: "conversation" })} aria-label="Back">
          ←
        </button>
      </div>

      <div className="px-4 py-3 border-b border-canvas-line">
        <div className="flex items-center justify-between">
          <h4 className="text-base font-extrabold">{collection.occasion_summary}</h4>
          <span className="text-[11px] font-semibold bg-sand-100 rounded-full px-2 py-0.5">
            {includedCount < collection.items.length
              ? `${includedCount} of ${collection.items.length} items`
              : `${collection.items.length} items`}
          </span>
        </div>
        <p className="text-xs text-ink-500 mt-0.5">Picked from real Blinkit reviews -- skip anything you don't want</p>
        {collection.note && (
          <p className="text-xs text-coral-600 bg-coral-100 rounded-lg px-2.5 py-1.5 mt-2">{collection.note}</p>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        {collection.items.map((item, i) => (
          <CollectionCard key={i} item={item} skipped={skipped.has(i)} onToggleSkip={() => toggleSkip(i)} />
        ))}
      </div>

      <div className="px-4 py-3 border-t border-canvas-line">
        <button
          onClick={() => dispatch({ type: "RESET" })}
          disabled={includedCount === 0}
          className="w-full bg-coral-500 text-white rounded-full py-3 text-sm font-bold disabled:opacity-40"
        >
          {includedCount === 0 ? "Nothing selected" : `Add ${includedCount} to cart`}
        </button>
      </div>
    </div>
  );
}
