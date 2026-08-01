import { useConcierge } from "./state/ConciergeContext";
import Home from "./screens/Home";
import Entry from "./screens/Entry";
import Conversation from "./screens/Conversation";
import Result from "./screens/Result";

export default function App() {
  const { state } = useConcierge();

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center p-8">
      <div className="w-[390px] h-[780px] bg-app-bg rounded-phone shadow-phone overflow-hidden flex flex-col relative">
        {state.screen === "home" && <Home />}
        {state.screen === "entry" && <Entry />}
        {state.screen === "conversation" && <Conversation />}
        {state.screen === "result" && <Result />}
      </div>
    </div>
  );
}
