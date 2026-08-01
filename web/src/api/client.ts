import type { ChatTurn, ConverseResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export async function converse(message: string, chatHistory: ChatTurn[]): Promise<ConverseResponse> {
  const res = await fetch(`${API_BASE_URL}/api/converse`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, chat_history: chatHistory }),
  });
  if (!res.ok) {
    throw new Error(`Concierge API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}
