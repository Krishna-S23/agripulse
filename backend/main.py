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
import logging
import json
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Make the /agents package importable from the backend
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from models import FarmCreateRequest, AskRequest  # noqa: E402
import farm_store  # noqa: E402
from orchestrator import get_today_intelligence, answer_question, get_vertex_ai_status  # noqa: E402


def convert_dates_to_strings(obj, path=""):
    """Recursively convert date/datetime objects to ISO format strings."""
    if isinstance(obj, (date, datetime)):
        logger.debug(f"[convert_dates_to_strings] Converting date at {path}: {obj}")
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: convert_dates_to_strings(v, f"{path}.{k}") for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_dates_to_strings(item, f"{path}[{i}]") for i, item in enumerate(obj)]
    elif hasattr(obj, '__dict__'):
        # Handle objects with __dict__ (custom classes)
        logger.debug(f"[convert_dates_to_strings] Found object with __dict__ at {path}: {type(obj)}")
        return convert_dates_to_strings(obj.__dict__, path)
    return obj


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle date and datetime objects."""
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


class CustomJSONResponse(JSONResponse):
    """Custom JSONResponse that uses DateTimeEncoder."""
    def render(self, content):
        return json.dumps(content, cls=DateTimeEncoder).encode("utf-8")


app = FastAPI(
    title="AgriPulse API",
    version="1.0.0",
    default_response_class=CustomJSONResponse
)

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
    try:
        logger.debug(f"[/ask] Received request: farm_id={payload.farm_id}, question={payload.question}")
        
        farm = farm_store.get_farm(payload.farm_id)
        if not farm:
            logger.warning(f"[/ask] Farm not found: {payload.farm_id}")
            raise HTTPException(status_code=404, detail="Farm not found")
        
        logger.debug(f"[/ask] Farm found: {farm}")
        result = answer_question(farm, payload.question)
        logger.debug(f"[/ask] Raw result type: {type(result)}")
        logger.debug(f"[/ask] Raw result: {result}")
        
        converted = convert_dates_to_strings(result)
        logger.debug(f"[/ask] Converted result: {converted}")
        logger.debug(f"[/ask] Answer generated successfully")
        return converted
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[/ask] Error processing question: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")


@app.on_event("startup")
def startup_event():
    """Log environment variable status on startup."""
    logger.info("=== Environment Variables Check ===")
    logger.info(f"GOOGLE_APPLICATION_CREDENTIALS: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'NOT SET')}")
    logger.info(f"GOOGLE_CLOUD_PROJECT: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'NOT SET')}")
    logger.info(f"GEMINI_API_KEY present: {'GEMINI_API_KEY' in os.environ}")
    logger.info(f"DATA_GOV_IN_KEY present: {'DATA_GOV_IN_KEY' in os.environ}")
    logger.info("=====================================")


# Serve the built React frontend if present (populated by the Docker build).
# Mounted last so it doesn't shadow the API routes above.
_frontend_dist = Path(__file__).parent / "static"
if _frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_dist), html=True), name="frontend")
