"""Persist normalized games into the DB, deduplicating on (source, external_id)."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Game, User
from .types import IngestedGame


@dataclass(slots=True)
class IngestReport:
    inserted: int = 0
    skipped_duplicate: int = 0
    game_ids: list[int] = field(default_factory=list)


def _get_or_create_user(db: Session, lichess_username: str | None, chesscom_username: str | None) -> User:
    """Find or create the single-user MVP row keyed by one of the provided handles."""
    stmt = select(User)
    if lichess_username:
        stmt = stmt.where(User.lichess_username == lichess_username)
    elif chesscom_username:
        stmt = stmt.where(User.chesscom_username == chesscom_username)
    else:
        raise ValueError("Provide at least one of lichess_username or chesscom_username")

    user = db.execute(stmt).scalar_one_or_none()
    if user is None:
        user = User(lichess_username=lichess_username, chesscom_username=chesscom_username)
        db.add(user)
        db.flush()
    # backfill the other handle if missing
    if lichess_username and user.lichess_username is None:
        user.lichess_username = lichess_username
    if chesscom_username and user.chesscom_username is None:
        user.chesscom_username = chesscom_username
    return user


def ingest_games(
    db: Session,
    games: list[IngestedGame],
    *,
    lichess_username: str | None = None,
    chesscom_username: str | None = None,
) -> IngestReport:
    user = _get_or_create_user(db, lichess_username, chesscom_username)
    report = IngestReport()

    for g in games:
        existing = db.execute(
            select(Game.id).where(Game.source == g.source, Game.external_id == g.external_id)
        ).scalar_one_or_none()
        if existing is not None:
            report.skipped_duplicate += 1
            continue

        row = Game(
            user_id=user.id,
            source=g.source,
            external_id=g.external_id,
            time_control=g.time_control,
            played_as=g.played_as,
            opponent_name=g.opponent_name,
            opponent_rating=g.opponent_rating,
            user_rating=g.user_rating,
            result=g.result,
            pgn=g.pgn,
            started_at=g.started_at,
        )
        db.add(row)
        db.flush()
        report.inserted += 1
        report.game_ids.append(row.id)

    db.commit()
    return report
