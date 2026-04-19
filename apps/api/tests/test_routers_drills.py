from knightwise_api.content import seed_nodes_and_puzzles


def test_list_nodes(client, db_session):
    seed_nodes_and_puzzles(db_session)
    r = client.get("/v1/nodes")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 10
    slugs = {n["slug"] for n in body}
    assert "back-rank-basics" in slugs


def test_get_node_404(client):
    r = client.get("/v1/nodes/does-not-exist")
    assert r.status_code == 404


def test_next_drill_auto_creates_user(client, db_session):
    seed_nodes_and_puzzles(db_session)
    r = client.get("/v1/drills/next?node_slug=back-rank-basics")
    assert r.status_code == 200
    body = r.json()
    assert body["node"]["slug"] == "back-rank-basics"
    assert body["puzzle"] is not None
    assert body["puzzle"]["fen"]


def test_next_drill_unknown_node(client, db_session):
    seed_nodes_and_puzzles(db_session)
    r = client.get("/v1/drills/next?node_slug=does-not-exist")
    assert r.status_code == 404


def test_attempt_full_flow(client, db_session):
    seed_nodes_and_puzzles(db_session)
    # Auto-create user via /drills/next first
    client.get("/v1/drills/next?node_slug=back-rank-basics")
    next_drill = client.get("/v1/drills/next?node_slug=back-rank-basics").json()
    puzzle_id = next_drill["puzzle"]["id"]

    r = client.post(
        "/v1/drills/attempt",
        json={
            "user_id": 1,
            "puzzle_id": puzzle_id,
            "correct": True,
            "time_ms": 4500,
            "hints_used": 0,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["repetitions"] == 1
    assert body["interval_days"] == 1


def test_attempt_unknown_puzzle_returns_404(client, db_session):
    seed_nodes_and_puzzles(db_session)
    client.get("/v1/drills/next?node_slug=back-rank-basics")
    r = client.post(
        "/v1/drills/attempt",
        json={
            "user_id": 1,
            "puzzle_id": 999_999,
            "correct": True,
            "time_ms": 1000,
            "hints_used": 0,
        },
    )
    assert r.status_code == 404
    assert "puzzle not found" in r.json()["detail"]
