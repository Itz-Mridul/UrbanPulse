"""
WebSocket connection manager — broadcasts live alert updates to all connected dashboards.
"""
from __future__ import annotations

import json
from typing import Any

from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WS connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections = [c for c in self.active_connections if c != websocket]
        logger.info(f"WS disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]):
        """Send a JSON message to all connected dashboards."""
        payload = json.dumps(message)
        dead = []
        for connection in self.active_connections:
            try:
                await connection.send_text(payload)
            except Exception:
                dead.append(connection)
        for d in dead:
            self.disconnect(d)

    async def send_alert(self, alert_data: dict[str, Any]):
        """Convenience method: broadcast an alert event."""
        await self.broadcast({"type": "ALERT", "data": alert_data})

    async def send_prediction_update(self, prediction_data: dict[str, Any]):
        """Broadcast a prediction update (e.g., from the replay engine)."""
        await self.broadcast({"type": "PREDICTION_UPDATE", "data": prediction_data})


ws_manager = ConnectionManager()
