"""Weakness tagger v2 — Maia-delta-aware.

Takes the per-move analysis already stored on a game (from `engine/analysis.py`)
plus the user's rating, asks Maia "what would a player of your rating play here?",
and emits a prioritized list of weakness tags.

The Maia-delta insight: if the user played the Maia-predicted-at-rating move and
it was a mistake, that is a *systematic* rating-level mistake — the kind the
bandit should target for drills. If the user played *worse* than Maia-at-rating,
it's a concentration error, not a knowledge gap.

Also layers in structural tags that work off FEN alone:
  - back_rank_weakness: user's king on first rank with no luft
  - passed_pawn_technique: passed pawn positions where user converted poorly
  - opening_out_of_book: high CPL in the first 10 moves
  - endgame_technique: high CPL in the last 15 moves of a >25-move game
  - frequent_blunders / frequent_mistakes: counts per game
  - rating_level_mistake: user matched Maia-at-rating but it was a blunder
  - concentration_error: user played worse than Maia-at-rating would
  - missed_tactic: Stockfish saw an eval swing >= 2.0 the user missed

Real Maia-3 (trained on human games) will make these much sharper — tracked in
PR #5. Until then, the StockfishMaiaAdapter Elo-limiter gives us a usable signal.
"""

from __future__ import annotations

from dataclasses import dataclass, fields

import chess

from .analysis import MoveAnalysis
from .maia import MaiaAdapter, NullMaiaAdapter, get_maia


@dataclass(slots=True)
class TaggedMove(MoveAnalysis):
    maia_move_uci: str | None = None
    matched_maia: bool | None = None


def _tagged_from(m: MoveAnalysis) -> TaggedMove:
    values = {f.name: getattr(m, f.name) for f in fields(MoveAnalysis)}
    return TaggedMove(**values)


def _has_back_rank_weakness(fen: str, user_color: str) -> bool:
    """True when the user's king is on its back rank with all adjacent 2nd-rank
    escape squares blocked by its own pawns (no luft). That's the classic
    back-rank-mate setup.
    """
    board = chess.Board(fen)
    color = chess.WHITE if user_color == "white" else chess.BLACK
    king_sq = board.king(color)
    if king_sq is None:
        return False
    back_rank = 0 if color == chess.WHITE else 7
    if chess.square_rank(king_sq) != back_rank:
        return False

    luft_rank = 1 if color == chess.WHITE else 6
    king_file = chess.square_file(king_sq)
    blocked = 0
    available = 0
    for file_offset in (-1, 0, 1):
        f = king_file + file_offset
        if not (0 <= f <= 7):
            continue
        available += 1
        sq = chess.square(f, luft_rank)
        piece = board.piece_at(sq)
        if piece is not None and piece.piece_type == chess.PAWN and piece.color == color:
            blocked += 1
    # all reachable luft squares blocked by own pawns -> back-rank weakness
    return available > 0 and blocked == available


def _missed_tactic(m: MoveAnalysis) -> bool:
    """The user's move cost >= 200cp versus the best move (mistake or worse)."""
    return m.by_user and m.cpl is not None and m.cpl >= 200


def tag_game(
    per_move: list[MoveAnalysis],
    *,
    user_rating: int | None,
    user_color: str,
    adapter: MaiaAdapter | None = None,
) -> tuple[list[TaggedMove], list[str]]:
    """Run the tagger. Returns (per_move_with_maia_info, list_of_tags).

    When no rating is known or no engine is available, falls through to the
    heuristic-only path (still works, just no Maia delta).
    """
    maia = adapter or get_maia()
    use_maia = user_rating is not None and not isinstance(maia, NullMaiaAdapter)

    tagged: list[TaggedMove] = []
    for m in per_move:
        t = _tagged_from(m)
        if use_maia and m.by_user:
            try:
                pred = maia.predict(m.fen_before, int(user_rating))
                t.maia_move_uci = pred.move_uci
                t.matched_maia = pred.move_uci == m.move_uci
            except Exception:
                # keep tagging even if one position fails
                t.maia_move_uci = None
                t.matched_maia = None
        tagged.append(t)

    user_moves = [t for t in tagged if t.by_user]
    tags: list[str] = []

    blunders = [t for t in user_moves if t.classification == "blunder"]
    mistakes = [t for t in user_moves if t.classification == "mistake"]
    if len(blunders) >= 2:
        tags.append("frequent_blunders")
    if len(mistakes) >= 3:
        tags.append("frequent_mistakes")

    if user_moves:
        opening = user_moves[:10]
        opening_bad = sum(1 for m in opening if m.classification in {"mistake", "blunder"})
        if opening_bad >= 2:
            tags.append("opening_out_of_book")

        if len(user_moves) > 25:
            endgame = user_moves[-15:]
            endgame_bad = sum(1 for m in endgame if m.classification in {"mistake", "blunder"})
            if endgame_bad >= 2:
                tags.append("endgame_technique")

    missed_tactics = [t for t in user_moves if _missed_tactic(t)]
    if len(missed_tactics) >= 2:
        tags.append("missed_tactic")

    back_rank_hits = sum(
        1 for t in user_moves if t.classification in {"mistake", "blunder"}
        and _has_back_rank_weakness(t.fen_before, user_color)
    )
    if back_rank_hits >= 1:
        tags.append("back_rank_weakness")

    if use_maia:
        matched_maia_mistakes = [
            t for t in user_moves
            if t.matched_maia and t.classification in {"mistake", "blunder"}
        ]
        if len(matched_maia_mistakes) >= 2:
            tags.append("rating_level_mistake")

        below_maia = [
            t for t in user_moves
            if t.matched_maia is False and t.classification in {"mistake", "blunder"}
            and t.cpl is not None and t.cpl >= 150
        ]
        if len(below_maia) >= 2:
            tags.append("concentration_error")

    return tagged, tags


__all__ = ["TaggedMove", "tag_game"]
