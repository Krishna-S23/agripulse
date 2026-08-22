"""
Crop production/yield history ingestion — this dataset updates yearly, not
daily, so run this manually (or via an annual Cloud Scheduler job) rather
than the daily pipeline.

Source: data.gov.in "District-wise, Season-wise Crop Production Statistics"
(Ministry of Agriculture & Farmers Welfare). Download the CSV manually from
the portal (no API key needed for this dataset) and point RAW_CSV_PATH at it,
or adapt fetch_from_api() if the resource has an API endpoint enabled.

Run: RAW_CSV_PATH=/path/to/downloaded.csv python crop_history_ingest.py
"""
import csv
import logging
import os
from datetime import date

from gcp_clients import upload_to_gcs, load_csv_to_bq, PROCESSED_BUCKET

logger = logging.getLogger("agripulse.ingestion.crop_history")

TARGET_DISTRICTS = ["Coimbatore", "Erode", "Salem"]
TARGET_CROPS = ["Tomato", "Onion"]

RAW_CSV_PATH = os.environ.get("RAW_CSV_PATH", "/tmp/crop_production_raw.csv")


def transform(raw_path: str) -> list:
    """Reads the raw data.gov.in export and reshapes it to match our schema.
    Column names below match the standard export from that dataset as of
    this writing — check the header row of your download and adjust if the
    portal has changed field names."""
    rows = []
    with open(raw_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            district = (r.get("District_Name") or r.get("district") or "").strip().title()
            crop = (r.get("Crop") or r.get("crop") or "").strip().title()
            if district not in TARGET_DISTRICTS or crop not in TARGET_CROPS:
                continue
            try:
                year_raw = r.get("Crop_Year") or r.get("year") or ""
                year = int(str(year_raw)[:4])
                production = float(r.get("Production") or 0)
                area = float(r.get("Area") or 0)
                yield_val = round(production / area, 3) if area else None
            except (ValueError, ZeroDivisionError):
                continue
            rows.append({
                "year": year,
                "district": district,
                "crop": crop,
                "production": production,
                "yield": yield_val,
            })
    return rows


def write_csv(rows: list, path: str):
    fieldnames = ["year", "district", "crop", "production", "yield"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run():
    if not os.path.exists(RAW_CSV_PATH):
        logger.error("Raw file not found at %s — download it from data.gov.in first.", RAW_CSV_PATH)
        return

    rows = transform(RAW_CSV_PATH)
    if not rows:
        logger.warning("No matching rows after filtering — check district/crop names.")
        return

    local_path = "/tmp/crop_history_clean.csv"
    write_csv(rows, local_path)

    blob_name = f"crop_history/{date.today().isoformat()}.csv"
    gcs_uri = upload_to_gcs(local_path, PROCESSED_BUCKET, blob_name)
    load_csv_to_bq(gcs_uri, "crop_history", write_disposition="WRITE_TRUNCATE")


if __name__ == "__main__":
    run()
