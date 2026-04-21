"""Chess.com public player games API client.

Docs: https://www.chess.com/news/view/published-data-api
"""

from __future__ import annotations

from datetime import UTC, datetime

import httpx

from .types import IngestedGame

CHESSCOM_API = "https://api.chess.com"
USER_AGENT = "KnightWise/0.1 (+https://knightwise.app)"


class ChesscomClient:
    def __init__(self, base_url: str = CHESSCOM_API, client: httpx.Client | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(
            timeout=30.0, headers={"User-Agent": USER_AGENT, "Accept": "application/json"}
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ChesscomClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def list_archives(self, username: str) -> list[str]:
        r = self._client.get(f"{self.base_url}/pub/player/{username.lower()}/games/archives")
        r.raise_for_status()
        archives = r.json().get("archives", [])
        return [str(url) for url in archives]

    def fetch_archive(self, archive_url: str) -> list[dict]:
        r = self._client.get(archive_url)
        r.raise_for_status()
        return list(r.json().get("games", []))


_RESULT_MAP_WIN = {"win"}
_RESULT_MAP_DRAW = {
    "agreed",
    "repetition",
    "stalemate",
    "insufficient",
    "50move",
    "timevsinsufficient",
}


def _chesscom_result(user_result: str) -> str:
    if user_result in _RESULT_MAP_WIN:
        return "win"
    if user_result in _RESULT_MAP_DRAW:
        return "draw"
    return "loss"


def _normalize_chesscom(raw: dict, username: str) -> IngestedGame:
    white = raw.get("white", {})
    black = raw.get("black", {})
    user_is_white = white.get("username", "").lower() == username.lower()
    played_as = "white" if user_is_white else "black"

    user_side = white if user_is_white else black
    opp_side = black if user_is_white else white

    result = _chesscom_result(str(user_side.get("result", "")))

    end_time = raw.get("end_time") or 0
    started_at = datetime.fromtimestamp(end_time, tz=UTC)

    # chess.com game URL looks like https://www.chess.com/game/live/124543
    external_id = str(raw.get("uuid") or raw.get("url", "").rsplit("/", 1)[-1])

    return IngestedGame(
        source="chesscom",
        external_id=external_id,
        time_control=str(raw.get("time_class") or raw.get("time_control") or ""),
        played_as=played_as,
        opponent_name=opp_side.get("username"),
        opponent_rating=opp_side.get("rating"),
        user_rating=user_side.get("rating"),
        result=result,  # type: ignore[arg-type]
        pgn=raw.get("pgn") or "",
        started_at=started_at,
    )


def fetch_chesscom_games(
    username: str,
    max_games: int = 20,
    client: ChesscomClient | None = None,
) -> list[IngestedGame]:
    """Fetch + normalize the user's most recent games from chess.com.

    Walks monthly archives newest-first until `max_games` are collected.
    """
    owner = client or ChesscomClient()
    try:
        archives = owner.list_archives(username)
        out: list[IngestedGame] = []
        for archive_url in reversed(archives):  # newest first
            for raw in reversed(owner.fetch_archive(archive_url)):  # newest first within month
                out.append(_normalize_chesscom(raw, username))
                if len(out) >= max_games:
                    return out
        return out
    finally:
        if client is None:
            owner.close()
