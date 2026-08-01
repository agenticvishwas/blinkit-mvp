import HomeChrome from "../components/HomeChrome";
import { useConcierge } from "../state/ConciergeContext";

// Screen 02 -- Screen 01 plus the one coral prompt card. Tapping it is pure
// navigation into the conversation; no API call happens on this screen.
export default function Entry() {
  const { dispatch } = useConcierge();

  const promptCard = (
    <button
      onClick={() => dispatch({ type: "GO_TO", screen: "conversation" })}
      className="w-full flex items-center gap-3 bg-coral-500 text-white rounded-2xl px-4 py-3 mb-3 text-left"
    >
      <div className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center shrink-0">💬</div>
      <div className="flex-1">
        <div className="text-sm font-bold">Planning something?</div>
        <div className="text-xs text-white/85">Tell Blinkit the occasion</div>
      </div>
      <span>›</span>
    </button>
  );

  return <HomeChrome promptCard={promptCard} />;
}
