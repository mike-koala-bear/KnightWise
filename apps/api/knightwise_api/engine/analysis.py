"""Batch Stockfish analysis over a whole game's PGN.

Produces per-move centipawn loss (CPL), best-move suggestions, and a light heuristic
weakness tag set. Maia-3 human-likeness tagging lands in PR #3.
"""

from __future__ import annotations

import io
from dataclasses import dataclass, field

import chess
import chess.engine
import chess.pgn

from .stockfish import StockfishUnavailableError, resolve_stockfish_path


@dataclass(slots=True)
class MoveAnalysis:
    ply: int
    fen_before: str
    move_uci: str
    move_san: str
    best_uci: str | None
    eval_cp_before: int | None
    eval_cp_after: int | None
    cpl: int | None  # user centipawn loss (positive = worse)
    classification: str  # "best" | "good" | "inaccuracy" | "mistake" | "blunder"
    by_user: bool


@dataclass(slots=True)
class GameAnalysisResult:
    engine: str
    depth: int
    per_move: list[MoveAnalysis] = field(default_factory=list)
    cpl_avg: float | None = None
    weakness_tags: list[str] = field(default_factory=list)


def _classify(cpl: int | None) -> str:
    if cpl is None:
        return "unknown"
    if cpl <= 10:
        return "best"
    if cpl <= 50:
        return "good"
    if cpl <= 100:
        return "inaccuracy"
    if cpl <= 200:
        return "mistake"
    return "blunder"


def _score_cp(score: chess.engine.Score, perspective: chess.Color) -> int:
    pov = score.white() if perspective == chess.WHITE else score.black()
    if pov.is_mate():
        return 100000 if (pov.mate() or 0) > 0 else -100000
    return pov.score(mate_score=100000) or 0


def _summarize_weaknesses(per_move: list[MoveAnalysis]) -> list[str]:
    """Heuristic weakness tags from classifications alone. Real Maia-aware tagging in PR #3."""
    user_moves = [m for m in per_move if m.by_user]
    if not user_moves:
        return []

    tags: list[str] = []
    blunders = sum(1 for m in user_moves if m.classification == "blunder")
    mistakes = sum(1 for m in user_moves if m.classification == "mistake")
    opening_moves = user_moves[:10]
    opening_bad = sum(1 for m in opening_moves if m.classification in {"mistake", "blunder"})
    endgame_moves = user_moves[-15:] if len(user_moves) > 25 else []
    endgame_bad = sum(1 for m in endgame_moves if m.classification in {"mistake", "blunder"})

    if blunders >= 2:
        tags.append("frequent_blunders")
    if mistakes >= 3:
        tags.append("frequent_mistakes")
    if opening_bad >= 2:
        tags.append("opening_out_of_book")
    if endgame_bad >= 2:
        tags.append("endgame_technique")

    return tags


def analyze_pgn(pgn: str, *, user_color: str = "white", depth: int = 14) -> GameAnalysisResult:
    """Analyze every move in a PGN. `user_color` picks whose CPL we report."""
    path = resolve_stockfish_path()  # raises StockfishUnavailableError
    game = chess.pgn.read_game(io.StringIO(pgn))
    if game is None:
        raise ValueError("Could not parse PGN")

    user_is_white = user_color == "white"
    board = game.board()
    per_move: list[MoveAnalysis] = []

    with chess.engine.SimpleEngine.popen_uci(str(path)) as engine:
        for ply, move in enumerate(game.mainline_moves(), start=1):
            fen_before = board.fen()
            mover = board.turn  # whose move
            info_before = engine.analyse(board, chess.engine.Limit(depth=depth))
            best = (info_before.get("pv") or [None])[0]
            score_before = info_before.get("score")

            san = board.san(move)
            board.push(move)

            info_after = engine.analyse(board, chess.engine.Limit(depth=depth))
            score_after = info_after.get("score")

            cp_before = _score_cp(score_before, mover) if score_before is not None else None
            cp_after = _score_cp(score_after, mover) if score_after is not None else None
            cpl = None
            if cp_before is not None and cp_after is not None:
                cpl = max(0, cp_before - cp_after)

            by_user = (mover == chess.WHITE) == user_is_white

            per_move.append(
                MoveAnalysis(
                    ply=ply,
                    fen_before=fen_before,
                    move_uci=move.uci(),
                    move_san=san,
                    best_uci=best.uci() if best else None,
                    eval_cp_before=cp_before,
                    eval_cp_after=cp_after,
                    cpl=cpl,
                    classification=_classify(cpl) if by_user else "opponent",
                    by_user=by_user,
                )
            )

    user_cpls = [m.cpl for m in per_move if m.by_user and m.cpl is not None]
    cpl_avg = sum(user_cpls) / len(user_cpls) if user_cpls else None

    return GameAnalysisResult(
        engine="stockfish-17.1",
        depth=depth,
        per_move=per_move,
        cpl_avg=cpl_avg,
        weakness_tags=_summarize_weaknesses(per_move),
    )


__all__ = [
    "MoveAnalysis",
    "GameAnalysisResult",
    "StockfishUnavailableError",
    "analyze_pgn",
]
