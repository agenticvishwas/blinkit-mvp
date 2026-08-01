"""Retrieval over the vendored Blinkit review corpus.

Ports the retrieval pattern from NLGradProject/discovery_engine/chat_app.py
(same embedding model, same cosine-via-normalized-dot-product approach) with
no runtime dependency on that repo. The corpus here is real App Store / Play
Store review text tagged by the Part 1 pipeline (data/corpus.jsonl) -- there
is no per-product catalog, so `rating` on an Evidence is the reviewer's own
star rating for their overall Blinkit experience, not a product rating.
Callers must not present it as the latter.
"""
import json
import os
from dataclasses import dataclass, field

import numpy as np
from sentence_transformers import SentenceTransformer

EMBED_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "corpus.jsonl")

# Similarity floor below which a match is treated as no evidence rather than a
# forced low-quality one. Chosen empirically in tests/test_retrieval_smoke.py;
# see that file's comment for how it was picked.
DEFAULT_MIN_SIMILARITY = 0.20


@dataclass
class Evidence:
    id: str
    source: str
    text: str
    rating: int | None
    tags: list[str] = field(default_factory=list)
    sentiment: str | None = None
    similarity: float = 0.0


def _load_corpus(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


class RetrievalIndex:
    def __init__(self, records: list[dict], embeddings: np.ndarray, embedder: SentenceTransformer):
        self._records = records
        self._embeddings = embeddings
        self._embedder = embedder

    def search(self, query: str, top_k: int = 5, min_similarity: float = DEFAULT_MIN_SIMILARITY) -> list[Evidence]:
        if not self._records:
            return []
        q_emb = self._embedder.encode([query], normalize_embeddings=True)[0]
        scores = self._embeddings @ q_emb
        top_idx = np.argsort(-scores)[:top_k]
        results = []
        for i in top_idx:
            score = float(scores[i])
            if score < min_similarity:
                continue
            r = self._records[i]
            results.append(
                Evidence(
                    id=r["id"],
                    source=r["source"],
                    text=r["text"],
                    rating=r.get("rating"),
                    tags=r.get("tags", []),
                    sentiment=r.get("sentiment"),
                    similarity=score,
                )
            )
        return results

    def get_by_id(self, evidence_id: str) -> Evidence | None:
        for r in self._records:
            if r["id"] == evidence_id:
                return Evidence(
                    id=r["id"],
                    source=r["source"],
                    text=r["text"],
                    rating=r.get("rating"),
                    tags=r.get("tags", []),
                    sentiment=r.get("sentiment"),
                    similarity=1.0,
                )
        return None


_index_cache: RetrievalIndex | None = None


def build_index(corpus_path: str = DEFAULT_CORPUS_PATH) -> RetrievalIndex:
    records = _load_corpus(corpus_path)
    embedder = SentenceTransformer(EMBED_MODEL)
    if records:
        texts = [r["text"] for r in records]
        embeddings = np.array(embedder.encode(texts, normalize_embeddings=True, show_progress_bar=False))
    else:
        embeddings = np.zeros((0, embedder.get_sentence_embedding_dimension()))
    return RetrievalIndex(records, embeddings, embedder)


def get_index(corpus_path: str = DEFAULT_CORPUS_PATH) -> RetrievalIndex:
    """Process-wide cached index -- embedding 588 records takes a few seconds;
    callers (the API layer, tests) should share one instance per process."""
    global _index_cache
    if _index_cache is None:
        _index_cache = build_index(corpus_path)
    return _index_cache
