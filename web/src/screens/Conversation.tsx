import { useState } from "react";
import ChatBubble from "../components/ChatBubble";
import { useConcierge } from "../state/ConciergeContext";
import { converse } from "../api/client";

const GREETING = "Hey! Tell me what's coming up and I'll put together a list -- with real ratings and reviews, not guesses.";

// Hybrid-entry chips (docs/phases/phase-5-stretch-hybrid-entry/architecture.md):
// seeded only from occasion categories with real precedent -- these two are
// confirmed live merchandising tiles from the production audit in
// docs/differentiation.md #1, not invented. Tapping one populates and submits
// the same free-text path a typed message goes through, so it doesn't touch
// agent/loop.py's contract at all.
const OCCASION_CHIPS: { label: string; phrase: string }[] = [
  { label: "🎁 Gifting Corner", phrase: "I need a gift for someone" },
  { label: "🎉 Party With Friends", phrase: "Friends are coming over, need snacks and drinks" },
];

// Screen 03 -- the first screen that talks to the API. A "redirect" response
// (reorder-mode request) is rendered inline and the user stays here, per H3:
// the Concierge never produces a collection for a routine reorder message.
export default function Conversation() {
  const { state, dispatch } = useConcierge();
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend(override?: string) {
    const message = (override ?? draft).trim();
    if (!message || sending) return;
    setDraft("");
    setError(null);
    dispatch({ type: "APPEND_TURN", turn: { role: "user", content: message } });

    setSending(true);
    try {
      const response = await converse(message, [...state.chatHistory, { role: "user", content: message }]);

      if (response.type === "clarifying_question") {
        dispatch({
          type: "APPEND_TURN",
          turn: { role: "assistant", content: response.question ?? "", kind: "clarifying_question" },
        });
      } else if (response.type === "redirect") {
        dispatch({
          type: "APPEND_TURN",
          turn: { role: "assistant", content: response.redirect_message ?? "", kind: "redirect" },
        });
      } else if (response.type === "collection" && response.collection) {
        dispatch({ type: "SET_COLLECTION", collection: response.collection });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong reaching the Concierge.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="flex flex-col h-full bg-app-bg">
      <div className="flex items-center gap-3 px-4 py-3 border-b border-canvas-line">
        <button onClick={() => dispatch({ type: "GO_TO", screen: "entry" })} aria-label="Back">
          ←
        </button>
        <div className="flex-1">
          <div className="text-sm font-bold">Occasion Concierge</div>
          <div className="text-[11px] text-ink-500">grounded in real reviews</div>
        </div>
        <button onClick={() => dispatch({ type: "RESET" })} aria-label="Close">
          ✕
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-3">
        <ChatBubble role="assistant" content={GREETING} />
        {state.chatHistory.length === 0 && (
          <div className="flex gap-2 mb-2 flex-wrap">
            {OCCASION_CHIPS.map((chip) => (
              <button
                key={chip.label}
                onClick={() => handleSend(chip.phrase)}
                disabled={sending}
                className="text-xs font-semibold bg-coral-100 text-coral-600 rounded-full px-3 py-1.5 disabled:opacity-40"
              >
                {chip.label}
              </button>
            ))}
          </div>
        )}
        {state.chatHistory.map((turn, i) => (
          <ChatBubble key={i} role={turn.role} content={turn.content} />
        ))}
        {sending && (
          <div className="flex justify-start mb-2">
            <div className="bg-sand-100 rounded-2xl rounded-bl-sm px-3.5 py-2.5 text-sm text-ink-500">…</div>
          </div>
        )}
        {error && <div className="text-xs text-coral-600 mt-2">{error}</div>}
      </div>

      <div className="flex items-center gap-2 px-4 py-3 border-t border-canvas-line">
        <input
          className="flex-1 bg-sand-100 rounded-full px-4 py-2.5 text-sm outline-none"
          placeholder="Type a reply…"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          disabled={sending}
        />
        <button
          onClick={() => handleSend()}
          disabled={sending || !draft.trim()}
          className="w-9 h-9 rounded-full bg-coral-500 text-white flex items-center justify-center disabled:opacity-40"
          aria-label="Send"
        >
          ➤
        </button>
      </div>
    </div>
  );
}
