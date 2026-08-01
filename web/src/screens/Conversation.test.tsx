import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ConciergeProvider } from "../state/ConciergeContext";
import Conversation from "./Conversation";
import * as apiClient from "../api/client";

// api/client.ts does a real fetch() against the backend -- mock it so these
// tests are fast, free, and deterministic (the real backend is covered by
// tests/test_agent_loop.py in the Python suite instead).
vi.mock("../api/client", () => ({ converse: vi.fn() }));

function renderConversation() {
  return render(
    <ConciergeProvider>
      <Conversation />
    </ConciergeProvider>
  );
}

describe("Conversation screen -- hybrid-entry chips (docs/phases/phase-5-stretch-hybrid-entry)", () => {
  beforeEach(() => {
    vi.mocked(apiClient.converse).mockReset();
  });

  it("shows both occasion chips before any message is sent", () => {
    renderConversation();
    expect(screen.getByText("🎁 Gifting Corner")).toBeInTheDocument();
    expect(screen.getByText("🎉 Party With Friends")).toBeInTheDocument();
  });

  it("tapping a chip submits its phrase through the same path as typed text", async () => {
    vi.mocked(apiClient.converse).mockResolvedValue({
      type: "clarifying_question",
      question: "How many people?",
      redirect_message: null,
      collection: null,
    });
    const user = userEvent.setup();
    renderConversation();
    await user.click(screen.getByText("🎉 Party With Friends"));

    await waitFor(() => expect(apiClient.converse).toHaveBeenCalledTimes(1));
    expect(apiClient.converse).toHaveBeenCalledWith(
      "Friends are coming over, need snacks and drinks",
      expect.any(Array)
    );
    expect(await screen.findByText("How many people?")).toBeInTheDocument();
  });

  it("hides the chips once a message has been sent (chip or typed)", async () => {
    vi.mocked(apiClient.converse).mockResolvedValue({
      type: "redirect",
      question: null,
      redirect_message: "Use search or Buy Again for that.",
      collection: null,
    });
    const user = userEvent.setup();
    renderConversation();
    await user.type(screen.getByPlaceholderText("Type a reply…"), "I need milk");
    await user.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => expect(screen.queryByText("🎁 Gifting Corner")).not.toBeInTheDocument());
    expect(screen.queryByText("🎉 Party With Friends")).not.toBeInTheDocument();
  });

  it("renders a redirect response inline instead of navigating away", async () => {
    vi.mocked(apiClient.converse).mockResolvedValue({
      type: "redirect",
      question: null,
      redirect_message: "That's a routine reorder -- search or Buy Again will be faster.",
      collection: null,
    });
    const user = userEvent.setup();
    renderConversation();
    await user.type(screen.getByPlaceholderText("Type a reply…"), "I need milk");
    await user.click(screen.getByRole("button", { name: "Send" }));

    expect(await screen.findByText(/routine reorder/)).toBeInTheDocument();
    // Still on the conversation screen -- the input box is still present.
    expect(screen.getByPlaceholderText("Type a reply…")).toBeInTheDocument();
  });
});
