from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..sync import JOB_REGISTRY, SyncJobStatus, run_sync

router = APIRouter(tags=["sync"])

DBSession = Annotated[Session, Depends(get_db)]


class SyncRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    lichess_username: str | None = Field(None, min_length=1, max_length=64)
    chesscom_username: str | None = Field(None, min_length=1, max_length=64)
    max_games: int = Field(10, ge=1, le=50)
    analyze: bool = True
    depth: int = Field(14, ge=6, le=22)


class SyncStartedResponse(BaseModel):
    job_id: str
    status: SyncJobStatus


class SyncStatusResponse(BaseModel):
    job_id: str
    status: SyncJobStatus
    message: str
    lichess_fetched: int
    lichess_inserted: int
    chesscom_fetched: int
    chesscom_inserted: int
    games_analyzed: int
    games_failed: int
    total_games_to_analyze: int
    total_fetched: int
    total_inserted: int
    error: str | None
    started_at: str
    finished_at: str | None


@router.post("/sync", response_model=SyncStartedResponse)
def start_sync(
    req: SyncRequest,
    background: BackgroundTasks,
    db: DBSession,
) -> SyncStartedResponse:
    user = db.execute(select(User).where(User.id == req.user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail=f"user not found: {req.user_id}")

    lichess = req.lichess_username or user.lichess_username
    chesscom = req.chesscom_username or user.chesscom_username
    if not lichess and not chesscom:
        raise HTTPException(
            status_code=400,
            detail="No Lichess or Chess.com username available for this user",
        )

    job = JOB_REGISTRY.create(
        user_id=req.user_id,
        lichess_username=lichess,
        chesscom_username=chesscom,
        max_games=req.max_games,
        analyze=req.analyze,
        depth=req.depth,
    )
    background.add_task(run_sync, job.job_id)
    return SyncStartedResponse(job_id=job.job_id, status=job.status)


@router.get("/sync/status/{job_id}", response_model=SyncStatusResponse)
def sync_status(job_id: str) -> SyncStatusResponse:
    job = JOB_REGISTRY.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"job not found: {job_id}")
    return SyncStatusResponse(
        job_id=job.job_id,
        status=job.status,
        message=job.message,
        lichess_fetched=job.lichess_fetched,
        lichess_inserted=job.lichess_inserted,
        chesscom_fetched=job.chesscom_fetched,
        chesscom_inserted=job.chesscom_inserted,
        games_analyzed=job.games_analyzed,
        games_failed=job.games_failed,
        total_games_to_analyze=job.total_games_to_analyze,
        total_fetched=job.total_fetched,
        total_inserted=job.total_inserted,
        error=job.error,
        started_at=job.started_at.isoformat(),
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
    )
