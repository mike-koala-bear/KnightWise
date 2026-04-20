"""Lichess public games API client.

Docs: https://lichess.org/api#tag/Games/operation/apiGamesUser
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import UTC, datetime

import httpx

from ..settings import settings
from .types import IngestedGame

LICHESS_API = "https://lichess.org"


class LichessClient:
    def __init__(
        self,
        base_url: str = LICHESS_API,
        token: str | None = None,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token or settings.lichess_token
        self._client = client or httpx.Client(timeout=30.0)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> LichessClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def fetch_user_games(self, username: str, max_games: int = 20) -> Iterable[dict]:
        """Stream the user's most recent games as parsed NDJSON dicts (newest first)."""
        headers = {"Accept": "application/x-ndjson"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        url = f"{self.base_url}/api/games/user/{username}"
        params = {"max": str(max_games), "pgnInJson": "true", "clocks": "false"}
        with self._client.stream("GET", url, headers=headers, params=params) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                yield json.loads(line)


def _normalize_lichess(raw: dict, username: str) -> IngestedGame:
    players = raw.get("players", {})
    white = players.get("white", {}).get("user", {}).get("name")
    user_is_white = (white or "").lower() == username.lower()
    played_as = "white" if user_is_white else "black"

    winner = raw.get("winner")
    if winner is None:
        result = "draw"
    elif winner == played_as:
        result = "win"
    else:
        result = "loss"

    user_side = players.get("white" if user_is_white else "black", {})
    opp_side = players.get("black" if user_is_white else "white", {})

    time_control = raw.get("speed") or raw.get("perf")

    started_ms = raw.get("createdAt") or 0
    started_at = datetime.fromtimestamp(started_ms / 1000, tz=UTC)

    return IngestedGame(
        source="lichess",
        external_id=str(raw["id"]),
        time_control=time_control,
        played_as=played_as,
        opponent_name=opp_side.get("user", {}).get("name"),
        opponent_rating=opp_side.get("rating"),
        user_rating=user_side.get("rating"),
        result=result,  # type: ignore[arg-type]
        pgn=raw.get("pgn") or "",
        started_at=started_at,
    )


def fetch_lichess_games(
    username: str,
    max_games: int = 20,
    client: LichessClient | None = None,
) -> list[IngestedGame]:
    """Fetch + normalize the user's latest games from Lichess."""
    owner = client or LichessClient()
    try:
        return [_normalize_lichess(raw, username) for raw in owner.fetch_user_games(username, max_games)]
    finally:
        if client is None:
            owner.close()
