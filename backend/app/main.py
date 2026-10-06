"""
CascadeIQ Backend — Main FastAPI Application
AI for Cascading Hazard Impact & Response
Indradhanu PCCOE International Grand Challenge 2026
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.db import init_db
from app.api import regions, predictions, alerts, impact, replay, feedback
from app.ws.manager import ws_manager
from app.api.auth import router as auth_router
from app.ingestion.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup / shutdown lifecycle."""
    logger.info("🌊 CascadeIQ backend starting up …")
    await init_db()
    await start_scheduler()
    yield
    logger.info("🛑 CascadeIQ backend shutting down …")
    await stop_scheduler()


app = FastAPI(
    title="CascadeIQ API",
    description=(
        "Multi-hazard cascade prediction engine. "
        "Computes P(hazard B | hazard A, terrain, river state) "
        "for disaster-resilience early warning."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server and production frontend
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
API_V1 = "/api/v1"

app.include_router(auth_router,          prefix=f"{API_V1}/auth",        tags=["auth"])
app.include_router(regions.router,       prefix=f"{API_V1}/regions",     tags=["regions"])
app.include_router(predictions.router,   prefix=f"{API_V1}/predictions", tags=["predictions"])
app.include_router(alerts.router,        prefix=f"{API_V1}/alerts",      tags=["alerts"])
app.include_router(impact.router,        prefix=f"{API_V1}/impact",      tags=["impact"])
app.include_router(replay.router,        prefix=f"{API_V1}/replay",      tags=["replay"])
app.include_router(feedback.router,      prefix=f"{API_V1}/feedback",    tags=["feedback"])



# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------
from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """Live alert stream — dashboard subscribes here for real-time updates."""
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; server pushes via ws_manager.broadcast()
            data = await websocket.receive_text()
            # Echo back pings so client-side heartbeat works
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/api/health", tags=["health"])
async def health():
    return {"status": "ok", "service": "CascadeIQ", "version": "0.1.0"}
