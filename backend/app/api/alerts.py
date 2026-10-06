"""
Alerts API — human-in-the-loop verification endpoint.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.db import get_db, Alert, CascadePrediction
from app.api.auth import get_current_user
from app.ws.manager import ws_manager

router = APIRouter()


class VerifyRequest(BaseModel):
    action: str   # "verify" | "dismiss"
    notes: Optional[str] = None


@router.get("")
async def list_alerts(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List alerts, optionally filtered by status."""
    q = select(Alert).order_by(Alert.created_at.desc()).limit(50)
    if status:
        q = q.where(Alert.status == status.upper())
    result = await db.execute(q)
    alerts = result.scalars().all()
    return [
        {
            "id": a.id,
            "prediction_id": a.prediction_id,
            "tier": a.tier,
            "recommended_action": a.recommended_action,
            "status": a.status,
            "verified_by": a.verified_by,
            "verified_at": a.verified_at.isoformat() if a.verified_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "notes": a.notes,
        }
        for a in alerts
    ]


@router.post("/{alert_id}/verify")
async def verify_alert(
    alert_id: int,
    body: VerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Human-in-the-loop: authority officer verifies or dismisses an alert.
    This is a core differentiator — no alert reaches 'public' status without this step.
    """
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    if alert.status not in ("PENDING_VERIFICATION",):
        raise HTTPException(
            status_code=400,
            detail=f"Alert already in terminal state: {alert.status}",
        )

    if body.action == "verify":
        alert.status = "VERIFIED"
    elif body.action == "dismiss":
        alert.status = "DISMISSED"
    else:
        raise HTTPException(status_code=400, detail="action must be 'verify' or 'dismiss'")

    alert.verified_by = current_user["username"]
    alert.verified_at = datetime.now(timezone.utc)
    alert.notes = body.notes

    await db.commit()

    # Broadcast status change
    await ws_manager.broadcast({
        "type": "ALERT_STATUS_CHANGED",
        "data": {
            "alert_id": alert_id,
            "status": alert.status,
            "verified_by": alert.verified_by,
            "tier": alert.tier,
        },
    })

    return {
        "alert_id": alert_id,
        "status": alert.status,
        "verified_by": alert.verified_by,
    }
