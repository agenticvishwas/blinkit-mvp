"""Phase 1 exit criterion: the real agent loop, against the real Claude API.
Costs real API calls -- skipped automatically unless ANTHROPIC_API_KEY is set
(e.g. in a local .env), so it never runs unintentionally in an environment
without a key configured.

Run with: .venv/Scripts/python.exe -m pytest tests/test_agent_loop.py -v -s
"""
import os

import pytest
from dotenv import load_dotenv

load_dotenv()

from agent.loop import ConciergeLoop
from agent.retrieval import build_index
from agent.schema import ChatTurn

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY not set -- see .env.example"
)

# Occasion language from NLGradProject/docs/part2.md interviews, same set Phase 3's
# committed eval uses -- kept small here since this is a build-time sanity check,
# not the full regression suite (that's docs/phases/phase-3-guardrails-eval).
OCCASION_PROMPTS = [
    "friends are coming over tonight",
    "gift for a 5 year old",
    "gym essentials",
]
REORDER_PROMPTS = ["I need milk", "add eggs"]
# Mixed intent: a routine item mentioned alongside genuine occasion content --
# must NOT be fully redirected (found live during QA review, see
# docs/phases/phase-1-agent-core/architecture.md revision notes).
MIXED_INTENT_PROMPTS = ["add milk for my party tonight"]


@pytest.fixture(scope="module")
def loop():
    return ConciergeLoop(index=build_index())


def test_occasion_prompts_never_fabricate_evidence(loop):
    for prompt in OCCASION_PROMPTS:
        response, evidence = loop.run(prompt)
        assert response.type in ("clarifying_question", "collection")
        if response.type == "collection":
            evidence_texts = [e.text for e in evidence]
            for item in response.collection.items:
                if item.has_evidence:
                    # evidence_quote is a snippet (agent/loop.py's _snippet), not
                    # necessarily the full text -- must still be a genuine prefix
                    # of some retrieved record, never free-floating model text.
                    quote = item.evidence_quote.rstrip("…")
                    assert any(quote in text for text in evidence_texts), (
                        f"item {item.label!r} claims evidence not actually retrieved this turn"
                    )
                    assert len(item.evidence_quote) <= 201, "evidence_quote should be a short snippet, not a full review"


def test_reorder_prompts_are_redirected_not_answered(loop):
    for prompt in REORDER_PROMPTS:
        response, _evidence = loop.run(prompt)
        assert response.type == "redirect", f"{prompt!r} should redirect, got type={response.type!r}"


def test_mixed_intent_gets_help_not_full_redirect(loop):
    for prompt in MIXED_INTENT_PROMPTS:
        response, _evidence = loop.run(prompt)
        assert response.type in ("collection", "clarifying_question"), (
            f"{prompt!r} has real occasion content and should not be fully redirected, got type={response.type!r}"
        )


def test_at_most_one_clarifying_question_per_conversation(loop):
    response1, _ = loop.run("friends are coming over")
    history = [ChatTurn(role="user", content="friends are coming over")]
    if response1.type == "clarifying_question":
        history.append(ChatTurn(role="assistant", content=response1.question, kind="clarifying_question"))
        response2, _ = loop.run("about 5 people, just snacks", history)
        assert response2.type != "clarifying_question", "asked a second clarifying question in one conversation"
