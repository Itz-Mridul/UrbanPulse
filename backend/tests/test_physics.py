"""
Tests for the physics constraints module.
These run without any DB/network dependencies.
"""
import pytest
from app.physics.constraints import (
    rainfall_trigger_exceeded,
    landslide_blockage_plausible,
    flood_wave_travel_time_hours,
    cascade_plausibility_check,
    TerrainParams,
)


class TestRainfallTrigger:
    def test_high_rainfall_triggers(self):
        r = rainfall_trigger_exceeded(190, 420, 32.0)
        assert r.plausible is True
        assert r.confidence_modifier > 0.5

    def test_low_rainfall_no_trigger(self):
        r = rainfall_trigger_exceeded(30, 80, 20.0)
        assert r.plausible is False
        assert r.confidence_modifier < 0.5

    def test_antecedent_saturation_lowers_threshold(self):
        # Same 24h rain, but high 72h antecedent
        r_dry = rainfall_trigger_exceeded(100, 50, 25.0)
        r_wet = rainfall_trigger_exceeded(100, 250, 25.0)
        # Wet antecedent should produce higher confidence modifier
        assert r_wet.confidence_modifier >= r_dry.confidence_modifier


class TestBlockagePlausibility:
    def test_large_debris_blocks(self):
        r = landslide_blockage_plausible(1_500_000, 120, 32)
        assert r.plausible is True

    def test_tiny_debris_does_not_block(self):
        r = landslide_blockage_plausible(1_000, 120, 32)
        assert r.plausible is False

    def test_zero_volume(self):
        r = landslide_blockage_plausible(0, 120, 32)
        assert r.plausible is False
        assert r.confidence_modifier <= 0.1


class TestFloodTravelTime:
    def test_returns_valid_range(self):
        min_h, max_h = flood_wave_travel_time_hours(45, 32, 120)
        assert min_h > 0
        assert max_h > min_h
        assert min_h < 24  # should arrive same day for 45km

    def test_longer_valley_takes_longer(self):
        min_short, _ = flood_wave_travel_time_hours(20, 32, 120)
        min_long, _ = flood_wave_travel_time_hours(80, 32, 120)
        assert min_long > min_short


class TestCascadePlausibility:
    def test_sikkim_scenario_feasible(self):
        terrain = TerrainParams(
            slope_degrees=32, channel_width_m=120,
            valley_length_km=45, debris_volume_m3=1_500_000,
        )
        result = cascade_plausibility_check(190, 420, terrain)
        assert result["cascade_physically_feasible"] is True
        assert result["overall_physics_confidence"] > 0.4
        assert result["flood_travel_time"]["min_hours"] > 0

    def test_dry_scenario_infeasible(self):
        terrain = TerrainParams(
            slope_degrees=15, channel_width_m=120,
            valley_length_km=45, debris_volume_m3=1_000,
        )
        result = cascade_plausibility_check(20, 60, terrain)
        assert result["cascade_physically_feasible"] is False
        assert result["overall_physics_confidence"] < 0.3
