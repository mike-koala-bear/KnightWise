from datetime import date, datetime, timedelta

from knightwise_api.models import Game, User
from knightwise_api.rating import build_rating_history


def _user(db, user_id: int = 1):
    db.add(User(id=user_id, display_name="dev"))
    db.commit()


def _game(db, *, started_at: datetime, user_rating: int | None, user_id: int = 1):
    db.add(
        Game(
            user_id=user_id,
            source="lichess",
            external_id=f"g{started_at.isoformat()}",
            played_as="white",
            result="win",
            pgn="1. e4 e5",
            started_at=started_at,
            user_rating=user_rating,
        )
    )
    db.commit()


def test_history_no_games(db_session):
    _user(db_session)
    today = date(2026, 4, 19)
    points = build_rating_history(db_session, user_id=1, days=7, today=today)
    assert len(points) == 7
    assert all(p.rating is None for p in points)
    assert points[0].day == today - timedelta(days=6)
    assert points[-1].day == today


def test_history_carries_forward(db_session):
    _user(db_session)
    today = date(2026, 4, 19)
    _game(db_session, started_at=datetime(2026, 4, 14, 10, 0), user_rating=1200)
    _game(db_session, started_at=datetime(2026, 4, 16, 20, 0), user_rating=1230)

    points = build_rating_history(db_session, user_id=1, days=7, today=today)
    assert [p.day for p in points] == [
        date(2026, 4, 13),
        date(2026, 4, 14),
        date(2026, 4, 15),
        date(2026, 4, 16),
        date(2026, 4, 17),
        date(2026, 4, 18),
        date(2026, 4, 19),
    ]
    assert [p.rating for p in points] == [None, 1200, 1200, 1230, 1230, 1230, 1230]


def test_history_latest_per_day(db_session):
    _user(db_session)
    today = date(2026, 4, 19)
    _game(db_session, started_at=datetime(2026, 4, 19, 8, 0), user_rating=1200)
    _game(db_session, started_at=datetime(2026, 4, 19, 20, 0), user_rating=1250)
    points = build_rating_history(db_session, user_id=1, days=1, today=today)
    assert len(points) == 1
    assert points[0].rating == 1250


def test_endpoint_returns_history(client, db_session):
    _user(db_session)
    _game(db_session, started_at=datetime.utcnow() - timedelta(days=3), user_rating=1100)
    _game(db_session, started_at=datetime.utcnow() - timedelta(days=1), user_rating=1150)

    r = client.get("/v1/rating/history?user_id=1&days=7")
    assert r.status_code == 200
    body = r.json()
    assert body["days"] == 7
    assert len(body["points"]) == 7
    assert body["current_rating"] == 1150
    assert body["delta"] == 50


def test_endpoint_user_not_found(client):
    r = client.get("/v1/rating/history?user_id=9999&days=7")
    assert r.status_code == 404
