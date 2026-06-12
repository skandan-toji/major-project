"""
simulation_runner.py -- Simulation Lifecycle Manager

Manages the simulation lifecycle: start, run, stop.
Connects SmartMeter, ControlCenter, AttackInjector, and
WebSocketManager together for the dashboard.
"""

import asyncio
import time
import json
import os
import random
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime

from api.websocket_manager import WebSocketManager
from config import MAX_EXECUTOR_WORKERS, METER_STARTUP_STAGGER, PACKET_INTERVAL
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter

RESULTS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                            "verification_results.json")


def _make_rows(n=300):
    """Generate synthetic payload rows for meters."""
    rows = []
    for _ in range(n):
        rows.append({
            "date": "01/01/2026", "time": "00:00:00",
            "global_active_power": round(random.uniform(0.5, 25.0), 3),
            "global_reactive_power": round(random.uniform(0.0, 5.0), 3),
            "voltage": round(random.uniform(218.0, 242.0), 2),
            "global_intensity": round(random.uniform(1.0, 15.0), 2),
            "sub_metering_1": round(random.uniform(0.0, 40.0), 1),
            "sub_metering_2": round(random.uniform(0.0, 40.0), 1),
            "sub_metering_3": round(random.uniform(0.0, 20.0), 1),
        })
    return rows


def _classify_reason(reason: str) -> str:
    """Classify rejection reason into category."""
    r = reason.lower()
    if "hmac" in r:
        return "hmac_failed"
    if "replay" in r or "sequence" in r:
        return "replay_detected"
    if "stale" in r or "timestamp" in r:
        return "stale_timestamp"
    if "expired" in r:
        return "session_expired"
    if "blacklist" in r:
        return "blacklisted"
    if "decrypt" in r:
        return "decryption_failed"
    return "other"


def _detect_attack_type(reason: str) -> str:
    """Infer attack type from rejection reason."""
    r = reason.lower()
    if "hmac" in r:
        return "mitm"
    if "replay" in r or "sequence" in r:
        return "replay"
    if "stale" in r or "timestamp" in r:
        return "replay"
    if "flood" in r:
        return "flood"
    return "unknown"


def _detect_method(reason: str) -> str:
    """Infer detection method from rejection reason."""
    r = reason.lower()
    if "hmac" in r:
        return "hmac"
    if "replay" in r or "sequence" in r:
        return "sequence"
    if "stale" in r or "timestamp" in r:
        return "timestamp"
    if "ml" in r:
        return "ml"
    return "crypto"


