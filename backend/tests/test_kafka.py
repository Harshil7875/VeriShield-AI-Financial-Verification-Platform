# backend/tests/test_kafka.py

import time
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User

client = TestClient(app)

@pytest.mark.integration
def test_kafka_user_created_flow():
    # Step 1: create user via API
    payload = {"email": "kafka_user@example.com", "password": "TestPass123"}
    resp = client.post("/users", json=payload)
    assert resp.status_code == 201, f"Create user failed: {resp.text}"
    data = resp.json()
    user_id = data["id"]

    # Step 2: wait for consumer to process
    # In real tests, you might poll or have a shorter delay. 
    time.sleep(5)

    # Step 3: check DB to see if consumer has verified user
    with SessionLocal() as db:
        user_in_db = db.query(User).filter_by(id=user_id).first()
        assert user_in_db, "User not found in DB"
        assert user_in_db.is_verified is True, "User was not verified by consumer"
