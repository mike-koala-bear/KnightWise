from datetime import UTC, datetime, timedelta

from knightwise_api.models import Puzzle, PuzzleAttempt, User
from knightwise_api.progress import drills_solved_today, streak_stats


def _seed_user(db):
    user = User(display_name="p", lichess_username="p")
    db.add(user)
    db.commit()
    return user


def _seed_puzzle(db, ext="p-1") -> Puzzle:
    p = Puzzle(
        external_id=ext,
        fen="8/8/8/8/8/8/8/4K2k w - - 0 1",
        solution_uci=["e1f1"],
        themes=[],
        rating=1000,
        source="t",
    )
    db.add(p)
    db.commit()
    return p


def _attempt(db, user_id: int, puzzle_id: int, *, correct: bool, when: datetime) -> None:
    db.add(
        PuzzleAttempt(
            user_id=user_id,
            puzzle_id=puzzle_id,
            correct=correct,
            time_ms=1000,
            hints_used=0,
            created_at=when,
        )
    )
    db.commit()


def test_drills_solved_today_zero_when_empty(db_session):
    user = _seed_user(db_session)
    p = drills_solved_today(db_session, user_id=user.id, target=8)
    assert p.solved == 0
    assert p.attempts == 0
    assert p.target == 8
    assert p.complete is False


def test_drills_solved_today_counts_correct_only(db_session):
    user = _seed_user(db_session)
    puzzle = _seed_puzzle(db_session)
    now = datetime.now(UTC)
    _attempt(db_session, user.id, puzzle.id, correct=True, when=now)
    _attempt(db_session, user.id, puzzle.id, correct=False, when=now)
    _attempt(db_session, user.id, puzzle.id, correct=True, when=now)

    p = drills_solved_today(db_session, user_id=user.id, target=2)
    assert p.solved == 2
    assert p.attempts == 3
    assert p.complete is True


def test_drills_solved_today_ignores_yesterday(db_session):
    user = _seed_user(db_session)
    puzzle = _seed_puzzle(db_session)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    _attempt(db_session, user.id, puzzle.id, correct=True, when=yesterday)

    p = drills_solved_today(db_session, user_id=user.id)
    assert p.solved == 0
    assert p.attempts == 0


def test_streak_stats_no_attempts(db_session):
    user = _seed_user(db_session)
    s = streak_stats(db_session, user_id=user.id)
    assert s.current == 0
    assert s.longest == 0
    assert s.last_active is None


def test_streak_stats_current_and_longest(db_session):
    user = _seed_user(db_session)
    puzzle = _seed_puzzle(db_session)
    today = datetime.now(UTC).replace(hour=12, minute=0, second=0, microsecond=0)

    # Active today, yesterday, day-before -> current streak of 3
    for delta in (0, 1, 2):
        _attempt(db_session, user.id, puzzle.id, correct=True, when=today - timedelta(days=delta))

    # Gap of a day, then a 2-day run 5-6 days ago -> longest should still be 3
    _attempt(db_session, user.id, puzzle.id, correct=True, when=today - timedelta(days=5))
    _attempt(db_session, user.id, puzzle.id, correct=True, when=today - timedelta(days=6))

    s = streak_stats(db_session, user_id=user.id)
    assert s.current == 3
    assert s.longest == 3
    assert s.last_active == today.date()


def test_streak_stats_wrong_answers_do_not_count(db_session):
    user = _seed_user(db_session)
    puzzle = _seed_puzzle(db_session)
    today = datetime.now(UTC)
    _attempt(db_session, user.id, puzzle.id, correct=False, when=today)

    s = streak_stats(db_session, user_id=user.id)
    assert s.current == 0
    assert s.last_active is None


def test_streak_current_holds_when_not_yet_active_today(db_session):
    """If user was active yesterday but not yet today, current streak should still count."""
    user = _seed_user(db_session)
    puzzle = _seed_puzzle(db_session)
    yesterday = datetime.now(UTC) - timedelta(days=1)
    day_before = datetime.now(UTC) - timedelta(days=2)
    _attempt(db_session, user.id, puzzle.id, correct=True, when=yesterday)
    _attempt(db_session, user.id, puzzle.id, correct=True, when=day_before)

    s = streak_stats(db_session, user_id=user.id)
    assert s.current == 2


def test_progress_endpoints_shape(client, session_factory):
    # Use the client's bound session so the user exists in the same in-memory DB
    with session_factory() as db:
        user = _seed_user(db)
        uid = user.id

    r1 = client.get(f"/v1/progress/today?user_id={uid}&target=5")
    assert r1.status_code == 200
    body = r1.json()
    assert body == {
        "date": body["date"],
        "solved": 0,
        "attempts": 0,
        "target": 5,
        "complete": False,
    }

    r2 = client.get(f"/v1/streak?user_id={uid}")
    assert r2.status_code == 200
    assert r2.json() == {"current": 0, "longest": 0, "last_active": None}

    r3 = client.get("/v1/progress/today?user_id=9999")
    assert r3.status_code == 404
    r4 = client.get("/v1/streak?user_id=9999")
    assert r4.status_code == 404
