def make_recommendation(category, recommendation, confidence="LOW", priority="LOW", evidence=None, explanation=""):
    return {
        "recommendation_type": category,
        "recommendation": recommendation,
        "confidence": confidence,
        "priority": priority,
        "evidence": evidence or [],
        "explanation": explanation,
    }

def build_recommendations(weather, soil, market):
    recommendations = []

    # Weather always appears
    weather_evidence = weather.get("evidence", [])
    if weather.get("status") == "OK":
        recommendations.append(
            make_recommendation(
                "WEATHER",
                "MONITOR_WEATHER",
                "LOW",
                "LOW",
                weather_evidence,
                "Weather is within a normal range. Continue monitoring rainfall and humidity trends."
            )
        )
    else:
        recommendations.append(
            make_recommendation(
                "WEATHER",
                "CHECK_WEATHER",
                "MEDIUM",
                "MEDIUM",
                weather_evidence,
                "Weather conditions require attention."
            )
        )

    # Soil always appears
    if soil.get("status") == "NO_DATA":
        recommendations.append(
            make_recommendation(
                "SOIL",
                "CHECK_SOIL_DATA",
                "LOW",
                "LOW",
                [],
                "Soil data is not available yet. Collect soil readings before making irrigation or nutrient decisions."
            )
        )
    else:
        recommendations.append(
            make_recommendation(
                "SOIL",
                "MONITOR_SOIL",
                "LOW",
                "LOW",
                soil.get("evidence", []),
                "Soil status is being monitored."
            )
        )

    # Market always appears
    market_evidence = market.get("evidence", [])
    recommendations.append(
        make_recommendation(
            "MARKET",
            "MONITOR_MARKET",
            "LOW",
            "LOW",
            market_evidence,
            "Market conditions are being monitored for price and arrival trends."
        )
    )

    return recommendations