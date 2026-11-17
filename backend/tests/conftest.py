"""Test setup.

- Tests run against a separate Postgres database (TEST_DATABASE_URL), never the dev one.
- The schema is built with Alembic migrations, exactly like production. No create_all.
- Each test runs inside a transaction that is rolled back afterwards, so tests never see
  each other's data.
"""

from collections.abc import Callable, Iterator
from datetime import date
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.core import clock
from app.core.config import get_settings
from app.core.db import get_db
from app.core.email import Email, get_email_sender
from app.core.rate_limit import login_limiter
from app.main import app

PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    settings = get_settings()
    url = settings.test_database_url
    if not url:
        pytest.exit("TEST_DATABASE_URL is not set.", returncode=1)
    if url == settings.database_url:
        pytest.exit("TEST_DATABASE_URL must differ from DATABASE_URL.", returncode=1)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(alembic_cfg, "head")

    engine = create_engine(url)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine: Engine) -> Iterator[Session]:
    connection = test_engine.connect()
    transaction = connection.begin()
    # Commits inside app code become savepoints, so the outer rollback undoes everything.
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


class FakeSender:
    """Collects emails instead of sending them."""

    def __init__(self) -> None:
        self.sent: list[Email] = []
        self.fail = False

    def send(self, email: Email) -> None:
        if self.fail:
            from app.core.errors import ServiceUnavailableError

            raise ServiceUnavailableError("down")
        self.sent.append(email)


@pytest.fixture
def outbox() -> FakeSender:
    return FakeSender()


@pytest.fixture(autouse=True)
def _overrides(db: Session, outbox: FakeSender) -> Iterator[None]:
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_email_sender] = lambda: outbox
    login_limiter.clear()
    yield
    app.dependency_overrides.clear()
    login_limiter.clear()


@pytest.fixture
def anon() -> Iterator[TestClient]:
    """A client with no one logged in."""
    with TestClient(app) as c:
        yield c


def register(c: TestClient, email: str, name: str = "Tester") -> dict[str, Any]:
    response = c.post(
        "/api/auth/register", json={"email": email, "password": PASSWORD, "name": name}
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Logged in as user A (the cookie lives in this client's cookie jar)."""
    with TestClient(app) as c:
        register(c, "alice@example.com", "Alice")
        yield c


@pytest.fixture
def client_b() -> Iterator[TestClient]:
    """Logged in as user B, for isolation tests."""
    with TestClient(app) as c:
        register(c, "bob@example.com", "Bob")
        yield c


@pytest.fixture
def today(monkeypatch: pytest.MonkeyPatch) -> date:
    """Freeze "today" so date-based rules are deterministic."""
    fixed = date(2026, 3, 15)
    monkeypatch.setattr(clock, "today", lambda: fixed)
    return fixed


@pytest.fixture
def make_todo(client: TestClient) -> Callable[..., dict[str, Any]]:
    def _make(**fields: Any) -> dict[str, Any]:
        body = {"title": "Task", **fields}
        response = client.post("/api/todos", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make


@pytest.fixture
def make_entry(client: TestClient) -> Callable[..., dict[str, Any]]:
    def _make(**fields: Any) -> dict[str, Any]:
        body = {"title": "Entry", "amount": "100.00", "entry_date": "2026-03-10", **fields}
        response = client.post("/api/finances", json=body)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
