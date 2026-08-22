"""
Weather ingestion for AgriPulse.

Pulls:
  - Historical daily weather from NASA POWER (temp, rainfall, humidity)
  - Forecast (rain probability) from Open-Meteo

Writes a combined CSV per district to GCS, then loads into
agripulse_data.weather.

Run: python weather_ingest.py
Env vars needed: GCP_PROJECT_ID, RAW_BUCKET, PROCESSED_BUCKET (see gcp_clients.py)
"""
import csv
import logging
from datetime import date, timedelta

import requests

from gcp_clients import upload_to_gcs, load_csv_to_bq, PROCESSED_BUCKET

logger = logging.getLogger("agripulse.ingestion.weather")

# District centroid coordinates — extend this dict as you add districts
DISTRICT_COORDS = {
    "Coimbatore": (11.0168, 76.9558),
    "Erode": (11.3410, 77.7172),
    "Salem": (11.6643, 78.1460),
}

NASA_POWER_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_nasa_power_history(district: str, lat: float, lon: float, days_back: int = 30):
    """Fetch historical daily weather from NASA POWER for the last N days."""
    end = date.today() - timedelta(days=2)  # POWER has ~2 day lag
    start = end - timedelta(days=days_back)
    params = {
        "parameters": "T2M,PRECTOTCORR,RH2M",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    resp = requests.get(NASA_POWER_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["properties"]["parameter"]

    rows = []
    for date_str, temp in data["T2M"].items():
        d = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
        rows.append({
            "date": d,
            "district": district,
            "temperature_c": temp,
            "rainfall_mm": data["PRECTOTCORR"].get(date_str),
            "humidity_pct": data["RH2M"].get(date_str),
            "rain_prob_pct": None,
            "source": "nasa_power",
        })
    return rows


def fetch_open_meteo_forecast(district: str, lat: float, lon: float, days_ahead: int = 3):
    """Fetch short-range forecast (with rain probability) from Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,precipitation_sum,relative_humidity_2m_mean,precipitation_probability_max",
        "forecast_days": days_ahead,
        "timezone": "Asia/Kolkata",
    }
    resp = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()["daily"]

    rows = []
    for i, d in enumerate(data["time"]):
        rows.append({
            "date": d,
            "district": district,
            "temperature_c": data["temperature_2m_max"][i],
            "rainfall_mm": data["precipitation_sum"][i],
            "humidity_pct": data["relative_humidity_2m_mean"][i],
            "rain_prob_pct": data["precipitation_probability_max"][i],
            "source": "open_meteo",
        })
    return rows


def write_csv(rows: list, path: str):
    fieldnames = ["date", "district", "temperature_c", "rainfall_mm",
                  "humidity_pct", "rain_prob_pct", "source"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def run():
    all_rows = []
    for district, (lat, lon) in DISTRICT_COORDS.items():
        try:
            all_rows.extend(fetch_nasa_power_history(district, lat, lon))
        except requests.RequestException as e:
            logger.error("NASA POWER fetch failed for %s: %s", district, e)
        try:
            all_rows.extend(fetch_open_meteo_forecast(district, lat, lon))
        except requests.RequestException as e:
            logger.error("Open-Meteo fetch failed for %s: %s", district, e)

    if not all_rows:
        logger.warning("No weather rows fetched — aborting load.")
        return

    local_path = "/tmp/weather_latest.csv"
    write_csv(all_rows, local_path)

    blob_name = f"weather/{date.today().isoformat()}.csv"
    gcs_uri = upload_to_gcs(local_path, PROCESSED_BUCKET, blob_name)
    load_csv_to_bq(gcs_uri, "weather")


if __name__ == "__main__":
    run()
