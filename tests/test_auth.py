"""Auth flow: register, duplicate, login, bad credentials, protected route."""


def test_register_and_me(client, auth_headers):
    resp = client.get("/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "test@example.com"


def test_register_duplicate_email(client, auth_headers):
    resp = client.post(
        "/auth/register", json={"email": "test@example.com", "password": "secret123"}
    )
    assert resp.status_code == 400


def test_login_wrong_password(client):
    resp = client.post(
        "/auth/login", data={"username": "test@example.com", "password": "wrongpass"}
    )
    assert resp.status_code == 401


def test_protected_route_without_token(client):
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_register_short_password_rejected(client):
    resp = client.post("/auth/register", json={"email": "x@y.com", "password": "short"})
    assert resp.status_code == 422
