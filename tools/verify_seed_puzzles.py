"""Validate every puzzle in ``content/nodes/seed.json`` and ``onboarding.json``.

For each puzzle we check:
1. The starting FEN parses.
2. Every move in ``solution_uci`` is legal in turn (alternating sides).
3. If a puzzle's themes include ``mate-in-1`` or ``mate-in-2``, the final
   position is checkmate. Otherwise we just print the material delta.

Run from the repo root::

    cd apps/api && uv run python ../../tools/verify_seed_puzzles.py

Exits non-zero on any failure. CI runs this before any seed change is
allowed onto main, so puzzles can never silently rot.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import chess

REPO_ROOT = Path(__file__).resolve().parent.parent
SEED_FILES = [
    REPO_ROOT / "content" / "nodes" / "seed.json",
    REPO_ROOT / "content" / "nodes" / "onboarding.json",
]

MATE_THEMES = {"mate-in-1", "mate-in-2", "mate-in-3", "mateIn1", "mateIn2"}


def material_delta(board: chess.Board, baseline: int) -> int:
    current = sum(
        len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK))
        for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
    )
    return current - baseline


def main() -> int:
    failures: list[tuple[str, str]] = []
    total = 0
    for seed_file in SEED_FILES:
        if not seed_file.exists():
            continue
        data = json.loads(seed_file.read_text())
        for puzzle in data.get("puzzles", []):
            total += 1
            ext_id = puzzle["external_id"]
            try:
                board = chess.Board(puzzle["fen"])
            except ValueError as e:
                failures.append((ext_id, f"invalid FEN: {e}"))
                continue

            baseline = sum(
                len(board.pieces(pt, chess.WHITE)) - len(board.pieces(pt, chess.BLACK))
                for pt in (chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN)
            )
            ok = True
            for i, uci in enumerate(puzzle["solution_uci"]):
                try:
                    move = chess.Move.from_uci(uci)
                except chess.InvalidMoveError as e:
                    failures.append((ext_id, f"invalid uci {uci}: {e}"))
                    ok = False
                    break
                if move not in board.legal_moves:
                    failures.append(
                        (ext_id, f"illegal move #{i + 1} {uci} in {board.fen()}")
                    )
                    ok = False
                    break
                board.push(move)
            if not ok:
                continue

            themes = set(puzzle.get("themes", []))
            if themes & MATE_THEMES and not board.is_checkmate():
                failures.append((ext_id, f"expected mate but final position is not mate: {board.fen()}"))
                continue

            print(
                f"  ✓ {ext_id:32s} "
                f"plies={len(puzzle['solution_uci']):2d} "
                f"Δmaterial={material_delta(board, baseline):+d} "
                f"{'mate' if board.is_checkmate() else ''}"
            )

    print()
    if failures:
        print("FAILURES:")
        for ext, msg in failures:
            print(f"  ✗ {ext}: {msg}")
        return 1
    print(f"OK — {total} puzzles validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
