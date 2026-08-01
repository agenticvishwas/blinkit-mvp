"""Thin FastAPI service wrapping agent/loop.py -- see docs/phases/phase-2-ui-screens/
architecture.md. This process is the only one that ever holds ANTHROPIC_API_KEY;
the web/ SPA only ever talks to this over HTTP.

Run with: .venv/Scripts/python.exe -m uvicorn api.main:app --reload --port 8000
"""
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from agent.loop import get_loop
from agent.schema import ChatTurn
from api.schemas import CollectionCardItemOut, CollectionOut, ConverseRequest, ConverseResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Eagerly build the retrieval index (BM25 over the 588-record corpus, see
    # agent/retrieval.py) at startup instead of lazily on the first real
    # /api/converse call. Originally added when retrieval was embedding-based
    # (sentence-transformers + torch) and slow/memory-heavy enough on a
    # free-tier host to surface as a confusing 502 on someone's first message
    # -- BM25 indexing is fast enough now that this matters less, but the
    # principle still holds: a startup failure shows up clearly in deploy
    # logs instead of hiding inside a user's first request.
    logger.info("Warming retrieval index at startup...")
    get_loop()
    logger.info("Retrieval index ready.")
    yield


app = FastAPI(title="Occasion Concierge API", lifespan=lifespan)

# CORS_ORIGINS: comma-separated exact origins, e.g. "https://occasion-concierge.vercel.app".
# Defaults to the local Vite dev server only -- never falls back to "*", per
# Phase 2/4's CORS requirement (an open policy risks unrelated sites spending
# this service's ANTHROPIC_API_KEY through a user's browser).
_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
ALLOWED_ORIGINS = [o.strip() for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    # This is an API-only service with no page to render at "/" -- exists so a
    # bare hit to the deployed URL (a health-check probe, or a browser visiting
    # the Render URL directly) gets a 200 instead of a 404. Real health checks
    # should still point at /api/health.
    return {"service": "occasion-concierge-api", "docs": "/docs", "health": "/api/health"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/converse", response_model=ConverseResponse)
def converse(req: ConverseRequest) -> ConverseResponse:
    chat_history = [ChatTurn(role=t.role, content=t.content, kind=t.kind) for t in req.chat_history]
    agent_response, _evidence = get_loop().run(req.message, chat_history)

    collection_out = None
    if agent_response.collection is not None:
        collection_out = CollectionOut(
            occasion_summary=agent_response.collection.occasion_summary,
            items=[
                CollectionCardItemOut(
                    label=i.label,
                    rationale=i.rationale,
                    has_evidence=i.has_evidence,
                    evidence_quote=i.evidence_quote,
                    evidence_rating=i.evidence_rating,
                    evidence_source=i.evidence_source,
                )
                for i in agent_response.collection.items
            ],
            note=agent_response.collection.note,
        )

    return ConverseResponse(
        type=agent_response.type,
        question=agent_response.question,
        redirect_message=agent_response.redirect_message,
        collection=collection_out,
    )
