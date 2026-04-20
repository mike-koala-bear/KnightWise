from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..engine.analysis import StockfishUnavailableError
from ..engine.pipeline import analyze_and_store
from ..models import Game, GameAnalysis

router = APIRouter(tags=["games"])

DBSession = Annotated[Session, Depends(get_db)]


class GameRow(BaseModel):
    id: int
    source: str
    external_id: str
    time_control: str | None
    played_as: str
    opponent_name: str | None
    opponent_rating: int | None
    user_rating: int | None
    result: str
    started_at: datetime


class AnalysisOut(BaseModel):
    game_id: int
    engine: str
    depth: int
    cpl_avg: float | None
    weakness_tags: list[str]
    per_move: list[dict]


@router.get("/games", response_model=list[GameRow])
def list_games(db: DBSession, limit: int = Query(20, ge=1, le=200)) -> list[GameRow]:
    rows = db.execute(select(Game).order_by(Game.started_at.desc()).limit(limit)).scalars().all()
    return [GameRow.model_validate(r, from_attributes=True) for r in rows]


@router.get("/games/{game_id}/analysis", response_model=AnalysisOut)
def get_analysis(game_id: int, db: DBSession) -> AnalysisOut:
    row = db.execute(select(GameAnalysis).where(GameAnalysis.game_id == game_id)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="no analysis; run POST /v1/games/{id}/analyze")
    return AnalysisOut(
        game_id=game_id,
        engine=row.engine,
        depth=row.depth,
        cpl_avg=row.cpl_avg,
        weakness_tags=list(row.weakness_tags or []),
        per_move=list(row.per_move or []),
    )


@router.post("/games/{game_id}/analyze", response_model=AnalysisOut)
def analyze_game(
    game_id: int, db: DBSession, depth: int = Query(14, ge=1, le=24)
) -> AnalysisOut:
    try:
        row = analyze_and_store(db, game_id, depth=depth)
    except StockfishUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return AnalysisOut(
        game_id=game_id,
        engine=row.engine,
        depth=row.depth,
        cpl_avg=row.cpl_avg,
        weakness_tags=list(row.weakness_tags or []),
        per_move=list(row.per_move or []),
    )
