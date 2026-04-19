from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base


class Game(Base):
    __tablename__ = "games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    source: Mapped[str] = mapped_column(String(16))  # "lichess" | "chesscom"
    external_id: Mapped[str] = mapped_column(String, index=True)
    time_control: Mapped[str | None] = mapped_column(String(32), nullable=True)
    played_as: Mapped[str] = mapped_column(String(8))  # "white" | "black"
    opponent_name: Mapped[str | None] = mapped_column(String, nullable=True)
    opponent_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    result: Mapped[str] = mapped_column(String(8))  # "win" | "loss" | "draw"
    pgn: Mapped[str] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    analysis: Mapped["GameAnalysis | None"] = relationship(back_populates="game", uselist=False)


class GameAnalysis(Base):
    __tablename__ = "game_analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    game_id: Mapped[int] = mapped_column(ForeignKey("games.id"), unique=True, index=True)
    engine: Mapped[str] = mapped_column(String(32), default="stockfish-17.1")
    depth: Mapped[int] = mapped_column(Integer, default=18)
    per_move: Mapped[list[dict]] = mapped_column(JSON, default=list)
    weakness_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    cpl_avg: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    game: Mapped[Game] = relationship(back_populates="analysis")
