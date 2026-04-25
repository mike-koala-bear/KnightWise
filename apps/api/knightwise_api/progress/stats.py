"""Daily progress + streak calculations, derived from `puzzle_attempts`.

These stats power the home-page widgets (today's drill count, current streak).
We deliberately compute from raw attempts rather than caching — volumes are
tiny for the single-user MVP and staleness bugs are worse than a few extra ms.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import Integer, func, select
from sqlalchemy.orm import Session

from ..models import PuzzleAttempt

DEFAULT_DAILY_TARGET = 8


@dataclass(slots=True)
class DailyProgress:
    date: date
    solved: int
    attempts: int
    target: int

    @property
    def complete(self) -> bool:
        return self.solved >= self.target


@dataclass(slots=True)
class StreakStats:
    current: int
    longest: int
    last_active: date | None


def _day_bounds(on: date) -> tuple[datetime, datetime]:
    start = datetime(on.year, on.month, on.day, tzinfo=UTC)
    return start, start + timedelta(days=1)


def drills_solved_today(
    db: Session,
    *,
    user_id: int,
    target: int = DEFAULT_DAILY_TARGET,
    on: date | None = None,
) -> DailyProgress:
    """Count correct + total attempts for `user_id` on `on` (default: today UTC)."""
    day = on or datetime.now(UTC).date()
    start, end = _day_bounds(day)

    stmt = select(
        func.count().label("attempts"),
        # Cast the bool to int so SUM works on both SQLite and Postgres.
        func.sum(PuzzleAttempt.correct.cast(Integer)).label("solved"),
    ).where(
        PuzzleAttempt.user_id == user_id,
        PuzzleAttempt.created_at >= start,
        PuzzleAttempt.created_at < end,
    )
    row = db.execute(stmt).one()
    attempts = int(row.attempts or 0)
    solved = int(row.solved or 0)
    return DailyProgress(date=day, solved=solved, attempts=attempts, target=target)


def streak_stats(
    db: Session,
    *,
    user_id: int,
    on: date | None = None,
) -> StreakStats:
    """Consecutive days (counting today if active) with >=1 correct attempt.

    `longest` scans the full history of correct-day dates. Both numbers use
    UTC day boundaries — the MVP is single-timezone.
    """
    today = on or datetime.now(UTC).date()

    stmt = (
        select(func.date(PuzzleAttempt.created_at))
        .where(PuzzleAttempt.user_id == user_id, PuzzleAttempt.correct.is_(True))
        .group_by(func.date(PuzzleAttempt.created_at))
    )
    raw_days = {_coerce_date(r[0]) for r in db.execute(stmt).all()}
    raw_days.discard(None)
    days = sorted(d for d in raw_days if d is not None)
    if not days:
        return StreakStats(current=0, longest=0, last_active=None)

    # longest: walk the sorted unique days and count the longest run of
    # consecutive calendar days.
    longest = run = 1
    for prev, cur in zip(days, days[1:], strict=False):
        run = run + 1 if (cur - prev).days == 1 else 1
        longest = max(longest, run)

    # current: count back from today (or yesterday, so a user who hasn't
    # logged in today yet still sees their streak until UTC rolls over).
    last_active = days[-1]
    if last_active == today:
        anchor = today
    elif last_active == today - timedelta(days=1):
        anchor = last_active
    else:
        return StreakStats(current=0, longest=longest, last_active=last_active)

    day_set = set(days)
    current = 0
    d = anchor
    while d in day_set:
        current += 1
        d -= timedelta(days=1)

    return StreakStats(current=current, longest=longest, last_active=last_active)


def _coerce_date(value: object) -> date | None:
    """`func.date(...)` returns `str` on SQLite, `date` on Postgres."""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None
