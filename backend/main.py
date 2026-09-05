"""
AgriPulse FastAPI backend.

Run locally:
    cd backend
    pip install -r ../requirements.txt
    uvicorn main:app --reload --port 8080

Endpoints:
    POST /farm                 -> create a farm profile
    GET  /farm/{farm_id}       -> fetch a farm profile
    GET  /farms                -> list all farm profiles
    GET  /intelligence/{farm_id} -> today's prioritized intelligence report
    POST /ask                  -> free-text question routed through agents + Vertex AI
    GET  /health                -> liveness check for Cloud Run
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Make the /agents package importable from the backend
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from models import FarmCreateRequest, AskRequest  # noqa: E402
import farm_store  # noqa: E402
from orchestrator import get_today_intelligence, answer_question, get_vertex_ai_status  # noqa: E402

app = FastAPI(title="AgriPulse API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/vertex-ai")
def vertex_ai_health():
    """Report whether Vertex AI is configured without generating billable content."""
    return get_vertex_ai_status()


@app.post("/farm")
def create_farm(payload: FarmCreateRequest):
    farm = farm_store.create_farm(payload.model_dump())
    return farm


@app.get("/farm/{farm_id}")
def get_farm(farm_id: str):
    farm = farm_store.get_farm(farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


@app.get("/farms")
def list_farms():
    return farm_store.list_farms()


@app.get("/intelligence/{farm_id}")
def get_intelligence(farm_id: str):
    farm = farm_store.get_farm(farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return get_today_intelligence(farm)


@app.post("/ask")
def ask(payload: AskRequest):
    farm = farm_store.get_farm(payload.farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    return answer_question(farm, payload.question)


# Serve the built React frontend if present (populated by the Docker build).
# Mounted last so it doesn't shadow the API routes above.
_frontend_dist = Path(__file__).parent / "static"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
