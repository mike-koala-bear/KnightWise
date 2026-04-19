from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, drills, games, health, ingest, nodes
from .settings import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title="KnightWise API",
        version="0.1.0",
        description="Personalized chess learning. Analysis, progress, lessons.",
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
    return app


app = create_app()
