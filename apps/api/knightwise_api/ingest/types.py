from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Source = Literal["lichess", "chesscom"]
PlayedAs = Literal["white", "black"]
Result = Literal["win", "loss", "draw"]


class IngestedGame(BaseModel):
    """Normalized, source-agnostic game record ready to persist."""

    source: Source
    external_id: str
    time_control: str | None = None
    played_as: PlayedAs
    opponent_name: str | None = None
    opponent_rating: int | None = None
    user_rating: int | None = None
    result: Result
    pgn: str
    started_at: datetime
