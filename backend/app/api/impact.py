"""
Impact API router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db import get_db, ImpactScore, CascadePrediction

router = APIRouter()


@router.get("/{prediction_id}")
async def get_impact(prediction_id: int, db: AsyncSession = Depends(get_db)):
    """Return exposure and impact score for a prediction."""
    result = await db.execute(
        select(ImpactScore).where(ImpactScore.prediction_id == prediction_id)
    )
    impact = result.scalar_one_or_none()
    if not impact:
        raise HTTPException(status_code=404, detail="Impact score not found for this prediction")
    return {
        "prediction_id": prediction_id,
        "impact_score": impact.impact_score,
        "population_exposed": impact.population_exposed,
        "hospitals_exposed": impact.hospitals_exposed,
        "roads_affected_km": impact.roads_affected_km,
        "shelters_available": impact.shelters_available,
        "vulnerability_index": impact.vulnerability_index,
    }
