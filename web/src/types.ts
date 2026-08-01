// Mirrors api/schemas.py -- keep these two in sync by hand (no shared codegen
// at this project's scale, see docs/phases/phase-2-ui-screens/architecture.md).

export type TurnKind = "clarifying_question" | "collection" | "redirect";

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
  kind?: TurnKind;
}

export interface CollectionCardItem {
  label: string;
  rationale: string;
  has_evidence: boolean;
  evidence_quote: string | null;
  evidence_rating: number | null;
  evidence_source: string | null;
}

export interface Collection {
  occasion_summary: string;
  items: CollectionCardItem[];
  note: string | null;
}

export interface ConverseResponse {
  type: TurnKind;
  question: string | null;
  redirect_message: string | null;
  collection: Collection | null;
}

export type Screen = "home" | "entry" | "conversation" | "result";
