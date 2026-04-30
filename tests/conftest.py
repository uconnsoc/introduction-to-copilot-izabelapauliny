"""
Pytest configuration and fixtures for FastAPI tests.
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient

# Import the app and original activities
from src.app import app, activities as original_activities


@pytest.fixture
def fresh_activities():
    """Provide a fresh copy of activities for each test."""
    return deepcopy(original_activities)


@pytest.fixture
def client(fresh_activities, monkeypatch):
    """
    Create a test client with fresh activities state.
    Each test gets an isolated copy of the activities database.
    """
    # Replace the app's activities with fresh copy
    monkeypatch.setattr("src.app.activities", fresh_activities)
    
    return TestClient(app)
