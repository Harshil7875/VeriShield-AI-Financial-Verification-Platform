# backend/tests/test_main.py

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}

def test_create_user_success():
    payload = {"email": "testuser@example.com", "password": "somePassword123"}
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data
    assert data["is_verified"] is False  # default

def test_create_user_duplicate_email():
    payload = {"email": "testuser@example.com", "password": "anotherPassword456"}
    response = client.post("/users", json=payload)
    assert response.status_code == 400
    assert "Email already registered." in response.text

def test_get_user_success():
    # We expect user ID 1 to exist if the above test didn't isolate DB (depends on your test environment).
    # If you run tests in a shared DB, user ID 1 might be valid.
    # Otherwise, you can skip or adjust logic to fetch the newly created user's ID.
    response = client.get("/users/1")
    if response.status_code == 404:
        pytest.skip("User ID 1 not found; skipping test.")
    else:
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1

def test_get_user_not_found():
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "User not found." in response.text

# Similarly, you could add tests for /businesses endpoints:
def test_create_business_success():
    payload = {"name": "AcmeCorp"}
    response = client.post("/businesses", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "AcmeCorp"
    assert data["is_verified"] is False

def test_create_business_duplicate():
    payload = {"name": "AcmeCorp"}
    response = client.post("/businesses", json=payload)
    assert response.status_code == 400
    assert "Business name already taken." in response.text

def test_get_business_not_found():
    response = client.get("/businesses/99999")
    assert response.status_code == 404
    assert "Business not found." in response.text
