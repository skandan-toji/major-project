"""
isolation_forest.py -- Runtime Anomaly Detection Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Provides IsolationForestDetector — scores packets using the
pre-trained model, scaler, and threshold selected during training.

Key architecture fix: ML scoring happens BEFORE crypto verification
in the Control Center, so attack packets with anomalous features
(seq_delta < 0 for replay, hmac_valid=0 for MITM) are scored while
those features are still visible.
"""

import os
import json
import joblib
import numpy as np

# ── Paths (relative to this file's directory) ────────────────
_ML_DIR    = os.path.dirname(os.path.abspath(__file__))
_SAVE_DIR  = os.path.join(_ML_DIR, "saved_model")
MODEL_PATH     = os.path.join(_SAVE_DIR, "isolation_forest.pkl")
SCALER_PATH    = os.path.join(_SAVE_DIR, "scaler.pkl")
THRESHOLD_PATH = os.path.join(_SAVE_DIR, "threshold.json")

# ── Feature order — MUST match training exactly ──────────────
FEATURE_ORDER = [
    "packet_rate",
    "inter_arrival_time",
    "payload_size",
    "sequence_delta",
    "timestamp_delta",
    "session_duration",
    "hmac_valid",
    "seq_check_valid",
    "timestamp_valid",
    "payload_size_zscore",
    "inter_arrival_zscore",
    "rate_spike_ratio",
    "consecutive_failures",
    "session_packet_count",
]


class IsolationForestDetector:
    """
    Scores incoming packets for anomaly using a pre-trained
    Isolation Forest. Loads model, scaler, and threshold once
    at init. Degrades gracefully if model files are missing.

    Online Calibration:
        The model is trained on synthetic data which may produce a
        different score distribution than live traffic (scaler mismatch).
        To fix this, the detector collects scores from the first
        CALIBRATION_SAMPLES crypto-ACCEPTED packets and computes the
        live normal score mean and std.  The effective threshold is then
        set to  live_mean - CALIBRATION_SIGMA * live_std,
        which places it N sigma below the observed normal distribution.
        This auto-adjusts for any scaler drift without retraining.
    """

    CALIBRATION_SAMPLES = 100   # packets before calibrating (fires after ~1 per meter)
    CALIBRATION_SIGMA   = 3.0   # 3 sigma below normal mean -- low FPR, catches flood anomalies

    def __init__(self):
        self.model_loaded = False
        self.threshold    = -0.15   # fallback default (pre-calibration, tighter to catch flood)
        self._base_threshold = -0.15

        try:
            self.model  = joblib.load(MODEL_PATH)
            self.scaler = joblib.load(SCALER_PATH)
            if os.path.exists(THRESHOLD_PATH):
                with open(THRESHOLD_PATH, "r") as f:
                    data = json.load(f)
                self._base_threshold = float(data.get("threshold", -0.10))
                self.threshold = self._base_threshold
            self.model_loaded = True
            print(f"[ML] IsolationForestDetector loaded. Base threshold: {self.threshold:.4f}")
        except Exception as e:
            print(f"[ML] Model not loaded: {e}")
            print("[ML] Scoring will return neutral scores until model is trained.")

        # Online calibration state
        self._calibrated       = False
        self._calib_scores     = []   # scores from accepted (normal) packets
        self._effective_thresh = self._base_threshold  # starts at -0.15, updated after calibration

        # Calibration callback — set by SimulationRunner to broadcast events
        self.calibration_callback = None

    def record_accepted_score(self, score: float) -> None:
        """
        Called by ControlCenter after a packet is accepted by crypto.
        Collects scores from confirmed-normal packets to calibrate
        the effective threshold against the live score distribution.
        """
        if self._calibrated or not self.model_loaded:
            return

        self._calib_scores.append(score)

        # Compute running stats for calibration event
        arr  = np.array(self._calib_scores)
        cur_mean = float(np.mean(arr))
        cur_std  = float(np.std(arr)) if np.std(arr) > 0 else 0.01

        if len(self._calib_scores) >= self.CALIBRATION_SAMPLES:
            # Threshold = mean - N*sigma (N sigma below live normal mean).
            # This auto-adjusts for scaler drift between training and live traffic.
            # The training threshold (-0.548) was tuned on synthetic data.
            # Live normal packets score around mean=-0.54 with std~0.03.
            # At 3 sigma below: -0.54 - 0.09 = -0.63 threshold.
            # Flood at 50pps has very high rate_spike_ratio/packet_rate features
            # → scores more negative than -0.63 → correctly flagged.
            # Normal packets are 3 sigma from threshold → ~0.13% theoretical FPR.
            calibrated = cur_mean - self.CALIBRATION_SIGMA * cur_std
            self._effective_thresh = calibrated
            self.threshold = calibrated
            self._calibrated = True
            print(f"[ML] Online calibration complete:")
            print(f"     Normal score mean={cur_mean:.4f}  std={cur_std:.4f}")
            print(f"     Effective threshold -> {calibrated:.4f}  "
                  f"(base was {self._base_threshold:.4f})")

        # Emit calibration event if callback set
        if self.calibration_callback:
            self.calibration_callback({
                "event_type"        : "ml_calibration",
                "samples_collected" : len(self._calib_scores),
                "current_threshold" : self._effective_thresh,
                "score_mean"        : cur_mean,
                "score_std"         : cur_std,
                "calibrated"        : self._calibrated,
            })

    def score_packet(self, features: dict) -> dict:
        """
        Score one packet's feature dict.

        Args:
            features: dict with keys matching FEATURE_ORDER.
                      Missing keys default to 0.0.

        Returns:
            {
                "anomaly_score": float,   (lower = more anomalous)
                "is_anomaly":    bool,
                "threshold_used": float,
                "confidence":    float,   (|score - threshold|)
                "model_loaded":  bool,
                "calibrated":    bool,
            }
        """
        if not self.model_loaded:
            return {
                "anomaly_score" : 0.0,
                "is_anomaly"    : False,
                "threshold_used": self.threshold,
                "confidence"    : 0.0,
                "model_loaded"  : False,
                "calibrated"    : False,
            }

        try:
            vector = [float(features.get(f, 0.0)) for f in FEATURE_ORDER]
            scaled = self.scaler.transform([vector])
            score  = float(self.model.score_samples(scaled)[0])
            thresh = self._effective_thresh
            is_anom = score < thresh
            return {
                "anomaly_score" : score,
                "is_anomaly"    : is_anom,
                "threshold_used": thresh,
                "confidence"    : abs(score - thresh),
                "model_loaded"  : True,
                "calibrated"    : self._calibrated,
            }
        except Exception:
            return {
                "anomaly_score" : 0.0,
                "is_anomaly"    : False,
                "threshold_used": self.threshold,
                "confidence"    : 0.0,
                "model_loaded"  : False,
                "calibrated"    : False,
            }



