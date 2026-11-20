"""App-wide protections: request size limit and security headers."""

import base64
import hashlib
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import create_app


def test_oversized_body_is_refused_before_parsing(client: TestClient) -> None:
    huge = {"title": "x" * 70_000}  # over the 64 KB cap
    response = client.post("/api/todos", json=huge)
    assert response.status_code == 413
    assert response.json() == {"detail": "Request body too large."}
    assert client.get("/api/todos").json()["total"] == 0


def test_chunked_body_without_length_is_refused(client: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        yield b'{"title": '
        yield b'"sneaky"}'

    response = client.post(
        "/api/todos", content=chunks(), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 411


def test_normal_requests_still_work(client: TestClient) -> None:
    assert client.post("/api/todos", json={"title": "x" * 200}).status_code == 201


def test_basic_security_headers_on_every_response(anon: TestClient) -> None:
    response = anon.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    # Development: no HTTPS-only rule, and the API docs are available.
    assert "strict-transport-security" not in response.headers
    assert anon.get("/docs").status_code == 200


INDEX_HTML = """<!doctype html><html><head>
<script>document.documentElement.dataset.theme = "dark";</script>
<script type="module" src="/assets/index.js"></script>
</head><body><div id="root"></div></body></html>"""


@pytest.fixture
def production_app(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[TestClient]:
    """The app as Render runs it: production mode, serving a built frontend."""
    (tmp_path / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    settings = get_settings()
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "static_dir", str(tmp_path))
    with TestClient(create_app()) as c:
        yield c


def test_production_sends_hsts_and_csp(production_app: TestClient) -> None:
    response = production_app.get("/dashboard")
    assert response.status_code == 200
    assert response.headers["strict-transport-security"].startswith("max-age=31536000")

    csp = response.headers["content-security-policy"]
    inline = 'document.documentElement.dataset.theme = "dark";'
    digest = base64.b64encode(hashlib.sha256(inline.encode()).digest()).decode()
    # Exactly our one inline script, by hash (the <script src=...> tag is not hashed).
    assert f"script-src 'self' 'sha256-{digest}';" in csp
    assert csp.count("sha256-") == 1
    assert "'unsafe-inline'" not in csp.split("script-src")[1].split(";")[0]
    assert "frame-ancestors 'none'" in csp


def test_production_hides_api_docs(production_app: TestClient) -> None:
    for path in ("/openapi.json", "/redoc"):
        response = production_app.get(path)
        # Falls through to the React app (index.html), not the API schema.
        assert "Personal Tracker API" not in response.text
    assert "swagger" not in production_app.get("/docs").text.lower()
