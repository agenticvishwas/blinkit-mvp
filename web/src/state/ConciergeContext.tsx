import React, { createContext, useContext, useReducer, type ReactNode } from "react";
import type { ChatTurn, Collection, Screen } from "../types";

interface ConciergeState {
  screen: Screen;
  chatHistory: ChatTurn[];
  clarifyingQuestionPending: boolean;
  collection: Collection | null;
}

type Action =
  | { type: "GO_TO"; screen: Screen }
  | { type: "APPEND_TURN"; turn: ChatTurn }
  | { type: "SET_COLLECTION"; collection: Collection }
  | { type: "RESET" };

// Starts at "entry", not "home": Screen 01 is the untouched baseline kept
// only for the pixel-parity comparison in docs/differentiation.md #1 -- it has
// no navigation into the rest of the app by design (nothing on it changed).
// The live product a real user opens is Screen 02's state (Screen 01 plus the
// one prompt card), so that's where this app actually starts.
const initialState: ConciergeState = {
  screen: "entry",
  chatHistory: [],
  clarifyingQuestionPending: false,
  collection: null,
};

function reducer(state: ConciergeState, action: Action): ConciergeState {
  switch (action.type) {
    case "GO_TO":
      return { ...state, screen: action.screen };
    case "APPEND_TURN": {
      const next = { ...state, chatHistory: [...state.chatHistory, action.turn] };
      if (action.turn.role === "assistant") {
        if (action.turn.kind === "clarifying_question") {
          if (state.clarifyingQuestionPending) {
            // A second clarifying question in one conversation is a Phase 1
            // prompt regression, not something the UI should silently accept --
            // surface it rather than quietly allowing an unbounded back-and-forth.
            console.warn(
              "Concierge asked a second clarifying question in one conversation -- this indicates a prompt regression (see docs/phases/phase-3-guardrails-eval)."
            );
          }
          next.clarifyingQuestionPending = true;
        } else {
          next.clarifyingQuestionPending = false;
        }
      }
      return next;
    }
    case "SET_COLLECTION":
      return { ...state, collection: action.collection, screen: "result" };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const ConciergeContext = createContext<{ state: ConciergeState; dispatch: React.Dispatch<Action> } | null>(null);

export function ConciergeProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return <ConciergeContext.Provider value={{ state, dispatch }}>{children}</ConciergeContext.Provider>;
}

export function useConcierge() {
  const ctx = useContext(ConciergeContext);
  if (!ctx) throw new Error("useConcierge must be used within ConciergeProvider");
  return ctx;
}
