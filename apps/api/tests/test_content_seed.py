from knightwise_api.content import seed_nodes_and_puzzles
from knightwise_api.models import Node, NodeEdge, NodePuzzle, Puzzle


def test_seed_loads_all_ten_nodes(db_session):
    report = seed_nodes_and_puzzles(db_session)
    assert report.nodes_inserted == 10
    assert report.puzzles_inserted >= 10
    assert report.edges_inserted >= 1

    nodes = db_session.query(Node).all()
    assert len(nodes) == 10
    slugs = {n.slug for n in nodes}
    assert {"back-rank-basics", "opposition-basics", "kr-vs-k-technique"} <= slugs


def test_seed_is_idempotent(db_session):
    seed_nodes_and_puzzles(db_session)
    again = seed_nodes_and_puzzles(db_session)
    assert again.nodes_inserted == 0
    assert again.nodes_updated == 10
    assert db_session.query(Node).count() == 10


def test_seed_creates_node_puzzle_links(db_session):
    seed_nodes_and_puzzles(db_session)
    back_rank = db_session.query(Node).filter_by(slug="back-rank-basics").one()
    links = db_session.query(NodePuzzle).filter_by(node_id=back_rank.id).all()
    assert len(links) >= 2
    puzzle_ids = [link.puzzle_id for link in links]
    puzzles = db_session.query(Puzzle).filter(Puzzle.id.in_(puzzle_ids)).all()
    assert any("back-rank" in (p.themes or []) for p in puzzles)


def test_seed_creates_prereq_edges(db_session):
    seed_nodes_and_puzzles(db_session)
    edges = db_session.query(NodeEdge).filter_by(edge_type="prereq").all()
    assert len(edges) >= 1
