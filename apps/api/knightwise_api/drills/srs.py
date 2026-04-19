"""SM-2 spaced-repetition scheduler.

This is the PR #3 SRS — SM-2 with ease/interval/reps columns. FSRS v6 (stability,
difficulty, decay) fields already exist on `srs_cards` but are only populated once
we switch to the fsrs-rs scheduler in PR #4.

SM-2 quality mapping (0-5):
  - correct + fast    -> 5
  - correct + slow    -> 4
  - correct + hint    -> 3
  - incorrect + close -> 2
  - incorrect + wrong -> 1

We hide that from callers: `record_attempt(correct, time_ms, hints_used)` picks a
quality behind the scenes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import PuzzleAttempt, SrsCard


@dataclass(slots=True)
class SrsState:
    ease: float
    interval_days: int
    repetitions: int
    due_at: datetime


def _quality(correct: bool, time_ms: int, hints_used: int) -> int:
    if correct:
        if hints_used > 0:
            return 3
        if time_ms <= 10_000:
            return 5
        return 4
    # incorrect
    return 1 if hints_used > 0 else 2


def sm2_update(state: SrsState, quality: int, now: datetime | None = None) -> SrsState:
    """Standard SM-2 update. `quality` in [0, 5]."""
    now = now or datetime.now(UTC)
    ease = max(1.3, state.ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

    if quality < 3:
        repetitions = 0
        interval_days = 1
    else:
        repetitions = state.repetitions + 1
        if repetitions == 1:
            interval_days = 1
        elif repetitions == 2:
            interval_days = 6
        else:
            interval_days = max(1, round(state.interval_days * ease))

    due_at = now + timedelta(days=interval_days)
    return SrsState(ease=ease, interval_days=interval_days, repetitions=repetitions, due_at=due_at)


def _get_or_create_card(db: Session, user_id: int, puzzle_id: int) -> SrsCard:
    card = db.execute(
        select(SrsCard).where(SrsCard.user_id == user_id, SrsCard.puzzle_id == puzzle_id)
    ).scalar_one_or_none()
    if card is None:
        card = SrsCard(user_id=user_id, puzzle_id=puzzle_id)
        db.add(card)
        db.flush()
    return card


def record_attempt(
    db: Session,
    *,
    user_id: int,
    puzzle_id: int,
    correct: bool,
    time_ms: int,
    hints_used: int = 0,
    node_id: int | None = None,
    now: datetime | None = None,
) -> SrsCard:
    """Log the attempt + update the SRS card. Returns the updated card."""
    now = now or datetime.now(UTC)
    db.add(
        PuzzleAttempt(
            user_id=user_id,
            puzzle_id=puzzle_id,
            node_id=node_id,
            correct=correct,
            time_ms=time_ms,
            hints_used=hints_used,
        )
    )

    card = _get_or_create_card(db, user_id, puzzle_id)
    state = SrsState(
        ease=card.ease,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        due_at=card.due_at if card.due_at is not None else now,
    )
    q = _quality(correct, time_ms, hints_used)
    new_state = sm2_update(state, q, now=now)
    card.ease = new_state.ease
    card.interval_days = new_state.interval_days
    card.repetitions = new_state.repetitions
    card.due_at = new_state.due_at
    db.commit()
    db.refresh(card)
    return card


def next_due_puzzle_id(
    db: Session, *, user_id: int, node_id: int | None = None, now: datetime | None = None
) -> int | None:
    """Pick the next puzzle for the user:
    1. Due SRS cards for this node (or any node) come first.
    2. Otherwise, a not-yet-attempted puzzle from the node.
    3. Otherwise, None.
    """
    from ..models import NodePuzzle, Puzzle

    now = now or datetime.now(UTC)

    due_stmt = select(SrsCard.puzzle_id).where(
        SrsCard.user_id == user_id, SrsCard.due_at <= now
    )
    if node_id is not None:
        due_stmt = (
            select(SrsCard.puzzle_id)
            .join(NodePuzzle, NodePuzzle.puzzle_id == SrsCard.puzzle_id)
            .where(SrsCard.user_id == user_id, SrsCard.due_at <= now, NodePuzzle.node_id == node_id)
        )
    due_stmt = due_stmt.order_by(SrsCard.due_at).limit(1)
    due_id = db.execute(due_stmt).scalar_one_or_none()
    if due_id is not None:
        return int(due_id)

    seen_stmt = select(SrsCard.puzzle_id).where(SrsCard.user_id == user_id)
    seen_ids = {row for (row,) in db.execute(seen_stmt).all()}

    if node_id is None:
        fallback_stmt = select(Puzzle.id).order_by(Puzzle.id)
    else:
        fallback_stmt = (
            select(Puzzle.id)
            .join(NodePuzzle, NodePuzzle.puzzle_id == Puzzle.id)
            .where(NodePuzzle.node_id == node_id)
            .order_by(NodePuzzle.position)
        )

    rows = [int(r) for (r,) in db.execute(fallback_stmt).all()]
    for rid in rows:
        if rid not in seen_ids:
            return rid
    return None
