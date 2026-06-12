"""
metrics_routes.py -- Performance metrics and system info endpoints
"""

import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

runner = None

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                            "verification_results.json")


@router.get("/performance")
async def get_performance_metrics():
    """Returns full post-session metrics from last run."""
    try:
        with open(RESULTS_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


@router.get("/system")
async def get_system_info():
    """Returns system configuration info."""
    return {
        "security_level": "NIST Level 5",
        "dilithium_variant": "Dilithium5",
        "kyber_variant": "Kyber1024",
        "aes_mode": "AES-256-GCM",
        "hmac_algorithm": "HMAC-SHA256",
        "session_lifetime": 900,
        "timestamp_window": 60,
        "ml_model": "Isolation Forest",
        "ml_estimators": 200,
        "ml_contamination": 0.08,
        "max_meters": 500,
        "key_sizes": {
            "dilithium5_public": 2592,
            "dilithium5_private": 4864,
            "dilithium5_signature": 4595,
            "kyber1024_public": 1568,
            "kyber1024_private": 3168,
            "kyber1024_ciphertext": 1568,
            "aes_key": 256,
            "hmac_output": 256,
        }
    }
