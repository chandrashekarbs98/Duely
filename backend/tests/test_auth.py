from fastapi.testclient import TestClient

from app.core.security import create_access_token
from tests.conftest import PASSWORD, register


def test_register_logs_in_and_sets_httponly_cookie(anon: TestClient) -> None:
    response = anon.post(
        "/api/auth/register",
        json={"email": "New@Example.COM", "password": PASSWORD, "name": "New"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"  # stored lower case
    assert body["currency"] == "INR"
    assert "password_hash" not in body
    cookie = response.headers["set-cookie"].lower()
    assert "access_token=" in cookie
    assert "httponly" in cookie
    assert "samesite=lax" in cookie
    assert anon.get("/api/auth/me").status_code == 200


def test_register_duplicate_email_is_409(anon: TestClient) -> None:
    register(anon, "dup@example.com")
    response = anon.post(
        "/api/auth/register",
        json={"email": "DUP@example.com", "password": PASSWORD, "name": "Again"},
    )
    assert response.status_code == 409


def test_register_validates_input(anon: TestClient) -> None:
    short = anon.post(
        "/api/auth/register", json={"email": "a@example.com", "password": "short", "name": "A"}
    )
    bad_email = anon.post(
        "/api/auth/register", json={"email": "nope", "password": PASSWORD, "name": "A"}
    )
    too_long = anon.post(
        "/api/auth/register", json={"email": "a@example.com", "password": "é" * 40, "name": "A"}
    )
    extra = anon.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": PASSWORD, "name": "A", "is_admin": True},
    )
    assert short.status_code == 422
    assert bad_email.status_code == 422
    assert too_long.status_code == 422  # 80 bytes > bcrypt's 72-byte limit
    assert extra.status_code == 422  # unknown fields are rejected


def test_login_logout_cycle(anon: TestClient) -> None:
    register(anon, "cycle@example.com")
    anon.post("/api/auth/logout")
    assert anon.get("/api/auth/me").status_code == 401

    response = anon.post(
        "/api/auth/login", json={"email": "Cycle@Example.com", "password": PASSWORD}
    )
    assert response.status_code == 200
    assert anon.get("/api/auth/me").json()["email"] == "cycle@example.com"


def test_login_errors_do_not_reveal_which_part_was_wrong(anon: TestClient) -> None:
    register(anon, "real@example.com")
    wrong_password = anon.post(
        "/api/auth/login", json={"email": "real@example.com", "password": "wrong-password"}
    )
    unknown_email = anon.post(
        "/api/auth/login", json={"email": "ghost@example.com", "password": PASSWORD}
    )
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_login_is_rate_limited_after_five_failures(anon: TestClient) -> None:
    register(anon, "target@example.com")
    for _ in range(5):
        bad = {"email": "target@example.com", "password": "wrong-password"}
        assert anon.post("/api/auth/login", json=bad).status_code == 401
    good = anon.post("/api/auth/login", json={"email": "target@example.com", "password": PASSWORD})
    assert good.status_code == 429


def test_me_requires_a_valid_token(anon: TestClient) -> None:
    assert anon.get("/api/auth/me").status_code == 401
    anon.cookies.set("access_token", "not-a-jwt")
    assert anon.get("/api/auth/me").status_code == 401


def test_token_for_deleted_or_unknown_user_is_rejected(anon: TestClient) -> None:
    anon.cookies.set("access_token", create_access_token(999_999))
    assert anon.get("/api/auth/me").status_code == 401


def test_update_profile_patch_semantics(client: TestClient) -> None:
    response = client.patch(
        "/api/auth/me", json={"monthly_budget": "25000.50", "email_reminders": True}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["monthly_budget"] == "25000.50"
    assert body["email_reminders"] is True
    assert body["name"] == "Alice"  # untouched

    cleared = client.patch("/api/auth/me", json={"monthly_budget": None}).json()
    assert cleared["monthly_budget"] is None
    assert cleared["email_reminders"] is True

    assert client.patch("/api/auth/me", json={"monthly_budget": "-5"}).status_code == 422
    assert client.patch("/api/auth/me", json={"name": ""}).status_code == 422


def test_delete_account_removes_user_and_data(client: TestClient) -> None:
    client.post("/api/todos", json={"title": "Mine"})
    assert client.delete("/api/auth/me").status_code == 204
    assert client.get("/api/auth/me").status_code == 401
    relogin = client.post(
        "/api/auth/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    assert relogin.status_code == 401
