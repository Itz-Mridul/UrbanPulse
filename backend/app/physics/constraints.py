"""
Physics-informed constraints for cascading hazard modelling.

These are established geophysical equations that constrain the causal structure
of the Bayesian network — the AI/ML layer calibrates probabilities on top of
these physically-grounded constraints.

Refs:
  - Herschel-Bulkley / Voellmy dam-break runout: Hungr (1995)
  - GLOF propagation time: Huss et al. (2007), adapted for Sikkim Teesta basin
  - Critical blockage threshold: Korup (2002) log-linear relationship
"""
import math
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class TerrainParams:
    """Topographic and channel parameters for a river reach."""
    slope_degrees: float          # average channel slope (degrees)
    channel_width_m: float        # bankfull channel width (m)
    valley_length_km: float       # distance from blockage to downstream settlement (km)
    channel_roughness: float = 0.04  # Manning's n — default for mountain streams
    debris_volume_m3: float = 0.0    # estimated debris/landslide volume (m3)
    upstream_lake_area_km2: float = 0.0  # if a GLOF scenario, upstream proglacial lake area


@dataclass
class PhysicsConstraint:
    """Output of a physics check — whether a causal link is physically plausible."""
    plausible: bool
    confidence_modifier: float  # multiplicative factor applied to ML probability (0–1)
    reason: str


# ---------------------------------------------------------------------------
# 1. Landslide dam-blockage plausibility
# ---------------------------------------------------------------------------

def landslide_blockage_plausible(
    debris_volume_m3: float,
    channel_width_m: float,
    slope_degrees: float,
) -> PhysicsConstraint:
    """
    Check whether a landslide of given volume plausibly blocks a channel.

    Uses Korup (2002) log-linear discriminant:
        log10(V) > 1.5 * log10(W) + 0.8   →  blockage likely

    Args:
        debris_volume_m3: Volume of the landslide/debris flow (m³).
        channel_width_m: Bankfull channel width at the blockage point (m).
        slope_degrees: Channel slope at blockage point (degrees).

    Returns:
        PhysicsConstraint with plausibility flag and confidence modifier.
    """
    if debris_volume_m3 <= 0 or channel_width_m <= 0:
        return PhysicsConstraint(
            plausible=False,
            confidence_modifier=0.1,
            reason="Insufficient debris volume or invalid channel width.",
        )

    # Korup (2002) threshold
    log_v = math.log10(debris_volume_m3)
    log_w = math.log10(channel_width_m)
    threshold = 1.5 * log_w + 0.8

    # Steep channels drain faster — reduce blockage persistence
    slope_penalty = max(0.3, 1.0 - (slope_degrees - 10) * 0.02) if slope_degrees > 10 else 1.0

    if log_v >= threshold:
        confidence_modifier = min(1.0, slope_penalty)
        return PhysicsConstraint(
            plausible=True,
            confidence_modifier=confidence_modifier,
            reason=(
                f"Blockage physically plausible: log₁₀(V)={log_v:.2f} ≥ threshold {threshold:.2f}. "
                f"Slope penalty factor: {slope_penalty:.2f}."
            ),
        )
    else:
        deficit = threshold - log_v
        # Partial plausibility if close to threshold
        confidence_modifier = max(0.1, 1.0 - deficit * 0.5) * slope_penalty
        return PhysicsConstraint(
            plausible=deficit < 0.5,
            confidence_modifier=confidence_modifier,
            reason=(
                f"Blockage marginally {'plausible' if deficit < 0.5 else 'implausible'}: "
                f"log₁₀(V)={log_v:.2f} vs threshold {threshold:.2f} (deficit={deficit:.2f})."
            ),
        )


# ---------------------------------------------------------------------------
# 2. GLOF / dam-break flood wave travel time
# ---------------------------------------------------------------------------

def flood_wave_travel_time_hours(
    valley_length_km: float,
    slope_degrees: float,
    channel_width_m: float,
    peak_discharge_m3s: Optional[float] = None,
) -> tuple[float, float]:
    """
    Estimate time for a dam-break flood wave to travel downstream.

    Uses a simplified kinematic wave speed:
        c = (5/3) * V_mean
    where V_mean is estimated via Manning's equation on a trapezoidal channel.

    Returns (min_hours, max_hours) uncertainty range.

    Args:
        valley_length_km: Distance from blockage to downstream point (km).
        slope_degrees: Average valley slope (degrees).
        channel_width_m: Channel width (m).
        peak_discharge_m3s: Optional estimated peak discharge for Manning check.

    Returns:
        Tuple of (min_travel_hours, max_travel_hours).
    """
    slope_frac = math.tan(math.radians(slope_degrees))
    if slope_frac <= 0:
        slope_frac = 0.001  # flat valley floor minimum

    n = 0.04  # Manning's n for mountain streams
    # Hydraulic radius approximation: R ≈ d/2 for wide channels
    # Estimate flow depth from Manning: V = (1/n) * R^(2/3) * S^(1/2)
    # We don't know depth directly, so use empirical flood-wave celerity
    # based on slope and channel width (after Huss et al. 2007):
    # c [m/s] ≈ 0.7 * S^0.5 * W^0.25
    celerity_ms = 0.7 * math.sqrt(slope_frac) * (channel_width_m ** 0.25)
    celerity_ms = max(0.5, min(celerity_ms, 15.0))  # physical bounds

    distance_m = valley_length_km * 1000
    travel_time_s = distance_m / celerity_ms

    # Uncertainty range: ±40% (typical for GLOF travel time estimates)
    min_hours = travel_time_s * 0.6 / 3600
    max_hours = travel_time_s * 1.4 / 3600

    return round(min_hours, 2), round(max_hours, 2)


