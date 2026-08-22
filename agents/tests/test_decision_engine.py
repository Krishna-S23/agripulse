import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from decision_engine import (
    irrigation_decision,
    market_decision,
    crop_risk_decision,
    build_recommendations,
)

# Helper builders for evidence dicts, so each test only specifies what matters
def weather(flags=None, status="OK"):
    return {"status": status, "flags": flags or [], "evidence": ["rainfall_mm=10"]}


def soil(flags=None, status="OK"):
    return {"status": status, "flags": flags or [], "evidence": ["soil_moisture_pct=50"]}


def market(flags=None, status="OK"):
    return {"status": status, "flags": flags or [], "evidence": ["modal_price_inr=2000"]}


class TestIrrigationDecision:
    def test_rain_expected_and_adequate_moisture_delays_with_high_confidence(self):
        result = irrigation_decision(
            weather(["RAIN_EXPECTED"]), soil(["ADEQUATE_MOISTURE"])
        )
        assert result["recommendation"] == "DELAY_IRRIGATION"
        assert result["confidence"] == "HIGH"

    def test_rain_expected_but_not_adequate_moisture_delays_medium_confidence(self):
        result = irrigation_decision(weather(["RAIN_EXPECTED"]), soil([]))
        assert result["recommendation"] == "DELAY_IRRIGATION"
        assert result["confidence"] == "MEDIUM"

    def test_low_moisture_no_rain_irrigates_now(self):
        result = irrigation_decision(weather([]), soil(["LOW_MOISTURE"]))
        assert result["recommendation"] == "IRRIGATE_NOW"
        assert result["confidence"] == "HIGH"
        assert result["priority"] == "HIGH"

    def test_no_strong_signals_falls_back_to_monitor(self):
        result = irrigation_decision(weather([]), soil([]))
        assert result["recommendation"] == "MONITOR"

    def test_missing_weather_data_returns_none(self):
        result = irrigation_decision(weather(status="NO_DATA"), soil(["ADEQUATE_MOISTURE"]))
        assert result is None

    def test_missing_soil_data_returns_none(self):
        result = irrigation_decision(weather(["RAIN_EXPECTED"]), soil(status="NO_DATA"))
        assert result is None

    def test_evidence_combines_both_sources(self):
        result = irrigation_decision(weather(["RAIN_EXPECTED"]), soil(["ADEQUATE_MOISTURE"]))
        assert "rainfall_mm=10" in result["evidence"]
        assert "soil_moisture_pct=50" in result["evidence"]


class TestMarketDecision:
    def test_price_above_trend_suggests_selling(self):
        result = market_decision(market(["PRICE_ABOVE_TREND"]))
        assert result["recommendation"] == "CONSIDER_SELLING"

    def test_price_below_trend_suggests_holding(self):
        result = market_decision(market(["PRICE_BELOW_TREND"]))
        assert result["recommendation"] == "HOLD_AND_MONITOR"
        assert result["priority"] == "LOW"

    def test_no_flags_suggests_monitoring(self):
        result = market_decision(market([]))
        assert result["recommendation"] == "MONITOR_MARKET"

    def test_missing_data_returns_none(self):
        result = market_decision(market(status="NO_DATA"))
        assert result is None


class TestCropRiskDecision:
    def test_high_humidity_triggers_risk(self):
        result = crop_risk_decision(weather(["HIGH_HUMIDITY"]), soil([]))
        assert result is not None
        assert "high humidity (fungal disease risk)" in result["risk_signals"]

    def test_ph_out_of_range_triggers_risk(self):
        result = crop_risk_decision(weather([]), soil(["PH_OUT_OF_RANGE"]))
        assert result is not None
        assert "soil pH out of optimal range" in result["risk_signals"]

    def test_no_risk_signals_returns_none(self):
        result = crop_risk_decision(weather([]), soil([]))
        assert result is None

    def test_missing_weather_returns_none(self):
        result = crop_risk_decision(weather(status="NO_DATA"), soil(["PH_OUT_OF_RANGE"]))
        assert result is None

    def test_multiple_risk_signals_all_captured(self):
        result = crop_risk_decision(
            weather(["HIGH_HUMIDITY"]), soil(["PH_OUT_OF_RANGE", "LOW_NITROGEN"])
        )
        assert len(result["risk_signals"]) == 3


class TestBuildRecommendations:
    def test_sorted_by_priority_high_first(self):
        results = build_recommendations(
            weather([]), soil(["LOW_MOISTURE"]), market(["PRICE_ABOVE_TREND"])
        )
        priorities = [r["priority"] for r in results]
        # IRRIGATE_NOW (HIGH) should come before MARKET (MEDIUM)
        assert priorities[0] == "HIGH"

    def test_empty_when_all_agents_missing_data(self):
        results = build_recommendations(
            weather(status="NO_DATA"), soil(status="NO_DATA"), market(status="NO_DATA")
        )
        assert results == []

    def test_includes_all_applicable_recommendation_types(self):
        results = build_recommendations(
            weather(["RAIN_EXPECTED", "HIGH_HUMIDITY"]),
            soil(["ADEQUATE_MOISTURE"]),
            market(["PRICE_ABOVE_TREND"]),
        )
        types = {r["recommendation_type"] for r in results}
        assert types == {"IRRIGATION", "MARKET", "CROP_RISK"}
