"""WebSocket endpoints for real-time updates — design generation progress, notifications."""

import asyncio
import json
import time
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections per project/site."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}
        self.user_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, channel: str, user_id: Optional[str] = None):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        if user_id:
            self.user_connections[user_id] = websocket

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel] = [
                c for c in self.active_connections[channel] if c != websocket
            ]
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            dead = []
            for conn in self.active_connections[channel]:
                try:
                    await conn.send_json(message)
                except Exception:
                    dead.append(conn)
            for d in dead:
                self.active_connections[channel].remove(d)

    async def send_to_user(self, user_id: str, message: dict):
        if user_id in self.user_connections:
            try:
                await self.user_connections[user_id].send_json(message)
            except Exception:
                del self.user_connections[user_id]

    def get_stats(self) -> dict:
        total = sum(len(conns) for conns in self.active_connections.values())
        return {
            "total_connections": total,
            "channels": {ch: len(conns) for ch, conns in self.active_connections.items()},
        }


manager = ConnectionManager()


# ── Channel Endpoints ─────────────────────────────────────────────────

@router.websocket("/ws/project/{project_id}")
async def project_websocket(websocket: WebSocket, project_id: str):
    """
    WebSocket for real-time project updates.

    Events received:
    - `design.generation_started` — Generation queued
    - `design.generation_progress` — Progress update (0-100%)
    - `design.generation_completed` — Design ready
    - `validation.completed` — Validation finished
    - `review.decision` — Engineer made a decision
    """
    channel = f"project:{project_id}"
    await manager.connect(websocket, channel)
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "timestamp": time.time(),
            "message": f"Connected to project {project_id} updates",
        })

        while True:
            # Keep alive + receive client messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
                elif msg.get("type") == "subscribe":
                    sub_channel = msg.get("channel", channel)
                    await manager.connect(websocket, sub_channel)
                    await websocket.send_json({
                        "type": "subscribed",
                        "channel": sub_channel,
                    })
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/ws/design/{design_id}")
async def design_websocket(websocket: WebSocket, design_id: str):
    """
    WebSocket for real-time design generation progress.

    Sends progress events as the design is generated:
    ```json
    {"type": "progress", "step": "constraints", "percent": 10}
    {"type": "progress", "step": "generation", "percent": 30}
    {"type": "progress", "step": "geometry", "percent": 60}
    {"type": "progress", "step": "validation", "percent": 80}
    {"type": "progress", "step": "complete", "percent": 100}
    ```
    """
    channel = f"design:{design_id}"
    await manager.connect(websocket, channel)
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "timestamp": time.time(),
        })

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


@router.websocket("/ws/notifications/{user_id}")
async def notifications_websocket(websocket: WebSocket, user_id: str):
    """WebSocket for real-time notifications to a specific user."""
    channel = f"user:{user_id}"
    await manager.connect(websocket, channel, user_id=user_id)
    try:
        await websocket.send_json({
            "type": "connected",
            "channel": channel,
            "timestamp": time.time(),
            "message": "Notification stream active",
        })

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": time.time()})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)


# ── HTTP endpoint for broadcasting (called from other services) ───────

@router.get("/ws/stats", summary="WebSocket connection statistics")
async def websocket_stats():
    """Get current WebSocket connection statistics."""
    return manager.get_stats()
