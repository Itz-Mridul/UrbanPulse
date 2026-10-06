"""
Feedback loop API — FR11
==========================
Allows new sensor readings to trigger re-inference on an existing prediction.
A lower river level or reduced rainfall can downgrade a PENDING alert.

Also provides the graceful-degradation health endpoint — FR12.
"""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.inference.engine import run_inference
from app.physics.constraints import TerrainParams
from app.action.engine import compute_tier

router = APIRouter()


# ── Request / response models ────────────────────────────────────────────────

class SensorUpdate(BaseModel):
    """A new sensor reading used to update an in-flight prediction."""
    region_id: int = Field(..., example=1)
    prediction_id: int | None = Field(None, description="If set, will attempt to update this prediction's alert tier")

    # Updated readings (only send what you have — omit unknowns)
    rainfall_24h_mm: float | None = Field(None, ge=0, le=500, example=95.0)
    rainfall_72h_mm: float | None = Field(None, ge=0, le=1500)
    soil_saturation: float | None = Field(None, ge=0, le=1.0)
    river_level_normalised: float | None = Field(None, ge=0, le=1.0)

    # Terrain (optional override — typically fixed per region)
    slope_degrees: float | None = Field(None, ge=0, le=90)
    debris_volume_m3: float | None = Field(None, ge=0)
    channel_width_m: float | None = Field(None, ge=0)
    valley_length_km: float | None = Field(None, ge=0)

    source: str = Field("LIVE_SENSOR", description="Data source identifier")
    reading_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackResponse(BaseModel):
    prediction_id: int | None
    previous_tier: str | None
    updated_tier: str
    previous_probability: float | None
    updated_probability: float
    downgraded: bool
    upgraded: bool
    message: str
    recalculated_at: datetime


# Sikkim default terrain (used when overrides not provided)
REGION_DEFAULTS = {
    1: TerrainParams(slope_degrees=32.0, channel_width_m=120.0, valley_length_km=45.0, debris_volume_m3=0),
    2: TerrainParams(slope_degrees=38.0, channel_width_m=80.0, valley_length_km=24.0, debris_volume_m3=0),
}
REGION_DEFAULT_INFERENCE = {
    1: {"rainfall_24h_mm": 90.0, "rainfall_72h_mm": 280.0, "soil_saturation": 0.65, "river_level_normalised": 0.50},
    2: {"rainfall_24h_mm": 60.0, "rainfall_72h_mm": 180.0, "soil_saturation": 0.55, "river_level_normalised": 0.40},
}


@router.post("/sensor-reading", response_model=FeedbackResponse)
async def submit_sensor_reading(update: SensorUpdate):
    """
    FR11 — Feedback Loop: submit a new sensor reading.

    Re-runs cascade inference with the updated readings.
    If the resulting probability is lower than the current alert, the alert
    can be downgraded (still requires human verification before taking effect).

    This implements the \"feedback loop\" requirement: new evidence can
    reduce as well as increase the predicted cascade probability.
    """
    region_defaults = REGION_DEFAULTS.get(update.region_id)
    if region_defaults is None:
        raise HTTPException(status_code=404, detail=f"Region {update.region_id} not found")

    defaults = REGION_DEFAULT_INFERENCE.get(update.region_id, {})

    # Merge incoming readings with regional defaults
    r24 = update.rainfall_24h_mm  if update.rainfall_24h_mm  is not None else defaults["rainfall_24h_mm"]
    r72 = update.rainfall_72h_mm  if update.rainfall_72h_mm  is not None else defaults["rainfall_72h_mm"]
    soil = update.soil_saturation if update.soil_saturation  is not None else defaults["soil_saturation"]
    river = update.river_level_normalised if update.river_level_normalised is not None else defaults["river_level_normalised"]

    terrain = TerrainParams(
        slope_degrees=update.slope_degrees   or region_defaults.slope_degrees,
        channel_width_m=update.channel_width_m or region_defaults.channel_width_m,
        valley_length_km=update.valley_length_km or region_defaults.valley_length_km,
        debris_volume_m3=update.debris_volume_m3 if update.debris_volume_m3 is not None else region_defaults.debris_volume_m3,
    )

    # Re-run inference
    result = run_inference(r24, r72, terrain.slope_degrees, soil, river, terrain)

    # Compare to a mock "previous" state for the response
    # In production, this would look up the DB record for prediction_id
    prev_prob = 0.47  # Placeholder: would come from DB lookup
    prev_tier = "ORANGE"
    updated_prob = result["probability"]
    updated_tier = result["tier"]

    downgraded = _tier_rank(updated_tier) < _tier_rank(prev_tier)
    upgraded   = _tier_rank(updated_tier) > _tier_rank(prev_tier)

    msg = (
        f"Alert DOWNGRADED from {prev_tier} to {updated_tier} based on updated sensor readings."
        if downgraded else
        f"Alert UPGRADED from {prev_tier} to {updated_tier} — still requires human verification."
        if upgraded else
        f"Alert tier unchanged at {updated_tier}. Probability updated to {updated_prob:.1%}."
    )

    return FeedbackResponse(
        prediction_id=update.prediction_id,
        previous_tier=prev_tier,
        updated_tier=updated_tier,
        previous_probability=prev_prob,
        updated_probability=round(updated_prob, 4),
        downgraded=downgraded,
        upgraded=upgraded,
        message=msg,
        recalculated_at=datetime.now(timezone.utc),
    )


