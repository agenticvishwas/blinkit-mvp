import type { CollectionCardItem } from "../types";

const SOURCE_LABEL: Record<string, string> = {
  play_store: "Play Store review",
  app_store: "App Store review",
  reddit: "Reddit",
  product_reviews: "Review site",
};

interface Props {
  item: CollectionCardItem;
  skipped: boolean;
  onToggleSkip: () => void;
}

// Deliberately does NOT show a per-item product rating/price -- this project
// has no real product catalog, only real Blinkit-app review text (see
// agent/retrieval.py's docstring). evidence_rating is the reviewer's own
// star rating for their overall Blinkit experience, shown attached to their
// quote, not presented as a rating of this specific item.
export default function CollectionCard({ item, skipped, onToggleSkip }: Props) {
  return (
    <div
      className={`bg-app-raised border border-canvas-line rounded-2xl p-3.5 mb-2.5 ${skipped ? "opacity-50" : ""}`}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className={`text-sm font-bold ${skipped ? "line-through" : ""}`}>{item.label}</div>
        <button
          onClick={onToggleSkip}
          className={`shrink-0 text-[11px] font-semibold rounded-full px-2.5 py-1 ${
            skipped ? "bg-sand-200 text-ink-700" : "bg-sand-100 text-ink-500"
          }`}
        >
          {skipped ? "Add back" : "Skip"}
        </button>
      </div>
      <p className="text-xs text-ink-700 mb-2">{item.rationale}</p>
      {item.has_evidence ? (
        <div className="bg-sand-100 rounded-xl p-2.5">
          <div className="flex items-center gap-1 text-[11px] font-semibold text-star mb-1">
            {item.evidence_rating != null ? (
              <>
                {"★".repeat(item.evidence_rating)}
                {"☆".repeat(5 - item.evidence_rating)}
              </>
            ) : null}
            <span className="text-ink-500 font-normal ml-1">
              {SOURCE_LABEL[item.evidence_source ?? ""] ?? item.evidence_source}
            </span>
          </div>
          <p className="text-xs italic text-ink-700">"{item.evidence_quote}"</p>
        </div>
      ) : (
        <div className="text-[11px] text-ink-500 italic">No direct review evidence -- general suggestion.</div>
      )}
    </div>
  );
}