# ---------------------------------------------------------------------------
# 3. Rainfall → landslide trigger threshold
# ---------------------------------------------------------------------------

def rainfall_trigger_exceeded(
    rainfall_24h_mm: float,
    rainfall_72h_mm: float,
    slope_degrees: float,
    soil_type: str = "MIXED",
) -> PhysicsConstraint:
    """
    Check whether rainfall intensity exceeds empirical landslide triggering thresholds.

    Uses the Caine (1980) intensity-duration threshold adapted for Himalayan terrain:
        I > 14.82 * D^(-0.39)   for I in mm/hr, D in hours
    and the Glade et al. antecedent rainfall approach for 72h totals.

    Args:
        rainfall_24h_mm: Cumulative rainfall over 24 hours (mm).
        rainfall_72h_mm: Cumulative rainfall over 72 hours (mm).
        slope_degrees: Slope angle at the potential landslide site.
        soil_type: 'CLAY' | 'SANDY' | 'MIXED' — affects threshold.

    Returns:
        PhysicsConstraint.
    """
    # Himalayan Caine threshold for 24h (intensity = mm/24)
    intensity_24h = rainfall_24h_mm / 24.0
    caine_threshold = 14.82 * (24 ** -0.39)  # ≈ 4.4 mm/hr for 24h duration

    # Soil type modifiers
    soil_modifiers = {"CLAY": 0.7, "SANDY": 1.2, "MIXED": 1.0}
    mod = soil_modifiers.get(soil_type.upper(), 1.0)
    caine_threshold *= mod

    # Slope modifier: steep slopes fail at lower thresholds
    if slope_degrees > 35:
        caine_threshold *= 0.6
    elif slope_degrees > 25:
        caine_threshold *= 0.8

    # Antecedent saturation proxy: 72h total > 200mm raises susceptibility
    antecedent_factor = 1.3 if rainfall_72h_mm > 200 else 1.0

    effective_threshold = caine_threshold / antecedent_factor

    ratio = intensity_24h / effective_threshold

    if ratio >= 1.0:
        return PhysicsConstraint(
            plausible=True,
            confidence_modifier=min(1.0, ratio),
            reason=(
                f"Rainfall threshold exceeded: {intensity_24h:.2f} mm/hr > "
                f"threshold {effective_threshold:.2f} mm/hr (ratio={ratio:.2f}). "
                f"Antecedent factor={antecedent_factor:.1f}, soil={soil_type}."
            ),
        )
    else:
        return PhysicsConstraint(
            plausible=False,
            confidence_modifier=max(0.05, ratio * 0.8),
            reason=(
                f"Rainfall below trigger threshold: {intensity_24h:.2f} mm/hr < "
                f"{effective_threshold:.2f} mm/hr (ratio={ratio:.2f})."
            ),
        )


# ---------------------------------------------------------------------------
# 4. Combined cascade plausibility check
# ---------------------------------------------------------------------------

def cascade_plausibility_check(
    rainfall_24h_mm: float,
    rainfall_72h_mm: float,
    terrain: TerrainParams,
    soil_type: str = "MIXED",
) -> dict:
    """
    Run all physics checks for the full rain → landslide → blockage → flood cascade.

    Returns a dict summarising each step's physical plausibility and an overall
    confidence modifier for the Bayesian network.
    """
    rain_check = rainfall_trigger_exceeded(
        rainfall_24h_mm, rainfall_72h_mm, terrain.slope_degrees, soil_type
    )
    blockage_check = landslide_blockage_plausible(
        terrain.debris_volume_m3, terrain.channel_width_m, terrain.slope_degrees
    )
    travel_min, travel_max = flood_wave_travel_time_hours(
        terrain.valley_length_km, terrain.slope_degrees, terrain.channel_width_m
    )

    overall_modifier = (
        rain_check.confidence_modifier
        * blockage_check.confidence_modifier
    )

    return {
        "rainfall_trigger": {
            "plausible": rain_check.plausible,
            "confidence_modifier": rain_check.confidence_modifier,
            "reason": rain_check.reason,
        },
        "landslide_blockage": {
            "plausible": blockage_check.plausible,
            "confidence_modifier": blockage_check.confidence_modifier,
            "reason": blockage_check.reason,
        },
        "flood_travel_time": {
            "min_hours": travel_min,
            "max_hours": travel_max,
        },
        "overall_physics_confidence": round(overall_modifier, 3),
        "cascade_physically_feasible": rain_check.plausible and blockage_check.plausible,
    }
