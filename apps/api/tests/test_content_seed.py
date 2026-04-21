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


def test_seed_updates_node_puzzle_position_on_reseed(db_session, tmp_path):
    """Regression: position was frozen at first-seed value on re-seed."""
    import json

    seed_a = {
        "nodes": [
            {"slug": "n1", "domain": "tactics", "title": "N1"},
        ],
        "puzzles": [
            {
                "external_id": "p-a", "fen": "8/8/8/8/8/8/8/4K2k w - - 0 1",
                "solution_uci": ["e1f1"], "themes": [], "rating": 1000,
                "source": "t", "nodes": ["n1"],
            },
            {
                "external_id": "p-b", "fen": "8/8/8/8/8/8/8/4K2k w - - 0 1",
                "solution_uci": ["e1f1"], "themes": [], "rating": 1000,
                "source": "t", "nodes": ["n1"],
            },
        ],
    }
    seed_b = {
        "nodes": seed_a["nodes"],
        # swap order -> positions should flip
        "puzzles": [seed_a["puzzles"][1], seed_a["puzzles"][0]],
    }
    # initial positions: p-a=0, p-b=1
    path_a = tmp_path / "a.json"
    path_a.write_text(json.dumps(seed_a))
    seed_nodes_and_puzzles(db_session, seed_path=path_a)

    node = db_session.query(Node).filter_by(slug="n1").one()
    links = {
        db_session.query(Puzzle).get(link.puzzle_id).external_id: link.position
        for link in db_session.query(NodePuzzle).filter_by(node_id=node.id).all()
    }
    assert links == {"p-a": 0, "p-b": 1}

    # re-seed with swapped order -> positions must update
    path_b = tmp_path / "b.json"
    path_b.write_text(json.dumps(seed_b))
    seed_nodes_and_puzzles(db_session, seed_path=path_b)

    links = {
        db_session.query(Puzzle).get(link.puzzle_id).external_id: link.position
        for link in db_session.query(NodePuzzle).filter_by(node_id=node.id).all()
    }
    assert links == {"p-b": 0, "p-a": 1}
