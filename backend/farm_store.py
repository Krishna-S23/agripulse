"""
Farm profile storage. Uses Firestore in production; falls back to a local
JSON file when AGRIPULSE_MOCK_DATA=1 (default), so the API is runnable
without any GCP setup.
"""
import os
import json
import uuid
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

MOCK_MODE = os.environ.get("AGRIPULSE_MOCK_DATA", "1") == "1"
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
LOCAL_STORE_PATH = Path(__file__).parent / "local_farms.json"

_firestore_client = None


def _get_firestore():
    global _firestore_client
    if _firestore_client is None:
        from google.cloud import firestore
        _firestore_client = firestore.Client(project=PROJECT_ID or None)
    return _firestore_client


def _load_local() -> dict:
    if not LOCAL_STORE_PATH.exists():
        return {}
    with open(LOCAL_STORE_PATH) as f:
        return json.load(f)


def _save_local(data: dict):
    with open(LOCAL_STORE_PATH, "w") as f:
        json.dump(data, f, indent=2)


def create_farm(farm_data: dict) -> dict:
    farm_id = f"F{uuid.uuid4().hex[:6].upper()}"
    farm_data = {"farm_id": farm_id, **farm_data}

    if MOCK_MODE:
        farms = _load_local()
        farms[farm_id] = farm_data
        _save_local(farms)
    else:
        db = _get_firestore()
        db.collection("farms").document(farm_id).set(farm_data)

    return farm_data


def get_farm(farm_id: str) -> Optional[dict]:
    if MOCK_MODE:
        farms = _load_local()
        return farms.get(farm_id)
    else:
        db = _get_firestore()
        doc = db.collection("farms").document(farm_id).get()
        return doc.to_dict() if doc.exists else None


def list_farms() -> list[dict]:
    if MOCK_MODE:
        return list(_load_local().values())
    else:
        db = _get_firestore()
        return [doc.to_dict() for doc in db.collection("farms").stream()]
