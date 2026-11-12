"""Integration tests for the Events API (Happy Path & Negative/Edge Cases).

Requires the Events API server to be running on http://localhost:5000.
"""

from datetime import datetime, timezone
import requests


# ==============================================================================
# Happy Path Tests
# ==============================================================================

def test_health_endpoint_returns_healthy(base_url: str) -> None:
    """Check that the /api/health endpoint returns 200 and healthy status."""
    response = requests.get(f"{base_url}/api/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "healthy"}


def test_register_user_creates_new_user(base_url: str, unique_username: str) -> None:
    """Verify that registering a new user returns 201 with created user details."""
    payload = {
        "username": unique_username,
        "password": "Password123!",
    }
    response = requests.post(f"{base_url}/api/auth/register", json=payload, timeout=5)
    assert response.status_code == 201
    data = response.json()
    assert data.get("message") == "User created successfully"
    user_info = data.get("user")
    assert isinstance(user_info, dict)
    assert user_info.get("username") == unique_username
    assert "id" in user_info


def test_login_returns_jwt_token(base_url: str, registered_user: dict[str, str]) -> None:
    """Verify that a registered user can log in and receives a JWT token."""
    payload = {
        "username": registered_user["username"],
        "password": registered_user["password"],
    }
    response = requests.post(f"{base_url}/api/auth/login", json=payload, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 0
    assert data.get("user", {}).get("username") == registered_user["username"]


def test_create_public_event_requires_auth_and_succeeds_with_token(
    base_url: str, auth_headers: dict[str, str]
) -> None:
    """Verify that an authenticated user can successfully create a public event."""
    event_payload = {
        "title": "Community Pytest Meetup",
        "description": "Discussing test automation best practices",
        "date": datetime.now(timezone.utc).isoformat(),
        "location": "Room 404",
        "capacity": 25,
        "is_public": True,
        "requires_admin": False,
    }
    response = requests.post(
        f"{base_url}/api/events",
        json=event_payload,
        headers=auth_headers,
        timeout=5,
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["title"] == event_payload["title"]
    assert data["description"] == event_payload["description"]
    assert data["location"] == event_payload["location"]
    assert data["capacity"] == event_payload["capacity"]
    assert data["is_public"] is True
    assert data["requires_admin"] is False


def test_rsvp_to_public_event_succeeds(
    base_url: str, auth_headers: dict[str, str]
) -> None:
    """Verify that an RSVP can be submitted for an existing public event."""
    event_payload = {
        "title": "RSVP Target Event",
        "date": datetime.now(timezone.utc).isoformat(),
        "is_public": True,
    }
    create_resp = requests.post(
        f"{base_url}/api/events",
        json=event_payload,
        headers=auth_headers,
        timeout=5,
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    rsvp_resp = requests.post(
        f"{base_url}/api/rsvps/event/{event_id}",
        json={"attending": True},
        timeout=5,
    )
    assert rsvp_resp.status_code in (200, 201)
    rsvp_data = rsvp_resp.json()
    assert rsvp_data["event_id"] == event_id
    assert rsvp_data["attending"] is True


# ==============================================================================
# Edge / Error / Negative Tests
# ==============================================================================

def test_register_duplicate_username_returns_400(
    base_url: str, registered_user: dict[str, str]
) -> None:
    """Verify that attempting to register an already existing username fails with HTTP 400."""
    duplicate_payload = {
        "username": registered_user["username"],
        "password": "AnyPassword123!",
    }
    response = requests.post(
        f"{base_url}/api/auth/register",
        json=duplicate_payload,
        timeout=5,
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert data["error"] == "Username already exists"


def test_create_event_without_token_returns_401(base_url: str) -> None:
    """Verify that creating an event without Authorization header fails with HTTP 401."""
    event_payload = {
        "title": "Unauthorized Event",
        "date": datetime.now(timezone.utc).isoformat(),
        "is_public": True,
    }
    response = requests.post(
        f"{base_url}/api/events",
        json=event_payload,
        timeout=5,
    )
    assert response.status_code == 401
    data = response.json()
    assert "msg" in data or "error" in data


def test_rsvp_to_protected_event_without_token_returns_401(
    base_url: str, auth_headers: dict[str, str]
) -> None:
    """Verify that submitting an RSVP to a non-public (protected) event without authentication fails with HTTP 401."""
    # 1. Authenticated user creates a non-public (protected) event
    event_payload = {
        "title": "Members Only Event",
        "date": datetime.now(timezone.utc).isoformat(),
        "is_public": False,
        "requires_admin": False,
    }
    create_resp = requests.post(
        f"{base_url}/api/events",
        json=event_payload,
        headers=auth_headers,
        timeout=5,
    )
    assert create_resp.status_code == 201
    event_id = create_resp.json()["id"]

    # 2. Unauthenticated request to RSVP on that protected event
    rsvp_resp = requests.post(
        f"{base_url}/api/rsvps/event/{event_id}",
        json={"attending": True},
        timeout=5,
    )
    assert rsvp_resp.status_code == 401
    data = rsvp_resp.json()
    assert "error" in data
    assert data["error"] == "Authentication required for this event"
