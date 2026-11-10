"""Test health and language endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == settings.APP_NAME
    assert "services" in data
    assert "version" in data


def test_languages_endpoint():
    response = client.get("/api/v1/languages")
    assert response.status_code == 200
    data = response.json()
    assert "supported_languages" in data
    codes = [item["code"] for item in data["supported_languages"]]
    assert "en" in codes
    assert "ta" in codes


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "docs" in data

