"""KnightWise CLI.

Usage:
  uv run --directory apps/api python -m knightwise_api.cli ingest --source lichess --user mike-bear --max 20
  uv run --directory apps/api python -m knightwise_api.cli analyze --game-id 1 --depth 14
  uv run --directory apps/api python -m knightwise_api.cli analyze-all --depth 14 --limit 20
  uv run --directory apps/api python -m knightwise_api.cli games
"""

from __future__ import annotations

import argparse
import sys
from typing import cast

from sqlalchemy import select

from .db import SessionLocal
from .engine.analysis import StockfishUnavailableError
from .engine.pipeline import analyze_and_store
from .ingest import fetch_chesscom_games, fetch_lichess_games, ingest_games
from .models import Game


def cmd_ingest(args: argparse.Namespace) -> int:
    username = cast(str, args.user)
    if args.source == "lichess":
        games = fetch_lichess_games(username, max_games=args.max)
        handle_kwargs = {"lichess_username": username}
    else:
        games = fetch_chesscom_games(username, max_games=args.max)
        handle_kwargs = {"chesscom_username": username}

    with SessionLocal() as db:
        report = ingest_games(db, games, **handle_kwargs)
    print(
        f"ingest: source={args.source} fetched={len(games)} "
        f"inserted={report.inserted} skipped_dupe={report.skipped_duplicate}"
    )
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    try:
        with SessionLocal() as db:
            result = analyze_and_store(db, args.game_id, depth=args.depth)
        print(
            f"analyzed game {args.game_id}: depth={result.depth} "
            f"avg_cpl={result.cpl_avg:.1f} tags={result.weakness_tags}"
            if result.cpl_avg is not None
            else f"analyzed game {args.game_id}: depth={result.depth} tags={result.weakness_tags}"
        )
        return 0
    except StockfishUnavailableError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except LookupError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def cmd_analyze_all(args: argparse.Namespace) -> int:
    with SessionLocal() as db:
        stmt = select(Game.id).order_by(Game.started_at.desc()).limit(args.limit)
        game_ids = [gid for (gid,) in db.execute(stmt).all()]

    if not game_ids:
        print("no games to analyze (run `ingest` first)")
        return 0

    ok = 0
    for gid in game_ids:
        try:
            with SessionLocal() as db:
                analyze_and_store(db, gid, depth=args.depth)
            ok += 1
            print(f"  [{ok}/{len(game_ids)}] game {gid}: analyzed")
        except StockfishUnavailableError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        except Exception as e:  # noqa: BLE001
            print(f"  game {gid}: skipped ({e})", file=sys.stderr)

    print(f"analyzed {ok}/{len(game_ids)} games")
    return 0


def cmd_games(_: argparse.Namespace) -> int:
    with SessionLocal() as db:
        rows = db.execute(
            select(Game).order_by(Game.started_at.desc()).limit(20)
        ).scalars().all()
    if not rows:
        print("no games")
        return 0
    for g in rows:
        print(
            f"{g.id:>4} {g.source:>8} {g.started_at:%Y-%m-%d} {g.time_control or '?':>8} "
            f"{g.played_as:>5} {g.result:>4} vs {g.opponent_name or '?'} ({g.opponent_rating or '?'})"
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="knightwise")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="Fetch games from Lichess or Chess.com")
    p_ingest.add_argument("--source", choices=["lichess", "chesscom"], required=True)
    p_ingest.add_argument("--user", required=True)
    p_ingest.add_argument("--max", type=int, default=20)
    p_ingest.set_defaults(func=cmd_ingest)

    p_analyze = sub.add_parser("analyze", help="Analyze a single ingested game")
    p_analyze.add_argument("--game-id", type=int, required=True)
    p_analyze.add_argument("--depth", type=int, default=14)
    p_analyze.set_defaults(func=cmd_analyze)

    p_all = sub.add_parser("analyze-all", help="Analyze the N most recent games")
    p_all.add_argument("--depth", type=int, default=14)
    p_all.add_argument("--limit", type=int, default=20)
    p_all.set_defaults(func=cmd_analyze_all)

    p_games = sub.add_parser("games", help="List recently ingested games")
    p_games.set_defaults(func=cmd_games)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
