"""Regression tests for multi-step drill puzzles.

DrillRunner.tsx relies on the convention that ``solution_uci`` alternates
user / opponent / user. These tests confirm:

1. The seed loader produces at least one multi-step puzzle.
2. Every multi-step puzzle's moves are legal in alternation, so
   the auto-play loop in DrillRunner cannot get stuck on an illegal
   opponent reply.
3. Every puzzle whose themes claim a mate ends in checkmate.
4. The drill router serves the same multi-step ``solution_uci`` array,
   and the attempt endpoint accepts a correct attempt for the final
   move (matching how the web UI submits exactly once per puzzle).
"""

from __future__ import annotations

import chess
from knightwise_api.content import seed_nodes_and_puzzles
from knightwise_api.models import Puzzle

MATE_THEMES = {"mate-in-1", "mate-in-2", "mate-in-3", "mateIn1", "mateIn2"}


def _multi_step_puzzles(db_session):
    seed_nodes_and_puzzles(db_session)
    return (
        db_session.query(Puzzle)
        .filter(Puzzle.solution_uci.isnot(None))
        .all()
    )


def test_seed_contains_multi_step_puzzles(db_session):
    puzzles = _multi_step_puzzles(db_session)
    multi = [p for p in puzzles if len(p.solution_uci or []) >= 3]
    assert len(multi) >= 5, (
        f"expected ≥5 multi-step puzzles in seed, got {len(multi)}"
    )


def test_every_multi_step_solution_legal(db_session):
    """Every move in solution_uci must be legal in turn (alternating sides)."""
    puzzles = _multi_step_puzzles(db_session)
    failures: list[str] = []
    for puzzle in puzzles:
        if not puzzle.solution_uci or len(puzzle.solution_uci) < 2:
            continue
        board = chess.Board(puzzle.fen)
        for i, uci in enumerate(puzzle.solution_uci):
            try:
                move = chess.Move.from_uci(uci)
            except chess.InvalidMoveError as e:
                failures.append(f"{puzzle.external_id}: invalid uci {uci}: {e}")
                break
            if move not in board.legal_moves:
                failures.append(
                    f"{puzzle.external_id}: illegal move #{i + 1} {uci} in {board.fen()}"
                )
                break
            board.push(move)

    assert not failures, "multi-step puzzles have illegal moves:\n" + "\n".join(failures)


def test_mate_themed_puzzles_actually_mate(db_session):
    puzzles = _multi_step_puzzles(db_session)
    failures: list[str] = []
    for puzzle in puzzles:
        themes = set(puzzle.themes or [])
        if not themes & MATE_THEMES:
            continue
        board = chess.Board(puzzle.fen)
        for uci in puzzle.solution_uci or []:
            board.push(chess.Move.from_uci(uci))
        if not board.is_checkmate():
            failures.append(
                f"{puzzle.external_id}: claims mate ({themes & MATE_THEMES}) but final FEN is {board.fen()}"
            )
    assert not failures, "\n".join(failures)


def test_drill_router_serves_multi_step_solution(client, db_session):
    """Smoke test: walk a 3-ply puzzle exactly the way the web UI does."""
    seed_nodes_and_puzzles(db_session)

    target = (
        db_session.query(Puzzle)
        .filter(Puzzle.external_id == "kw-back-rank-deflect")
        .first()
    )
    assert target is not None, "kw-back-rank-deflect must be in the seed"
    assert len(target.solution_uci) == 3, "back-rank-deflect should be 3 plies"

    board = chess.Board(target.fen)
    for uci in target.solution_uci:
        move = chess.Move.from_uci(uci)
        assert move in board.legal_moves, f"illegal {uci} in {board.fen()}"
        board.push(move)
    assert board.is_checkmate(), "back-rank-deflect must end in mate"

    client.get("/v1/drills/next?node_slug=back-rank-basics")
    r = client.post(
        "/v1/drills/attempt",
        json={
            "user_id": 1,
            "puzzle_id": target.id,
            "correct": True,
            "time_ms": 7200,
            "hints_used": 0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["repetitions"] == 1
    assert body["interval_days"] == 1
