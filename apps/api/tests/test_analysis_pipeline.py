"""Stockfish-gated tests. Skipped when no stockfish binary is available."""

import shutil
from datetime import UTC, datetime

import pytest
from knightwise_api.engine.analysis import (
    MoveAnalysis,
    _classify,
    _summarize_weaknesses,
    analyze_pgn,
)
from knightwise_api.engine.pipeline import analyze_and_store
from knightwise_api.ingest.service import ingest_games
from knightwise_api.ingest.types import IngestedGame

SCHOLARS_MATE_PGN = """
[Event "Test"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "mike-bear"]
[Black "opp"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0
""".strip()


def test_classify_thresholds():
    assert _classify(None) == "unknown"
    assert _classify(0) == "best"
    assert _classify(25) == "good"
    assert _classify(75) == "inaccuracy"
    assert _classify(150) == "mistake"
    assert _classify(500) == "blunder"


def test_summarize_weaknesses_tags_blunders_and_opening():
    moves = [
        MoveAnalysis(
            ply=i,
            fen_before="",
            move_uci="e2e4",
            move_san="e4",
            best_uci=None,
            eval_cp_before=0,
            eval_cp_after=0,
            cpl=(250 if i in (1, 3) else 120 if i == 5 else 20),
            classification=(
                "blunder" if i in (1, 3) else "mistake" if i == 5 else "good"
            ),
            by_user=True,
        )
        for i in range(1, 8)
    ]
    tags = _summarize_weaknesses(moves)
    assert "frequent_blunders" in tags
    assert "opening_out_of_book" in tags


@pytest.mark.skipif(shutil.which("stockfish") is None, reason="stockfish not installed")
def test_analyze_pgn_full(tmp_path):
    result = analyze_pgn(SCHOLARS_MATE_PGN, user_color="white", depth=8)
    assert result.engine.startswith("stockfish")
    assert result.depth == 8
    assert len(result.per_move) >= 6
    user_moves = [m for m in result.per_move if m.by_user]
    assert user_moves, "should have user moves"
    assert any(m.move_san in {"Qxf7#", "Qxf7"} for m in result.per_move)


@pytest.mark.skipif(shutil.which("stockfish") is None, reason="stockfish not installed")
def test_analyze_and_store_persists(db_session):
    ingest_games(
        db_session,
        [
            IngestedGame(
                source="lichess",
                external_id="pgntest-1",
                time_control="blitz",
                played_as="white",
                opponent_name="opp",
                opponent_rating=1400,
                user_rating=1400,
                result="win",
                pgn=SCHOLARS_MATE_PGN,
                started_at=datetime(2024, 1, 1, tzinfo=UTC),
            )
        ],
        lichess_username="mike-bear",
    )
    from knightwise_api.models import Game

    gid = db_session.query(Game.id).scalar()
    row = analyze_and_store(db_session, gid, depth=8)
    assert row.game_id == gid
    assert row.cpl_avg is None or row.cpl_avg >= 0
    assert isinstance(row.weakness_tags, list)
    assert isinstance(row.per_move, list)
    assert len(row.per_move) == 7
