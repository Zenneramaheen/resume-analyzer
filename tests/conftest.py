"""Test setup: isolated SQLite DB, TestClient, auth helper fixture."""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def _database():
    if os.path.exists("test.db"):
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)
    yield
    if os.path.exists("test.db"):
        os.remove("test.db")


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers(client):
    email = "test@example.com"
    client.post("/auth/register", json={"email": email, "password": "secret123"})
    resp = client.post("/auth/login", data={"username": email, "password": "secret123"})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


SAMPLE_RESUME_TEXT = """Zennera Maheen
zennera.maheen321@gmail.com | +91 98765 43210

Experience
Software Engineering Intern — Built a REST API with Python and FastAPI.
Deployed services with Docker and automated tests.

Education
B.E. Computer Science, 2024–2028

Skills
Python, JavaScript, SQL, Git, Docker, API design, testing

Projects
Recall — Incident Memory Copilot. Developed full-stack app, shipped MVP.
"""
