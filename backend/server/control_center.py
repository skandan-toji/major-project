"""
control_center.py -- Control Center Server (Scalable Architecture)

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

The Control Center:
  - Receives and verifies Dilithium5 authentication packets
  - Creates sessions and performs Kyber1024 key exchange
  - Receives encrypted data packets
  - Verifies: HMAC first, then sequence number, then timestamp
  - Decrypts payloads using AES-256-GCM
  - Extracts traffic features and logs them to CSV for ML dataset generation

Architecture (v2 — Scalable):
  - Dilithium5 verify() and Kyber1024 encrypt() run in ProcessPoolExecutor
    to avoid blocking the asyncio event loop with CPU-heavy PQC operations.
  - Each meter gets its own asyncio.Queue so packets from the same meter
    are always processed in strict FIFO order, preventing sequence
    desynchronization under load.
  - Timestamp window is configurable via config.py.
"""

import asyncio
import time

from crypto.dilithium_module import verify_signature
from crypto.kyber_module import generate_kyber_keypair, encrypt_aes_key
from crypto.aes_module import generate_aes_key, generate_nonce, decrypt_payload
from crypto.hmac_module import verify_hmac
from crypto.packet_builder import verify_auth_packet
from session.session_manager import SessionManager
from dataset_ML.traffic_feature_extractor import TrafficFeatureExtractor
from ml.isolation_forest import IsolationForestDetector, load_detector, AnomalyDetector
from ml.meter_baseline import MeterBaselineTracker
from config import TIMESTAMP_WINDOW


# ── Top-level functions for ProcessPoolExecutor ─────────────────
# These MUST be defined at module level (not as methods) so they
# can be pickled and sent to worker processes on Windows.

def _verify_auth_packet_sync(auth_packet: dict, public_key: bytes) -> bool:
    """Runs Dilithium5 signature verification (CPU-heavy) in a worker process."""
    return verify_auth_packet(auth_packet, public_key)


def _encrypt_aes_key_sync(kyber_public_key: bytes, aes_key: bytes) -> bytes:
    """Runs Kyber1024 key encapsulation (CPU-heavy) in a worker process."""
    return encrypt_aes_key(kyber_public_key, aes_key)


