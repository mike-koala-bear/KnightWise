from fastapi.testclient import TestClient


def test_healthz(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_openapi_mounts_analyze(client: TestClient) -> None:
    r = client.get("/openapi.json")
    assert r.status_code == 200
    paths = r.json()["paths"]
    assert "/v1/analyze" in paths
