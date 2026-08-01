"""Pydantic request/response models for the /api/converse endpoint. Mirror
agent/schema.py's dataclasses field-for-field -- see docs/phases/phase-2-ui-screens/
architecture.md's "Risks" section on why these two must be kept in sync by hand."""
from typing import Literal

from pydantic import BaseModel, field_validator


class ChatTurnIn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    kind: Literal["clarifying_question", "collection", "redirect"] | None = None


class ConverseRequest(BaseModel):
    message: str
    chat_history: list[ChatTurnIn] = []

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        # An empty/whitespace-only message has no occasion content for the model
        # to respond to and was observed to make it return a shape _parse_response
        # can't classify, surfacing as an unhandled 500 -- reject it here (422)
        # instead, at the actual system boundary, rather than forwarding garbage in.
        if not v.strip():
            raise ValueError("message must not be empty or whitespace-only")
        return v


class CollectionCardItemOut(BaseModel):
    label: str
    rationale: str
    has_evidence: bool
    evidence_quote: str | None = None
    evidence_rating: int | None = None
    evidence_source: str | None = None


class CollectionOut(BaseModel):
    occasion_summary: str
    items: list[CollectionCardItemOut]
    note: str | None = None


class ConverseResponse(BaseModel):
    type: Literal["clarifying_question", "collection", "redirect"]
    question: str | None = None
    redirect_message: str | None = None
    collection: CollectionOut | None = None
