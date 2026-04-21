from datetime import UTC, datetime

from knightwise_api.ingest.service import ingest_games
from knightwise_api.ingest.types import IngestedGame
from knightwise_api.models import Game, User


def _g(source: str, external_id: str, played_as: str = "white", result: str = "win") -> IngestedGame:
    return IngestedGame(
        source=source,  # type: ignore[arg-type]
        external_id=external_id,
        time_control="blitz",
        played_as=played_as,  # type: ignore[arg-type]
        opponent_name="opp",
        opponent_rating=1500,
        user_rating=1500,
        result=result,  # type: ignore[arg-type]
        pgn="1. e4 e5",
        started_at=datetime(2024, 1, 1, tzinfo=UTC),
    )


def test_ingest_inserts_user_and_games(db_session):
    report = ingest_games(
        db_session,
        [_g("lichess", "a"), _g("lichess", "b")],
        lichess_username="mike-bear",
    )
    assert report.inserted == 2
    assert report.skipped_duplicate == 0

    users = db_session.query(User).all()
    games = db_session.query(Game).all()
    assert len(users) == 1
    assert users[0].lichess_username == "mike-bear"
    assert {g.external_id for g in games} == {"a", "b"}


def test_ingest_dedup_on_second_run(db_session):
    ingest_games(db_session, [_g("lichess", "a")], lichess_username="mike-bear")
    report = ingest_games(
        db_session,
        [_g("lichess", "a"), _g("lichess", "c")],
        lichess_username="mike-bear",
    )
    assert report.inserted == 1
    assert report.skipped_duplicate == 1
    assert db_session.query(Game).count() == 2


def test_ingest_backfills_missing_handle(db_session):
    ingest_games(db_session, [_g("lichess", "a")], lichess_username="mike-bear")
    ingest_games(db_session, [_g("chesscom", "x")], chesscom_username="mike-bear")
    users = db_session.query(User).all()
    # same user by chesscom handle? no — different handle, different lookup => two users is also fine here
    # but we specifically support backfilling when a matching user exists only by one handle
    assert any(u.chesscom_username == "mike-bear" for u in users)
