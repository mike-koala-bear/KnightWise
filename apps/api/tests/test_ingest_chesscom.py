import json

import httpx
from knightwise_api.ingest.chesscom import ChesscomClient, fetch_chesscom_games

ARCHIVE_URL = "https://api.chess.com/pub/player/mike-bear/games/2025/04"


def _transport() -> httpx.MockTransport:
    def handler(req: httpx.Request) -> httpx.Response:
        if req.url.path.endswith("/games/archives"):
            return httpx.Response(200, json={"archives": [ARCHIVE_URL]})
        if str(req.url) == ARCHIVE_URL:
            return httpx.Response(
                200,
                json={
                    "games": [
                        {
                            "uuid": "game-1",
                            "url": "https://www.chess.com/game/live/game-1",
                            "end_time": 1712000000,
                            "time_class": "blitz",
                            "time_control": "180",
                            "white": {
                                "username": "mike-bear",
                                "rating": 1200,
                                "result": "win",
                            },
                            "black": {
                                "username": "somebody",
                                "rating": 1230,
                                "result": "checkmated",
                            },
                            "pgn": "1. e4 e5 1-0",
                        },
                        {
                            "uuid": "game-2",
                            "url": "https://www.chess.com/game/live/game-2",
                            "end_time": 1712000100,
                            "time_class": "rapid",
                            "white": {"username": "opp2", "rating": 1260, "result": "win"},
                            "black": {"username": "mike-bear", "rating": 1210, "result": "resigned"},
                            "pgn": "1. d4 d5 1-0",
                        },
                    ]
                },
            )
        return httpx.Response(404)

    return httpx.MockTransport(handler)


def test_chesscom_fetch_normalizes_games():
    http = httpx.Client(transport=_transport(), timeout=5.0, headers={"Accept": "application/json"})
    with ChesscomClient(client=http) as client:
        games = fetch_chesscom_games("mike-bear", max_games=10, client=client)
    assert len(games) == 2
    # Newest-in-month first (we reversed the list)
    latest = games[0]
    assert latest.source == "chesscom"
    assert latest.external_id == "game-2"
    assert latest.played_as == "black"
    assert latest.result == "loss"

    won = games[1]
    assert won.external_id == "game-1"
    assert won.played_as == "white"
    assert won.result == "win"
    assert won.user_rating == 1200
    assert won.opponent_rating == 1230


def test_chesscom_respects_max_games():
    http = httpx.Client(transport=_transport(), timeout=5.0, headers={"Accept": "application/json"})
    with ChesscomClient(client=http) as client:
        games = fetch_chesscom_games("mike-bear", max_games=1, client=client)
    assert len(games) == 1


def test_chesscom_archives_json_shape():
    # guard against accidental changes to the public schema assumption
    sample = {"archives": [ARCHIVE_URL]}
    assert "archives" in json.loads(json.dumps(sample))
