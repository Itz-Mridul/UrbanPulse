"""
Action Engine — converts (probability, impact_score) → tiered alert + recommended action.

Alert tiers: GREEN | YELLOW | ORANGE | RED
Recommended actions are region/tier specific and stored as template strings.
"""
from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Tier thresholds
# ---------------------------------------------------------------------------
# (probability, impact_score) → tier
# Both conditions must be met or the higher tier is used if either is exceeded.

TIER_THRESHOLDS = {
    #  (min_prob, min_impact)
    "RED":    (0.65, 60),
    "ORANGE": (0.40, 35),
    "YELLOW": (0.15, 15),
    "GREEN":  (0.00,  0),
}


def compute_tier(probability: float, impact_score: float) -> str:
    """Determine alert tier from probability and impact score."""
    for tier, (min_p, min_i) in TIER_THRESHOLDS.items():
        if probability >= min_p and impact_score >= min_i:
            return tier
    return "GREEN"


# ---------------------------------------------------------------------------
# Recommended action templates
# Per-region, per-tier. Keyed by (region_name, tier).
# ---------------------------------------------------------------------------

ACTION_TEMPLATES: dict[tuple[str, str], str] = {
    # Sikkim / Teesta Valley
    ("Sikkim", "RED"): (
        "IMMEDIATE: Issue evacuation order for downstream settlements in South Sikkim district "
        "between Singtam and Rangpo. Close NH-10 (Teesta riverside sections). "
        "Activate Rangpo Emergency Shelter (capacity 800). "
        "Alert SDMA Sikkim and notify NDRF team stationed at Gangtok. "
        "Estimated flood wave arrival: {min_h}–{max_h} hours."
    ),
    ("Sikkim", "ORANGE"): (
        "ADVISORY: Pre-position evacuation transport for communities within 500m of Teesta riverbank "
        "between Chungthang and Singtam. "
        "Prepare Rangpo Emergency Shelter. Alert district administration. "
        "Monitor river level gauges at Dikchu and Singtam every 30 minutes. "
        "Estimated window before elevated risk: {min_h}–{max_h} hours."
    ),
    ("Sikkim", "YELLOW"): (
        "WATCH: Elevated cascade risk detected. "
        "Advise communities in Teesta flood plain to review evacuation routes. "
        "District SDMAs to check readiness of emergency shelters. "
        "Continue monitoring rainfall and river levels."
    ),
    ("Sikkim", "GREEN"): (
        "NORMAL: No cascade trigger detected. Routine monitoring continues."
    ),
    # Kedarnath / Mandakini Valley
    ("Kedarnath", "RED"): (
        "IMMEDIATE: Evacuate all pilgrims and residents from Kedarnath valley floor. "
        "Close Rishikesh–Gangotri highway at Rudraprayag. "
        "Alert SDMA Uttarakhand and Char Dham Relief Camp. "
        "Estimated flood wave arrival: {min_h}–{max_h} hours."
    ),
    ("Kedarnath", "ORANGE"): (
        "ADVISORY: Restrict new pilgrim entry to Kedarnath. "
        "Pre-position NDRF teams at Rudraprayag. "
        "Monitor Mandakini gauge at Sonprayag every 30 minutes."
    ),
    ("Kedarnath", "YELLOW"): "WATCH: Elevated risk — monitor IMD alerts closely.",
    ("Kedarnath", "GREEN"): "NORMAL: Routine monitoring continues.",
}

_DEFAULT_ACTIONS: dict[str, str] = {
    "RED": (
        "IMMEDIATE: Issue evacuation order for downstream settlements. "
        "Close riverside roads. Activate emergency shelters. "
        "Alert SDMA/NDMA. Estimated flood wave: {min_h}–{max_h} hours."
    ),
    "ORANGE": (
        "ADVISORY: Pre-position evacuation transport. "
        "Alert district administration. Monitor river gauges every 30 minutes. "
        "Expected risk window: {min_h}–{max_h} hours."
    ),
    "YELLOW": "WATCH: Elevated cascade risk. Review evacuation plans. Continuous monitoring.",
    "GREEN": "NORMAL: No cascade trigger. Routine monitoring continues.",
}


def generate_recommended_action(
    tier: str,
    region_name: str,
    time_lag_min_hours: float,
    time_lag_max_hours: float,
) -> str:
    """Return a filled recommended-action string for the given region and tier."""
    template = ACTION_TEMPLATES.get(
        (region_name, tier),
        _DEFAULT_ACTIONS.get(tier, "Monitor situation."),
    )
    return template.format(
        min_h=round(time_lag_min_hours, 1),
        max_h=round(time_lag_max_hours, 1),
    )


def generate_alert(
    probability: float,
    impact_score: float,
    region_name: str,
    time_lag_min_hours: float,
    time_lag_max_hours: float,
) -> dict[str, Any]:
    """
    Full action engine output: tier + recommended action.

    Returns a dict ready for persisting to the alerts table.
    """
    tier = compute_tier(probability, impact_score)
    action = generate_recommended_action(
        tier, region_name, time_lag_min_hours, time_lag_max_hours
    )
    return {
        "tier": tier,
        "recommended_action": action,
        "probability": probability,
        "impact_score": impact_score,
        "status": "PENDING_VERIFICATION",
    }
