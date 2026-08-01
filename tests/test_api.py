"""API contract tests -- mock ConciergeLoop.run so these don't spend real
Claude API calls or need ANTHROPIC_API_KEY. What's under test is the FastAPI
request/response translation (api/main.py + api/schemas.py), not the model's
behavior -- that's tests/test_agent_loop.py's job, against the real API.

Run with: .venv/Scripts/python.exe -m pytest tests/test_api.py -v
"""
from unittest.mock import patch

from fastapi.testclient import TestClient

from agent.schema import AgentResponse, Collection, CollectionCardItem


def _client():
    from api.main import app

    return TestClient(app)


@patch("api.main.get_loop")
def test_converse_returns_collection_shape(mock_get_loop):
    mock_loop = mock_get_loop.return_value
    mock_loop.run.return_value = (
        AgentResponse(
            type="collection",
            collection=Collection(
                occasion_summary="Snacks for friends coming over",
                items=[
                    CollectionCardItem(
                        label="Chips & namkeen",
                        rationale="Real user ordered last-minute snacks, delivered in 10 mins.",
                        has_evidence=True,
                        evidence_quote="fast delivery great app, ordered snacks last minute",
                        evidence_rating=5,
                        evidence_source="play_store",
                    )
                ],
            ),
        ),
        [],
    )
    resp = _client().post("/api/converse", json={"message": "friends coming over", "chat_history": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "collection"
    assert body["collection"]["occasion_summary"] == "Snacks for friends coming over"
    assert body["collection"]["items"][0]["has_evidence"] is True
    assert body["collection"]["items"][0]["evidence_quote"].startswith("fast delivery")


@patch("api.main.get_loop")
def test_converse_returns_clarifying_question_shape(mock_get_loop):
    mock_loop = mock_get_loop.return_value
    mock_loop.run.return_value = (AgentResponse(type="clarifying_question", question="How many people?"), [])
    resp = _client().post("/api/converse", json={"message": "friends coming over", "chat_history": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "clarifying_question"
    assert body["question"] == "How many people?"
    assert body["collection"] is None


@patch("api.main.get_loop")
def test_converse_returns_redirect_shape(mock_get_loop):
    mock_loop = mock_get_loop.return_value
    mock_loop.run.return_value = (
        AgentResponse(type="redirect", redirect_message="Use search or Buy Again for that."),
        [],
    )
    resp = _client().post("/api/converse", json={"message": "I need milk", "chat_history": []})
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "redirect"
    assert "Buy Again" in body["redirect_message"]


@patch("api.main.get_loop")
def test_blank_message_is_rejected_not_500(mock_get_loop):
    """Regression test: an empty/whitespace message used to reach the model and
    come back in a shape _parse_response couldn't classify, raising an unhandled
    ValueError that surfaced as a 500. Must now be rejected at the boundary (422)
    before ever reaching the loop -- get_loop().run must not even be called."""
    client = _client()
    for bad_message in ["", "   ", "\n\t"]:
        resp = client.post("/api/converse", json={"message": bad_message, "chat_history": []})
        assert resp.status_code == 422, f"{bad_message!r} should be rejected, got {resp.status_code}"
    mock_get_loop.return_value.run.assert_not_called()


def test_health_endpoint():
    resp = _client().get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@patch("api.main.get_loop")
def test_lifespan_warms_the_index_at_startup(mock_get_loop):
    """Regression test: the FastAPI lifespan handler must call get_loop() once
    on startup (agent/retrieval.py's build_index -- slow/memory-heavy) so that
    cost happens at boot and shows up in deploy logs, not hidden inside a
    user's first /api/converse request (observed live as a confusing 502).
    NOTE: lifespan only fires when TestClient is used as a context manager --
    the plain _client() helper other tests use does NOT trigger it, which is
    exactly why this needs its own explicit `with` block."""
    from api.main import app

    with TestClient(app):
        pass
    mock_get_loop.assert_called_once()


def test_root_returns_200_not_404():
    """Regression test: Render's default health probe (and anyone hitting the
    bare deployed URL) requests "/" -- there was no route for it, so it 404'd.
    Real health checks should still target /api/health (see render.yaml's
    healthCheckPath), but "/" itself must not 404."""
    resp = _client().get("/")
    assert resp.status_code == 200


def test_cors_rejects_unlisted_origin():
    resp = _client().options(
        "/api/converse",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in {k.lower() for k in resp.headers}
