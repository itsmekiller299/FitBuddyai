import os
from pathlib import Path

os.environ["DEMO_MODE"] = "true"
os.environ["DATABASE_URL"] = "sqlite:///./data/test_fitbuddy.db"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "secret"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_generate_and_feedback():
    response = client.post("/generate-workout", data={
        "name": "Test User",
        "user_id": "TEST001",
        "age": "21",
        "weight": "65",
        "goal": "general wellness",
        "intensity": "medium",
    })
    assert response.status_code == 200
    assert "Day 1" in response.text

    response = client.post("/submit-feedback", data={
        "user_id": "TEST001",
        "feedback": "Add more mobility and keep the cardio light.",
    })
    assert response.status_code == 200
    assert "updated" in response.text.lower()


def test_api_user():
    response = client.get("/api/users/TEST001")
    assert response.status_code == 200
    assert response.json()["user_id"] == "TEST001"


def test_admin_auth():
    response = client.get("/view-all-users")
    assert response.status_code == 401
    response = client.get("/view-all-users", auth=("admin", "secret"))
    assert response.status_code == 200
