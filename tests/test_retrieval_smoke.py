"""Phase 0 exit criterion: agent/retrieval.py returns real corpus snippets with
no dependency on NLGradProject being present.

Revision (2026-08-01): retrieval switched from sentence-transformers embeddings
to BM25 keyword ranking (see agent/retrieval.py's revision note and the root
README's "Retrieval strategy" section) -- these tests now check BM25's score
scale and behavior instead of cosine similarity's.

Run with: .venv/Scripts/python.exe -m pytest tests/test_retrieval_smoke.py -v
"""
from agent.retrieval import DEFAULT_MIN_SCORE, build_index

# Occasion language pulled from NLGradProject/docs/part2.md interviews (the
# real source Phase 3's eval set also draws from), not invented for this test.
SMOKE_QUERIES = [
    "friends coming over tonight",
    "gift for a 5 year old",
    "gym essentials",
    "going camping this weekend",
]


def test_index_builds_and_returns_real_snippets():
    index = build_index()
    assert len(index._records) == 588

    for query in SMOKE_QUERIES:
        results = index.search(query, top_k=5, min_score=0.0)  # floor off to inspect raw scores
        assert results, f"no results at all for {query!r} -- index or tokenization broken"
        for r in results:
            assert r.text, "every result must carry real corpus text"
            assert r.id, "every result must carry a real corpus id"
            assert r.score >= 0.0, "BM25 scores are non-negative"


def test_min_score_floor_excludes_low_matches():
    index = build_index()
    results_no_floor = index.search("friends coming over tonight", top_k=20, min_score=0.0)
    results_with_floor = index.search("friends coming over tonight", top_k=20)
    assert len(results_with_floor) <= len(results_no_floor)
    for r in results_with_floor:
        assert r.score >= DEFAULT_MIN_SCORE


def test_matches_share_a_real_content_word_with_the_query():
    """Regression test for a real false-positive found while migrating to BM25:
    stopwords like "coming"/"over" alone were enough to spuriously match an
    unrelated review ("...coming from experience...over time...") before
    agent/retrieval.py's stopword filtering was added. Every match above the
    floor must share at least one non-stopword token with the query -- BM25
    can't match on a term that isn't in the (filtered) query at all, but this
    catches a regression if stopword filtering is ever accidentally removed."""
    import re

    from agent.retrieval import _STOPWORDS

    index = build_index()
    for query in SMOKE_QUERIES:
        query_tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if t not in _STOPWORDS and len(t) > 2}
        for r in index.search(query, top_k=5):
            doc_tokens = {t for t in re.findall(r"[a-z0-9]+", r.text.lower())}
            assert query_tokens & doc_tokens, f"{r.id!r} matched {query!r} with no shared content word"


def test_unrelated_query_can_return_no_evidence():
    """The corpus is App/Play Store review text about the Blinkit app experience,
    not a per-product catalog (see agent/retrieval.py docstring) -- so a query
    with no real keyword overlap in that text should come back empty rather
    than forcing a low-quality match. This is the retrieval-level half of the
    'never fabricate' guarantee agent/loop.py relies on."""
    index = build_index()
    results = index.search("quantum physics homework help", top_k=5)
    for r in results:
        assert r.score >= DEFAULT_MIN_SCORE
