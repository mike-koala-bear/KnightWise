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

from .content import seed_nodes_and_puzzles
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


def cmd_seed_nodes(_: argparse.Namespace) -> int:
    with SessionLocal() as db:
        report = seed_nodes_and_puzzles(db)
    print(
        f"seed: nodes {report.nodes_inserted}+/{report.nodes_updated}~  "
        f"puzzles {report.puzzles_inserted}+/{report.puzzles_updated}~  "
        f"edges {report.edges_inserted}+  "
        f"node_puzzle_links {report.node_puzzle_links_inserted}+"
    )
    return 0


def cmd_maia_check(args: argparse.Namespace) -> int:
    """Smoke-test the Maia-3 ONNX install.

    Prints the active adapter, runs a single inference on the supplied FEN at
    the supplied rating, and reports the top-3 predicted moves. Useful for
    confirming ``--extra maia3`` is wired correctly without spinning up the
    full API.
    """
    from .engine.maia import Maia3Adapter, Maia3Unavailable, _get_session, adapter_name, get_maia

    adapter = get_maia()
    name = adapter_name(adapter)
    print(f"active adapter: {name}")

    if name != "maia3":
        print("Maia-3 is not active. To enable:")
        print("  uv sync --extra maia3")
        print("  KNIGHTWISE_MAIA_ADAPTER=auto knightwise maia-check")
        return 1

    fen = cast(str, args.fen)
    rating = int(args.rating)
    try:
        session = _get_session()
    except Maia3Unavailable as exc:
        print(f"Maia-3 unavailable: {exc}", file=sys.stderr)
        return 1
    move_probs, ldw = session.probs(fen=fen, elo_self=float(rating), elo_oppo=float(rating))
    print(f"FEN: {fen}")
    print(f"rating: {rating} (self vs self)")
    print(f"LDW (loss/draw/win, side to move): {ldw[0]:.3f} / {ldw[1]:.3f} / {ldw[2]:.3f}")
    print("top 3 moves:")
    for uci, prob in list(move_probs.items())[:3]:
        print(f"  {uci}  {prob * 100:5.1f}%")
    # Also exercise the adapter so we cover the full call path users hit.
    pred = Maia3Adapter(model=session).predict(fen, rating)
    print(f"adapter top: {pred.move_uci} ({pred.prob * 100:.1f}%)")
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

    p_seed = sub.add_parser("seed-nodes", help="Seed authored lesson nodes + puzzles")
    p_seed.set_defaults(func=cmd_seed_nodes)

    p_maia = sub.add_parser(
        "maia-check",
        help="Smoke-test the optional Maia-3 ONNX install (requires --extra maia3)",
    )
    p_maia.add_argument(
        "--fen",
        default="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        help="FEN to evaluate (default: starting position)",
    )
    p_maia.add_argument("--rating", type=int, default=1500)
    p_maia.set_defaults(func=cmd_maia_check)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
