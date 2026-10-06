"""
Tests for action engine: tier thresholds and recommended actions.
"""
from app.action.engine import compute_tier, generate_alert


class TestTierThresholds:
    def test_red_high_prob_high_impact(self):
        assert compute_tier(0.75, 70) == "RED"

    def test_orange_medium(self):
        assert compute_tier(0.45, 40) == "ORANGE"

    def test_yellow_low_medium(self):
        assert compute_tier(0.20, 20) == "YELLOW"

    def test_green_low(self):
        assert compute_tier(0.05, 5) == "GREEN"

    def test_boundary_orange_not_red(self):
        # Just below RED threshold
        assert compute_tier(0.64, 59) == "ORANGE"


class TestGenerateAlert:
    def test_sikkim_red_alert_has_action(self):
        alert = generate_alert(0.75, 75, "Sikkim", 3.2, 5.8)
        assert alert["tier"] == "RED"
        assert "evacuation" in alert["recommended_action"].lower()
        assert "3.2" in alert["recommended_action"] or "hour" in alert["recommended_action"].lower()

    def test_status_pending(self):
        alert = generate_alert(0.75, 75, "Sikkim", 3, 6)
        assert alert["status"] == "PENDING_VERIFICATION"

    def test_unknown_region_gets_default(self):
        alert = generate_alert(0.80, 80, "UnknownRegion", 2, 4)
        assert alert["tier"] == "RED"
        assert len(alert["recommended_action"]) > 10
