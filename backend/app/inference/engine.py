"""
Cascade Intelligence Engine — Bayesian Network inference.

Architecture:
  - Structure (DAG): defined here from domain knowledge + physics constraints
  - CPDs: learned from historical data, seeded with physics-informed priors
  - Inference: Variable Elimination (exact), falls back to sampling for large nets

Causal graph (MVP):
  Rainfall_Intensity → Landslide_Probability
  Soil_Saturation    → Landslide_Probability
  Slope_Angle        → Landslide_Probability
  Landslide_Probability → River_Blockage
  River_Blockage     → Downstream_Flood
  River_Level        → Downstream_Flood

  (Nodes are discretised to L/M/H for pgmpy BayesianNetwork)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

import numpy as np
from loguru import logger

try:
    from pgmpy.models import BayesianNetwork
    from pgmpy.factors.discrete import TabularCPD
    from pgmpy.inference import VariableElimination
    PGMPY_AVAILABLE = True
except ImportError:
    PGMPY_AVAILABLE = False
    logger.warning("pgmpy not installed — cascade engine will run in mock mode.")

from app.physics.constraints import (
    cascade_plausibility_check,
    TerrainParams,
)


# ---------------------------------------------------------------------------
# Discretisation bins (L=Low, M=Medium, H=High)
# ---------------------------------------------------------------------------
# All continuous inputs are discretised before entering the BN
RAIN_BINS = [0, 50, 150, 9999]       # mm/24h: L=[0,50), M=[50,150), H=≥150
SLOPE_BINS = [0, 15, 30, 90]         # degrees: L, M, H
SOIL_BINS = [0.0, 0.4, 0.7, 1.0]    # saturation index 0–1: L, M, H
RIVER_BINS = [0, 0.4, 0.7, 1.0]     # normalised river level 0–1: L, M, H


def _discretise(value: float, bins: list[float]) -> int:
    """Map a continuous value to a 0-indexed bin (0=Low, 1=Medium, 2=High)."""
    for i, upper in enumerate(bins[1:], start=0):
        if value < upper:
            return i
    return len(bins) - 2  # clip to highest bin


# ---------------------------------------------------------------------------
# Network definition
# ---------------------------------------------------------------------------

def _build_network() -> Optional["BayesianNetwork"]:  # type: ignore[return]
    if not PGMPY_AVAILABLE:
        return None

    model = BayesianNetwork([
        ("Rainfall", "LandslideProbability"),
        ("SoilSaturation", "LandslideProbability"),
        ("Slope", "LandslideProbability"),
        ("LandslideProbability", "RiverBlockage"),
        ("RiverBlockage", "DownstreamFlood"),
        ("RiverLevel", "DownstreamFlood"),
    ])

    # ------------------------------------------------------------------
    # Prior CPDs — physics-informed, not arbitrary
    # Each CPD is a TabularCPD(variable, card, values, evidence, evidence_card)
    # card = number of states (3: L/M/H)
    # ------------------------------------------------------------------

    # Rainfall: marginal, seasonal Himalayan prior
    cpd_rain = TabularCPD("Rainfall", 3, [[0.50], [0.30], [0.20]])

    # Soil saturation: marginal
    cpd_soil = TabularCPD("SoilSaturation", 3, [[0.45], [0.35], [0.20]])

    # Slope: terrain-specific prior (Himalayan valleys are steep)
    cpd_slope = TabularCPD("Slope", 3, [[0.20], [0.45], [0.35]])

    # River level: marginal, correlated with monsoon but modelled independently
    cpd_river = TabularCPD("RiverLevel", 3, [[0.50], [0.30], [0.20]])

    # LandslideProbability | Rainfall, SoilSaturation, Slope
    # 3^3 = 27 parent combinations → 3 states × 27 = shape (3, 27)
    # Values derived from Himalayan landslide literature and physics constraints
    # Ordering: Rainfall iterates slowest, Slope fastest (pgmpy column ordering)
    ls_values = _build_landslide_cpd()
    cpd_landslide = TabularCPD(
        "LandslideProbability", 3, ls_values,
        evidence=["Rainfall", "SoilSaturation", "Slope"],
        evidence_card=[3, 3, 3],
    )

    # RiverBlockage | LandslideProbability
    # Low landslide → very unlikely blockage; High → more likely
    cpd_blockage = TabularCPD(
        "RiverBlockage", 3,
        [
            [0.90, 0.35, 0.10],   # P(blockage=L | landslide L/M/H)
            [0.08, 0.45, 0.30],   # P(blockage=M | …)
            [0.02, 0.20, 0.60],   # P(blockage=H | …)
        ],
        evidence=["LandslideProbability"],
        evidence_card=[3],
    )

    # DownstreamFlood | RiverBlockage, RiverLevel
    # 3×3 = 9 parent combos → shape (3, 9)
    cpd_flood = TabularCPD(
        "DownstreamFlood", 3,
        _build_flood_cpd(),
        evidence=["RiverBlockage", "RiverLevel"],
        evidence_card=[3, 3],
    )

    model.add_cpds(cpd_rain, cpd_soil, cpd_slope, cpd_river,
                   cpd_landslide, cpd_blockage, cpd_flood)

    assert model.check_model(), "Bayesian Network is inconsistent!"
    return model


def _build_landslide_cpd() -> list[list[float]]:
    """
    Build the 3×27 CPD matrix for LandslideProbability.

    Physics insight: landslide probability is HIGH only when at least two of
    {Rainfall=H, SoilSaturation=H, Slope=H} are met (redundant safety principle).
    """
    # Enumerate all 27 parent combos: Rain in {0,1,2} × Soil × Slope
    low_row, med_row, high_row = [], [], []
    for rain in range(3):
        for soil in range(3):
            for slope in range(3):
                # Count how many factors are at HIGH level
                high_count = sum(x == 2 for x in [rain, soil, slope])
                med_count = sum(x == 1 for x in [rain, soil, slope])

                if high_count >= 2:
                    p_high, p_med, p_low = 0.70, 0.20, 0.10
                elif high_count == 1 and med_count >= 1:
                    p_high, p_med, p_low = 0.35, 0.40, 0.25
                elif med_count >= 2:
                    p_high, p_med, p_low = 0.15, 0.50, 0.35
                elif high_count == 1:
                    p_high, p_med, p_low = 0.20, 0.35, 0.45
                elif med_count == 1:
                    p_high, p_med, p_low = 0.05, 0.25, 0.70
                else:
                    p_high, p_med, p_low = 0.01, 0.09, 0.90

                low_row.append(p_low)
                med_row.append(p_med)
                high_row.append(p_high)

    return [low_row, med_row, high_row]


def _build_flood_cpd() -> list[list[float]]:
    """
    Build the 3×9 CPD matrix for DownstreamFlood.

    Blockage increases flood risk independent of current river level;
    high river level amplifies it.
    """
    low_row, med_row, high_row = [], [], []
    for blockage in range(3):
        for river in range(3):
            if blockage == 2 and river == 2:
                p_h, p_m, p_l = 0.80, 0.15, 0.05
            elif blockage == 2:
                p_h, p_m, p_l = 0.55 + river * 0.1, 0.30, 0.15 - river * 0.05
            elif blockage == 1 and river == 2:
                p_h, p_m, p_l = 0.40, 0.40, 0.20
            elif blockage == 1:
                p_h, p_m, p_l = 0.15, 0.45, 0.40
            elif river == 2:
                p_h, p_m, p_l = 0.20, 0.40, 0.40
            elif river == 1:
                p_h, p_m, p_l = 0.05, 0.25, 0.70
            else:
                p_h, p_m, p_l = 0.01, 0.09, 0.90

            low_row.append(p_l)
            med_row.append(p_m)
            high_row.append(p_h)

    return [low_row, med_row, high_row]


# ---------------------------------------------------------------------------
# Singleton network
# ---------------------------------------------------------------------------
_network: Optional["BayesianNetwork"] = None  # type: ignore[assignment]
_inference_engine: Optional["VariableElimination"] = None  # type: ignore[assignment]


def get_inference_engine():
    global _network, _inference_engine
    if _network is None:
        _network = _build_network()
        if _network:
            _inference_engine = VariableElimination(_network)
    return _inference_engine


# ---------------------------------------------------------------------------
# Main inference call
# ---------------------------------------------------------------------------

def run_inference(
    rainfall_24h_mm: float,
    rainfall_72h_mm: float,
    slope_degrees: float,
    soil_saturation: float,        # 0–1
    river_level_normalised: float, # 0–1
    terrain: TerrainParams,
    soil_type: str = "MIXED",
) -> dict[str, Any]:
    """
    Run the full cascade inference pipeline.

    Returns a dict with:
      - probability: P(DownstreamFlood=HIGH)
      - time_lag_min_hours / time_lag_max_hours
      - causal_path: list of {node, state_probs, evidence} for explainability
      - physics: the raw physics constraint outputs
      - alert_level: heuristic tier (GREEN/YELLOW/ORANGE/RED)
    """
    # Step 1: Physics constraints
    physics = cascade_plausibility_check(
        rainfall_24h_mm, rainfall_72h_mm, terrain, soil_type
    )

    # Step 2: Discretise inputs
    rain_state = _discretise(rainfall_24h_mm, RAIN_BINS)
    slope_state = _discretise(slope_degrees, SLOPE_BINS)
    soil_state = _discretise(soil_saturation, SOIL_BINS)
    river_state = _discretise(river_level_normalised, RIVER_BINS)

    # Step 3: Bayesian inference
    ie = get_inference_engine()
    if ie is not None:
        evidence = {
            "Rainfall": rain_state,
            "Slope": slope_state,
            "SoilSaturation": soil_state,
            "RiverLevel": river_state,
        }

        flood_q = ie.query(["DownstreamFlood"], evidence=evidence, show_progress=False)
        blockage_q = ie.query(["RiverBlockage"], evidence=evidence, show_progress=False)
        landslide_q = ie.query(["LandslideProbability"], evidence=evidence, show_progress=False)

        p_flood_high = float(flood_q.values[2])    # P(flood=HIGH)
        p_blockage_high = float(blockage_q.values[2])
        p_landslide_high = float(landslide_q.values[2])
    else:
        # Mock mode: physics-based fallback
        p_flood_high = min(0.95, physics["overall_physics_confidence"] * 0.8)
        p_blockage_high = min(0.90, physics["landslide_blockage"]["confidence_modifier"])
        p_landslide_high = min(0.85, physics["rainfall_trigger"]["confidence_modifier"])

    # Step 4: Apply physics confidence modifier
    adjusted_probability = p_flood_high * physics["overall_physics_confidence"]
    adjusted_probability = round(min(1.0, max(0.0, adjusted_probability)), 4)

    # Step 5: Causal path for explainability
    causal_path = [
        {
            "node": "Rainfall",
            "label": f"Rainfall ({rainfall_24h_mm:.0f} mm/24h)",
            "probability": round(rainfall_24h_mm / max(RAIN_BINS[2], 1), 3),
            "state": ["LOW", "MEDIUM", "HIGH"][rain_state],
        },
        {
            "node": "SoilSaturation",
            "label": f"Soil Saturation ({soil_saturation:.0%})",
            "probability": soil_saturation,
            "state": ["LOW", "MEDIUM", "HIGH"][soil_state],
        },
        {
            "node": "LandslideProbability",
            "label": "Landslide Trigger",
            "probability": round(p_landslide_high, 4),
            "state": "HIGH" if p_landslide_high > 0.5 else "MEDIUM" if p_landslide_high > 0.2 else "LOW",
        },
        {
            "node": "RiverBlockage",
            "label": "River Blockage",
            "probability": round(p_blockage_high, 4),
            "state": "HIGH" if p_blockage_high > 0.5 else "MEDIUM" if p_blockage_high > 0.2 else "LOW",
        },
        {
            "node": "DownstreamFlood",
            "label": "Downstream Flood",
            "probability": round(adjusted_probability, 4),
            "state": "HIGH" if adjusted_probability > 0.6 else "MEDIUM" if adjusted_probability > 0.3 else "LOW",
        },
    ]

    # Step 6: Alert tier
    tier = _probability_to_tier(adjusted_probability)

    return {
        "probability": adjusted_probability,
        "time_lag_min_hours": physics["flood_travel_time"]["min_hours"],
        "time_lag_max_hours": physics["flood_travel_time"]["max_hours"],
        "causal_path": causal_path,
        "physics": physics,
        "tier": tier,
        "raw_bayesian_p_flood": round(p_flood_high, 4),
        "physics_confidence_modifier": physics["overall_physics_confidence"],
    }


def _probability_to_tier(p: float) -> str:
    if p < 0.15:
        return "GREEN"
    elif p < 0.40:
        return "YELLOW"
    elif p < 0.65:
        return "ORANGE"
    else:
        return "RED"
