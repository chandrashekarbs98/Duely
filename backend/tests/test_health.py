from fastapi.testclient import TestClient


def test_health_reports_ok_and_database(anon: TestClient) -> None:
    response = anon.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_security_headers_present(anon: TestClient) -> None:
    response = anon.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_unknown_api_path_is_json_404(anon: TestClient) -> None:
    response = anon.get("/api/does-not-exist")
    assert response.status_code == 404
    assert "detail" in response.json()
