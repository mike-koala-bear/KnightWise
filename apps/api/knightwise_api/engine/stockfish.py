"""Minimal Stockfish UCI wrapper using python-chess.

This is a stub for PR #1 — the real batch analysis pipeline arrives in PR #2.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import chess
import chess.engine

from ..settings import settings


class StockfishUnavailableError(RuntimeError):
    """Raised when the Stockfish binary cannot be located or launched."""


@dataclass(slots=True)
class AnalysisResult:
    eval_cp: int | None
    eval_mate: int | None
    best_move: str | None


def resolve_stockfish_path() -> Path:
    configured = Path(settings.stockfish_path)
    if configured.exists():
        return configured
    located = shutil.which("stockfish")
    if located:
        return Path(located)
    raise StockfishUnavailableError(
        f"Stockfish binary not found at {configured} or on PATH. "
        "See engine/README.md for install instructions."
    )


def analyze_fen(fen: str, depth: int = 14) -> AnalysisResult:
    path = resolve_stockfish_path()
    try:
        board = chess.Board(fen)
    except ValueError as e:
        raise ValueError(f"Invalid FEN: {e}") from e

    with chess.engine.SimpleEngine.popen_uci(str(path)) as engine:
        info = engine.analyse(board, chess.engine.Limit(depth=depth))

    score = info.get("score")
    pv = info.get("pv") or []
    best = pv[0].uci() if pv else None

    eval_cp: int | None = None
    eval_mate: int | None = None
    if score is not None:
        pov = score.white() if board.turn == chess.WHITE else score.black()
        if pov.is_mate():
            eval_mate = pov.mate()
        else:
            eval_cp = pov.score(mate_score=100000)

    return AnalysisResult(eval_cp=eval_cp, eval_mate=eval_mate, best_move=best)
