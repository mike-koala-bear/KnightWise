"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("clerk_id", sa.String, nullable=True, unique=True),
        sa.Column("email", sa.String, nullable=True, unique=True),
        sa.Column("display_name", sa.String, nullable=True),
        sa.Column("lichess_username", sa.String, nullable=True),
        sa.Column("chesscom_username", sa.String, nullable=True),
        sa.Column("rating_mu", sa.Float, nullable=True),
        sa.Column("rating_sigma", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )
    op.create_index("ix_users_lichess_username", "users", ["lichess_username"])
    op.create_index("ix_users_chesscom_username", "users", ["chesscom_username"])

    op.create_table(
        "games",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True),
        sa.Column("source", sa.String(16)),
        sa.Column("external_id", sa.String, index=True),
        sa.Column("time_control", sa.String(32), nullable=True),
        sa.Column("played_as", sa.String(8)),
        sa.Column("opponent_name", sa.String, nullable=True),
        sa.Column("opponent_rating", sa.Integer, nullable=True),
        sa.Column("user_rating", sa.Integer, nullable=True),
        sa.Column("result", sa.String(8)),
        sa.Column("pgn", sa.Text),
        sa.Column("started_at", sa.DateTime),
        sa.Column("ingested_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "game_analysis",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("game_id", sa.Integer, sa.ForeignKey("games.id"), unique=True, index=True),
        sa.Column("engine", sa.String(32), server_default="stockfish-17.1"),
        sa.Column("depth", sa.Integer, server_default="18"),
        sa.Column("per_move", sa.JSON),
        sa.Column("weakness_tags", sa.JSON),
        sa.Column("cpl_avg", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "nodes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("slug", sa.String(128), unique=True, index=True),
        sa.Column("domain", sa.String(32)),
        sa.Column("title", sa.String(128)),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("rating_min", sa.Integer, server_default="0"),
        sa.Column("rating_max", sa.Integer, server_default="3000"),
        sa.Column("branch_group", sa.String(64), nullable=True, index=True),
        sa.Column("content_path", sa.String(256), nullable=True),
    )

    op.create_table(
        "node_edges",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("from_node_id", sa.Integer, sa.ForeignKey("nodes.id"), index=True),
        sa.Column("to_node_id", sa.Integer, sa.ForeignKey("nodes.id"), index=True),
        sa.Column("edge_type", sa.String(16), server_default="prereq"),
    )

    op.create_table(
        "puzzles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("external_id", sa.String, nullable=True, unique=True),
        sa.Column("fen", sa.String(128), index=True),
        sa.Column("solution_uci", sa.JSON),
        sa.Column("themes", sa.JSON),
        sa.Column("rating", sa.Integer, server_default="1500"),
        sa.Column("source", sa.String(32), server_default="lichess"),
        sa.Column("description", sa.Text, nullable=True),
    )

    op.create_table(
        "node_puzzles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("node_id", sa.Integer, sa.ForeignKey("nodes.id"), index=True),
        sa.Column("puzzle_id", sa.Integer, sa.ForeignKey("puzzles.id"), index=True),
        sa.Column("position", sa.Integer, server_default="0"),
    )

    op.create_table(
        "node_progress",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True),
        sa.Column("node_id", sa.Integer, sa.ForeignKey("nodes.id"), index=True),
        sa.Column("status", sa.String(16), server_default="locked"),
        sa.Column("mastery", sa.Float, server_default="0.0"),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "puzzle_attempts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True),
        sa.Column("puzzle_id", sa.Integer, sa.ForeignKey("puzzles.id"), index=True),
        sa.Column("node_id", sa.Integer, sa.ForeignKey("nodes.id"), nullable=True),
        sa.Column("correct", sa.Boolean),
        sa.Column("time_ms", sa.Integer),
        sa.Column("hints_used", sa.Integer, server_default="0"),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "srs_cards",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id"), index=True),
        sa.Column("puzzle_id", sa.Integer, sa.ForeignKey("puzzles.id"), index=True),
        sa.Column("ease", sa.Float, server_default="2.5"),
        sa.Column("interval_days", sa.Integer, server_default="0"),
        sa.Column("repetitions", sa.Integer, server_default="0"),
        sa.Column("due_at", sa.DateTime, server_default=sa.func.now(), index=True),
        sa.Column("stability", sa.Float, nullable=True),
        sa.Column("difficulty", sa.Float, nullable=True),
        sa.Column("decay", sa.Float, nullable=True, server_default="-0.5"),
    )


def downgrade() -> None:
    for t in [
        "srs_cards",
        "puzzle_attempts",
        "node_progress",
        "node_puzzles",
        "puzzles",
        "node_edges",
        "nodes",
        "game_analysis",
        "games",
        "users",
    ]:
        op.drop_table(t)
