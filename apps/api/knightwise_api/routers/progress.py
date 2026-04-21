from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..progress import DEFAULT_DAILY_TARGET, drills_solved_today, streak_stats

router = APIRouter(tags=["progress"])

DBSession = Annotated[Session, Depends(get_db)]


class DailyProgressOut(BaseModel):
    date: str
    solved: int
    attempts: int
    target: int
    complete: bool


class StreakOut(BaseModel):
    current: int
    longest: int
    last_active: str | None


def _require_user(db: Session, user_id: int) -> None:
    exists = db.execute(select(User.id).where(User.id == user_id)).scalar_one_or_none()
    if exists is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")


@router.get("/progress/today", response_model=DailyProgressOut)
def progress_today(
    db: DBSession,
    user_id: int = Query(..., ge=1),
    target: int = Query(DEFAULT_DAILY_TARGET, ge=1, le=100),
) -> DailyProgressOut:
    _require_user(db, user_id)
    p = drills_solved_today(db, user_id=user_id, target=target)
    return DailyProgressOut(
        date=p.date.isoformat(),
        solved=p.solved,
        attempts=p.attempts,
        target=p.target,
        complete=p.complete,
    )


@router.get("/streak", response_model=StreakOut)
def streak(
    db: DBSession,
    user_id: int = Query(..., ge=1),
) -> StreakOut:
    _require_user(db, user_id)
    s = streak_stats(db, user_id=user_id)
    return StreakOut(
        current=s.current,
        longest=s.longest,
        last_active=s.last_active.isoformat() if s.last_active else None,
    )
