"""Endpoint integration tests for /v1/onboarding/*."""

from __future__ import annotations

from knightwise_api.models import OnboardingAttempt, User
from knightwise_api.onboarding.seed import seed_onboarding_puzzles


def _create_user(db) -> int:
    user = User(display_name="testuser")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user.id


def test_start_initialises_defaults(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)

    r = client.post(f"/v1/onboarding/start?user_id={user_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["user_id"] == user_id
    assert body["rating_mu"] == 1500.0
    assert body["rating_sigma"] == 350.0
    assert body["attempts_so_far"] == 0
    assert body["completed_at"] is None
    assert body["min_attempts"] == 6
    assert body["max_attempts"] == 12


def test_next_returns_puzzle_near_default_estimate(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    r = client.get(f"/v1/onboarding/next?user_id={user_id}")
    assert r.status_code == 200
    body = r.json()
    assert body["done"] is False
    assert body["puzzle"] is not None
    # Default mu=1500; nearest in our seed pool is 1500 (kw-onb-007 or kw-onb-011).
    assert body["puzzle"]["rating"] == 1500


def test_next_503_when_no_puzzles_seeded(client, db_session):
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    r = client.get(f"/v1/onboarding/next?user_id={user_id}")
    assert r.status_code == 503


def test_attempt_correct_raises_estimate_and_writes_audit(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")
    nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
    puzzle = nxt["puzzle"]

    r = client.post(
        "/v1/onboarding/attempt",
        json={
            "user_id": user_id,
            "puzzle_id": puzzle["id"],
            "move_uci": "h1h8",  # well-formed UCI but wrong for any seed puzzle
            "time_ms": 1000,
        },
    )
    # Wrong attempt: response 200 with correct=False
    assert r.status_code == 200
    body = r.json()
    assert body["correct"] is False
    assert body["expected_uci"]
    assert body["state"]["attempts_so_far"] == 1

    # Audit row exists
    rows = db_session.query(OnboardingAttempt).filter_by(user_id=user_id).all()
    assert len(rows) == 1
    assert rows[0].correct is False


def test_attempt_correct_solution_marks_correct(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")
    nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
    puzzle = nxt["puzzle"]

    # Look up the real expected solution from the DB
    from knightwise_api.models import Puzzle as PuzzleModel
    expected = db_session.get(PuzzleModel, puzzle["id"]).solution_uci[0]

    r = client.post(
        "/v1/onboarding/attempt",
        json={
            "user_id": user_id,
            "puzzle_id": puzzle["id"],
            "move_uci": expected,
            "time_ms": 1000,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["correct"] is True
    assert body["state"]["rating_mu"] >= 1500.0


def test_attempt_unknown_puzzle_404(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    r = client.post(
        "/v1/onboarding/attempt",
        json={
            "user_id": user_id,
            "puzzle_id": 9_999_999,
            "move_uci": "e2e4",
            "time_ms": 1000,
        },
    )
    assert r.status_code == 404


def test_finish_stamps_completed_at_idempotent(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    r1 = client.post("/v1/onboarding/finish", json={"user_id": user_id})
    assert r1.status_code == 200
    first = r1.json()["completed_at"]
    assert first is not None

    r2 = client.post("/v1/onboarding/finish", json={"user_id": user_id})
    assert r2.json()["completed_at"] == first  # idempotent


def test_attempt_after_finish_409(client, db_session):
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")
    client.post("/v1/onboarding/finish", json={"user_id": user_id})

    nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
    assert nxt["done"] is True

    r = client.post(
        "/v1/onboarding/attempt",
        json={
            "user_id": user_id,
            "puzzle_id": 1,
            "move_uci": "e2e4",
            "time_ms": 100,
        },
    )
    assert r.status_code == 409


def test_attempt_rejects_duplicate_puzzle(client, db_session):
    """A client cannot rig their rating by re-attempting the same puzzle."""
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")
    nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
    puzzle_id = nxt["puzzle"]["id"]

    from knightwise_api.models import Puzzle as PuzzleModel
    expected = db_session.get(PuzzleModel, puzzle_id).solution_uci[0]

    # First attempt: ok.
    r1 = client.post(
        "/v1/onboarding/attempt",
        json={"user_id": user_id, "puzzle_id": puzzle_id, "move_uci": expected, "time_ms": 1},
    )
    assert r1.status_code == 200

    # Second attempt at same puzzle: rejected.
    r2 = client.post(
        "/v1/onboarding/attempt",
        json={"user_id": user_id, "puzzle_id": puzzle_id, "move_uci": expected, "time_ms": 1},
    )
    assert r2.status_code == 409


def test_attempt_rejected_after_session_done(client, db_session):
    """Server enforces MAX_ATTEMPTS even if the client ignores `done=true`."""
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    from knightwise_api.models import Puzzle as PuzzleModel
    # Solve every puzzle correctly until session is done.
    for _ in range(20):
        nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
        if nxt["done"] or nxt["puzzle"] is None:
            break
        pid = nxt["puzzle"]["id"]
        expected = db_session.get(PuzzleModel, pid).solution_uci[0]
        client.post(
            "/v1/onboarding/attempt",
            json={"user_id": user_id, "puzzle_id": pid, "move_uci": expected, "time_ms": 1},
        )

    # Pick any unseen puzzle id and try to submit anyway.
    from knightwise_api.models import OnboardingAttempt as Att
    seen = {row.puzzle_id for row in db_session.query(Att).filter_by(user_id=user_id).all()}
    all_ids = {pid for (pid,) in db_session.query(PuzzleModel.id).all()}
    unseen = next(iter(all_ids - seen))

    r = client.post(
        "/v1/onboarding/attempt",
        json={"user_id": user_id, "puzzle_id": unseen, "move_uci": "e2e4", "time_ms": 1},
    )
    assert r.status_code == 409


def test_full_session_terminates_within_max_attempts(client, db_session):
    """Solve every puzzle correctly and confirm the session finishes by
    MAX_ATTEMPTS even with all wins."""
    seed_onboarding_puzzles(db_session)
    user_id = _create_user(db_session)
    client.post(f"/v1/onboarding/start?user_id={user_id}")

    from knightwise_api.models import Puzzle as PuzzleModel
    for _ in range(20):
        nxt = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
        if nxt["done"] or nxt["puzzle"] is None:
            break
        expected = db_session.get(PuzzleModel, nxt["puzzle"]["id"]).solution_uci[0]
        client.post(
            "/v1/onboarding/attempt",
            json={
                "user_id": user_id,
                "puzzle_id": nxt["puzzle"]["id"],
                "move_uci": expected,
                "time_ms": 100,
            },
        )

    final = client.get(f"/v1/onboarding/next?user_id={user_id}").json()
    assert final["done"] is True
    assert final["state"]["attempts_so_far"] <= 12
