"""Shared pytest configuration and fixtures for the Events API test suite."""

from pathlib import Path
import sys
import uuid
import pytest
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL: str = "http://localhost:5000"


@pytest.fixture(scope="session")
def base_url() -> str:
    """Return the base URL of the running Events API server."""
    return BASE_URL


@pytest.fixture
def unique_username() -> str:
    """Generate a unique username to avoid conflicts in registration tests."""
    return f"user_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def registered_user(base_url: str, unique_username: str) -> dict[str, str]:
    """Register a new user and return credentials."""
    password = "securePassword123!"
    response = requests.post(
        f"{base_url}/api/auth/register",
        json={"username": unique_username, "password": password},
        timeout=5,
    )
    assert response.status_code == 201, f"Failed to register user: {response.text}"
    return {"username": unique_username, "password": password}


@pytest.fixture
def auth_token(base_url: str, registered_user: dict[str, str]) -> str:
    """Login with the registered user and return the JWT access token."""
    response = requests.post(
        f"{base_url}/api/auth/login",
        json={
            "username": registered_user["username"],
            "password": registered_user["password"],
        },
        timeout=5,
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Return authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}
