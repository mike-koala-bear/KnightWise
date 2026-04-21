from datetime import UTC, datetime
from unittest.mock import patch

from knightwise_api.ingest.service import IngestReport
from knightwise_api.ingest.types import IngestedGame
from knightwise_api.models import User
from knightwise_api.sync import JOB_REGISTRY, run_sync


def _make_user(session_factory, lichess="mike-bear", chesscom="mike-bear"):
    with session_factory() as db:
        user = User(display_name="mb", lichess_username=lichess, chesscom_username=chesscom)
        db.add(user)
        db.commit()
        return user.id


def test_start_sync_404_when_user_missing(client):
    r = client.post("/v1/sync", json={"user_id": 9999, "max_games": 5})
    assert r.status_code == 404


def test_start_sync_400_when_no_handles(client, session_factory):
    with session_factory() as db:
        u = User(display_name="no-handles")
        db.add(u)
        db.commit()
        uid = u.id
    r = client.post("/v1/sync", json={"user_id": uid})
    assert r.status_code == 400


def test_sync_status_404_for_unknown_job(client):
    r = client.get("/v1/sync/status/does-not-exist")
    assert r.status_code == 404


def test_start_sync_returns_job_id_and_is_trackable(client, session_factory):
    uid = _make_user(session_factory)
    with (
        patch("knightwise_api.sync.jobs.fetch_lichess_games", return_value=[]),
        patch("knightwise_api.sync.jobs.fetch_chesscom_games", return_value=[]),
    ):
        r = client.post(
            "/v1/sync",
            json={"user_id": uid, "max_games": 5, "analyze": False},
        )
    assert r.status_code == 200
    body = r.json()
    assert "job_id" in body
    job_id = body["job_id"]

    status = client.get(f"/v1/sync/status/{job_id}").json()
    assert status["status"] in {"pending", "running", "done"}


def test_run_sync_happy_path(session_factory, monkeypatch):
    """Drives run_sync synchronously so we can assert on job counters."""
    uid = _make_user(session_factory)

    fake_game = IngestedGame(
        source="lichess",
        external_id="FAKE1",
        time_control="180+2",
        played_as="white",
        opponent_name="opp",
        opponent_rating=1500,
        user_rating=1500,
        result="win",
        pgn='[Event "test"]\n1. e4 e5 1-0',
        started_at=datetime.now(UTC),
    )

    monkeypatch.setattr(
        "knightwise_api.sync.jobs.fetch_lichess_games",
        lambda username, max_games: [fake_game],
    )
    monkeypatch.setattr(
        "knightwise_api.sync.jobs.fetch_chesscom_games",
        lambda username, max_games: [],
    )
    monkeypatch.setattr(
        "knightwise_api.sync.jobs.SessionLocal",
        session_factory,
    )

    # Stub out engine analysis so we don't need Stockfish in CI.
    def _stub_analyze(db, game_id, depth=14):
        return None

    monkeypatch.setattr("knightwise_api.sync.jobs.analyze_and_store", _stub_analyze)

    job = JOB_REGISTRY.create(
        user_id=uid,
        lichess_username="mike-bear",
        chesscom_username="mike-bear",
        max_games=5,
        analyze=True,
        depth=14,
    )
    run_sync(job.job_id)

    finished = JOB_REGISTRY.get(job.job_id)
    assert finished is not None
    assert finished.status == "done"
    assert finished.lichess_fetched == 1
    assert finished.lichess_inserted == 1
    assert finished.chesscom_fetched == 0
    assert finished.total_games_to_analyze == 1
    assert finished.games_analyzed == 1
    assert finished.games_failed == 0


def test_run_sync_error_is_captured_per_provider(session_factory, monkeypatch):
    """A lichess failure should not prevent chess.com from running, and job finishes 'done'."""
    uid = _make_user(session_factory)

    def _boom(*a, **kw):
        raise RuntimeError("lichess down")

    monkeypatch.setattr("knightwise_api.sync.jobs.fetch_lichess_games", _boom)
    monkeypatch.setattr("knightwise_api.sync.jobs.fetch_chesscom_games", lambda *a, **kw: [])
    monkeypatch.setattr("knightwise_api.sync.jobs.SessionLocal", session_factory)

    job = JOB_REGISTRY.create(
        user_id=uid,
        lichess_username="mike-bear",
        chesscom_username="mike-bear",
        max_games=5,
        analyze=False,
        depth=14,
    )
    run_sync(job.job_id)

    finished = JOB_REGISTRY.get(job.job_id)
    assert finished is not None
    assert finished.status == "done"
    assert finished.lichess_inserted == 0
    assert finished.chesscom_inserted == 0
    assert "Lichess failed" in finished.message or finished.message == "complete"


def test_ingest_report_shape_sanity():
    # Guard against signature drift of IngestReport since run_sync depends on .game_ids
    r = IngestReport()
    assert hasattr(r, "game_ids")
    assert r.inserted == 0
