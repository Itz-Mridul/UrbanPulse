"""
Replay API router — historical event replay endpoint.
Supports: sikkim_2023, kedarnath_2013
"""
from fastapi import APIRouter, HTTPException
from app.replay.sikkim_2023 import get_cached_replay
from app.replay.kedarnath_2013 import get_kedarnath_replay

router = APIRouter()

DATA_DISCLAIMER = (
    "Synthetic reconstruction from published research (labeled SYNTHETIC_HISTORICAL). "
    "Not live or real-time operational data."
)


@router.get("/")
async def list_replays():
    """List all available historical replay events."""
    return {
        "events": [
            {
                "name": "sikkim_2023",
                "label": "South Lhonak GLOF — Sikkim, 4 Oct 2023",
                "region": "Sikkim — Teesta Valley",
                "hazard_pair": "GLOF → River Blockage → Flood",
                "frames": 7,
            },
            {
                "name": "kedarnath_2013",
                "label": "Kedarnath Cloudburst + GLOF — Uttarakhand, 16–17 Jun 2013",
                "region": "Kedarnath — Mandakini Valley",
                "hazard_pair": "Cloudburst → Debris Flow → Flash Flood",
                "frames": 6,
            },
        ],
        "data_disclaimer": DATA_DISCLAIMER,
    }


@router.get("/{event_name}")
async def replay_event(event_name: str):
    """
    Replay a named historical event.

    Returns the full timeline of inference results at each time step,
    so the frontend can animate the alert escalation on a scrubber.

    Supported events: sikkim_2023, kedarnath_2013
    """
    if event_name == "sikkim_2023":
        frames = await get_cached_replay()
        return {
            "event": event_name,
            "region": "Sikkim — Teesta Valley",
            "frame_count": len(frames),
            "data_disclaimer": DATA_DISCLAIMER,
            "frames": frames,
        }
    elif event_name == "kedarnath_2013":
        data = get_kedarnath_replay()
        return {
            "event": event_name,
            "region": data["region"],
            "frame_count": len(data["frames"]),
            "data_disclaimer": DATA_DISCLAIMER,
            "frames": data["frames"],
        }
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown event '{event_name}'. Supported: sikkim_2023, kedarnath_2013",
        )
