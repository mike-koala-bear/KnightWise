from datetime import datetime, timedelta

from knightwise_api.content import seed_nodes_and_puzzles
from knightwise_api.models import Game, GameAnalysis, User


def _user(db, user_id: int = 1):
    db.add(User(id=user_id, display_name="dev"))
    db.commit()


def _analyzed(db, *, tags: list[str], days_ago: int, user_id: int = 1):
    now = datetime.utcnow() - timedelta(days=days_ago)
    g = Game(
        user_id=user_id,
        source="lichess",
        external_id=f"g{now.isoformat()}",
        played_as="white",
        result="loss",
        pgn="1. e4 e5",
        started_at=now,
        user_rating=1200,
    )
    db.add(g)
    db.flush()
    db.add(
        GameAnalysis(
            game_id=g.id,
            engine="stockfish-17.1",
            depth=14,
            per_move=[],
            weakness_tags=tags,
            cpl_avg=50.0,
        )
    )
    db.commit()


def test_warp_today_user_not_found(client):
    r = client.get("/v1/warp/today?user_id=999")
    assert r.status_code == 404


def test_warp_today_no_games_fallback(client, db_session):
    seed_nodes_and_puzzles(db_session)
    _user(db_session)
    r = client.get("/v1/warp/today?user_id=1")
    assert r.status_code == 200
    body = r.json()
    assert body["top_weakness_tag"] is None
    assert body["node_slug"] == "back-rank-basics"
    assert body["coach_note"]
    assert len(body["drill_puzzles"]) >= 1
    assert body["games_analyzed"] == 0


def test_warp_today_with_weaknesses(client, db_session):
    seed_nodes_and_puzzles(db_session)
    _user(db_session)
    _analyzed(db_session, tags=["back_rank_weakness"], days_ago=1)
    _analyzed(db_session, tags=["back_rank_weakness", "missed_tactic"], days_ago=2)

    r = client.get("/v1/warp/today?user_id=1&drills=3")
    assert r.status_code == 200
    body = r.json()
    assert body["top_weakness_tag"] == "back_rank_weakness"
    assert body["node_slug"] == "back-rank-basics"
    assert body["games_analyzed"] == 2
    assert len(body["drill_puzzles"]) <= 3
    assert len(body["drill_puzzles"]) >= 1
    # tag_counts is sorted desc by count
    counts = body["tag_counts"]
    assert counts[0]["tag"] == "back_rank_weakness"
    assert counts[0]["count"] == 2
