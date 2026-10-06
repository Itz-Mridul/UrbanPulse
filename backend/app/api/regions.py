"""
Regions API router — pilot regions listing and state.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from typing import Any

from app.db import get_db, Region, SensorReading

router = APIRouter()


@router.get("", response_model=list[dict])
async def list_regions(db: AsyncSession = Depends(get_db)):
    """List all pilot regions."""
    result = await db.execute(select(Region))
    regions = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "pilot": r.pilot,
        }
        for r in regions
    ]


@router.get("/{region_id}/state")
async def region_state(region_id: int, db: AsyncSession = Depends(get_db)):
    """Return the latest sensor readings summary for a region."""
    result = await db.execute(
        select(SensorReading)
        .where(SensorReading.region_id == region_id)
        .order_by(SensorReading.recorded_at.desc())
        .limit(50)
    )
    readings = result.scalars().all()

    # Group by metric, take latest value
    latest: dict[str, Any] = {}
    for r in readings:
        if r.metric not in latest:
            latest[r.metric] = {
                "metric": r.metric,
                "value": r.value,
                "source": r.source,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }

    return {
        "region_id": region_id,
        "latest_readings": list(latest.values()),
    }
