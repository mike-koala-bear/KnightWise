"""Daily Warp endpoint — the composed 15-minute training session."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Puzzle, User
from ..warp import compose_daily_warp

router = APIRouter(tags=["warp"])

DBSession = Annotated[Session, Depends(get_db)]


class PuzzleOut(BaseModel):
    id: int
    fen: str
    solution_uci: list[str]
    themes: list[str]
    rating: int
    description: str | None


class TagCount(BaseModel):
    tag: str
    count: int


class DailyWarpOut(BaseModel):
    user_id: int
    generated_at: datetime
    games_analyzed: int
    top_weakness_tag: str | None
    tag_counts: list[TagCount]
    node_id: int | None
    node_slug: str | None
    node_title: str | None
    coach_note: str
    drill_puzzles: list[PuzzleOut]


@router.get("/warp/today", response_model=DailyWarpOut)
def get_daily_warp(
    db: DBSession,
    user_id: int = Query(..., ge=1),
    games_window: int = Query(20, ge=1, le=100),
    drills: int = Query(8, ge=1, le=30),
) -> DailyWarpOut:
    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {user_id}")

    warp = compose_daily_warp(
        db, user_id=user_id, games_window=games_window, drills=drills
    )

    puzzles_by_id: dict[int, Puzzle] = {}
    if warp.drill_puzzle_ids:
        rows = db.execute(
            select(Puzzle).where(Puzzle.id.in_(warp.drill_puzzle_ids))
        ).scalars().all()
        puzzles_by_id = {p.id: p for p in rows}

    drill_puzzles = [
        PuzzleOut(
            id=p.id,
            fen=p.fen,
            solution_uci=list(p.solution_uci or []),
            themes=list(p.themes or []),
            rating=p.rating,
            description=p.description,
        )
        for pid in warp.drill_puzzle_ids
        if (p := puzzles_by_id.get(pid)) is not None
    ]

    return DailyWarpOut(
        user_id=warp.user_id,
        generated_at=warp.generated_at,
        games_analyzed=warp.games_analyzed,
        top_weakness_tag=warp.top_weakness_tag,
        tag_counts=[TagCount(tag=t, count=c) for t, c in warp.tag_counts],
        node_id=warp.node_id,
        node_slug=warp.node_slug,
        node_title=warp.node_title,
        coach_note=warp.coach_note,
        drill_puzzles=drill_puzzles,
    )
