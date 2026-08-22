"""
Soil Agent — analyzes the latest soil reading for a farm and flags
conditions relevant to irrigation, fertilization, or crop stress decisions.
"""
from bq_helper import run_query

SQL = """
  SELECT farm_id, date, moisture, ph, nitrogen
  FROM `agripulse_data.v_latest_soil`
  WHERE farm_id = @farm_id
"""

# Thresholds — tune these against agronomic guidance for your target crops.
MOISTURE_LOW = 35
MOISTURE_ADEQUATE = 55
PH_LOW = 6.0
PH_HIGH = 7.5


def get_soil_signal(farm_id: str) -> dict:
    rows = run_query(SQL, {"farm_id": farm_id, "mock_key": "soil"})

    if not rows:
        return {"farm_id": farm_id, "status": "NO_DATA", "evidence": []}

    latest = rows[0]
    moisture = latest.get("moisture") or 0
    ph = latest.get("ph") or 0
    nitrogen = latest.get("nitrogen") or "Unknown"

    flags = []
    if moisture < MOISTURE_LOW:
        flags.append("LOW_MOISTURE")
    elif moisture >= MOISTURE_ADEQUATE:
        flags.append("ADEQUATE_MOISTURE")

    if ph < PH_LOW or ph > PH_HIGH:
        flags.append("PH_OUT_OF_RANGE")

    if nitrogen == "Low":
        flags.append("LOW_NITROGEN")

    return {
        "farm_id": farm_id,
        "status": "OK",
        "date": latest.get("date"),
        "moisture": moisture,
        "ph": ph,
        "nitrogen": nitrogen,
        "flags": flags,
        "evidence": [
            f"soil_moisture_pct={moisture}",
            f"soil_ph={ph}",
            f"nitrogen_level={nitrogen}",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_soil_signal("F001"), indent=2))
