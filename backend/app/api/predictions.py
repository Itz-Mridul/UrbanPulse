"""
Predictions API — live cascade predictions and causal path explainability.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any

from app.db import get_db, CascadePrediction, HazardEvent, Region
from app.inference.engine import run_inference
from app.physics.constraints import TerrainParams
from app.impact.scorer import compute_full_impact
from app.action.engine import generate_alert
from app.db import ImpactScore, Alert
from app.ws.manager import ws_manager

router = APIRouter()


@router.get("/current")
async def get_current_predictions(
    region_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Return live (non-replay) cascade predictions for a region."""
    q = select(CascadePrediction).where(CascadePrediction.is_replay == False)
    if region_id:
        q = q.where(CascadePrediction.region_id == region_id)
    q = q.order_by(CascadePrediction.created_at.desc()).limit(20)
    result = await db.execute(q)
    preds = result.scalars().all()

    return [
        {
            "id": p.id,
            "region_id": p.region_id,
            "target_hazard_type": p.target_hazard_type,
            "probability": p.probability,
            "time_lag_min_hours": p.time_lag_min_hours,
            "time_lag_max_hours": p.time_lag_max_hours,
            "causal_path": p.causal_path,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in preds
    ]


@router.get("/{prediction_id}/causal-path")
async def get_causal_path(prediction_id: int, db: AsyncSession = Depends(get_db)):
    """Return explainability graph for a single prediction."""
    result = await db.execute(
        select(CascadePrediction).where(CascadePrediction.id == prediction_id)
    )
    pred = result.scalar_one_or_none()
    if not pred:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction not found")

    return {
        "prediction_id": prediction_id,
        "probability": pred.probability,
        "causal_path": pred.causal_path,
        "time_lag_min_hours": pred.time_lag_min_hours,
        "time_lag_max_hours": pred.time_lag_max_hours,
    }


@router.post("/trigger")
async def trigger_inference(
    region_id: int,
    rainfall_24h_mm: float = 180.0,
    rainfall_72h_mm: float = 380.0,
    slope_degrees: float = 28.0,
    soil_saturation: float = 0.75,
    river_level_normalised: float = 0.65,
    debris_volume_m3: float = 500_000.0,
    channel_width_m: float = 80.0,
    valley_length_km: float = 45.0,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually trigger cascade inference for a region (dev/demo endpoint).
    In production, this is called by the ingestion scheduler on new data.
    """
    terrain = TerrainParams(
        slope_degrees=slope_degrees,
        channel_width_m=channel_width_m,
        valley_length_km=valley_length_km,
        debris_volume_m3=debris_volume_m3,
    )

    result = run_inference(
        rainfall_24h_mm=rainfall_24h_mm,
        rainfall_72h_mm=rainfall_72h_mm,
        slope_degrees=slope_degrees,
        soil_saturation=soil_saturation,
        river_level_normalised=river_level_normalised,
        terrain=terrain,
    )

    # Persist prediction
    pred = CascadePrediction(
        region_id=region_id,
        target_hazard_type="FLOOD",
        probability=result["probability"],
        time_lag_min_hours=result["time_lag_min_hours"],
        time_lag_max_hours=result["time_lag_max_hours"],
        causal_path=result["causal_path"],
        is_replay=False,
    )
    db.add(pred)
    await db.flush()  # get pred.id

    # Impact
    bbox = (27.0, 88.3, 27.5, 88.8)  # Sikkim Teesta valley approximate bbox
    impact = await compute_full_impact(result["probability"], bbox)

    imp = ImpactScore(
        prediction_id=pred.id,
        **{k: v for k, v in impact.items() if k != "exposure_index" and k != "vulnerability_index"},
    )
    db.add(imp)

    # Alert
    alert_data = generate_alert(
        result["probability"],
        impact["impact_score"],
        "Sikkim",
        result["time_lag_min_hours"],
        result["time_lag_max_hours"],
    )
    alert = Alert(prediction_id=pred.id, **alert_data)
    db.add(alert)
    await db.commit()

    # Broadcast via WebSocket
    await ws_manager.send_alert({
        "prediction_id": pred.id,
        "tier": alert.tier,
        "probability": result["probability"],
        "recommended_action": alert.recommended_action,
        "causal_path": result["causal_path"],
        "impact": impact,
    })

    return {
        "prediction_id": pred.id,
        "result": result,
        "impact": impact,
        "alert": alert_data,
    }
