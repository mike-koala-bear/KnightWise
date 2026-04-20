"""Rating tracker.

We don't run a Glicko-2 regression here — instead we derive a daily rating
point series from the `games.user_rating` column (which the ingest layer
pulls from Lichess / Chess.com). Each day's rating is the user's rating on
their most recent game that day; days with no games carry forward the
previous day's rating.

This is intentionally simple: the MVP goal is to show "did my rating move
in the last 7 days?", not to replace a ratings engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Game


@dataclass(slots=True)
class RatingPoint:
    day: date
    rating: int | None  # None when no games yet and no carry-forward available


def _latest_rating_per_day(
    rows: list[tuple[datetime, int | None]],
) -> dict[date, int]:
    """Return {day -> rating} using the *latest* (by started_at) game per day."""
    by_day: dict[date, tuple[datetime, int]] = {}
    for started_at, rating in rows:
        if rating is None:
            continue
        day = started_at.date()
        existing = by_day.get(day)
        if existing is None or started_at > existing[0]:
            by_day[day] = (started_at, rating)
    return {d: r for d, (_, r) in by_day.items()}


def _last_rating_before(
    rows: list[tuple[datetime, int | None]], cutoff: date
) -> int | None:
    best: tuple[datetime, int] | None = None
    for started_at, rating in rows:
        if rating is None or started_at.date() >= cutoff:
            continue
        if best is None or started_at > best[0]:
            best = (started_at, rating)
    return best[1] if best else None


def build_rating_history(
    db: Session, *, user_id: int, days: int = 7, today: date | None = None
) -> list[RatingPoint]:
    """Return one `RatingPoint` per day for the last `days` days (inclusive).

    Carries the last known rating forward across days with no games.
    """
    if days < 1:
        raise ValueError("days must be >= 1")

    end_day = today or datetime.utcnow().date()
    start_day = end_day - timedelta(days=days - 1)

    rows = db.execute(
        select(Game.started_at, Game.user_rating)
        .where(Game.user_id == user_id)
        .order_by(Game.started_at)
    ).all()
    all_rows: list[tuple[datetime, int | None]] = [
        (started_at, rating) for (started_at, rating) in rows
    ]

    per_day = _latest_rating_per_day(all_rows)
    carry = _last_rating_before(all_rows, start_day)

    out: list[RatingPoint] = []
    current = start_day
    while current <= end_day:
        if current in per_day:
            carry = per_day[current]
        out.append(RatingPoint(day=current, rating=carry))
        current += timedelta(days=1)
    return out
