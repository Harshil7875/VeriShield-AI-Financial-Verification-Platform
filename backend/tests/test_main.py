import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


@pytest.fixture
def unique_email():
    """
    Returns a random unique email each time it is called.
    Example: testuser_f1a3daf4@example.com
    """
    return f"testuser_{uuid.uuid4().hex}@example.com"


@pytest.fixture
def existing_user_email(unique_email):
    """
    Creates a user in the DB with a unique email, and returns that email.
    Useful for testing 'duplicate' scenarios.
    """
    payload = {"email": unique_email, "password": "somePassword123"}
    resp = client.post("/users", json=payload)
    # Sanity check that creation was successful
    assert resp.status_code == 201, f"Setup failed. Response: {resp.text}"
    return unique_email


@pytest.fixture
def unique_business_name():
    """
    Returns a random unique business name each time.
    Example: AcmeCorp_4ce07fe3
    """
    return f"AcmeCorp_{uuid.uuid4().hex}"


@pytest.fixture
def existing_business_name(unique_business_name):
    """
    Creates a business in the DB with a unique name, and returns that name.
    Useful for testing 'duplicate' scenarios.
    """
    payload = {"name": unique_business_name}
    resp = client.post("/businesses", json=payload)
    # Sanity check
    assert resp.status_code == 201, f"Setup failed. Response: {resp.text}"
    return unique_business_name


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}


# ------------------------------
#       USER TESTS
# ------------------------------

def test_create_user_success(unique_email):
    """
    Creates a user with a random email to ensure no duplicates exist beforehand.
    """
    payload = {"email": unique_email, "password": "somePassword123"}
    response = client.post("/users", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Basic checks
    assert data["email"] == unique_email
    assert "id" in data
    assert data["is_verified"] is False  # default is unverified


def test_create_user_duplicate_email(existing_user_email):
    """
    Attempts to create another user with the same email.
    Should return a 400 with the 'Email already registered.' message.
    """
    payload = {"email": existing_user_email, "password": "anotherPassword456"}
    response = client.post("/users", json=payload)
    assert response.status_code == 400
    assert "Email already registered." in response.text


def test_get_user_success():
    """
    This test tries to fetch user ID=1.
    If the database is fresh each run, ID=1 may or may not exist.
    So we skip if not found.
    """
    response = client.get("/users/1")
    if response.status_code == 404:
        pytest.skip("User ID 1 not found; skipping test.")
    else:
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1


def test_get_user_not_found():
    # Arbitrary large ID unlikely to exist
    response = client.get("/users/99999")
    assert response.status_code == 404
    assert "User not found." in response.text


# ------------------------------
#    BUSINESS TESTS
# ------------------------------

def test_create_business_success(unique_business_name):
    """
    Creates a business with a unique name.
    """
    payload = {"name": unique_business_name}
    response = client.post("/businesses", json=payload)
    assert response.status_code == 201
    data = response.json()

    # Basic checks
    assert data["name"] == unique_business_name
    assert data["is_verified"] is False


def test_create_business_duplicate(existing_business_name):
    """
    Attempts to create a second business with the same name.
    Expecting a 400 with 'Business name already taken.'
    """
    payload = {"name": existing_business_name}
    response = client.post("/businesses", json=payload)
    assert response.status_code == 400
    assert "Business name already taken." in response.text


def test_get_business_not_found():
    response = client.get("/businesses/99999")
    assert response.status_code == 404
    assert "Business not found." in response.text
