"""Retrieval over the vendored Blinkit review corpus.

Revision (2026-08-01): originally embedding-based (sentence-transformers +
cosine similarity). Switched to BM25 keyword ranking because torch +
sentence-transformers was too heavy for a free-tier host's memory (~512MB) --
see the "Retrieval strategy" section in the root README.md for the full
tradeoff writeup. `rank_bm25` depends only on `numpy` (already required), no
large binaries, no model download, near-instant startup.

The corpus here is real App Store / Play Store review text tagged by the
Part 1 pipeline (data/corpus.jsonl) -- there is no per-product catalog, so
`rating` on an Evidence is the reviewer's own star rating for their overall
Blinkit experience, not a product rating. Callers must not present it as the
latter.
"""
import json
import os
import re
from dataclasses import dataclass, field

from rank_bm25 import BM25Okapi

DEFAULT_CORPUS_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "corpus.jsonl")

# BM25 scores are unbounded (unlike cosine similarity's [0,1]) and vary with
# corpus/query length, so this floor was picked empirically by inspecting
# real scores against occasion queries from NLGradProject/docs/part2.md
# during the embedding->BM25 migration: matches built on a single coincidental
# stopword-adjacent overlap scored ~3-4, matches with a genuine shared
# content word (e.g. "gift", "gym", "party") scored ~5+. Revisit if quality
# issues emerge -- this is a starting point, not a validated threshold.
DEFAULT_MIN_SCORE = 4.5

# Common English function words excluded from tokenization -- without this,
# BM25 was observed matching purely on words like "coming"/"over" in
# unrelated sentences (e.g. "coming over tonight" spuriously matching a
# review about "coming from experience... learning Kannada... over time"),
# which defeats the point of a relevance floor.
_STOPWORDS = frozenset(
    """a an the and or but if then else for to of in on at by with from up down over under
    again further once here there all any both each few more most other some such no nor not only
    own same so than too very can will just don dont should now is am are was were be been being do
    does did having have has had this that these those i me my myself you your yours he him his she
    her it its we us our they them their what which who whom as its im ive youre youve theyre were""".split()
)


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOPWORDS and len(t) > 2]


@dataclass
class Evidence:
    id: str
    source: str
    text: str
    rating: int | None
    tags: list[str] = field(default_factory=list)
    sentiment: str | None = None
    score: float = 0.0


def _load_corpus(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _to_evidence(record: dict, score: float) -> Evidence:
    return Evidence(
        id=record["id"],
        source=record["source"],
        text=record["text"],
        rating=record.get("rating"),
        tags=record.get("tags", []),
        sentiment=record.get("sentiment"),
        score=score,
    )


class RetrievalIndex:
    def __init__(self, records: list[dict], bm25: BM25Okapi | None):
        self._records = records
        self._bm25 = bm25

    def search(self, query: str, top_k: int = 5, min_score: float = DEFAULT_MIN_SCORE) -> list[Evidence]:
        if not self._records or self._bm25 is None:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scores = self._bm25.get_scores(query_tokens)
        top_idx = sorted(range(len(scores)), key=lambda i: -scores[i])[:top_k]
        results = []
        for i in top_idx:
            score = float(scores[i])
            if score < min_score:
                continue
            results.append(_to_evidence(self._records[i], score))
        return results

    def get_by_id(self, evidence_id: str) -> Evidence | None:
        for r in self._records:
            if r["id"] == evidence_id:
                return _to_evidence(r, score=0.0)
        return None


_index_cache: RetrievalIndex | None = None


def build_index(corpus_path: str = DEFAULT_CORPUS_PATH) -> RetrievalIndex:
    records = _load_corpus(corpus_path)
    if not records:
        return RetrievalIndex(records, None)
    tokenized_corpus = [_tokenize(r["text"]) for r in records]
    bm25 = BM25Okapi(tokenized_corpus)
    return RetrievalIndex(records, bm25)


def get_index(corpus_path: str = DEFAULT_CORPUS_PATH) -> RetrievalIndex:
    """Process-wide cached index -- callers (the API layer, tests) should
    share one instance per process. BM25 indexing 588 records is well under a
    second, unlike the embedding model this replaced, but the cache is still
    useful to avoid redundant work per request."""
    global _index_cache
    if _index_cache is None:
        _index_cache = build_index(corpus_path)
    return _index_cache
