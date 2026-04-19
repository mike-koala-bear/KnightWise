"""Analyze endpoint tests.

The real Stockfish binary is not required for CI — the endpoint returns 503 if the
binary is absent. We assert the endpoint wiring works either way.
"""

from fastapi.testclient import TestClient

STARTING_FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def test_analyze_returns_200_or_503(client: TestClient) -> None:
    r = client.post("/v1/analyze", json={"fen": STARTING_FEN, "depth": 6})
    assert r.status_code in {200, 503}
    if r.status_code == 200:
        body = r.json()
        assert body["fen"] == STARTING_FEN
        assert body["best_move"] is not None


def test_analyze_rejects_invalid_depth(client: TestClient) -> None:
    r = client.post("/v1/analyze", json={"fen": STARTING_FEN, "depth": 0})
    assert r.status_code == 422


def test_llm_router_stub() -> None:
    from knightwise_api.llm import generate

    out = generate("ping", purpose="test")
    assert "LLM router reachable" in out
