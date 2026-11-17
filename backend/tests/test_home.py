from collections.abc import Callable
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

Make = Callable[..., dict[str, Any]]


def test_requires_login(anon: TestClient) -> None:
    assert anon.get("/api/home").status_code == 401


def test_urgent_todos_rule(client: TestClient, make_todo: Make, today: date) -> None:
    # today = 2026-03-15
    make_todo(title="overdue low", priority="low", due_date="2026-03-10")
    make_todo(title="today medium", priority="medium", due_date="2026-03-15")
    make_todo(title="high no date", priority="high")
    make_todo(title="future low", priority="low", due_date="2026-03-20")  # not urgent
    done = make_todo(title="done overdue", priority="high", due_date="2026-03-01")
    client.patch(f"/api/todos/{done['id']}/toggle")  # completed: not urgent

    home = client.get("/api/home").json()
    assert home["today"] == "2026-03-15"
    assert [t["title"] for t in home["urgent_todos"]] == [
        "overdue low",
        "today medium",
        "high no date",
    ]
    assert home["counts"]["open_todos"] == 4
    assert home["counts"]["overdue_todos"] == 1


def test_month_summary_and_budget(client: TestClient, make_entry: Make, today: date) -> None:
    client.patch("/api/auth/me", json={"monthly_budget": "1000.00"})
    make_entry(amount="250.25", entry_date="2026-03-02")
    make_entry(amount="99.75", entry_date="2026-03-14")
    make_entry(amount="5000.00", kind="income", entry_date="2026-03-01")
    make_entry(amount="777.00", entry_date="2026-02-28")  # last month
    make_entry(amount="888.00", entry_date="2026-03-20", status="planned")  # not paid

    month = client.get("/api/home").json()["month"]
    assert month["month"] == "2026-03"
    assert month["expense"] == "350.00"
    assert month["income"] == "5000.00"
    assert month["net"] == "4650.00"
    assert month["budget"] == "1000.00"
    assert month["budget_remaining"] == "650.00"
    assert month["budget_used_percent"] == 35


def test_no_budget_means_nulls(client: TestClient, today: date) -> None:
    month = client.get("/api/home").json()["month"]
    assert month["budget"] is None
    assert month["budget_used_percent"] is None
    assert month["expense"] == "0.00"


def test_upcoming_payments_next_7_days(client: TestClient, make_entry: Make, today: date) -> None:
    make_entry(title="today", status="planned", entry_date="2026-03-15")
    make_entry(title="in a week", status="planned", entry_date="2026-03-22")
    make_entry(title="too far", status="planned", entry_date="2026-03-23")
    make_entry(title="already paid", status="paid", entry_date="2026-03-16")
    make_entry(title="income", kind="income", status="planned", entry_date="2026-03-16")

    upcoming = client.get("/api/home").json()["upcoming_payments"]
    assert [p["title"] for p in upcoming] == ["today", "in a week"]


def test_isolation(client: TestClient, client_b: TestClient, make_todo: Make, today: date) -> None:
    make_todo(title="A urgent", priority="high")
    home_b = client_b.get("/api/home").json()
    assert home_b["urgent_todos"] == []
    assert home_b["counts"]["open_todos"] == 0
