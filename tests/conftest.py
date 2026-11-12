"""Shared pytest configuration and fixtures for the Events API test suite."""

from pathlib import Path
import sys
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE_URL: str = "http://localhost:5000"


@pytest.fixture
def base_url() -> str:
    """Return the base URL of the running Events API server."""
    return BASE_URL
