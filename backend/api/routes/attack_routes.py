"""
attack_routes.py -- Attack log and summary endpoints
"""

from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/attacks", tags=["attacks"])

runner = None


@router.get("/log")
async def get_attack_log(limit: int = Query(default=100, le=500)):
    if runner is None:
        return {"attacks": [], "total": 0}
    log = runner.attack_log[-limit:]
    return {"attacks": list(reversed(log)), "total": len(runner.attack_log)}


@router.get("/summary")
async def get_attack_summary():
    if runner is None:
        return {"replay": 0, "mitm": 0, "flood": 0, "unknown": 0, "total": 0}
    counts = {"replay": 0, "mitm": 0, "flood": 0, "unknown": 0}
    for atk in runner.attack_log:
        atype = atk.get("attack_type", "unknown")
        counts[atype] = counts.get(atype, 0) + 1
    counts["total"] = len(runner.attack_log)
    return counts
