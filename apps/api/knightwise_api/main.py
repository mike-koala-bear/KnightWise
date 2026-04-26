import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .content import seed_nodes_and_puzzles
from .db import SessionLocal
from .onboarding.seed import seed_onboarding_puzzles
from .routers import (
    analyze,
    drills,
    engine,
    games,
    health,
    ingest,
    llm,
    nodes,
    onboarding,
    progress,
    rating,
    sync,
    warp,
)
from .settings import settings

log = logging.getLogger(__name__)


def _auto_seed() -> None:
    try:
        with SessionLocal() as db:
            r = seed_nodes_and_puzzles(db)
            o = seed_onboarding_puzzles(db)
        log.info(
            "auto-seed: nodes +%d ~%d  puzzles +%d ~%d  onboarding +%d ~%d",
            r.nodes_inserted, r.nodes_updated,
            r.puzzles_inserted, r.puzzles_updated,
            o.inserted, o.updated,
        )
    except Exception:  # noqa: BLE001
        log.warning("auto-seed skipped (DB not ready or seed data missing)", exc_info=True)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    _auto_seed()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="KnightWise API",
        version="0.1.0",
        description="Personalized chess learning. Analysis, progress, lessons.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(analyze.router, prefix="/v1")
    app.include_router(ingest.router, prefix="/v1")
    app.include_router(games.router, prefix="/v1")
    app.include_router(nodes.router, prefix="/v1")
    app.include_router(drills.router, prefix="/v1")
    app.include_router(warp.router, prefix="/v1")
    app.include_router(rating.router, prefix="/v1")
    app.include_router(progress.router, prefix="/v1")
    app.include_router(sync.router, prefix="/v1")
    app.include_router(llm.router, prefix="/v1")
    app.include_router(engine.router, prefix="/v1")
    app.include_router(onboarding.router, prefix="/v1")
    return app


app = create_app()
