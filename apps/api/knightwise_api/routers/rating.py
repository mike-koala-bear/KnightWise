"""Rating history endpoint."""

from __future__ import annotations

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..rating import build_rating_history

router = APIRouter(tags=["rating"])

DBSession = Annotated[Session, Depends(get_db)]


class RatingPointOut(BaseModel):
    day: date
    rating: int | None


class RatingHistoryOut(BaseModel):
    user_id: int
    days: int
    points: list[RatingPointOut]
    current_rating: int | None
    delta: int | None  # last - first (ignoring leading Nones)


def _compute_delta(points: list[RatingPointOut]) -> int | None:
    ratings = [p.rating for p in points if p.rating is not None]
    if len(ratings) < 2:
        return None
    return ratings[-1] - ratings[0]


@router.get("/rating/history", response_model=RatingHistoryOut)
def get_rating_history(
    db: DBSession,
    user_id: int = Query(..., ge=1),
    days: int = Query(7, ge=1, le=90),
) -> RatingHistoryOut:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")

    history = build_rating_history(db, user_id=user_id, days=days)
    points = [RatingPointOut(day=p.day, rating=p.rating) for p in history]
    current = points[-1].rating if points else None
    return RatingHistoryOut(
        user_id=user_id,
        days=days,
        points=points,
        current_rating=current,
        delta=_compute_delta(points),
    )
