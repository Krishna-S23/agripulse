"""
Market Agent — analyzes current price vs. recent trend and arrivals for a
crop, and flags conditions worth surfacing to the farmer.
"""
from bq_helper import run_query

SQL = """
  SELECT date, crop, market, district, modal_price, arrivals,
         prior_7day_avg_price, pct_change_vs_prior_week
  FROM `agripulse_data.v_weekly_price_trend`
  WHERE crop = @crop AND district = @district
  ORDER BY date DESC
  LIMIT 1
"""

PRICE_SPIKE_PCT = 8
PRICE_DROP_PCT = -8


def get_market_signal(crop: str, district: str) -> dict:
    rows = run_query(SQL, {"crop": crop, "district": district, "mock_key": "market"})

    if not rows:
        return {"crop": crop, "district": district, "status": "NO_DATA", "evidence": []}

    latest = rows[0]
    pct_change = latest.get("pct_change_vs_prior_week") or 0

    flags = []
    if pct_change >= PRICE_SPIKE_PCT:
        flags.append("PRICE_ABOVE_TREND")
    elif pct_change <= PRICE_DROP_PCT:
        flags.append("PRICE_BELOW_TREND")

    return {
        "crop": crop,
        "district": district,
        "status": "OK",
        "date": latest.get("date"),
        "modal_price": latest.get("modal_price"),
        "prior_7day_avg_price": latest.get("prior_7day_avg_price"),
        "pct_change_vs_prior_week": pct_change,
        "arrivals": latest.get("arrivals"),
        "flags": flags,
        "evidence": [
            f"modal_price_inr={latest.get('modal_price')}",
            f"pct_change_vs_prior_week={pct_change}",
            f"arrivals_tonnes={latest.get('arrivals')}",
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(get_market_signal("Tomato", "Coimbatore"), indent=2))
