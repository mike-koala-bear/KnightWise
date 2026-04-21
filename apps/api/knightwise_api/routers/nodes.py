from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Node, NodeEdge

router = APIRouter(tags=["nodes"])

DBSession = Annotated[Session, Depends(get_db)]


class NodeOut(BaseModel):
    id: int
    slug: str
    domain: str
    title: str
    description: str | None
    rating_min: int
    rating_max: int
    branch_group: str | None
    prereq_slugs: list[str]


def _row_to_out(db: Session, node: Node) -> NodeOut:
    prereq_rows = db.execute(
        select(Node.slug)
        .join(NodeEdge, NodeEdge.from_node_id == Node.id)
        .where(NodeEdge.to_node_id == node.id, NodeEdge.edge_type == "prereq")
    ).all()
    return NodeOut(
        id=node.id,
        slug=node.slug,
        domain=node.domain,
        title=node.title,
        description=node.description,
        rating_min=node.rating_min,
        rating_max=node.rating_max,
        branch_group=node.branch_group,
        prereq_slugs=[r[0] for r in prereq_rows],
    )


@router.get("/nodes", response_model=list[NodeOut])
def list_nodes(db: DBSession) -> list[NodeOut]:
    rows = db.execute(select(Node).order_by(Node.rating_min, Node.slug)).scalars().all()
    return [_row_to_out(db, n) for n in rows]


@router.get("/nodes/{slug}", response_model=NodeOut)
def get_node(slug: str, db: DBSession) -> NodeOut:
    node = db.execute(select(Node).where(Node.slug == slug)).scalar_one_or_none()
    if node is None:
        raise HTTPException(status_code=404, detail=f"node not found: {slug}")
    return _row_to_out(db, node)
