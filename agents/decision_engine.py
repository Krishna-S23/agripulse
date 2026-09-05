"""
Decision Engine — deterministic rules that turn Weather/Soil/Market agent
evidence into structured recommendations. Kept rule-based (not an LLM call)
so every recommendation is reproducible and defensible: same input always
produces the same output, and you can point to the exact rule that fired.

Vertex AI's job (in orchestrator.py) is ONLY to explain and prioritize these
outputs in natural language — never to invent the recommendation itself.
"""
from typing import Optional


def irrigation_decision(weather: dict, soil: dict) -> Optional[dict]:
    """Should irrigation happen, be delayed, or is data insufficient?"""
    if weather.get("status") != "OK" or soil.get("status") != "OK":
        return None

    rain_expected = "RAIN_EXPECTED" in weather.get("flags", [])
    adequate_moisture = "ADEQUATE_MOISTURE" in soil.get("flags", [])
    low_moisture = "LOW_MOISTURE" in soil.get("flags", [])

    if rain_expected and adequate_moisture:
        recommendation, confidence = "DELAY_IRRIGATION", "HIGH"
    elif rain_expected and not adequate_moisture:
        recommendation, confidence = "DELAY_IRRIGATION", "MEDIUM"
    elif low_moisture and not rain_expected:
        recommendation, confidence = "IRRIGATE_NOW", "HIGH"
    else:
        recommendation, confidence = "MONITOR", "MEDIUM"

    return {
        "recommendation_type": "IRRIGATION",
        "recommendation": recommendation,
        "confidence": confidence,
        "evidence": weather.get("evidence", []) + soil.get("evidence", []),
        "priority": "HIGH" if recommendation == "IRRIGATE_NOW" else "MEDIUM",
    }


def market_decision(market: dict) -> Optional[dict]:
    """Should the farmer consider selling now or holding?"""
    if market.get("status") != "OK":
        return None

    flags = market.get("flags", [])
    if "PRICE_ABOVE_TREND" in flags:
        recommendation, confidence, priority = "CONSIDER_SELLING", "MEDIUM", "MEDIUM"
    elif "PRICE_BELOW_TREND" in flags:
        recommendation, confidence, priority = "HOLD_AND_MONITOR", "MEDIUM", "LOW"
    else:
        recommendation, confidence, priority = "MONITOR_MARKET", "LOW", "LOW"

    return {
        "recommendation_type": "MARKET",
        "recommendation": recommendation,
        "confidence": confidence,
        "evidence": market.get("evidence", []),
        "priority": priority,
    }


def crop_risk_decision(weather: dict, soil: dict) -> Optional[dict]:
    """Flag crop stress risk from combined humidity/moisture conditions."""
    if weather.get("status") != "OK":
        return None

    flags = weather.get("flags", [])
    soil_flags = soil.get("flags", []) if soil.get("status") == "OK" else []

    risk_signals = []
    if "HIGH_HUMIDITY" in flags:
        risk_signals.append("high humidity (fungal disease risk)")
    if "PH_OUT_OF_RANGE" in soil_flags:
        risk_signals.append("soil pH out of optimal range")
    if "LOW_NITROGEN" in soil_flags:
        risk_signals.append("low nitrogen")

    if not risk_signals:
        return None

    return {
        "recommendation_type": "CROP_RISK",
        "recommendation": "MONITOR_CROP_CONDITION",
        "confidence": "MEDIUM",
        "evidence": weather.get("evidence", []) + soil.get("evidence", []),
        "priority": "MEDIUM",
        "risk_signals": risk_signals,
    }


def build_recommendations(weather: dict, soil: dict, market: dict) -> list[dict]:
    """Runs all rule sets and returns non-null recommendations, sorted by
    priority (HIGH first)."""
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    results = [
        irrigation_decision(weather, soil),
        market_decision(market),
        crop_risk_decision(weather, soil),
    ]
    results = [r for r in results if r is not None]
    results.sort(key=lambda r: priority_order.get(r["priority"], 3))
    return results
