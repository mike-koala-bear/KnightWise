from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Node(Base):
    """A learning-graph node (a lesson / micro-topic)."""

    __tablename__ = "nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    domain: Mapped[str] = mapped_column(String(32))  # "tactics" | "endgame" | "strategy" | ...
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_min: Mapped[int] = mapped_column(Integer, default=0)
    rating_max: Mapped[int] = mapped_column(Integer, default=3000)
    branch_group: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # 'prereq' traversal from NodeEdge builds the DAG; see node_edges
    content_path: Mapped[str | None] = mapped_column(String(256), nullable=True)  # MDX path


class NodeEdge(Base):
    __tablename__ = "node_edges"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    from_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    to_node_id: Mapped[int] = mapped_column(ForeignKey("nodes.id"), index=True)
    edge_type: Mapped[str] = mapped_column(String(16), default="prereq")  # "prereq" | "wormhole"
