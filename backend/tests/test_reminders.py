from collections.abc import Callable
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from tests.conftest import FakeSender

Make = Callable[..., dict[str, Any]]
RUN = "/api/internal/reminders/run"


@pytest.fixture
def cron_secret(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setattr(get_settings(), "cron_secret", "test-cron-secret")
    return "test-cron-secret"


def test_requires_login(anon: TestClient) -> None:
    assert anon.get("/api/reminders").status_code == 401
    assert anon.post("/api/reminders/test-email").status_code == 401


def test_lists_are_split_by_day(
    client: TestClient, make_todo: Make, make_entry: Make, today: date
) -> None:
    make_todo(title="late", due_date="2026-03-14")
    make_todo(title="now", due_date="2026-03-15")
    make_todo(title="soon", due_date="2026-03-22")
    make_todo(title="later", due_date="2026-03-23")
    make_entry(title="late bill", status="planned", entry_date="2026-03-01")
    make_entry(title="bill today", status="planned", entry_date="2026-03-15")
    make_entry(title="bill soon", status="planned", entry_date="2026-03-18")

    r = client.get("/api/reminders").json()
    assert [t["title"] for t in r["overdue_todos"]] == ["late"]
    assert [t["title"] for t in r["due_today_todos"]] == ["now"]
    assert [t["title"] for t in r["upcoming_todos"]] == ["soon"]
    assert [p["title"] for p in r["overdue_payments"]] == ["late bill"]
    assert [p["title"] for p in r["due_today_payments"]] == ["bill today"]
    assert [p["title"] for p in r["upcoming_payments"]] == ["bill soon"]


def test_test_email_goes_to_current_user_and_escapes_html(
    client: TestClient, make_todo: Make, outbox: FakeSender, today: date
) -> None:
    make_todo(title="<script>alert(1)</script>", due_date="2026-03-15")
    response = client.post("/api/reminders/test-email")
    assert response.status_code == 200
    assert response.json() == {"sent_to": "alice@example.com"}

    (email,) = outbox.sent
    assert email.to_address == "alice@example.com"
    assert "<script>" not in email.html
    assert "&lt;script&gt;" in email.html
    assert "To-dos due today" in email.text


def test_run_is_hidden_when_no_secret_configured(
    anon: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(get_settings(), "cron_secret", None)
    assert anon.post(RUN, headers={"X-Cron-Secret": "anything"}).status_code == 404


def test_run_rejects_wrong_secret(anon: TestClient, cron_secret: str) -> None:
    assert anon.post(RUN).status_code == 401
    assert anon.post(RUN, headers={"X-Cron-Secret": "guess"}).status_code == 401


def test_run_emails_opted_in_users_once_per_day(
    client: TestClient,
    client_b: TestClient,
    make_todo: Make,
    outbox: FakeSender,
    cron_secret: str,
    today: date,
) -> None:
    client.patch("/api/auth/me", json={"email_reminders": True})
    make_todo(title="due", due_date="2026-03-15")
    client_b.post("/api/todos", json={"title": "B's task", "due_date": "2026-03-15"})
    # B has something due but did not opt in.

    headers = {"X-Cron-Secret": cron_secret}
    first = client.post(RUN, headers=headers).json()
    assert first == {"users_checked": 1, "emails_sent": 1}
    assert [e.to_address for e in outbox.sent] == ["alice@example.com"]

    second = client.post(RUN, headers=headers).json()  # e.g. the scheduler retried
    assert second == {"users_checked": 0, "emails_sent": 0}
    assert len(outbox.sent) == 1


def test_run_skips_users_with_nothing_due(
    client: TestClient, outbox: FakeSender, cron_secret: str, today: date
) -> None:
    client.patch("/api/auth/me", json={"email_reminders": True})
    result = client.post(RUN, headers={"X-Cron-Secret": cron_secret}).json()
    assert result == {"users_checked": 1, "emails_sent": 0}
    assert outbox.sent == []


def test_failed_send_is_retried_next_run(
    client: TestClient, make_todo: Make, outbox: FakeSender, cron_secret: str, today: date
) -> None:
    client.patch("/api/auth/me", json={"email_reminders": True})
    make_todo(due_date="2026-03-15")
    headers = {"X-Cron-Secret": cron_secret}

    outbox.fail = True
    assert client.post(RUN, headers=headers).json()["emails_sent"] == 0
    outbox.fail = False
    assert client.post(RUN, headers=headers).json()["emails_sent"] == 1


def test_isolation(client: TestClient, client_b: TestClient, make_todo: Make, today: date) -> None:
    make_todo(title="A's", due_date="2026-03-15")
    r = client_b.get("/api/reminders").json()
    assert r["due_today_todos"] == []
