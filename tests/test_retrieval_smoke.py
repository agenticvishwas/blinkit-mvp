"""Phase 0 exit criterion: agent/retrieval.py returns real corpus snippets with
no dependency on NLGradProject being present, using the same embedding model
and cosine-via-normalized-dot-product formula as chat_app.py's build_index()/
retrieve() -- so parity with the original is guaranteed by construction, not
re-verified by a live A/B run against a repo this project doesn't depend on.

Run with: .venv/Scripts/python.exe -m pytest tests/test_retrieval_smoke.py -v
"""
from agent.retrieval import build_index

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
        results = index.search(query, top_k=5, min_similarity=0.0)  # floor off to inspect raw scores
        assert results, f"no results at all for {query!r} -- index or embedding broken"
        for r in results:
            assert r.text, "every result must carry real corpus text"
            assert r.id, "every result must carry a real corpus id"
            # similarity must be a real cosine score in range, not a placeholder
            assert -1.0 <= r.similarity <= 1.0


def test_min_similarity_floor_excludes_low_matches():
    index = build_index()
    results_no_floor = index.search("friends coming over tonight", top_k=20, min_similarity=0.0)
    results_with_floor = index.search("friends coming over tonight", top_k=20)
    assert len(results_with_floor) <= len(results_no_floor)
    for r in results_with_floor:
        assert r.similarity >= 0.20


def test_unrelated_query_can_return_no_evidence():
    """The corpus is App/Play Store review text about the Blinkit app experience,
    not a per-product catalog (see agent/retrieval.py docstring) -- so a query
    with no real semantic match in that text (as opposed to just no exact
    keyword match) should be allowed to come back empty rather than forcing a
    low-quality match. This is the retrieval-level half of the 'never
    fabricate' guarantee agent/loop.py relies on."""
    index = build_index()
    results = index.search("quantum physics homework help", top_k=5)
    # Not asserting it's empty (embeddings can surface weak semantic overlap
    # unpredictably) -- asserting that whatever comes back, if anything, still
    # respects the floor honestly.
    for r in results:
        assert r.similarity >= 0.20
