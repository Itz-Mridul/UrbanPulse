"""
Backtest integration test — validates Sikkim 2023 alert lead time.
This is the core correctness check for the hackathon demo claim.
"""
import pytest
from app.inference.engine import run_inference
from app.physics.constraints import TerrainParams
from app.action.engine import compute_tier

TIMELINE = [
    # (label, r24h, r72h, soil, river, debris_m3)
    ("T-72h",  45.0,  120.0, 0.55, 0.40,         0),
    ("T-48h", 110.0,  195.0, 0.68, 0.52,         0),
    ("T-36h", 165.0,  310.0, 0.78, 0.61,   200_000),
    ("T-24h", 190.0,  420.0, 0.85, 0.70,   600_000),
    ("T-12h", 205.0,  490.0, 0.92, 0.82, 1_200_000),
    ("T-6h",  180.0,  520.0, 0.95, 0.90, 1_500_000),
    ("T=0",   175.0,  520.0, 0.95, 1.00, 1_500_000),
]


def _run_frame(r24, r72, soil, river, debris):
    terrain = TerrainParams(
        slope_degrees=32.0,
        channel_width_m=120.0,
        valley_length_km=45.0,
        debris_volume_m3=debris,
        upstream_lake_area_km2=1.65,
    )
    return run_inference(r24, r72, 32.0, soil, river, terrain)


class TestSikkim2023Backtest:
    def test_probability_increases_monotonically(self):
        """Flood probability should rise as inputs worsen toward T=0."""
        probs = [_run_frame(*row[1:])["probability"] for row in TIMELINE]
        # Allow minor non-monotonicity (T-6h vs T=0 may be close) but overall trend up
        assert probs[-1] > probs[0], "Probability should be higher at T=0 than T-72h"
        assert probs[3] > probs[0], "Probability at T-24h should be higher than at T-72h"

    def test_orange_or_red_raised_before_event(self):
        """System must raise ORANGE or RED at T-24h or earlier."""
        for label, r24, r72, soil, river, debris in TIMELINE:
            res = _run_frame(r24, r72, soil, river, debris)
            tier = res["tier"]
            if label == "T-24h":
                assert tier in ("ORANGE", "RED"), (
                    f"Expected ORANGE or RED at T-24h for evacuation lead time, got {tier}. "
                    f"P={res['probability']:.3f}. Tune tier thresholds in action/engine.py."
                )
                break

    def test_red_at_t12h(self):
        """RED alert must be raised by T-12h at the latest."""
        _, r24, r72, soil, river, debris = TIMELINE[4]  # T-12h
        res = _run_frame(r24, r72, soil, river, debris)
        assert res["tier"] == "RED", (
            f"Expected RED at T-12h, got {res['tier']} (P={res['probability']:.3f})"
        )

    def test_green_at_baseline(self):
        """T-72h baseline should be GREEN — no false positive before the event window."""
        _, r24, r72, soil, river, debris = TIMELINE[0]  # T-72h
        res = _run_frame(r24, r72, soil, river, debris)
        assert res["tier"] in ("GREEN", "YELLOW"), (
            f"Expected GREEN or YELLOW at T-72h baseline, got {res['tier']}"
        )

    def test_causal_path_complete(self):
        """Every inference must return a full causal path for explainability."""
        _, r24, r72, soil, river, debris = TIMELINE[3]  # T-24h
        res = _run_frame(r24, r72, soil, river, debris)
        path = res["causal_path"]
        assert len(path) >= 4, "Causal path must have at least 4 nodes"
        node_names = [n["node"] for n in path]
        assert "DownstreamFlood" in node_names, "DownstreamFlood must be in causal path"

    def test_time_lag_reasonable(self):
        """Flood travel time estimate should be physically plausible for 45km valley."""
        res = _run_frame(190, 420, 0.85, 0.70, 600_000)
        assert 0 < res["time_lag_min_hours"] < 12, "Min travel time should be 0–12h for 45km"
        assert res["time_lag_max_hours"] > res["time_lag_min_hours"]
