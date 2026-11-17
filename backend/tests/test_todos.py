from collections.abc import Callable
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

MakeTodo = Callable[..., dict[str, Any]]


def titles(response: Any) -> list[str]:
    return [t["title"] for t in response.json()["items"]]


def test_requires_login(anon: TestClient) -> None:
    assert anon.get("/api/todos").status_code == 401
    assert anon.post("/api/todos", json={"title": "x"}).status_code == 401


def test_create_uses_defaults_and_trims(client: TestClient) -> None:
    response = client.post("/api/todos", json={"title": "  Buy milk  "})
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert (body["period"], body["priority"], body["category"]) == ("daily", "medium", "misc")
    assert body["completed"] is False
    assert body["completed_at"] is None


def test_create_validation(client: TestClient) -> None:
    assert client.post("/api/todos", json={"title": ""}).status_code == 422
    assert client.post("/api/todos", json={"title": "x", "priority": "urgent"}).status_code == 422
    assert client.post("/api/todos", json={"title": "x", "due_date": "soon"}).status_code == 422


def test_get_put_delete(client: TestClient, make_todo: MakeTodo) -> None:
    todo = make_todo(title="Old")
    url = f"/api/todos/{todo['id']}"
    assert client.get(url).json()["title"] == "Old"

    updated = client.put(
        url,
        json={
            "title": "New",
            "priority": "high",
            "category": "office",
            "period": "monthly",
            "due_date": "2026-04-01",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["priority"] == "high"
    assert updated.json()["due_date"] == "2026-04-01"

    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_toggle_sets_and_clears_completed_at(client: TestClient, make_todo: MakeTodo) -> None:
    todo = make_todo()
    done = client.patch(f"/api/todos/{todo['id']}/toggle").json()
    assert done["completed"] is True
    assert done["completed_at"] is not None
    undone = client.patch(f"/api/todos/{todo['id']}/toggle").json()
    assert undone["completed"] is False
    assert undone["completed_at"] is None


def test_filters(client: TestClient, make_todo: MakeTodo) -> None:
    make_todo(title="A", period="daily", priority="high", category="home", due_date="2026-03-01")
    make_todo(title="B", period="monthly", priority="low", category="office", due_date="2026-03-20")
    c = make_todo(title="C", period="yearly", priority="medium", category="self")
    client.patch(f"/api/todos/{c['id']}/toggle")

    assert titles(client.get("/api/todos?period=monthly")) == ["B"]
    assert titles(client.get("/api/todos?priority=high")) == ["A"]
    assert titles(client.get("/api/todos?category=self")) == ["C"]
    assert titles(client.get("/api/todos?completed=true")) == ["C"]
    assert sorted(titles(client.get("/api/todos?completed=false"))) == ["A", "B"]
    assert titles(client.get("/api/todos?due_from=2026-03-10&due_to=2026-03-31")) == ["B"]
    assert client.get("/api/todos?unknown=1").status_code == 422


def test_search_is_case_insensitive(client: TestClient, make_todo: MakeTodo) -> None:
    make_todo(title="Pay Electricity")
    make_todo(title="Walk")
    assert titles(client.get("/api/todos?q=electric")) == ["Pay Electricity"]


def test_sorting(client: TestClient, make_todo: MakeTodo) -> None:
    make_todo(title="low", priority="low", due_date="2026-01-01")
    make_todo(title="high", priority="high", due_date="2026-03-01")
    make_todo(title="none", priority="medium")
    assert titles(client.get("/api/todos?sort=priority")) == ["high", "none", "low"]
    # Items without a due date go last either way.
    assert titles(client.get("/api/todos?sort=due_date")) == ["low", "high", "none"]
    assert titles(client.get("/api/todos?sort=due_date&order=desc")) == ["high", "low", "none"]


def test_pagination(client: TestClient, make_todo: MakeTodo) -> None:
    for i in range(5):
        make_todo(title=f"T{i}", due_date=f"2026-03-0{i + 1}")
    page = client.get("/api/todos?limit=2&offset=2").json()
    assert page["total"] == 5
    assert [t["title"] for t in page["items"]] == ["T2", "T3"]
    assert client.get("/api/todos?limit=0").status_code == 422
    assert client.get("/api/todos?limit=101").status_code == 422


def test_repeat_moves_to_next_period(client: TestClient, make_todo: MakeTodo) -> None:
    monthly = make_todo(title="Rent", period="monthly", due_date="2026-01-31")
    copy = client.post(f"/api/todos/{monthly['id']}/repeat")
    assert copy.status_code == 201
    assert copy.json()["due_date"] == "2026-02-28"  # clamped to month end
    assert copy.json()["completed"] is False

    yearly = make_todo(period="yearly", due_date="2028-02-29")
    assert client.post(f"/api/todos/{yearly['id']}/repeat").json()["due_date"] == "2029-02-28"


def test_repeat_without_due_date_uses_today(
    client: TestClient, make_todo: MakeTodo, today: date
) -> None:
    todo = make_todo(period="daily")
    assert client.post(f"/api/todos/{todo['id']}/repeat").json()["due_date"] == "2026-03-16"


def test_isolation_between_users(
    client: TestClient, client_b: TestClient, make_todo: MakeTodo
) -> None:
    """User B can neither see nor change user A's todos. Every attempt looks like a 404."""
    todo = make_todo(title="Alice's secret")
    url = f"/api/todos/{todo['id']}"

    assert client_b.get("/api/todos").json()["total"] == 0
    assert client_b.get(url).status_code == 404
    assert client_b.put(url, json={"title": "hacked"}).status_code == 404
    assert client_b.patch(f"{url}/toggle").status_code == 404
    assert client_b.post(f"{url}/repeat").status_code == 404
    assert client_b.delete(url).status_code == 404

    # A's todo is unchanged.
    still = client.get(url).json()
    assert still["title"] == "Alice's secret"
    assert still["completed"] is False