class SimulationRunner:
    """Manages the full simulation lifecycle."""

    def __init__(self, websocket_manager: WebSocketManager):
        self.ws_manager = websocket_manager
        self.is_running = False
        self.start_time = None
        self.stop_event = None
        self.meter_tasks = []
        self.control_center = None
        self.executor = None
        self.num_meters = 0
        self.meters = []

        # Live counters
        self.lock = asyncio.Lock()
        self.total_sent = 0
        self.total_accepted = 0
        self.total_rejected = 0
        self.total_attacks = 0
        self.attacks_detected = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        self.rejection_breakdown = {
            "hmac_failed": 0,
            "replay_detected": 0,
            "stale_timestamp": 0,
            "session_expired": 0,
            "blacklisted": 0,
            "decryption_failed": 0,
            "other": 0
        }
        self.latency_samples = []
        self.crypto_latencies = []
        self.attack_log = []
        self.ml_stats = {
            "scored": 0, "flagged": 0,
            "tp": 0, "fp": 0, "tn": 0, "fn": 0,
            "score_sum": 0.0
        }
        self.meter_stats = {}
        self._stats_task = None

    def _reset_counters(self):
        """Reset all counters for a new simulation run."""
        self.total_sent = 0
        self.total_accepted = 0
        self.total_rejected = 0
        self.total_attacks = 0
        self.attacks_detected = 0
        self.false_positives = 0
        self.true_negatives = 0
        self.false_negatives = 0
        self.crypto_detections = 0
        self.ml_only_detections = 0
        self.both_detections = 0
        self.rejection_breakdown = {
            "hmac_failed": 0,
            "replay_detected": 0,
            "stale_timestamp": 0,
            "session_expired": 0,
            "blacklisted": 0,
            "decryption_failed": 0,
            "other": 0
        }
        self.latency_samples = []
        self.crypto_latencies = []
        self.attack_log = []
        self.ml_stats = {
            "scored": 0, "flagged": 0,
            "tp": 0, "fp": 0, "tn": 0, "fn": 0,
            "score_sum": 0.0
        }
        self.meter_stats = {}

    async def start(self, num_meters: int) -> dict:
        """
        Starts the simulation.
        """
        if self.is_running:
            return {"status": "error", "message": "Simulation already running"}

        self.num_meters = num_meters
        self._reset_counters()
        self.is_running = True
        self.start_time = time.time()
        self.stop_event = asyncio.Event()

        self.executor = ProcessPoolExecutor(max_workers=MAX_EXECUTOR_WORKERS)
        self.control_center = ControlCenter(executor=self.executor)

        # Wire ML calibration callback to broadcast events via WebSocket
        ws_mgr = self.ws_manager
        loop = asyncio.get_event_loop()
        def _calibration_cb(event_data):
            try:
                loop.call_soon_threadsafe(
                    lambda: asyncio.ensure_future(
                        ws_mgr.broadcast(event_data)
                    )
                )
            except Exception:
                pass
        self.control_center.ml_detector.calibration_callback = _calibration_cb

        syn = _make_rows(300)
        self.meters = []

        for i in range(num_meters):
            mid = f"SM_{str(i + 1).zfill(3)}"
            d_pk, d_sk = generate_dilithium_keypair()
            k_pk, k_sk = generate_kyber_keypair()
            self.control_center.register_meter(mid, d_pk, k_pk)
            m = SmartMeter(mid, d_sk, k_sk, self.control_center.kyber_public_key,
                           data_rows=syn, executor=self.executor)
            self.meters.append(m)
            self.meter_stats[mid] = {
                "meter_id": mid,
                "packets_sent": 0,
                "packets_accepted": 0,
                "packets_rejected": 0,
                "attacks_injected": 0,
                "attacks_detected": 0,
                "false_positives": 0
            }

        # Start meter tasks with stagger
        self.meter_tasks = []
        for i, meter in enumerate(self.meters):
            task = asyncio.create_task(
                self._run_meter(meter, i)
            )
            self.meter_tasks.append(task)

        # Start stats broadcaster
        self._stats_task = asyncio.create_task(self._broadcast_stats_loop())

        return {
            "status": "started",
            "num_meters": num_meters,
            "started_at": datetime.now().isoformat()
        }

    async def stop(self) -> dict:
        """Stops the simulation cleanly."""
        if not self.is_running:
            return {"status": "error", "message": "No simulation running"}

        self.stop_event.set()

        # Wait for meter tasks with timeout
        if self.meter_tasks:
            done, pending = await asyncio.wait(
                self.meter_tasks, timeout=15
            )
            for t in pending:
                t.cancel()

        if self._stats_task:
            self._stats_task.cancel()

        self.is_running = False

        metrics = self.calculate_final_metrics()

        # Save to verification_results.json
        try:
            with open(RESULTS_PATH, "w") as f:
                json.dump(metrics, f, indent=2, default=str)
        except Exception:
            pass

        # Broadcast simulation ended
        await self.ws_manager.broadcast_simulation_ended(metrics)

        if self.executor:
            self.executor.shutdown(wait=False)
            self.executor = None

        return metrics

    async def _run_meter(self, meter: SmartMeter, meter_index: int):
        """Run one meter, sending packets until stop event.
        
        Key behavior:
        - Re-authenticates automatically when session expires (every 900s)
        - Properly detects flood attacks (which pass crypto but are ML-flagged)
        """
        await asyncio.sleep(meter_index * METER_STARTUP_STAGGER)

        if not await meter.authenticate(self.control_center):
            return

        mid = meter.meter_id
        ms = self.meter_stats.get(mid, {})

        # Broadcast session created
        raw_sid = meter.current_session["session_id"] if meter.current_session else b""
        session_id = raw_sid.hex() if isinstance(raw_sid, bytes) else str(raw_sid)
        await self.ws_manager.broadcast_session_event({
            "action": "created",
            "meter_id": mid,
            "session_id": session_id[:16] if session_id else "",
        })

        while not self.stop_event.is_set():
            # ── Session re-establishment ──────────────────────────
            # If session expired, re-authenticate before sending
            if not meter.has_active_session():
                meter.clear_session()
                if not await meter.authenticate(self.control_center):
                    # Wait a bit and retry
                    try:
                        await asyncio.wait_for(self.stop_event.wait(), timeout=2.0)
                        break
                    except asyncio.TimeoutError:
                        continue
                # Update session_id for broadcasts
                raw_sid = meter.current_session["session_id"] if meter.current_session else b""
                session_id = raw_sid.hex() if isinstance(raw_sid, bytes) else str(raw_sid)
                await self.ws_manager.broadcast_session_event({
                    "action": "renewed",
                    "meter_id": mid,
                    "session_id": session_id[:16] if session_id else "",
                })

            initial_atk = meter.total_attacks_injected

            t0 = time.perf_counter()
            result = await meter.send_packet(self.control_center)
            elapsed_ms = (time.perf_counter() - t0) * 1000

            was_attack = meter.total_attacks_injected > initial_atk
            valid = result.get("valid", False)
            reason = result.get("reason", "")
            ml_flagged = result.get("ml_flagged", False)
            ml_score = result.get("ml_score", 0.0)

            # Skip "no_active_session" results (should be rare now)
            if reason == "no_active_session":
                continue

            async with self.lock:
                self.total_sent += 1
                self.latency_samples.append(elapsed_ms)

                ms["packets_sent"] = ms.get("packets_sent", 0) + 1

                if was_attack:
                    self.total_attacks += 1
                    ms["attacks_injected"] = ms.get("attacks_injected", 0) + 1
                    if not valid and ml_flagged:
                        self.attacks_detected += 1
                        self.both_detections += 1
                        ms["attacks_detected"] = ms.get("attacks_detected", 0) + 1
                    elif not valid and not ml_flagged:
                        self.attacks_detected += 1
                        self.crypto_detections += 1
                        ms["attacks_detected"] = ms.get("attacks_detected", 0) + 1
                    elif valid and ml_flagged:
                        self.attacks_detected += 1
                        self.ml_only_detections += 1
                        ms["attacks_detected"] = ms.get("attacks_detected", 0) + 1
                    else:
                        self.false_negatives += 1
                else:
                    if not valid:
                        self.false_positives += 1
                        ms["false_positives"] = ms.get("false_positives", 0) + 1
                    else:
                        self.true_negatives += 1

                if valid:
                    self.total_accepted += 1
                    ms["packets_accepted"] = ms.get("packets_accepted", 0) + 1
                else:
                    self.total_rejected += 1
                    ms["packets_rejected"] = ms.get("packets_rejected", 0) + 1
                    cat = _classify_reason(reason)
                    self.rejection_breakdown[cat] = self.rejection_breakdown.get(cat, 0) + 1

                # ML tracking for ALL packets — ML scores before crypto
                if ml_score != 0.0:
                    self.ml_stats["scored"] += 1
                    self.ml_stats["score_sum"] += ml_score
                    if ml_flagged:
                        self.ml_stats["flagged"] += 1
                        if was_attack:
                            self.ml_stats["tp"] += 1
                        else:
                            self.ml_stats["fp"] += 1
                    else:
                        if was_attack:
                            self.ml_stats["fn"] += 1
                        else:
                            self.ml_stats["tn"] += 1

            # ── Determine attack type properly ────────────────────
            # Flood attacks pass crypto (valid=True) but are detected by ML
            # So we can't rely solely on rejection reason for type detection
            if was_attack:
                if not valid:
                    atk_type = _detect_attack_type(reason)
                elif ml_flagged:
                    # Passed crypto but ML caught it — likely flood
                    atk_type = "flood"
                else:
                    atk_type = "flood"  # Was attack, passed everything = undetected flood
            else:
                atk_type = None

            # Get actual sequence number from the meter's session state
            seq_num = 0
            if meter.current_session and isinstance(meter.current_session, dict):
                seq_num = meter.current_session.get("sequence_number", 0)
            payload_data = result.get("payload", "")
            payload_len = len(payload_data) if valid and payload_data else 0

            # ── Handle flood burst: broadcast each sub-packet individually ──
            flood_results = result.get("_flood_results")
            actual_attack_type = result.get("_attack_type", atk_type)
            if actual_attack_type:
                atk_type = actual_attack_type

            if flood_results and len(flood_results) > 1:
                # Broadcast individual events for each flood packet
                for fi, fr in enumerate(flood_results):
                    fr_valid = fr.get("valid", False)
                    fr_ml_flagged = fr.get("ml_flagged", False)
                    fr_ml_score = fr.get("ml_score", 0.0)
                    fr_payload = fr.get("payload", "")
                    fr_pkt_event = {
                        "meter_id": mid,
                        "sequence_number": int(seq_num) - len(flood_results) + fi + 1,
                        "timestamp": time.time(),
                        "result": "accepted" if fr_valid else "rejected",
                        "reason": str(fr.get("reason", "")),
                        "was_attack": True,
                        "attack_type": "flood",
                        "ml_score": round(float(fr_ml_score), 4),
                        "ml_flagged": bool(fr_ml_flagged),
                        "payload_size": len(fr_payload) if fr_valid and fr_payload else 0
                    }
                    await self.ws_manager.broadcast_packet_event(fr_pkt_event)

                # Broadcast a single attack event for the flood burst
                flood_ml_flagged = any(fr.get("ml_flagged", False) for fr in flood_results)
                atk_event = {
                    "meter_id": mid,
                    "attack_type": "flood",
                    "detection_method": "ml" if flood_ml_flagged else "rate_analysis",
                    "timestamp": time.time(),
                    "session_id": session_id[:16] if session_id else "",
                }
                await self.ws_manager.broadcast_attack_event(atk_event)
                async with self.lock:
                    self.attack_log.append(atk_event)
            else:
                # Normal single-packet event
                pkt_event = {
                    "meter_id": mid,
                    "sequence_number": int(seq_num),
                    "timestamp": time.time(),
                    "result": "accepted" if valid else "rejected",
                    "reason": str(reason),
                    "was_attack": bool(was_attack),
                    "attack_type": atk_type,
                    "ml_score": round(float(ml_score), 4),
                    "ml_flagged": bool(ml_flagged),
                    "payload_size": payload_len
                }
                await self.ws_manager.broadcast_packet_event(pkt_event)

                # If attack detected (rejected OR ML-flagged), broadcast attack event
                if was_attack and (not valid or ml_flagged):
                    atk_event = {
                        "meter_id": mid,
                        "attack_type": atk_type or "unknown",
                        "detection_method": "ml" if valid and ml_flagged else _detect_method(reason),
                        "timestamp": time.time(),
                        "session_id": session_id[:16] if session_id else "",
                    }
                    await self.ws_manager.broadcast_attack_event(atk_event)
                    async with self.lock:
                        self.attack_log.append(atk_event)

            try:
                await asyncio.wait_for(
                    self.stop_event.wait(), timeout=PACKET_INTERVAL
                )
                break
            except asyncio.TimeoutError:
                pass

    async def _broadcast_stats_loop(self):
        """Broadcasts stats every 2 seconds while running."""
        while not self.stop_event.is_set():
            try:
                await asyncio.wait_for(self.stop_event.wait(), timeout=2.0)
                break
            except asyncio.TimeoutError:
                stats = self.get_current_stats()
                await self.ws_manager.broadcast_stats_update(stats)

    def get_current_stats(self) -> dict:
        """Returns current live statistics dict."""
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        total = self.attacks_detected + self.false_positives + self.true_negatives + self.false_negatives
        det_acc = ((self.attacks_detected + self.true_negatives) / total * 100) if total > 0 else 0.0
        fp_tn = self.false_positives + self.true_negatives
        fpr = (self.false_positives / fp_tn * 100) if fp_tn > 0 else 0.0
        throughput = self.total_sent / elapsed if elapsed > 0 else 0.0

        # Count actual active sessions and session cycles
        active_count = sum(1 for m in self.meters if m.has_active_session())
        max_session_cycle = max((m.session_count for m in self.meters), default=1) if self.meters else 1

        return {
            "total_packets": self.total_sent,
            "accepted": self.total_accepted,
            "rejected": self.total_rejected,
            "attacks_injected": self.total_attacks,
            "attacks_detected": self.attacks_detected,
            "false_positives": self.false_positives,
            "true_negatives": self.true_negatives,
            "false_negatives": self.false_negatives,
            "throughput": round(throughput, 2),
            "active_sessions": active_count,
            "detection_accuracy": round(det_acc, 2),
            "fpr": round(fpr, 2),
            "elapsed_seconds": round(elapsed, 1),
            "meters_online": self.num_meters,
            "session_cycle": max_session_cycle,
            "rejection_breakdown": dict(self.rejection_breakdown),
            "ml_stats": dict(self.ml_stats),
            "crypto_detections": self.crypto_detections,
            "ml_only_detections": self.ml_only_detections,
            "both_detections": self.both_detections,
        }

    def calculate_final_metrics(self) -> dict:
        """Calculates complete post-session metrics."""
        elapsed = time.time() - self.start_time if self.start_time else 0.0
        total = self.attacks_detected + self.false_positives + self.true_negatives + self.false_negatives
        det_acc = ((self.attacks_detected + self.true_negatives) / total * 100) if total > 0 else 0.0
        fp_tn = self.false_positives + self.true_negatives
        fpr = (self.false_positives / fp_tn * 100) if fp_tn > 0 else 0.0
        tp_fp = self.attacks_detected + self.false_positives
        precision = (self.attacks_detected / tp_fp * 100) if tp_fp > 0 else 0.0
        tp_fn = self.attacks_detected + self.false_negatives
        recall = (self.attacks_detected / tp_fn * 100) if tp_fn > 0 else 0.0
        throughput = self.total_sent / elapsed if elapsed > 0 else 0.0

        ml_total = self.ml_stats["tp"] + self.ml_stats["fp"] + self.ml_stats["tn"] + self.ml_stats["fn"]
        ml_acc = ((self.ml_stats["tp"] + self.ml_stats["tn"]) / ml_total * 100) if ml_total > 0 else 0.0

        import numpy as np
        lat = self.latency_samples or [0]
        lat_arr = np.array(lat)

        return {
            "simulation_params": {
                "num_meters": self.num_meters,
                "duration": round(elapsed, 2),
                "interval": PACKET_INTERVAL,
                "stagger": METER_STARTUP_STAGGER,
                "attack_prob": 0.08,
                "ts_window": 60,
                "executor_workers": MAX_EXECUTOR_WORKERS,
            },
            "packet_stats": {
                "total_sent": self.total_sent,
                "total_accepted": self.total_accepted,
                "total_rejected": self.total_rejected,
                "acceptance_rate": round(self.total_accepted / self.total_sent * 100, 2) if self.total_sent else 0,
                "rejection_rate": round(self.total_rejected / self.total_sent * 100, 2) if self.total_sent else 0,
                "throughput_pps": round(throughput, 2),
            },
            "attack_detection": {
                "total_injected": self.total_attacks,
                "true_positives": self.attacks_detected,
                "false_negatives": self.false_negatives,
                "true_negatives": self.true_negatives,
                "false_positives": self.false_positives,
                "detection_accuracy": round(det_acc, 2),
                "false_positive_rate": round(fpr, 2),
                "precision": round(precision, 2),
                "recall": round(recall, 2),
            },
            "rejection_breakdown": dict(self.rejection_breakdown),
            "latency_ms": {
                "e2e_avg": round(float(np.mean(lat_arr)), 2),
                "e2e_min": round(float(np.min(lat_arr)), 2),
                "e2e_max": round(float(np.max(lat_arr)), 2),
                "e2e_p95": round(float(np.percentile(lat_arr, 95)), 2),
                "e2e_p99": round(float(np.percentile(lat_arr, 99)), 2),
            },
            "session_stats": {
                "created": self.num_meters,
                "active": self.num_meters,
            },
            "ml_stats": {
                "loaded": True,
                "scored": self.ml_stats["scored"],
                "flagged": self.ml_stats["flagged"],
                "tp": self.ml_stats["tp"],
                "fp": self.ml_stats["fp"],
                "tn": self.ml_stats["tn"],
                "fn": self.ml_stats["fn"],
                "accuracy": round(ml_acc, 2),
                "avg_score": round(self.ml_stats["score_sum"] / self.ml_stats["scored"], 4) if self.ml_stats["scored"] > 0 else 0,
            },
            "per_meter": list(self.meter_stats.values()),
            "attack_log": self.attack_log[-100:],
            "verdict": {
                "status": "PASS" if fpr <= 0.5 else "FAIL",
                "detection_accuracy": round(det_acc, 2),
                "fpr": round(fpr, 2),
                "precision": round(precision, 2),
                "recall": round(recall, 2),
            }
        }
