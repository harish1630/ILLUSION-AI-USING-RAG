"""Tests for all core API endpoints: schemes, matching, business profile, roadmap, and chat."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_schemes():
    response = client.get("/api/v1/schemes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) > 0
    # Check for NEEDS scheme
    scheme_names = [s["name"] for s in data["items"]]
    assert any("NEEDS" in name for name in scheme_names)
    assert any("UYEGP" in name for name in scheme_names)
    assert any("PMEGP" in name for name in scheme_names)


def test_scheme_matching_deterministic():
    # Profile that matches NEEDS: Manufacturing, ₹25 Lakhs, First generation, Tamil Nadu
    payload = {
        "preferred_language": "en",
        "state": "Tamil Nadu",
        "district": "Coimbatore",
        "business_activity": "Textile garment manufacturing unit",
        "business_category": "manufacturing",
        "investment_budget": 2500000,
        "business_stage": "idea",
        "first_generation_entrepreneur": True,
    }
    response = client.post("/api/v1/schemes/match", json=payload)
    assert response.status_code == 200
    matched = response.json()
    assert len(matched) > 0
    matched_ids = [s["id"] for s in matched]
    assert "scheme-needs-tn" in matched_ids


def test_scheme_disqualification():
    # Trading activity should disqualify NEEDS scheme
    payload = {
        "preferred_language": "en",
        "state": "Tamil Nadu",
        "district": "Madurai",
        "business_activity": "Retail grocery shop",
        "business_category": "trading",
        "investment_budget": 500000,
        "business_stage": "idea",
    }
    response = client.post("/api/v1/schemes/match", json=payload)
    assert response.status_code == 200
    matched = response.json()
    matched_ids = [s["id"] for s in matched]
    # NEEDS strictly excludes trading
    assert "scheme-needs-tn" not in matched_ids


def test_business_profile_creation():
    payload = {
        "district": "Salem",
        "business_idea": "Organic honey processing unit",
        "business_category": "manufacturing",
        "investment_budget": 800000,
        "business_stage": "planning",
        "preferred_language": "en"
    }
    response = client.post("/api/v1/business/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["district"] == "Salem"


def test_roadmap_creation_and_task_status_update():
    payload = {
        "title": "Bakery and Confectionery Launch",
        "business_summary": "Bakery manufacturing unit in Chennai",
        "category": "manufacturing",
        "district": "Chennai",
        "budget": 1200000,
        "stage": "idea"
    }
    create_res = client.post("/api/v1/roadmaps?language=en", json=payload)
    assert create_res.status_code == 200
    roadmap = create_res.json()
    assert len(roadmap["tasks"]) > 0
    roadmap_id = roadmap["id"]
    task_id = roadmap["tasks"][0]["id"]

    # Update task status
    update_res = client.patch(
        f"/api/v1/roadmaps/{roadmap_id}/tasks/{task_id}",
        json={"status": "completed"}
    )
    assert update_res.status_code == 200
    updated_roadmap = update_res.json()
    assert updated_roadmap["progress_percentage"] > 0


def test_bilingual_chat_assistant():
    # Test English query
    en_payload = {
        "question": "What is the maximum subsidy under NEEDS scheme?",
        "language": "en"
    }
    en_res = client.post("/api/v1/chat", json=en_payload)
    assert en_res.status_code == 200
    en_data = en_res.json()
    assert len(en_data["answer"]) > 10
    assert len(en_data["sources"]) > 0

    # Test Tamil query
    ta_payload = {
        "question": "உத்யாம் பதிவு இலவசமா?",
        "language": "ta"
    }
    ta_res = client.post("/api/v1/chat", json=ta_payload)
    assert ta_res.status_code == 200
    ta_data = ta_res.json()
    assert ta_data["language"] == "ta"
    assert len(ta_data["answer"]) > 5