class ControlCenter:
    """
    Simulates the Control Center that manages all smart meter
    communication, verification, and session management.

    Attributes:
        kyber_public_key (bytes):    Shared with meters at registration.
        kyber_private_key (bytes):   Never leaves the Control Center.
        session_manager (SessionManager): Manages active/expired sessions.
        device_registry (dict):      meter_id -> {dilithium_pk, kyber_pk}
        traffic_feature_extractor (TrafficFeatureExtractor): Extracts and logs features to CSV.
        packets_received (int):      Total packets received.
        packets_accepted (int):      Total packets accepted.
        packets_rejected (int):      Total packets rejected.
        auth_success_count (int):    Successful authentications.
        auth_fail_count (int):       Failed authentications.
        executor:                    ProcessPoolExecutor for CPU-heavy PQC ops.
        meter_queues (dict):         meter_id -> asyncio.Queue for ordered processing.
        queue_workers (dict):        meter_id -> asyncio.Task running the queue worker.
    """

    def __init__(self, executor=None):
        """
        Initialize the Control Center.

        Args:
            executor: A concurrent.futures.ProcessPoolExecutor instance.
                      If None, Dilithium/Kyber ops run synchronously (for tests).
        """
        self.kyber_public_key, self.kyber_private_key = generate_kyber_keypair()
        self.session_manager = SessionManager()
        self.device_registry = {}
        self.traffic_feature_extractor = TrafficFeatureExtractor()
        self.packets_received = 0
        self.packets_accepted = 0
        self.packets_rejected = 0
        self.auth_success_count = 0
        self.auth_fail_count = 0

        # ProcessPoolExecutor for CPU-heavy PQC operations
        self.executor = executor

        # Per-meter ordered packet queues
        self.meter_queues = {}      # meter_id -> asyncio.Queue
        self.queue_workers = {}     # meter_id -> asyncio.Task

        # ML components
        self.baseline_tracker = MeterBaselineTracker()
        self.ml_detector      = IsolationForestDetector()
        self.ml_flagged_count = 0

        # Legacy AnomalyDetector kept for stats reporting
        try:
            self.anomaly_detector = load_detector()
            print("[CONTROL CENTER] Anomaly detector loaded.")
        except RuntimeError:
            self.anomaly_detector = None
            print("[CONTROL CENTER] No ML model found. Run ml/retrain_model.py first.")

    def register_meter(self, meter_id: str,
                       dilithium_public_key: bytes,
                       kyber_public_key: bytes):
        """
        Registers a smart meter in the device registry.
        """
        self.device_registry[meter_id] = {
            "dilithium_public_key": dilithium_public_key,
            "kyber_public_key": kyber_public_key,
        }

    def get_public_key(self) -> bytes:
        """
        Returns the Control Center's Kyber1024 public key.
        """
        return self.kyber_public_key

    # ── Per-Meter Queue Management ──────────────────────────────

    def _get_or_create_meter_queue(self, meter_id: str) -> asyncio.Queue:
        """
        Gets existing queue for meter or creates a new one.
        Also starts a queue worker task if not running.
        """
        if meter_id not in self.meter_queues:
            self.meter_queues[meter_id] = asyncio.Queue()
            task = asyncio.create_task(
                self._process_meter_queue(meter_id)
            )
            self.queue_workers[meter_id] = task
        return self.meter_queues[meter_id]

    async def _process_meter_queue(self, meter_id: str):
        """
        Continuously processes packets from one meter's queue
        in strict FIFO order. This guarantees sequence numbers
        are checked in the correct order even under heavy load.
        """
        queue = self.meter_queues[meter_id]
        while True:
            packet, result_future = await queue.get()
            try:
                result = await self._verify_and_process(packet)
                if not result_future.done():
                    result_future.set_result(result)
            except Exception as e:
                if not result_future.done():
                    result_future.set_exception(e)
            finally:
                queue.task_done()

    # ── Authentication ──────────────────────────────────────────

    async def process_auth_request(self, auth_packet: dict) -> dict:
        """
        Processes an authentication request from a Smart Meter.

        Dilithium5 verify and Kyber1024 encrypt are offloaded to
        the ProcessPoolExecutor to avoid blocking the event loop.
        """
        try:
            meter_id = auth_packet.get("device_id")

            if meter_id not in self.device_registry:
                self.auth_fail_count += 1
                return {"success": False, "reason": "unregistered_device"}

            device_info = self.device_registry[meter_id]
            dil_pk = device_info["dilithium_public_key"]
            kyb_pk = device_info["kyber_public_key"]

            # Offload Dilithium5 verify to ProcessPoolExecutor
            if self.executor is not None:
                loop = asyncio.get_event_loop()
                sig_valid = await loop.run_in_executor(
                    self.executor,
                    _verify_auth_packet_sync,
                    auth_packet,
                    dil_pk
                )
            else:
                sig_valid = verify_auth_packet(auth_packet, dil_pk)

            if not sig_valid:
                self.auth_fail_count += 1
                return {"success": False, "reason": "invalid_signature"}

            aes_key = generate_aes_key()
            nonce = generate_nonce()

            session = self.session_manager.create_session(
                meter_id, aes_key, nonce
            )

            # Offload Kyber1024 encrypt to ProcessPoolExecutor
            if self.executor is not None:
                loop = asyncio.get_event_loop()
                encrypted_aes_key = await loop.run_in_executor(
                    self.executor,
                    _encrypt_aes_key_sync,
                    kyb_pk,
                    aes_key
                )
            else:
                encrypted_aes_key = encrypt_aes_key(kyb_pk, aes_key)

            self.auth_success_count += 1
            return {
                "success": True,
                "session_id": session.session_id,
                "nonce": session.nonce,
                "encrypted_aes_key": encrypted_aes_key,
            }

        except Exception as e:
            self.auth_fail_count += 1
            return {"success": False, "reason": "auth_error: " + str(e)}

    # ── Data Packet Processing (Queue Entry Point) ──────────────

    async def process_data_packet(self, packet: dict) -> dict:
        """
        Enqueues a data packet into the correct meter's ordered queue.

        The queue worker processes packets in strict FIFO order per meter,
        guaranteeing that sequence numbers are never checked out of order
        regardless of event loop scheduling.
        """
        meter_id = packet.get("device_id", "unknown")
        queue = self._get_or_create_meter_queue(meter_id)

        # Create a future to get the result back from the queue worker
        loop = asyncio.get_event_loop()
        future = loop.create_future()

        # Put packet in meter's ordered queue
        await queue.put((packet, future))

        # Wait for the queue worker to process it and return the result
        result = await future
        return result

    # ── Data Packet Verification (Actual Logic) ─────────────────

    async def _verify_and_process(self, packet: dict) -> dict:
        """
        Verification with ML-before-crypto architecture.

        Order:
            1. Extract identifiers and compute behavioral features
            2. ML scores packet (BEFORE crypto — sees anomalous features)
            3. Crypto verification: HMAC → seq → timestamp → decrypt
            4. Update baseline with crypto outcome
            5. Return result with ml_score attached
        """
        self.packets_received += 1

        meter_id    = packet.get("device_id", "unknown")
        pkt_seq     = packet.get("sequence_number", 0)
        pkt_ts      = packet.get("timestamp", 0.0)
        payload_size = len(packet.get("cipher_data", "")) // 2
        packet_time = time.time()
        session_start = 0.0

        # ── STEP 1: Behavioral feature computation ───────────────
        baseline = self.baseline_tracker.get_or_create(meter_id)

        if baseline.last_packet_time is not None:
            iat = packet_time - baseline.last_packet_time
            if iat <= 0:
                iat = 0.001
        else:
            iat = 1.0
        current_rate = 1.0 / iat

        ts_delta = abs(packet_time - pkt_ts)

        # Peek at session for seq_delta and session_duration
        # (safe read — does not modify session state)
        session_id_hex = packet.get("session_id", "")
        try:
            session_id_bytes = bytes.fromhex(session_id_hex)
            peek_session = self.session_manager.get_session(session_id_bytes)
        except Exception:
            peek_session = None

        if peek_session is not None:
            seq_delta    = pkt_seq - peek_session.expected_sequence()
            session_start = peek_session.created_at
            sess_dur     = packet_time - session_start
        else:
            seq_delta = 0
            sess_dur  = 0.0

        dev = self.baseline_tracker.get_deviation_features(
            meter_id, payload_size, iat, current_rate
        )

        # ── STEP 2: ML scores BEFORE crypto ─────────────────────
        # At this point hmac/seq/ts validity is still unknown.
        # We pass 1 as assumption; the seq_delta and ts_delta already
        # capture replay and stale-timestamp signals.
        ml_features = {
            "packet_rate"          : current_rate,
            "inter_arrival_time"   : iat,
            "payload_size"         : float(payload_size),
            "sequence_delta"       : float(seq_delta),
            "timestamp_delta"      : float(ts_delta),
            "session_duration"     : float(sess_dur),
            "hmac_valid"           : 1.0,
            "seq_check_valid"      : 1.0,
            "timestamp_valid"      : 1.0,
            "payload_size_zscore"  : dev["payload_size_zscore"],
            "inter_arrival_zscore" : dev["inter_arrival_zscore"],
            "rate_spike_ratio"     : dev["rate_spike_ratio"],
            "consecutive_failures" : float(dev["consecutive_failures"]),
            "session_packet_count" : float(dev["session_packet_count"]),
        }
        ml_result = self.ml_detector.score_packet(ml_features)
        if ml_result["is_anomaly"]:
            self.ml_flagged_count += 1

        # ── STEP 3: Crypto verification ──────────────────────────
        hmac_valid_flag  = 0
        seq_valid_flag   = 0
        ts_valid_flag    = 0
        crypto_passed    = False

        try:
            if not session_id_hex:
                self.packets_rejected += 1
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "missing_session_id"}, ml_result)

            if self.session_manager.is_session_blacklisted(session_id_bytes):
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 0, 0, 0)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "blacklisted_session"}, ml_result)

            session = self.session_manager.get_session(session_id_bytes)
            if session is None:
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 0, 0, 0)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "session_not_found_or_expired"}, ml_result)

            session_start = session.created_at

            pkt_nonce      = bytes.fromhex(packet["nonce"])
            pkt_cipher     = bytes.fromhex(packet["cipher_data"])
            pkt_auth_tag   = bytes.fromhex(packet["aes_auth_tag"])
            pkt_hmac       = bytes.fromhex(packet["hmac_tag"])

            hmac_ok = verify_hmac(
                aes_key=session.aes_key, session_id=session_id_bytes,
                nonce=pkt_nonce, sequence_number=pkt_seq, timestamp=pkt_ts,
                cipher_data=pkt_cipher, aes_auth_tag=pkt_auth_tag,
                received_hmac=pkt_hmac,
            )
            if not hmac_ok:
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 0, 0, 0)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "hmac_failed"}, ml_result)
            hmac_valid_flag = 1

            expected_seq = session.expected_sequence()
            if pkt_seq != expected_seq:
                actual_delta = pkt_seq - expected_seq
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 1, 0, 0, seq_delta=actual_delta)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "replay_detected"}, ml_result)
            seq_valid_flag = 1

            if abs(time.time() - pkt_ts) > TIMESTAMP_WINDOW:
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 1, 1, 0)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "stale_timestamp"}, ml_result)
            ts_valid_flag = 1

            try:
                decrypted = decrypt_payload(
                    aes_key=session.aes_key, nonce=session.nonce,
                    ciphertext=pkt_cipher, auth_tag=pkt_auth_tag,
                )
            except Exception:
                self.packets_rejected += 1
                self._log_rejection(meter_id, session_id_hex, pkt_seq, pkt_ts,
                                    packet, session_start, 1, 1, 1)
                self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
                return self._attach_ml({"valid": False, "reason": "decryption_failed"}, ml_result)

            # All checks passed
            session.increment_sequence()
            self.packets_accepted += 1
            crypto_passed = True

            # Feed accepted packet score into online calibration so the
            # detector learns the live normal score distribution and
            # auto-adjusts its effective threshold.
            if "anomaly_score" in ml_result:
                self.ml_detector.record_accepted_score(ml_result["anomaly_score"])

            # ── STEP 4: Update baseline with outcome ─────────────
            self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, True)

            # Log to CSV (label=0 for accepted packets)
            self.traffic_feature_extractor.log_packet(
                meter_id=meter_id, session_id=session_id_hex,
                sequence_number=pkt_seq, payload_size=payload_size,
                packet_timestamp=pkt_ts, sequence_delta=0,
                hmac_valid=1, seq_check_valid=1, timestamp_valid=1,
                session_start_time=session_start, label=0,
            )

            return self._attach_ml({
                "valid"  : True,
                "reason" : "accepted",
                "payload": decrypted,
            }, ml_result)

        except Exception as e:
            self.packets_rejected += 1
            self.baseline_tracker.update_meter(meter_id, payload_size, packet_time, False)
            return self._attach_ml({"valid": False, "reason": f"processing_error: {e}"}, ml_result)

    def _attach_ml(self, result: dict, ml_result: dict) -> dict:
        """Attach ML scoring fields to any result dict."""
        result["ml_score"]      = ml_result.get("anomaly_score", 0.0)
        result["ml_flagged"]    = ml_result.get("is_anomaly", False)
        result["ml_confidence"] = ml_result.get("confidence", 0.0)
        return result

    def _log_rejection(self, meter_id, session_id_hex, seq_num,
                       pkt_ts, packet, session_start,
                       hmac_valid=0, seq_valid=0, ts_valid=0,
                       seq_delta=None):
        """
        Helper to log a rejected packet to the TrafficFeatureExtractor with label=1.
        """
        payload_size = len(packet.get("cipher_data", "")) // 2
        if seq_delta is None:
            seq_delta = 0

        try:
            self.traffic_feature_extractor.log_packet(
                meter_id=meter_id,
                session_id=session_id_hex,
                sequence_number=seq_num,
                payload_size=payload_size,
                packet_timestamp=pkt_ts,
                sequence_delta=seq_delta,
                hmac_valid=hmac_valid,
                seq_check_valid=seq_valid,
                timestamp_valid=ts_valid,
                session_start_time=session_start,
                label=1,
            )
        except Exception:
            pass

    def get_stats(self) -> dict:
        """
        Returns Control Center operational statistics.
        """
        return {
            "packets_received": self.packets_received,
            "packets_accepted": self.packets_accepted,
            "packets_rejected": self.packets_rejected,
            "auth_success": self.auth_success_count,
            "auth_failed": self.auth_fail_count,
            "active_sessions": self.session_manager.list_active_sessions(),
            "ml_flagged_count": self.ml_flagged_count,
            "ml_loaded": self.anomaly_detector is not None
        }


print("[MODULE LOADED] control_center.py ready")
