"""Persist Stockfish analysis into the game_analysis table."""

from __future__ import annotations

from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Game, GameAnalysis
from .analysis import GameAnalysisResult, analyze_pgn


def _serialize(result: GameAnalysisResult) -> list[dict]:
    return [asdict(m) for m in result.per_move]


def analyze_and_store(db: Session, game_id: int, *, depth: int = 14) -> GameAnalysis:
    game = db.execute(select(Game).where(Game.id == game_id)).scalar_one_or_none()
    if game is None:
        raise LookupError(f"Game id={game_id} not found")

    result = analyze_pgn(game.pgn, user_color=game.played_as, depth=depth)

    existing = db.execute(
        select(GameAnalysis).where(GameAnalysis.game_id == game_id)
    ).scalar_one_or_none()
    if existing is None:
        existing = GameAnalysis(game_id=game_id)
        db.add(existing)

    existing.engine = result.engine
    existing.depth = result.depth
    existing.per_move = _serialize(result)
    existing.weakness_tags = result.weakness_tags
    existing.cpl_avg = result.cpl_avg
    db.commit()
    db.refresh(existing)
    return existing
