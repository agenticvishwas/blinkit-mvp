"""The Occasion Concierge agent loop: one turn in, one AgentResponse out.

Retrieval happens in Python (not as a model-invoked tool call) before the
Claude call, same shape as NLGradProject/discovery_engine/chat_app.py's
`ask()`. The model is then forced (tool_choice) to call a single `respond`
tool for structured output, same pattern as that repo's `generate_hypotheses`.

The strongest anti-fabrication guarantee lives here, not just in the prompt:
the review text and rating shown to the user are always read directly out of
the evidence retrieved this turn by Python, keyed by evidence_id -- the model
never gets to originate quote text itself. If the model cites an evidence_id
that wasn't actually retrieved this turn, that item is downgraded to
"no evidence" in code, not trusted.
"""
import logging

import anthropic

from agent.prompts import RESPOND_TOOL, build_system_prompt
from agent.retrieval import RetrievalIndex, Evidence, get_index
from agent.schema import AgentResponse, ChatTurn, Collection, CollectionCardItem

logger = logging.getLogger(__name__)

CHAT_MODEL = "claude-sonnet-5"
TOP_K = 5
SNIPPET_MAX_LEN = 200


def _snippet(text: str, max_len: int = SNIPPET_MAX_LEN) -> str:
    """A trust-signal quote should read like the short excerpts in
    design/mockup.html ("crispy, didn't disappoint for a party"), not the full
    review -- some corpus entries are multi-paragraph essays (observed live,
    see docs/phases/phase-3-guardrails-eval risk notes). Cuts at the last word
    boundary before max_len rather than mid-word. Always a prefix of the real
    text, so it stays a valid substring for the fabrication check."""
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rsplit(" ", 1)[0]
    return f"{cut}…"


def _format_evidence_block(evidence: list[Evidence]) -> str:
    if not evidence:
        return "(No evidence retrieved for this message -- nothing cleared the relevance floor.)"
    lines = []
    for e in evidence:
        lines.append(f'- id="{e.id}" source={e.source} rating={e.rating}: "{e.text[:300]}"')
    return "\n".join(lines)


def _clarifying_already_asked(chat_history: list[ChatTurn]) -> bool:
    return any(t.role == "assistant" and t.kind == "clarifying_question" for t in chat_history)


def _build_messages(message: str, chat_history: list[ChatTurn], evidence: list[Evidence], already_asked: bool) -> list[dict]:
    messages = [{"role": t.role, "content": t.content} for t in chat_history]
    note = (
        "[System note: you already asked your one allowed clarifying question earlier in "
        "this conversation. You must respond with type=collection or type=redirect now, not "
        "another clarifying_question.]\n\n"
        if already_asked
        else ""
    )
    augmented = f"{note}{message}\n\nRetrieved evidence:\n{_format_evidence_block(evidence)}"
    messages.append({"role": "user", "content": augmented})
    return messages


def _infer_type(tool_input: dict) -> str | None:
    """The `type` field is marked required in RESPOND_TOOL's schema, but a forced
    tool_choice is a strong nudge, not a schema-conformance guarantee -- observed in
    practice (see tests/test_agent_loop.py) the model can omit it while still filling
    in a self-consistent set of the other fields. Infer from shape rather than failing
    a well-formed response over one missing label."""
    resp_type = tool_input.get("type")
    if resp_type in ("clarifying_question", "redirect", "collection"):
        return resp_type
    if tool_input.get("items") is not None or tool_input.get("occasion_summary"):
        return "collection"
    if tool_input.get("question"):
        return "clarifying_question"
    if tool_input.get("redirect_message"):
        return "redirect"
    return None


def _parse_response(tool_input: dict, evidence: list[Evidence]) -> AgentResponse:
    evidence_by_id = {e.id: e for e in evidence}
    resp_type = _infer_type(tool_input)

    if resp_type == "clarifying_question":
        return AgentResponse(type="clarifying_question", question=tool_input.get("question", "").strip() or "Could you tell me a bit more about the occasion?")

    if resp_type == "redirect":
        return AgentResponse(
            type="redirect",
            redirect_message=tool_input.get("redirect_message", "").strip()
            or "That looks like a regular reorder -- search or Buy Again will be faster for that.",
        )

    if resp_type == "collection":
        items = []
        for raw_item in tool_input.get("items", []):
            evidence_id = raw_item.get("evidence_id")
            label = raw_item.get("label", "").strip()
            rationale = raw_item.get("rationale", "").strip()
            if not label:
                continue
            matched = evidence_by_id.get(evidence_id) if evidence_id else None
            if evidence_id and not matched:
                # Model cited an id we didn't actually retrieve this turn -- do not
                # trust it. This is the code-level fabrication guard, not just prompting.
                logger.warning("Dropping unverifiable evidence_id=%r cited for item %r", evidence_id, label)
            items.append(
                CollectionCardItem(
                    label=label,
                    rationale=rationale,
                    has_evidence=matched is not None,
                    evidence_quote=_snippet(matched.text) if matched else None,
                    evidence_rating=matched.rating if matched else None,
                    evidence_source=matched.source if matched else None,
                )
            )
        note = tool_input.get("note")
        collection = Collection(
            occasion_summary=tool_input.get("occasion_summary", "").strip() or "Suggestions for your occasion",
            items=items,
            note=note.strip() if isinstance(note, str) and note.strip() else None,
        )
        return AgentResponse(type="collection", collection=collection)

    # Defense in depth: api/schemas.py now rejects blank messages at the HTTP
    # boundary (the concrete case observed to trigger this), but if the model
    # ever returns a genuinely unclassifiable shape for some other reason, fail
    # soft -- ask a generic clarifying question -- rather than raising and
    # surfacing an unhandled 500 to the user.
    logger.warning("Could not classify model response, tool_input=%r -- falling back to a clarifying question", tool_input)
    return AgentResponse(
        type="clarifying_question",
        question="Sorry, I didn't quite catch that -- could you tell me what you're shopping for?",
    )


class ConciergeLoop:
    def __init__(self, index: RetrievalIndex | None = None, client: anthropic.Anthropic | None = None):
        self._index = index or get_index()
        self._client = client or anthropic.Anthropic()

    def run(self, message: str, chat_history: list[ChatTurn] | None = None) -> tuple[AgentResponse, list[Evidence]]:
        chat_history = chat_history or []
        already_asked = _clarifying_already_asked(chat_history)
        evidence = self._index.search(message, top_k=TOP_K)
        messages = _build_messages(message, chat_history, evidence, already_asked)

        resp = self._client.messages.create(
            model=CHAT_MODEL,
            max_tokens=1024,
            system=build_system_prompt(),
            tools=[RESPOND_TOOL],
            tool_choice={"type": "tool", "name": "respond"},
            messages=messages,
        )

        tool_input = None
        for block in resp.content:
            if block.type == "tool_use" and block.name == "respond":
                tool_input = block.input
                break
        if tool_input is None:
            raise RuntimeError("Model did not call the respond tool")

        agent_response = _parse_response(tool_input, evidence)

        if agent_response.type == "clarifying_question" and already_asked:
            logger.warning("Model asked a second clarifying question in one conversation -- prompt regression, see Phase 3 eval.")

        return agent_response, evidence


_loop_singleton: ConciergeLoop | None = None


def get_loop() -> ConciergeLoop:
    global _loop_singleton
    if _loop_singleton is None:
        _loop_singleton = ConciergeLoop()
    return _loop_singleton
