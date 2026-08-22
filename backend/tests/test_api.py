import sys
import os
from pathlib import Path

os.environ["AGRIPULSE_MOCK_DATA"] = "1"
sys.path.append(str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_create_and_get_farm():
    r = client.post("/farm", json={
        "district": "Coimbatore",
        "crop": "Tomato",
        "growth_stage": "Flowering",
        "area_acres": 2.0,
    })
    assert r.status_code == 200
    farm = r.json()
    assert farm["district"] == "Coimbatore"
    farm_id = farm["farm_id"]

    r2 = client.get(f"/farm/{farm_id}")
    assert r2.status_code == 200
    assert r2.json()["farm_id"] == farm_id


def test_intelligence_for_known_farm():
    # F001 exists in the mock fixtures (Coimbatore / Tomato)
    r = client.post("/farm", json={"district": "Coimbatore", "crop": "Tomato"})
    farm_id = r.json()["farm_id"]

    # Monkey-patch: fixtures are keyed to F001/Coimbatore/Tomato, so also
    # directly test the seeded fixture id path via orchestrator import
    from orchestrator import get_today_intelligence
    result = get_today_intelligence({
        "farm_id": "F001", "district": "Coimbatore", "crop": "Tomato",
        "growth_stage": "Flowering",
    })
    assert result["district"] == "Coimbatore"
    assert len(result["recommendations"]) > 0
    assert result["recommendations"][0]["recommendation_type"] in {
        "IRRIGATION", "MARKET", "CROP_RISK"
    }


def test_ask_endpoint():
    r = client.post("/farm", json={"district": "Coimbatore", "crop": "Tomato"})
    farm_id = r.json()["farm_id"]
    r2 = client.post("/ask", json={"farm_id": farm_id, "question": "Should I irrigate today?"})
    assert r2.status_code == 200
    body = r2.json()
    assert "answer" in body
    assert "evidence_used" in body


def test_farm_not_found():
    r = client.get("/farm/DOES_NOT_EXIST")
    assert r.status_code == 404
