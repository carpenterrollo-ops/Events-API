"""Unit tests for Evently database models and pure domain logic."""

from models import User


def test_user_password_hashing_behaves_correctly() -> None:
    """Verify that User password hashing stores a hash and validates passwords accurately."""
    user = User(username="test_user")
    user.set_password("password")

    assert user.password_hash is not None
    assert user.password_hash != "password"
    assert user.check_password("password") is True
    assert user.check_password("wrong_password") is False
