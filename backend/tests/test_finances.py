import csv
import io
from collections.abc import Callable
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

MakeEntry = Callable[..., dict[str, Any]]


def titles(response: Any) -> list[str]:
    return [e["title"] for e in response.json()["items"]]


def test_requires_login(anon: TestClient) -> None:
    assert anon.get("/api/finances").status_code == 401
    assert anon.get("/api/finances/stats").status_code == 401
    assert anon.get("/api/finances/export.csv").status_code == 401


def test_amount_round_trips_exactly(client: TestClient, make_entry: MakeEntry) -> None:
    entry = make_entry(amount="199.99")
    assert entry["amount"] == "199.99"  # a string: no float anywhere
    assert client.get(f"/api/finances/{entry['id']}").json()["amount"] == "199.99"
    big = make_entry(amount="9999999999.99")
    assert big["amount"] == "9999999999.99"


def test_amount_validation(client: TestClient) -> None:
    base = {"title": "x", "entry_date": "2026-03-01"}
    assert client.post("/api/finances", json={**base, "amount": "10.999"}).status_code == 422
    assert client.post("/api/finances", json={**base, "amount": "0"}).status_code == 422
    assert client.post("/api/finances", json={**base, "amount": "-5"}).status_code == 422
    too_big = {**base, "amount": "99999999999.00"}
    assert client.post("/api/finances", json=too_big).status_code == 422
    assert client.post("/api/finances", json={"title": "x", "amount": "1"}).status_code == 422


def test_defaults(make_entry: MakeEntry) -> None:
    entry = make_entry()
    assert (entry["kind"], entry["status"], entry["period"]) == ("expense", "paid", "daily")


def test_update_pay_delete(client: TestClient, make_entry: MakeEntry) -> None:
    entry = make_entry(status="planned")
    url = f"/api/finances/{entry['id']}"
    updated = client.put(
        url,
        json={
            "title": "Rent",
            "amount": "22000.00",
            "entry_date": "2026-03-05",
            "status": "planned",
            "category": "home",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "22000.00"
    assert client.patch(f"{url}/pay").json()["status"] == "paid"
    assert client.delete(url).status_code == 204
    assert client.get(url).status_code == 404


def test_filters_and_sort(client: TestClient, make_entry: MakeEntry) -> None:
    make_entry(title="Salary", kind="income", amount="5000.00", entry_date="2026-03-01")
    make_entry(title="Rent", amount="2000.00", entry_date="2026-03-02", status="planned")
    make_entry(title="Coffee", amount="3.50", entry_date="2026-02-15", category="self")

    assert titles(client.get("/api/finances?kind=income")) == ["Salary"]
    assert titles(client.get("/api/finances?status=planned")) == ["Rent"]
    assert titles(client.get("/api/finances?category=self")) == ["Coffee"]
    assert titles(client.get("/api/finances?date_from=2026-03-01&date_to=2026-03-01")) == ["Salary"]
    assert titles(client.get("/api/finances?q=COF")) == ["Coffee"]
    # Default order: newest first.
    assert titles(client.get("/api/finances")) == ["Rent", "Salary", "Coffee"]
    assert titles(client.get("/api/finances?sort=amount&order=asc")) == ["Coffee", "Rent", "Salary"]
    assert client.get("/api/finances?limit=1").json()["total"] == 3


def test_repeat_creates_planned_copy_next_period(client: TestClient, make_entry: MakeEntry) -> None:
    sub = make_entry(title="Netflix", period="monthly", entry_date="2026-01-31", amount="649.00")
    copy = client.post(f"/api/finances/{sub['id']}/repeat")
    assert copy.status_code == 201
    body = copy.json()
    assert body["entry_date"] == "2026-02-28"
    assert body["status"] == "planned"
    assert body["amount"] == "649.00"


def test_stats_counts_only_paid_and_is_exact(
    client: TestClient, make_entry: MakeEntry, today: date
) -> None:
    # Classic float trap: 0.1 + 0.2 must be exactly 0.30.
    make_entry(amount="0.10", entry_date="2026-01-05", category="home")
    make_entry(amount="0.20", entry_date="2026-01-06", category="home")
    make_entry(amount="1000.00", kind="income", entry_date="2026-02-01", category="office")
    make_entry(amount="500.00", entry_date="2026-02-02", status="planned")  # ignored

    stats = client.get("/api/finances/stats?date_from=2026-01-01&date_to=2026-03-31").json()
    assert stats["total_expense"] == "0.30"
    assert stats["total_income"] == "1000.00"
    assert stats["net"] == "999.70"
    assert stats["currency"] == "INR"

    by_cat = {c["category"]: c for c in stats["by_category"]}
    assert set(by_cat) == {"home", "office", "self", "misc"}  # zeros included
    assert by_cat["home"]["expense"] == "0.30"
    assert by_cat["misc"]["expense"] == "0.00"

    assert [m["month"] for m in stats["by_month"]] == ["2026-01", "2026-02", "2026-03"]
    assert stats["by_month"][0]["expense"] == "0.30"
    assert stats["by_month"][1]["net"] == "1000.00"
    assert stats["by_month"][2]["income"] == "0.00"


def test_stats_defaults_to_current_year(client: TestClient, today: date) -> None:
    stats = client.get("/api/finances/stats").json()
    assert stats["date_from"] == "2026-01-01"
    assert stats["date_to"] == "2026-12-31"
    assert len(stats["by_month"]) == 12


def test_stats_rejects_bad_ranges(client: TestClient) -> None:
    backwards = client.get("/api/finances/stats?date_from=2026-05-01&date_to=2026-01-01")
    huge = client.get("/api/finances/stats?date_from=1900-01-01&date_to=2026-01-01")
    assert backwards.status_code == 422
    assert huge.status_code == 422


def test_csv_export(client: TestClient, make_entry: MakeEntry) -> None:
    make_entry(title='=HYPERLINK("http://evil")', amount="10.50", kind="expense")
    make_entry(title="Salary", kind="income", amount="100.00")

    response = client.get("/api/finances/export.csv?kind=expense")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]

    rows = list(csv.reader(io.StringIO(response.text)))
    assert rows[0][:4] == ["date", "title", "kind", "amount"]
    assert len(rows) == 2  # header + the one expense
    assert rows[1][1].startswith("'=")  # formula neutralised
    assert rows[1][3] == "10.50"


def test_isolation_between_users(
    client: TestClient, client_b: TestClient, make_entry: MakeEntry
) -> None:
    entry = make_entry(title="Alice salary", kind="income", amount="999.00")
    url = f"/api/finances/{entry['id']}"
    body = {"title": "hacked", "amount": "1.00", "entry_date": "2026-03-01"}

    assert client_b.get("/api/finances").json()["total"] == 0
    assert client_b.get(url).status_code == 404
    assert client_b.put(url, json=body).status_code == 404
    assert client_b.patch(f"{url}/pay").status_code == 404
    assert client_b.post(f"{url}/repeat").status_code == 404
    assert client_b.delete(url).status_code == 404

    stats_b = client_b.get("/api/finances/stats?date_from=2026-01-01&date_to=2026-12-31").json()
    assert stats_b["total_income"] == "0.00"
    export_b = client_b.get("/api/finances/export.csv").text
    assert "Alice salary" not in export_b

    assert client.get(url).json()["title"] == "Alice salary"
