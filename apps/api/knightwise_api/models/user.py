from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clerk_id: Mapped[str | None] = mapped_column(String, unique=True, nullable=True, index=True)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    lichess_username: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    chesscom_username: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    # Glicko-2 rating estimate (after onboarding)
    rating_mu: Mapped[float | None] = mapped_column(nullable=True)
    rating_sigma: Mapped[float | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
