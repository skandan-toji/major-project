"""
fastapi_server.py -- Main FastAPI Application

Entry point for the Smart Grid Security Framework API.
Connects all route modules, WebSocket manager, and simulation runner.

Run: cd backend && python api/fastapi_server.py
"""

import sys
import os

# Ensure backend/ is on the path so all imports resolve
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from api.websocket_manager import WebSocketManager
from api.simulation_runner import SimulationRunner
from api.routes import stream_routes, stats_routes, session_routes, attack_routes, metrics_routes

# ── App ────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Grid Security Framework API",
    description="Hybrid Quantum-Resilient Security Framework for MitM Attack Detection",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# ── Global instances ───────────────────────────────────────────
manager = WebSocketManager()
runner = SimulationRunner(manager)

# Wire runner into route modules
stream_routes.runner = runner
stats_routes.runner = runner
session_routes.runner = runner
attack_routes.runner = runner
metrics_routes.runner = runner

# ── Include routers ────────────────────────────────────────────
app.include_router(stream_routes.router)
app.include_router(stats_routes.router)
app.include_router(session_routes.router)
app.include_router(attack_routes.router)
app.include_router(metrics_routes.router)


# ── WebSocket endpoint ─────────────────────────────────────────
@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception:
        await manager.disconnect(websocket)


# ── Health check ───────────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "modules": {
            "crypto": "loaded",
            "ml": "loaded",
            "simulation": "ready" if not runner.is_running else "running",
        }
    }


# ── Startup event ──────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    print("\n" + "=" * 60)
    print("  Smart Grid Security Framework — API Server")
    print("  Hybrid Quantum-Resilient MitM Detection")
    print("=" * 60)
    print("  REST API:   http://localhost:8000/docs")
    print("  WebSocket:  ws://localhost:8000/ws/dashboard")
    print("  Dashboard:  http://localhost:5173")
    print("=" * 60 + "\n")


# ── Entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "api.fastapi_server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
