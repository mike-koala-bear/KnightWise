from datetime import UTC, datetime

from knightwise_api.ingest.service import ingest_games
from knightwise_api.ingest.types import IngestedGame


def _ingest(db, **kwargs):
    g = IngestedGame(
        source="lichess",
        external_id=kwargs.get("external_id", "t1"),
        time_control="blitz",
        played_as="white",
        opponent_name="opp",
        opponent_rating=1500,
        user_rating=1500,
        result="win",
        pgn="1. e4 e5",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    return ingest_games(db, [g], lichess_username="mike-bear")


def test_list_games_empty(client):
    r = client.get("/v1/games")
    assert r.status_code == 200
    assert r.json() == []


def test_list_games_after_ingest(db_session, client):
    _ingest(db_session, external_id="t1")
    _ingest(db_session, external_id="t2")
    r = client.get("/v1/games")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 2
    assert {g["external_id"] for g in body} == {"t1", "t2"}


def test_get_analysis_missing(db_session, client):
    _ingest(db_session, external_id="t1")
    gid = 1
    r = client.get(f"/v1/games/{gid}/analysis")
    assert r.status_code == 404
