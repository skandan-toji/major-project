"""
session_routes.py -- Session management endpoints
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

runner = None


@router.get("/active")
async def get_active_sessions():
    if runner is None or not runner.is_running:
        return {"active": [], "count": 0}
    sessions = []
    for meter in runner.meters:
        sid = ""
        is_atk_session = False
        if meter.current_session:
            raw_sid = meter.current_session.get("session_id", "")
            if isinstance(raw_sid, bytes):
                sid = raw_sid.hex()
            else:
                sid = str(raw_sid)
            # Check if this meter's current session is an attack session
            is_atk_session = meter.attack_manager.is_attack_session(
                meter.current_session["session_id"]
            )
        sessions.append({
            "meter_id": meter.meter_id,
            "session_id": sid[:16] if sid else "",
            "packets_sent": meter.packet_count,
            "active": meter.has_active_session(),
            "session_cycle": meter.session_count,
            "attacks": meter.total_attacks_injected,
            "is_attack_session": is_atk_session,
        })
    return {"active": sessions, "count": len(sessions)}


@router.get("/stats")
async def get_session_stats():
    if runner is None:
        return {"created": 0, "active": 0, "expired": 0}
    return {
        "created": runner.num_meters,
        "active": runner.num_meters if runner.is_running else 0,
        "expired": 0
    }