# ── FR12 — Graceful degradation health check ─────────────────────────────────

class FeedStatus(BaseModel):
    name: str
    status: Literal["OK", "DEGRADED", "DOWN"]
    detail: str


class SystemHealthResponse(BaseModel):
    overall: Literal["OK", "DEGRADED", "DOWN"]
    degraded_mode: bool
    feeds: list[FeedStatus]
    fallback_active: bool
    message: str
    checked_at: datetime


@router.get("/health", response_model=SystemHealthResponse)
async def feed_health():
    """
    FR12 — Graceful Degradation: report the health of all data feeds.

    If any feed is DOWN, the system falls back to:
    - Last-known-state for that feed
    - Physics-based worst-case estimate where inference is not possible

    The dashboard shows a DEGRADED banner when any feed is unavailable.
    """
    # In production, each check would actually ping the external source.
    # For demo/MVP, we simulate known states.
    feeds = [
        FeedStatus(name="IMD Rainfall API",     status="DEGRADED", detail="Polling mode — 3h delay (public FTP, not real-time)"),
        FeedStatus(name="CWC River Gauge",       status="DEGRADED", detail="Data sourced from cached historical; no live API"),
        FeedStatus(name="PostGIS Database",      status="OK",       detail="Primary state store healthy"),
        FeedStatus(name="Redis Cache",           status="OK",       detail="Cache store healthy"),
        FeedStatus(name="OSM Overpass API",      status="OK",       detail="Impact layer data available"),
    ]

    any_down     = any(f.status == "DOWN"     for f in feeds)
    any_degraded = any(f.status == "DEGRADED" for f in feeds)

    if any_down:
        overall = "DOWN"
        msg = "One or more critical feeds are DOWN. Physics-only worst-case estimates active."
        fallback = True
    elif any_degraded:
        overall = "DEGRADED"
        msg = "Some feeds are DEGRADED (delayed data). Inference using last-known-state. Results may lag up to 3h."
        fallback = True
    else:
        overall = "OK"
        msg = "All feeds healthy."
        fallback = False

    return SystemHealthResponse(
        overall=overall,
        degraded_mode=fallback,
        feeds=feeds,
        fallback_active=fallback,
        message=msg,
        checked_at=datetime.now(timezone.utc),
    )


# ── Helper ────────────────────────────────────────────────────────────────────

_TIER_RANKS = {"GREEN": 0, "YELLOW": 1, "ORANGE": 2, "RED": 3}

def _tier_rank(tier: str) -> int:
    return _TIER_RANKS.get(tier, 0)