# ── Legacy AnomalyDetector kept for backward compatibility ───
# (control_center.py uses load_detector() in Week 4 code)
class AnomalyDetector:
    """
    Legacy wrapper — delegates to IsolationForestDetector.
    Kept so existing call sites still work.
    """
    def __init__(self):
        self._det = IsolationForestDetector()
        self.threshold      = self._det.threshold
        self.total_scored   = 0
        self.total_flagged  = 0

    def is_loaded(self) -> bool:
        return self._det.model_loaded

    def score_packet(self, meter_id, sequence_number, payload_size,
                     packet_timestamp, sequence_delta,
                     hmac_valid, seq_check_valid, timestamp_valid,
                     session_start_time) -> dict:
        import time
        iat  = 1.0
        rate = 1.0
        ts_delta  = abs(time.time() - packet_timestamp)
        sess_dur  = packet_timestamp - session_start_time
        features = {
            "packet_rate"          : rate,
            "inter_arrival_time"   : iat,
            "payload_size"         : float(payload_size),
            "sequence_delta"       : float(sequence_delta),
            "timestamp_delta"      : float(ts_delta),
            "session_duration"     : float(sess_dur),
            "hmac_valid"           : float(hmac_valid),
            "seq_check_valid"      : float(seq_check_valid),
            "timestamp_valid"      : float(timestamp_valid),
            "payload_size_zscore"  : 0.0,
            "inter_arrival_zscore" : 0.0,
            "rate_spike_ratio"     : 1.0,
            "consecutive_failures" : 0.0,
            "session_packet_count" : 0.0,
        }
        r = self._det.score_packet(features)
        self.total_scored += 1
        if r["is_anomaly"]:
            self.total_flagged += 1
        return {"score": r["anomaly_score"], "is_anomaly": r["is_anomaly"],
                "threshold": r["threshold_used"], "packet_rate": rate, "iat": iat}

    def get_stats(self) -> dict:
        rate = self.total_flagged / self.total_scored if self.total_scored > 0 else 0.0
        return {"total_scored": self.total_scored,
                "total_flagged": self.total_flagged, "flag_rate": rate}

    def reset(self):
        self.total_scored  = 0
        self.total_flagged = 0


def load_detector() -> AnomalyDetector:
    """Legacy function — creates AnomalyDetector (raises if model missing)."""
    if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
        raise RuntimeError("Model not found. Run ml/retrain_model.py first.")
    return AnomalyDetector()


print("[MODULE LOADED] isolation_forest.py ready")
