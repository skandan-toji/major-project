"""
stats_routes.py -- Live statistics and ML stats endpoints
"""

import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/api/stats", tags=["stats"])

runner = None

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "verification_results.json")


@router.get("/live")
async def get_live_stats():
    if runner is None or not runner.is_running:
        return {"status": "not_running", "stats": {}}
    return {"status": "running", "stats": runner.get_current_stats()}


@router.get("/crypto")
async def get_crypto_stats():
    """Returns crypto latency stats from last run."""
    try:
        with open(RESULTS_PATH, "r") as f:
            data = json.load(f)
        return data.get("latency_ms", {})
    except Exception:
        return {}


@router.get("/ml")
async def get_ml_stats():
    """Returns ML model info and current session ML stats."""
    ml_info = {
        "model_type": "Isolation Forest",
        "n_estimators": 200,
        "contamination": 0.08,
        "calibration": "Online (100 samples, 3-sigma)",
    }
    if runner and runner.is_running:
        ml_info["session_stats"] = runner.ml_stats
    else:
        try:
            with open(RESULTS_PATH, "r") as f:
                data = json.load(f)
            ml_info["session_stats"] = data.get("ml_stats", {})
        except Exception:
            ml_info["session_stats"] = {}
    return ml_info


@router.get("/historical")
async def get_historical_stats():
    """Reads verification_results.json for last completed session metrics."""
    try:
        with open(RESULTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}
