"""
Market price ingestion for AgriPulse — pulls daily mandi prices from the
Agmarknet resource on data.gov.in.

Requires a free API key from https://data.gov.in (register -> generate key).
Set it as env var DATA_GOV_IN_API_KEY.

Run: python market_ingest.py
"""
import csv
import logging
import os
import tempfile
from datetime import date
from pathlib import Path

import requests

from gcp_clients import upload_to_gcs, load_csv_to_bq, PROCESSED_BUCKET

logger = logging.getLogger("agripulse.ingestion.market")

API_KEY = os.environ.get("DATA_GOV_IN_API_KEY", "")
RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"  # Variety-wise Daily Market Prices
BASE_URL = f"https://api.data.gov.in/resource/{RESOURCE_ID}"

# Crops + district this deployment tracks — keep in sync with the farm grid
TARGET_STATE = "Tamil Nadu"
TARGET_CROPS = ["Tomato", "Onion"]
TARGET_DISTRICTS = ["Coimbatore", "Erode", "Salem"]


def fetch_prices(commodity: str, limit: int = 500) -> list:
    if not API_KEY:
        raise RuntimeError("DATA_GOV_IN_API_KEY not set — get one free at data.gov.in")

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": limit,
        "filters[state]": TARGET_STATE,
        "filters[commodity]": commodity,
    }
    resp = requests.get(BASE_URL, params=params, timeout=30)
    resp.raise_for_status()
    records = resp.json().get("records", [])

    rows = []
    for r in records:
        district = r.get("district")
        if district not in TARGET_DISTRICTS:
            continue
        try:
            rows.append({
                "date": _normalize_date(r.get("arrival_date")),
                "crop": commodity,
                "market": r.get("market"),
                "district": district,
                "modal_price": float(r.get("modal_price", 0) or 0),
                "min_price": float(r.get("min_price", 0) or 0),
                "max_price": float(r.get("max_price", 0) or 0),
                "arrivals": None,  # not always present in this resource
            })
        except (TypeError, ValueError):
            logger.warning("Skipping malformed row: %s", r)
    return rows


def _normalize_date(d: str) -> str:
    """Agmarknet returns dates as DD/MM/YYYY — convert to ISO for BigQuery."""
    if not d:
        return ""
    day, month, year = d.split("/")
    return f"{year}-{month}-{day}"


def write_csv(rows: list, path: str):
    fieldnames = ["date", "crop", "market", "district", "modal_price", "min_price", "max_price", "arrivals"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run():
    all_rows = []
    for crop in TARGET_CROPS:
        try:
            all_rows.extend(fetch_prices(crop))
        except (requests.RequestException, RuntimeError) as e:
            logger.error("Fetch failed for %s: %s", crop, e)

    if not all_rows:
        logger.warning("No market rows fetched — aborting load.")
        return

    local_path = str(Path(tempfile.gettempdir()) / "market_prices_latest.csv")
    write_csv(all_rows, local_path)

    blob_name = f"market_prices/{date.today().isoformat()}.csv"
    gcs_uri = upload_to_gcs(local_path, PROCESSED_BUCKET, blob_name)
    load_csv_to_bq(gcs_uri, "market_prices")


if __name__ == "__main__":
    run()
