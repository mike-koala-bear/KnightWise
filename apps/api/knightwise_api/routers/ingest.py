from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db import get_db
from ..ingest import fetch_chesscom_games, fetch_lichess_games, ingest_games

router = APIRouter(tags=["ingest"])

DBSession = Annotated[Session, Depends(get_db)]


class IngestRequest(BaseModel):
    source: str = Field(..., pattern="^(lichess|chesscom)$")
    username: str = Field(..., min_length=1)
    max_games: int = Field(10, ge=1, le=100)


class IngestResponse(BaseModel):
    fetched: int
    inserted: int
    skipped_duplicate: int


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest, db: DBSession) -> IngestResponse:
    try:
        if req.source == "lichess":
            games = fetch_lichess_games(req.username, max_games=req.max_games)
            report = ingest_games(db, games, lichess_username=req.username)
        else:
            games = fetch_chesscom_games(req.username, max_games=req.max_games)
            report = ingest_games(db, games, chesscom_username=req.username)
    except Exception as e:  # surface upstream API errors cleanly
        raise HTTPException(status_code=502, detail=f"upstream error: {e}") from e

    return IngestResponse(
        fetched=len(games),
        inserted=report.inserted,
        skipped_duplicate=report.skipped_duplicate,
    )
