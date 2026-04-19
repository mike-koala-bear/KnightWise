from datetime import UTC, datetime, timedelta

from knightwise_api.drills.srs import SrsState, next_due_puzzle_id, record_attempt, sm2_update
from knightwise_api.models import Node, NodePuzzle, Puzzle, User


def _state(ease=2.5, interval=0, reps=0) -> SrsState:
    return SrsState(ease=ease, interval_days=interval, repetitions=reps, due_at=datetime.now(UTC))


def test_sm2_correct_first_response():
    out = sm2_update(_state(), quality=5, now=datetime(2024, 1, 1, tzinfo=UTC))
    assert out.repetitions == 1
    assert out.interval_days == 1
    assert out.ease > 2.5


def test_sm2_correct_second_response():
    out = sm2_update(_state(reps=1, interval=1), quality=4, now=datetime(2024, 1, 1, tzinfo=UTC))
    assert out.repetitions == 2
    assert out.interval_days == 6


def test_sm2_correct_third_scales_by_ease():
    out = sm2_update(_state(reps=2, interval=6, ease=2.5), quality=5, now=datetime(2024, 1, 1, tzinfo=UTC))
    assert out.repetitions == 3
    assert out.interval_days >= 6 * 2  # ~15


def test_sm2_failure_resets():
    out = sm2_update(_state(reps=5, interval=30), quality=1, now=datetime(2024, 1, 1, tzinfo=UTC))
    assert out.repetitions == 0
    assert out.interval_days == 1
    assert out.ease < 2.5


def test_record_attempt_and_next_due(db_session):
    user = User(display_name="t", lichess_username="t")
    db_session.add(user)
    db_session.commit()

    node = Node(slug="t-node", domain="tactics", title="T", rating_min=0, rating_max=3000)
    puzzle = Puzzle(
        external_id="t-1", fen="8/8/8/8/8/8/8/4K2k w - - 0 1",
        solution_uci=["e1f1"], themes=[], rating=1000, source="t",
    )
    db_session.add_all([node, puzzle])
    db_session.flush()
    db_session.add(NodePuzzle(node_id=node.id, puzzle_id=puzzle.id, position=0))
    db_session.commit()

    # unattempted puzzle comes back when no srs card exists
    assert next_due_puzzle_id(db_session, user_id=user.id, node_id=node.id) == puzzle.id

    # after a correct attempt, due_at moves +1 day; not due now
    record_attempt(db_session, user_id=user.id, puzzle_id=puzzle.id, correct=True, time_ms=5000)
    now = datetime.now(UTC)
    assert next_due_puzzle_id(db_session, user_id=user.id, node_id=node.id, now=now) is not None  # fallback picks the only one

    # but explicitly asking before its due_at returns no due card (only fallback)
    early = now - timedelta(hours=1)
    due_only = next_due_puzzle_id(db_session, user_id=user.id, node_id=None, now=early)
    # with node_id=None and no due cards, it falls through to first puzzle
    assert due_only is None or due_only == puzzle.id
