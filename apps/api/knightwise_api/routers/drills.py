from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..drills import next_due_puzzle_id, record_attempt
from ..models import Node, Puzzle, User

router = APIRouter(tags=["drills"])

DBSession = Annotated[Session, Depends(get_db)]


class PuzzleOut(BaseModel):
    id: int
    external_id: str | None
    fen: str
    solution_uci: list[str]
    themes: list[str]
    rating: int
    description: str | None


class NodeOut(BaseModel):
    id: int
    slug: str
    domain: str
    title: str
    description: str | None


class NextDrillOut(BaseModel):
    puzzle: PuzzleOut | None
    node: NodeOut | None


class AttemptRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    puzzle_id: int = Field(..., ge=1)
    correct: bool
    time_ms: int = Field(..., ge=0, le=10 * 60 * 1000)
    hints_used: int = Field(0, ge=0, le=5)
    node_id: int | None = None


class AttemptResponse(BaseModel):
    ease: float
    interval_days: int
    repetitions: int
    due_at: str


def _get_or_create_single_user(db: Session) -> User:
    """Single-user MVP convenience: return the first user, or create one."""
    user = db.execute(select(User).order_by(User.id).limit(1)).scalar_one_or_none()
    if user is None:
        user = User(display_name="mike-bear", lichess_username="mike-bear", chesscom_username="mike-bear")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@router.get("/drills/next", response_model=NextDrillOut)
def next_drill(
    db: DBSession,
    node_slug: str | None = Query(None, description="Optional lesson-node slug"),
) -> NextDrillOut:
    user = _get_or_create_single_user(db)

    node_row: Node | None = None
    if node_slug is not None:
        node_row = db.execute(select(Node).where(Node.slug == node_slug)).scalar_one_or_none()
        if node_row is None:
            raise HTTPException(status_code=404, detail=f"node not found: {node_slug}")

    puzzle_id = next_due_puzzle_id(db, user_id=user.id, node_id=node_row.id if node_row else None)
    if puzzle_id is None:
        return NextDrillOut(puzzle=None, node=_node_out(node_row) if node_row else None)

    puzzle_row = db.execute(select(Puzzle).where(Puzzle.id == puzzle_id)).scalar_one()
    return NextDrillOut(
        puzzle=PuzzleOut(
            id=puzzle_row.id,
            external_id=puzzle_row.external_id,
            fen=puzzle_row.fen,
            solution_uci=list(puzzle_row.solution_uci or []),
            themes=list(puzzle_row.themes or []),
            rating=puzzle_row.rating,
            description=puzzle_row.description,
        ),
        node=_node_out(node_row) if node_row else None,
    )


@router.post("/drills/attempt", response_model=AttemptResponse)
def submit_attempt(req: AttemptRequest, db: DBSession) -> AttemptResponse:
    user = db.execute(select(User).where(User.id == req.user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {req.user_id}")

    puzzle = db.execute(select(Puzzle).where(Puzzle.id == req.puzzle_id)).scalar_one_or_none()
    if puzzle is None:
        raise HTTPException(status_code=404, detail=f"puzzle not found: {req.puzzle_id}")

    card = record_attempt(
        db,
        user_id=req.user_id,
        puzzle_id=req.puzzle_id,
        correct=req.correct,
        time_ms=req.time_ms,
        hints_used=req.hints_used,
        node_id=req.node_id,
    )
    return AttemptResponse(
        ease=card.ease,
        interval_days=card.interval_days,
        repetitions=card.repetitions,
        due_at=card.due_at.isoformat(),
    )


def _node_out(node: Node) -> NodeOut:
    return NodeOut(
        id=node.id, slug=node.slug, domain=node.domain, title=node.title, description=node.description
    )
