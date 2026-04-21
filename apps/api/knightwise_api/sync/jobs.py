"""In-memory sync-job registry for the single-user MVP.

A sync job pulls Lichess + Chess.com games for a user and then runs
Stockfish batch analysis on each newly-ingested game. Progress is streamed
back to the UI via a polled status endpoint.

We deliberately avoid Celery/RQ/Temporal at this stage — for one user with
~20 games per sync the workload fits comfortably in a FastAPI
BackgroundTasks coroutine and the registry can live in process memory. When
we move to Render (and then Fly) the registry will swap to Redis.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from ..db import SessionLocal
from ..engine.pipeline import analyze_and_store
from ..engine.stockfish import StockfishUnavailableError
from ..ingest import fetch_chesscom_games, fetch_lichess_games, ingest_games

logger = logging.getLogger(__name__)

SyncJobStatus = Literal["pending", "running", "done", "error"]


@dataclass(slots=True)
class SyncJob:
    job_id: str
    user_id: int
    lichess_username: str | None
    chesscom_username: str | None
    max_games: int
    analyze: bool
    depth: int
    status: SyncJobStatus = "pending"
    message: str = "queued"
    lichess_fetched: int = 0
    lichess_inserted: int = 0
    chesscom_fetched: int = 0
    chesscom_inserted: int = 0
    games_analyzed: int = 0
    games_failed: int = 0
    total_games_to_analyze: int = 0
    error: str | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    finished_at: datetime | None = None

    @property
    def total_fetched(self) -> int:
        return self.lichess_fetched + self.chesscom_fetched

    @property
    def total_inserted(self) -> int:
        return self.lichess_inserted + self.chesscom_inserted


class _Registry:
    """Thread-safe in-memory dict of job_id -> SyncJob."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._jobs: dict[str, SyncJob] = {}

    def create(
        self,
        *,
        user_id: int,
        lichess_username: str | None,
        chesscom_username: str | None,
        max_games: int,
        analyze: bool,
        depth: int,
    ) -> SyncJob:
        job = SyncJob(
            job_id=uuid.uuid4().hex[:12],
            user_id=user_id,
            lichess_username=lichess_username,
            chesscom_username=chesscom_username,
            max_games=max_games,
            analyze=analyze,
            depth=depth,
        )
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> SyncJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **changes: object) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            for k, v in changes.items():
                setattr(job, k, v)


JOB_REGISTRY = _Registry()


def run_sync(job_id: str) -> None:
    """Execute a sync job in the background. Errors are captured on the job."""
    job = JOB_REGISTRY.get(job_id)
    if job is None:
        logger.warning("run_sync: job %s not found", job_id)
        return

    JOB_REGISTRY.update(job_id, status="running", message="ingesting games")

    db: Session = SessionLocal()
    try:
        inserted_game_ids: list[int] = []

        if job.lichess_username:
            JOB_REGISTRY.update(job_id, message=f"fetching Lichess games for {job.lichess_username}")
            try:
                games = fetch_lichess_games(job.lichess_username, max_games=job.max_games)
                report = ingest_games(db, games, lichess_username=job.lichess_username)
                JOB_REGISTRY.update(
                    job_id,
                    lichess_fetched=len(games),
                    lichess_inserted=report.inserted,
                )
                inserted_game_ids.extend(report.game_ids)
            except Exception as e:  # network, API, parse errors
                logger.exception("lichess ingest failed for job %s", job_id)
                JOB_REGISTRY.update(job_id, message=f"Lichess failed: {e}")

        if job.chesscom_username:
            JOB_REGISTRY.update(job_id, message=f"fetching Chess.com games for {job.chesscom_username}")
            try:
                games = fetch_chesscom_games(job.chesscom_username, max_games=job.max_games)
                report = ingest_games(db, games, chesscom_username=job.chesscom_username)
                JOB_REGISTRY.update(
                    job_id,
                    chesscom_fetched=len(games),
                    chesscom_inserted=report.inserted,
                )
                inserted_game_ids.extend(report.game_ids)
            except Exception as e:
                logger.exception("chess.com ingest failed for job %s", job_id)
                JOB_REGISTRY.update(job_id, message=f"Chess.com failed: {e}")

        if job.analyze and inserted_game_ids:
            JOB_REGISTRY.update(
                job_id,
                total_games_to_analyze=len(inserted_game_ids),
                message=f"analyzing {len(inserted_game_ids)} new games at depth {job.depth}",
            )
            analyzed = 0
            failed = 0
            for gid in inserted_game_ids:
                try:
                    analyze_and_store(db, gid, depth=job.depth)
                    analyzed += 1
                except StockfishUnavailableError as e:
                    failed += 1
                    logger.warning("Stockfish unavailable for game %s: %s", gid, e)
                except Exception as e:
                    failed += 1
                    logger.exception("analyze failed for game %s in job %s", gid, job_id)
                    JOB_REGISTRY.update(job_id, message=f"analyze error on game {gid}: {e}")
                JOB_REGISTRY.update(job_id, games_analyzed=analyzed, games_failed=failed)

        JOB_REGISTRY.update(
            job_id,
            status="done",
            message="complete",
            finished_at=datetime.now(UTC),
        )
    except Exception as e:  # catastrophic; shouldn't hit the per-step handlers above
        logger.exception("run_sync catastrophic failure for job %s", job_id)
        JOB_REGISTRY.update(
            job_id,
            status="error",
            message="failed",
            error=str(e),
            finished_at=datetime.now(UTC),
        )
    finally:
        db.close()
