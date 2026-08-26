"""
Shared BigQuery query helper for agents.

In MOCK_MODE (default when GCP_PROJECT_ID isn't set, or when
AGRIPULSE_MOCK_DATA=1), agents read from local JSON fixtures instead of
BigQuery, so the whole pipeline is runnable and testable without GCP
credentials. Set AGRIPULSE_MOCK_DATA=0 with real credentials to hit BigQuery.
"""
import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Loads the .env file at the project root, regardless of which directory this
# module is imported from (find_dotenv walks up parent directories).
load_dotenv(find_dotenv(usecwd=True))

logger = logging.getLogger("agripulse.agents.bq")

MOCK_MODE = os.environ.get("AGRIPULSE_MOCK_DATA", "1") == "1"
FIXTURES_DIR = Path(__file__).parent / "fixtures"

PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "")
DATASET = os.environ.get("BQ_DATASET", "agripulse_data")

_bq_client = None


def _get_client():
    global _bq_client
    if _bq_client is None:
        from google.cloud import bigquery
        _bq_client = bigquery.Client(project=PROJECT_ID)
    return _bq_client


def run_query(sql: str, params: dict) -> list[dict]:
    """Runs a parameterized query against BigQuery, or serves from a mock
    fixture keyed by the `mock_key` param if MOCK_MODE is on."""
    if MOCK_MODE:
        return _run_mock(params)

    from google.cloud import bigquery
    client = _get_client()
    query_params = [
        bigquery.ScalarQueryParameter(k, "STRING", v) for k, v in params.items()
        if k != "mock_key"
    ]
    job_config = bigquery.QueryJobConfig(query_parameters=query_params)
    result = client.query(sql, job_config=job_config).result()
    return [dict(row) for row in result]


def _run_mock(params: dict) -> list[dict]:
    mock_key = params.get("mock_key")
    fixture_path = FIXTURES_DIR / f"{mock_key}.json"
    if not fixture_path.exists():
        logger.warning("No mock fixture at %s, returning empty result", fixture_path)
        return []
    with open(fixture_path) as f:
        data = json.load(f)
    # allow fixtures to be filtered by farm_id/district if present in params
    if "farm_id" in params:
        filtered = [r for r in data if r.get("farm_id") == params["farm_id"]]
        if not filtered and mock_key == "soil" and params["farm_id"] != "F999" and data:
            # Fall back to first soil fixture for dynamically created UI farms
            default_row = dict(data[0])
            default_row["farm_id"] = params["farm_id"]
            filtered = [default_row]
        data = filtered
    if "district" in params:
        data = [r for r in data if r.get("district") == params["district"]]
    if "crop" in params:
        data = [r for r in data if r.get("crop") == params["crop"]]
    return data
