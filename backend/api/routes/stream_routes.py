"""
stream_routes.py -- Simulation control endpoints
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime

router = APIRouter(prefix="/api/stream", tags=["stream"])

# Will be set by fastapi_server.py on startup
runner = None


class StartRequest(BaseModel):
    num_meters: int = Field(default=100, ge=10, le=500)


@router.post("/start")
async def start_simulation(req: StartRequest):
    if runner is None:
        raise HTTPException(500, "Simulation runner not initialized")
    result = await runner.start(req.num_meters)
    if result.get("status") == "error":
        raise HTTPException(400, result["message"])
    return result


@router.post("/stop")
async def stop_simulation():
    if runner is None:
        raise HTTPException(500, "Simulation runner not initialized")
    result = await runner.stop()
    if result.get("status") == "error":
        raise HTTPException(400, result["message"])
    return result


@router.get("/status")
async def get_status():
    if runner is None:
        return {"is_running": False, "num_meters": 0,
                "elapsed_seconds": 0, "current_stats": {}}
    return {
        "is_running": runner.is_running,
        "num_meters": runner.num_meters,
        "elapsed_seconds": round(
            (datetime.now().timestamp() - runner.start_time), 1
        ) if runner.start_time and runner.is_running else 0,
        "current_stats": runner.get_current_stats() if runner.is_running else {}
    }
