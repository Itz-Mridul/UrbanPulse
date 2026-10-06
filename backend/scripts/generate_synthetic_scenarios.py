"""
Synthetic Scenario Generator
==============================
Generates physically-plausible cascade scenarios for CPD calibration
when real labeled cascade events are scarce (only 2–3 for India).

All generated data is labeled `SYNTHETIC` — never silently mixed with
real historical events. See Q12 in judge_qa.md for the rationale.

Usage:
    python scripts/generate_synthetic_scenarios.py --n 500 --region sikkim
    python scripts/generate_synthetic_scenarios.py --n 200 --region kedarnath
"""
import argparse
import asyncio
import json
import random
import sys
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.physics.constraints import (
    rainfall_trigger_exceeded,
    landslide_blockage_plausible,
    flood_wave_travel_time_hours,
    TerrainParams,
)

# ── Region templates ───────────────────────────────────────────────────────
REGION_PARAMS = {
    "sikkim": {
        "slope_range": (25, 45),
        "channel_width_range": (80, 180),
        "valley_length_range": (30, 60),
        "debris_volume_range": (0, 2_500_000),
        "rainfall_24h_range": (20, 250),
        "rainfall_72h_range": (60, 600),
        "soil_saturation_range": (0.3, 1.0),
        "river_level_range": (0.1, 1.0),
    },
    "kedarnath": {
        "slope_range": (30, 55),
        "channel_width_range": (40, 120),
        "valley_length_range": (15, 40),
        "debris_volume_range": (0, 3_000_000),
        "rainfall_24h_range": (30, 280),
        "rainfall_72h_range": (80, 650),
        "soil_saturation_range": (0.4, 1.0),
        "river_level_range": (0.2, 1.0),
    },
}


@dataclass
class SyntheticScenario:
    scenario_id: int
    region: str
    rainfall_24h_mm: float
    rainfall_72h_mm: float
    slope_degrees: float
    soil_saturation: float
    river_level_normalised: float
    debris_volume_m3: float
    channel_width_m: float
    valley_length_km: float
    # Labels (computed from physics)
    rainfall_triggered: bool
    blockage_plausible: bool
    cascade_occurred: bool   # True if both triggers fire
    flood_prob_physics: float  # Physics-based probability estimate
    flood_travel_time_min_h: float
    flood_travel_time_max_h: float
    # Metadata
    is_synthetic: bool = True
    label_source: str = "PHYSICS_DERIVED"


def sample_scenario(region_key: str, scenario_id: int, rng: random.Random) -> SyntheticScenario:
    """Sample one physically-plausible synthetic scenario."""
    p = REGION_PARAMS[region_key]

    def randu(lo, hi): return rng.uniform(lo, hi)

    slope = randu(*p["slope_range"])
    channel_width = randu(*p["channel_width_range"])
    valley_length = randu(*p["valley_length_range"])
    rainfall_24h = randu(*p["rainfall_24h_range"])
    rainfall_72h = randu(*p["rainfall_72h_range"])
    soil_sat = randu(*p["soil_saturation_range"])
    river_lvl = randu(*p["river_level_range"])

    # Debris volume: correlated with rainfall + slope (more rain + steeper = more debris)
    # Simple physics proxy: exponential scaling
    rain_factor = max(0, (rainfall_24h - 80) / 170)
    slope_factor = max(0, (slope - 20) / 35)
    debris_base = p["debris_volume_range"][1] * rain_factor * slope_factor
    debris = max(0, debris_base * rng.gauss(1.0, 0.4))

    terrain = TerrainParams(
        slope_degrees=slope,
        channel_width_m=channel_width,
        valley_length_km=valley_length,
        debris_volume_m3=debris,
    )

    rain_result = rainfall_trigger_exceeded(rainfall_24h, rainfall_72h, slope)
    blockage_result = landslide_blockage_plausible(debris, channel_width, slope)

    both_triggered = rain_result.plausible and blockage_result.plausible

    # Physics-based flood probability (rough estimate)
    prob = (
        rain_result.confidence_modifier
        * blockage_result.confidence_modifier
        * (0.85 if both_triggered else 0.12)
        * min(1.0, river_lvl + 0.3)  # higher river → higher flood risk
    ) if both_triggered else (
        rain_result.confidence_modifier * 0.1
    )
    prob = min(1.0, max(0.0, prob))

    t_min, t_max = flood_wave_travel_time_hours(valley_length, slope, channel_width)

    return SyntheticScenario(
        scenario_id=scenario_id,
        region=region_key,
        rainfall_24h_mm=round(rainfall_24h, 1),
        rainfall_72h_mm=round(rainfall_72h, 1),
        slope_degrees=round(slope, 1),
        soil_saturation=round(soil_sat, 3),
        river_level_normalised=round(river_lvl, 3),
        debris_volume_m3=round(debris, 0),
        channel_width_m=round(channel_width, 1),
        valley_length_km=round(valley_length, 1),
        rainfall_triggered=rain_result.plausible,
        blockage_plausible=blockage_result.plausible,
        cascade_occurred=both_triggered,
        flood_prob_physics=round(prob, 4),
        flood_travel_time_min_h=round(t_min, 2),
        flood_travel_time_max_h=round(t_max, 2),
    )


def generate(n: int, region_key: str, seed: int = 42) -> list[SyntheticScenario]:
    rng = random.Random(seed)
    scenarios = [sample_scenario(region_key, i, rng) for i in range(n)]

    cascade_count = sum(s.cascade_occurred for s in scenarios)
    print(f"✅ Generated {n} synthetic scenarios for {region_key}")
    print(f"   Cascade events: {cascade_count} ({cascade_count/n*100:.1f}%)")
    print(f"   Non-cascade:    {n-cascade_count} ({(n-cascade_count)/n*100:.1f}%)")
    return scenarios


def save_json(scenarios: list[SyntheticScenario], output_path: str):
    """Save scenarios as JSON for import into the DB or CPD training."""
    data = [vars(s) for s in scenarios]
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "label_source": "PHYSICS_DERIVED",
                "is_synthetic": True,
                "caution": "SYNTHETIC DATA — derived from physics equations (Caine 1980, Korup 2002). "
                           "Not real historical events. Label as SYNTHETIC in all reports and DB inserts.",
                "references": [
                    "Caine, N. (1980). Rainfall intensity-duration control of shallow landslides.",
                    "Korup, O. (2002). Landslide-induced river channel avulsions.",
                ]
            },
            "scenarios": data,
        }, f, indent=2)
    print(f"✅ Saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate synthetic cascade scenarios")
    parser.add_argument("--n", type=int, default=500, help="Number of scenarios")
    parser.add_argument("--region", choices=list(REGION_PARAMS.keys()), default="sikkim")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="data/synthetic")
    args = parser.parse_args()

    scenarios = generate(args.n, args.region, args.seed)
    out = f"{args.output_dir}/{args.region}_synthetic_{args.n}.json"
    save_json(scenarios, out)
    print(f"\n📋 Label summary:")
    print(f"   {sum(s.cascade_occurred for s in scenarios)} positive (cascade) scenarios")
    print(f"   {sum(not s.cascade_occurred for s in scenarios)} negative (no cascade) scenarios")
    print(f"\n   Use these as CPD training data in inference/engine.py:")
    print(f"   python scripts/generate_synthetic_scenarios.py --n 2000 --region sikkim")
    print(f"   python scripts/generate_synthetic_scenarios.py --n 500 --region kedarnath")
