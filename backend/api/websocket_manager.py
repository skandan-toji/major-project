"""
websocket_manager.py -- WebSocket Connection Manager

Manages all active WebSocket connections for the Smart Grid
Security Framework dashboard. Broadcasts real-time simulation
events to all connected clients.
"""

import asyncio
from fastapi import WebSocket


class WebSocketManager:
    """
    Manages all active WebSocket connections.
    Broadcasts real-time simulation events to dashboard.
    """

    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self.lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Sends message to all connected clients.
        Removes disconnected clients silently.
        """
        if not self.active_connections:
            return
        dead = []
        async with self.lock:
            connections = list(self.active_connections)
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            await self.disconnect(ws)

    async def broadcast_packet_event(self, event: dict):
        """
        Broadcasts one packet processing event.

        Event structure:
        {
          "type"           : "packet",
          "meter_id"       : str,
          "session_id"     : str,
          "sequence_number": int,
          "timestamp"      : float,
          "result"         : "accepted" | "rejected",
          "reason"         : str,
          "was_attack"     : bool,
          "attack_type"    : str or null,
          "ml_score"       : float,
          "ml_flagged"     : bool,
          "payload_size"   : int
        }
        """
        await self.broadcast({"event_type": "packet", **event})

    async def broadcast_attack_event(self, event: dict):
        """
        Broadcasts a detected attack event.

        Event structure:
        {
          "type"            : "attack",
          "meter_id"        : str,
          "attack_type"     : "replay" | "mitm" | "flood",
          "detection_method": "hmac" | "sequence" | "timestamp" | "ml",
          "timestamp"       : float,
          "session_id"      : str
        }
        """
        await self.broadcast({"event_type": "attack", **event})

    async def broadcast_stats_update(self, stats: dict):
        """
        Broadcasts periodic stats update every 2 seconds.

        Stats structure:
        {
          "type"                : "stats",
          "total_packets"       : int,
          "accepted"            : int,
          "rejected"            : int,
          "attacks_detected"    : int,
          "false_positives"     : int,
          "throughput"          : float,
          "active_sessions"     : int,
          "detection_accuracy"  : float,
          "fpr"                 : float,
          "elapsed_seconds"     : float,
          "meters_online"       : int
        }
        """
        await self.broadcast({"event_type": "stats", **stats})

    async def broadcast_session_event(self, event: dict):
        """Session created or expired events."""
        await self.broadcast({"event_type": "session", **event})

    async def broadcast_simulation_ended(self, metrics: dict):
        """
        Sent when simulation stops.
        Contains full post-session metrics dict.
        """
        await self.broadcast({
            "event_type": "simulation_ended",
            "metrics": metrics
        })
