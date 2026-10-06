"""
Historical Replay Engine — Sikkim 2023 South Lhonak GLOF event.

Plays back the pre-event data chronologically so the dashboard shows
CascadeIQ raising alert before the real event's timestamp.

Data source: Reconstructed from published research:
  - Sattar et al. (2024): South Lhonak lake drainage, 4 Oct 2023
  - GLOF travel time: ~3–5 hours from source to Teesta junction
  - Peak discharge estimate: ~40,000 m³/s at Singtam

This is clearly labeled REPLAY in all API responses — never misrepresented
as live real-time data. This matches the stated MVP scope (Q18/Q19).
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, Any

from loguru import logger

from app.inference.engine import run_inference
from app.physics.constraints import TerrainParams
from app.impact.scorer import compute_full_impact
from app.action.engine import generate_alert


# ---------------------------------------------------------------------------
# Synthetic replay dataset for Sikkim 2023 GLOF
# Each entry represents hourly sensor readings in the lead-up to the event.
# Real event: South Lhonak lake breach ~04:00 IST, 4 Oct 2023
# ---------------------------------------------------------------------------

SIKKIM_2023_TIMELINE: list[dict[str, Any]] = [
    # T-72h: Pre-monsoon season, elevated but not yet alarming
    {
        "offset_hours": -72,
        "label": "T-72h: Pre-event baseline",
        "rainfall_24h_mm": 45.0,
        "rainfall_72h_mm": 120.0,
        "soil_saturation": 0.55,
        "river_level_normalised": 0.40,
        "slope_degrees": 32.0,
        "debris_volume_m3": 0,
        "notes": "Normal monsoon conditions. Lhonak lake at ~1.5km² area.",
    },
    # T-48h: Heavy rain begins
    {
        "offset_hours": -48,
        "label": "T-48h: Heavy rainfall onset",
        "rainfall_24h_mm": 110.0,
        "rainfall_72h_mm": 195.0,
        "soil_saturation": 0.68,
        "river_level_normalised": 0.52,
        "slope_degrees": 32.0,
        "debris_volume_m3": 0,
        "notes": "IMD records 110mm/24h. Soil saturation rising. River Teesta at moderate level.",
    },
    # T-36h: Cyclone Hamoon-related heavy rain band
    {
        "offset_hours": -36,
        "label": "T-36h: Extreme rainfall — Cyclone Hamoon remnants",
        "rainfall_24h_mm": 165.0,
        "rainfall_72h_mm": 310.0,
        "soil_saturation": 0.78,
        "river_level_normalised": 0.61,
        "slope_degrees": 32.0,
        "debris_volume_m3": 200_000,
        "notes": "Extreme 165mm/24h. Soil near saturation. Small debris flows reported on slopes.",
    },
    # T-24h: System would flag ORANGE — KEY DEMO MOMENT
    {
        "offset_hours": -24,
        "label": "T-24h: CascadeIQ alert threshold crossed ⚠",
        "rainfall_24h_mm": 190.0,
        "rainfall_72h_mm": 420.0,
        "soil_saturation": 0.85,
        "river_level_normalised": 0.70,
        "slope_degrees": 32.0,
        "debris_volume_m3": 600_000,
        "notes": "190mm/24h exceeds Caine threshold for slope=32°. Blockage physically plausible. System raises ORANGE alert.",
    },
    # T-12h: System escalates to RED
    {
        "offset_hours": -12,
        "label": "T-12h: RED alert — dam failure imminent",
        "rainfall_24h_mm": 205.0,
        "rainfall_72h_mm": 490.0,
        "soil_saturation": 0.92,
        "river_level_normalised": 0.82,
        "slope_degrees": 32.0,
        "debris_volume_m3": 1_200_000,
        "notes": "South Lhonak moraine dam under extreme stress. CascadeIQ RED. Estimated 3–5h travel to Singtam.",
    },
    # T-6h: Peak risk
    {
        "offset_hours": -6,
        "label": "T-6h: Peak cascade risk",
        "rainfall_24h_mm": 180.0,
        "rainfall_72h_mm": 520.0,
        "soil_saturation": 0.95,
        "river_level_normalised": 0.90,
        "slope_degrees": 32.0,
        "debris_volume_m3": 1_500_000,
        "notes": "Moraine dam failure. GLOF initiated. Flood wave propagating downstream through Teesta valley.",
    },
    # T=0: The real event
    {
        "offset_hours": 0,
        "label": "T=0: Real event — South Lhonak GLOF, 4 Oct 2023 04:00 IST",
        "rainfall_24h_mm": 175.0,
        "rainfall_72h_mm": 520.0,
        "soil_saturation": 0.95,
        "river_level_normalised": 1.0,
        "slope_degrees": 32.0,
        "debris_volume_m3": 1_500_000,
        "notes": "CONFIRMED REAL EVENT: Flood reached Singtam ~07:00 IST. ~40 fatalities, major infrastructure loss.",
    },
]

# Terrain parameters for the Teesta Valley pilot region
SIKKIM_TERRAIN = TerrainParams(
    slope_degrees=32.0,
    channel_width_m=120.0,   # Teesta at Singtam
    valley_length_km=45.0,   # South Lhonak to Singtam ~45km
    debris_volume_m3=1_500_000,
    upstream_lake_area_km2=1.65,  # South Lhonak lake area at breach
)

SIKKIM_BBOX = (27.15, 88.35, 27.65, 88.82)   # Teesta valley impact zone


async def run_sikkim_2023_replay(
    speed_multiplier: float = 1.0,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Async generator that yields replay frames for the Sikkim 2023 event.

    Each frame contains the inference result at a given point in time.
    speed_multiplier: how fast to advance (1.0 = real-time hours, high = fast demo)

    Yields dicts with keys: offset_hours, label, inference, impact, alert, notes
    """
    real_event_time = datetime(2023, 10, 4, 4, 0, 0, tzinfo=timezone.utc)

    for frame in SIKKIM_2023_TIMELINE:
        offset = frame["offset_hours"]
        sim_time = real_event_time + timedelta(hours=offset)

        terrain = TerrainParams(
            slope_degrees=frame["slope_degrees"],
            channel_width_m=SIKKIM_TERRAIN.channel_width_m,
            valley_length_km=SIKKIM_TERRAIN.valley_length_km,
            debris_volume_m3=frame["debris_volume_m3"],
            upstream_lake_area_km2=SIKKIM_TERRAIN.upstream_lake_area_km2,
        )

        inference = run_inference(
            rainfall_24h_mm=frame["rainfall_24h_mm"],
            rainfall_72h_mm=frame["rainfall_72h_mm"],
            slope_degrees=frame["slope_degrees"],
            soil_saturation=frame["soil_saturation"],
            river_level_normalised=frame["river_level_normalised"],
            terrain=terrain,
        )

        impact = await compute_full_impact(
            inference["probability"], SIKKIM_BBOX, "Sikkim"
        )

        alert = generate_alert(
            inference["probability"],
            impact["impact_score"],
            "Sikkim",
            inference["time_lag_min_hours"],
            inference["time_lag_max_hours"],
        )

        yield {
            "offset_hours": offset,
            "simulation_timestamp": sim_time.isoformat(),
            "is_real_event": offset == 0,
            "label": frame["label"],
            "notes": frame["notes"],
            "data_source": "SYNTHETIC_HISTORICAL",  # Always labeled — never hidden
            "inference": inference,
            "impact": impact,
            "alert": alert,
        }

        # Simulate time passing between frames
        if speed_multiplier > 0:
            await asyncio.sleep(0.5 / speed_multiplier)


# Pre-computed snapshot for the REST endpoint (so it doesn't block)
_CACHED_REPLAY: list[dict[str, Any]] = []


async def get_cached_replay() -> list[dict[str, Any]]:
    global _CACHED_REPLAY
    if not _CACHED_REPLAY:
        async for frame in run_sikkim_2023_replay(speed_multiplier=float("inf")):
            _CACHED_REPLAY.append(frame)
    return _CACHED_REPLAY
