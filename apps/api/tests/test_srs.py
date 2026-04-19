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

    # after a correct attempt, due_at moves +1 day; puzzle is seen and not due, so None
    record_attempt(db_session, user_id=user.id, puzzle_id=puzzle.id, correct=True, time_ms=5000)
    now = datetime.now(UTC)
    assert next_due_puzzle_id(db_session, user_id=user.id, node_id=node.id, now=now) is None

    # much later, the card is due -> returns the seen puzzle for review
    future = now + timedelta(days=2)
    assert next_due_puzzle_id(db_session, user_id=user.id, node_id=node.id, now=future) == puzzle.id


def test_next_due_skips_seen_puzzle_when_no_node(db_session):
    """Regression: node_id=None path used to return the same puzzle forever."""
    user = User(display_name="u2", lichess_username="u2")
    db_session.add(user)
    db_session.commit()

    p1 = Puzzle(
        external_id="n-1", fen="8/8/8/8/8/8/8/4K2k w - - 0 1",
        solution_uci=["e1f1"], themes=[], rating=1000, source="t",
    )
    p2 = Puzzle(
        external_id="n-2", fen="8/8/8/8/8/8/8/4K2k w - - 0 1",
        solution_uci=["e1f1"], themes=[], rating=1000, source="t",
    )
    db_session.add_all([p1, p2])
    db_session.commit()

    first = next_due_puzzle_id(db_session, user_id=user.id, node_id=None)
    assert first == p1.id

    record_attempt(
        db_session, user_id=user.id, puzzle_id=p1.id, correct=True, time_ms=5000
    )
    # Before p1's due_at, node_id=None should skip p1 and return p2
    early = datetime.now(UTC)
    second = next_due_puzzle_id(db_session, user_id=user.id, node_id=None, now=early)
    assert second == p2.id

    # After both are attempted, no unseen puzzles, no due cards -> None
    record_attempt(
        db_session, user_id=user.id, puzzle_id=p2.id, correct=True, time_ms=5000
    )
    third = next_due_puzzle_id(db_session, user_id=user.id, node_id=None, now=early)
    assert third is None
