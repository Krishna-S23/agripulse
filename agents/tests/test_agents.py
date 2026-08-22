import sys
import os
from pathlib import Path

os.environ["AGRIPULSE_MOCK_DATA"] = "1"
sys.path.append(str(Path(__file__).parent.parent))

from weather_agent import get_weather_signal
from soil_agent import get_soil_signal
from market_agent import get_market_signal


class TestWeatherAgent:
    def test_known_district_returns_ok(self):
        result = get_weather_signal("Coimbatore")
        assert result["status"] == "OK"
        assert result["district"] == "Coimbatore"

    def test_flags_rain_expected_when_high_probability(self):
        # fixture has rain_prob_pct=78 for Coimbatore's latest row
        result = get_weather_signal("Coimbatore")
        assert "RAIN_EXPECTED" in result["flags"]

    def test_flags_high_humidity(self):
        result = get_weather_signal("Coimbatore")
        assert "HIGH_HUMIDITY" in result["flags"]

    def test_low_risk_district_has_fewer_flags(self):
        # Erode fixture: low rain probability, moderate humidity
        result = get_weather_signal("Erode")
        assert result["status"] == "OK"
        assert "RAIN_EXPECTED" not in result["flags"]

    def test_unknown_district_returns_no_data(self):
        result = get_weather_signal("Nonexistent District")
        assert result["status"] == "NO_DATA"
        assert result["evidence"] == []

    def test_evidence_list_is_populated(self):
        result = get_weather_signal("Coimbatore")
        assert len(result["evidence"]) == 4
        assert all("=" in e for e in result["evidence"])


class TestSoilAgent:
    def test_known_farm_returns_ok(self):
        result = get_soil_signal("F001")
        assert result["status"] == "OK"
        assert result["farm_id"] == "F001"

    def test_adequate_moisture_flag(self):
        # F001 fixture: moisture=61.4 -> above ADEQUATE_MOISTURE threshold (55)
        result = get_soil_signal("F001")
        assert "ADEQUATE_MOISTURE" in result["flags"]

    def test_low_moisture_and_low_nitrogen_flag(self):
        # F002 fixture: moisture=38.2 (below 55, above 35 -> no flag),
        # F008 fixture: moisture=29.5 -> LOW_MOISTURE, nitrogen=Low -> LOW_NITROGEN
        result = get_soil_signal("F008")
        assert "LOW_MOISTURE" in result["flags"]
        assert "LOW_NITROGEN" in result["flags"]

    def test_unknown_farm_returns_no_data(self):
        result = get_soil_signal("F999")
        assert result["status"] == "NO_DATA"


class TestMarketAgent:
    def test_known_crop_district_returns_ok(self):
        result = get_market_signal("Tomato", "Coimbatore")
        assert result["status"] == "OK"

    def test_price_above_trend_flag(self):
        # Tomato fixture: pct_change_vs_prior_week=11.1 (>= 8 threshold)
        result = get_market_signal("Tomato", "Coimbatore")
        assert "PRICE_ABOVE_TREND" in result["flags"]

    def test_price_below_trend_flag(self):
        # Onion fixture: pct_change_vs_prior_week=-4.1 (does not cross -8 threshold)
        result = get_market_signal("Onion", "Coimbatore")
        assert "PRICE_ABOVE_TREND" not in result["flags"]
        assert "PRICE_BELOW_TREND" not in result["flags"]

    def test_unknown_crop_returns_no_data(self):
        result = get_market_signal("Wheat", "Coimbatore")
        assert result["status"] == "NO_DATA"
