"""Shared data shapes for the agent loop and its API wrapper. Kept dependency-free
(no pydantic here) so agent/ has no framework coupling -- api/schemas.py mirrors
these as pydantic models for request/response validation at the HTTP boundary."""
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ChatTurn:
    role: Literal["user", "assistant"]
    content: str
    kind: Literal["clarifying_question", "collection", "redirect"] | None = None


@dataclass
class CollectionCardItem:
    label: str
    rationale: str
    has_evidence: bool
    evidence_quote: str | None = None
    evidence_rating: int | None = None
    evidence_source: str | None = None


@dataclass
class Collection:
    occasion_summary: str
    items: list[CollectionCardItem] = field(default_factory=list)
    note: str | None = None


@dataclass
class AgentResponse:
    type: Literal["clarifying_question", "collection", "redirect"]
    question: str | None = None
    redirect_message: str | None = None
    collection: Collection | None = None
