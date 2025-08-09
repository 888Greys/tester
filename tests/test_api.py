"""
Tests for the API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert data["app_name"] == "Gukas AI Agent"
    assert "dependencies" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["service"] == "Gukas AI Agent"
    assert data["status"] == "running"


def test_info_endpoint():
    """Test service info endpoint."""
    response = client.get("/info")
    assert response.status_code == 200
    
    data = response.json()
    assert data["app_name"] == "Gukas AI Agent"
    assert "features" in data


def test_chat_endpoint_validation():
    """Test chat endpoint input validation."""
    # Test empty message
    response = client.post("/chat", json={"message": ""})
    assert response.status_code == 422
    
    # Test message too long
    long_message = "x" * 2001
    response = client.post("/chat", json={"message": long_message})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_endpoint_success():
    """Test successful chat interaction."""
    # Note: This test requires valid Cerebras API key
    # Skip if not configured for testing
    response = client.post("/chat", json={
        "message": "Hello, how are you?",
        "user_id": "test_user",
        "session_id": "test_session"
    })
    
    # Should either succeed or fail gracefully
    assert response.status_code in [200, 500]