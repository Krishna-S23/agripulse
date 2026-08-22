"""
Weather Agent — analyzes rainfall/temperature/humidity signals for a
district and flags anything relevant to irrigation or crop risk decisions.

This is a "tool function" — plain Python, no LLM call inside it. It returns
structured evidence. The Orchestrator hands this evidence to Gemini for
explanation later; the agent itself must stay deterministic and auditable.
"""
from bq_helper import run_query

SQL = """
  SELECT date, district, rainfall_mm, temperature_c, humidity_pct,
         rain_prob_pct, rainfall_7day_avg
  FROM `agripulse_data.v_rainfall_7day`
  WHERE district = @district
  ORDER BY date DESC
  LIMIT 7
"""


def get_weather_signal(district: str) -> dict:
    """Returns structured weather evidence + a risk flag for the given district."""
    rows = run_query(SQL, {"district": district, "mock_key": "weather"})

    if not rows:
        return {
            "district": district,
            "status": "NO_DATA",
            "evidence": [],
        }

    latest = rows[0]
    rain_expected = (latest.get("rain_prob_pct") or 0) >= 60
    high_humidity = (latest.get("humidity_pct") or 0) >= 80
    rainfall_above_avg = (latest.get("rainfall_mm") or 0) > (latest.get("rainfall_7day_avg") or 0) * 1.3

    flags = []
    if rain_expected:
        flags.append("RAIN_EXPECTED")
    if high_humidity:
        flags.append("HIGH_HUMIDITY")
    if rainfall_above_avg:
        flags.append("RAINFALL_SPIKE")

    return {
        "district": district,
        "status": "OK",
        "date": latest.get("date"),
        "temperature_c": latest.get("temperature_c"),
        "rainfall_mm": latest.get("rainfall_mm"),
        "humidity_pct": latest.get("humidity_pct"),
        "rain_prob_pct": latest.get("rain_prob_pct"),
        "rainfall_7day_avg": latest.get("rainfall_7day_avg"),
        "flags": flags,
        "evidence": [
            f"rainfall_mm={latest.get('rainfall_mm')}",
            f"rain_probability_pct={latest.get('rain_prob_pct')}",
            f"humidity_pct={latest.get('humidity_pct')}",
            f"temperature_c={latest.get('temperature_c')}",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_weather_signal("Coimbatore"), indent=2))
