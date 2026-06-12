"""
smart_meter.py -- Smart Meter Simulator (Scalable Architecture)

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Simulates one physical smart meter node that:
  - Loads power consumption data from a real dataset CSV
  - Authenticates with the Control Center using Dilithium5
  - Establishes a session using Kyber1024 key exchange
  - Sends encrypted data packets using AES-256-GCM + HMAC-SHA256
  - Tracks its own session expiry and re-authenticates automatically
  - Integrates automated attack injection for ML dataset generation

Architecture (v2 — Scalable):
  - Dilithium5 sign() and Kyber1024 decrypt() are offloaded to a
    ProcessPoolExecutor to avoid blocking the asyncio event loop.
  - Timestamps are stamped at send time (not build time) and HMAC
    is recomputed with the fresh timestamp, eliminating stale
    timestamp false positives under load.
"""

import asyncio
import time
import json
import csv
import os

from crypto.packet_builder import build_auth_packet, build_data_packet
from crypto.dilithium_module import sign_message
from crypto.kyber_module import decrypt_aes_key
from crypto.hmac_module import compute_hmac
from attacks.attack_injector import AttackSessionManager, inject_attack

# Default path to the power consumption dataset (relative to backend/)
DEFAULT_DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "dataset_traffic",
    "power_dataset_clean_100k.csv",
)


# ── Top-level functions for ProcessPoolExecutor ─────────────────
# These MUST be at module level (not methods) so they can be pickled
# and sent to worker processes on Windows.

def _build_auth_packet_sync(meter_id: str, private_key: bytes) -> dict:
    """Builds auth packet (includes Dilithium5 sign — CPU-heavy) in a worker."""
    return build_auth_packet(meter_id, private_key)


def _decrypt_aes_key_sync(kyber_private_key: bytes, encrypted_key: bytes) -> bytes:
    """Decrypts AES key using Kyber1024 (CPU-heavy) in a worker."""
    return decrypt_aes_key(kyber_private_key, encrypted_key)


class SmartMeter:
    """
    Simulates one physical smart meter node.

    Every packet payload is sourced from a real power consumption dataset.
    The meter cycles through its assigned data rows automatically.
    No hardcoded values are ever transmitted.

    Integrated with an AttackSessionManager to simulate malicious traffic
    probabilistically for ML training.

    Attributes:
        meter_id (str):                Meter identifier e.g. "SM_001".
        dilithium_private_key (bytes): Dilithium5 private key (never transmitted).
        kyber_private_key (bytes):     Kyber1024 private key (never transmitted).
        kyber_public_key_cc (bytes):   Control Center's Kyber public key.
        data_rows (list):              Dataset rows loaded from CSV.
        row_index (int):               Current position in data_rows (cycles).
        current_session (dict or None): Current active session material.
        last_packet_time (float):      Timestamp of last sent packet.
        packet_count (int):            Total packets sent across all sessions.
        session_count (int):           Total sessions established.
        attack_manager (AttackSessionManager): Manages attack probabilities.
        total_attacks_injected (int):  Count of attack decisions made.
        attack_packets_sent (int):     Actual count of malicious packets sent.
        executor:                      ProcessPoolExecutor for CPU-heavy PQC ops.
    """

    def __init__(self, meter_id: str,
                 dilithium_private_key: bytes,
                 kyber_private_key: bytes,
                 kyber_public_key_cc: bytes,
                 data_rows: list = None,
                 dataset_path: str = None,
                 max_rows: int = None,
                 executor=None):
        """
        Initialize the SmartMeter with its cryptographic keys and dataset.

        Args:
            executor: ProcessPoolExecutor for Dilithium/Kyber ops.
                      If None, ops run synchronously (for simple tests).
        """
        self.meter_id = meter_id
        self.dilithium_private_key = dilithium_private_key
        self.kyber_private_key = kyber_private_key
        self.kyber_public_key_cc = kyber_public_key_cc
        self.current_session = None
        self.last_packet_time = 0.0
        self.packet_count = 0
        self.session_count = 0

        # ProcessPoolExecutor for CPU-heavy PQC operations
        self.executor = executor

        # Initialize Attack Manager
        self.attack_manager = AttackSessionManager()
        self.total_attacks_injected = 0
        self.attack_packets_sent = 0

        # Load dataset: use provided rows or load from CSV
        if data_rows is not None:
            self.data_rows = data_rows
        else:
            self.data_rows = SmartMeter.load_dataset_from_csv(
                csv_path=dataset_path, max_rows=max_rows
            )
        self.row_index = 0

    @staticmethod
    def load_dataset_from_csv(csv_path: str = None,
                              max_rows: int = None) -> list:
        """
        Loads power consumption data from the real dataset CSV.
        """
        if csv_path is None:
            csv_path = DEFAULT_DATASET_PATH

        rows = []
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if max_rows is not None and i >= max_rows:
                    break
                rows.append({
                    "date": row["Date"],
                    "time": row["Time"],
                    "global_active_power": float(row["Global_active_power"]),
                    "global_reactive_power": float(row["Global_reactive_power"]),
                    "voltage": float(row["Voltage"]),
                    "global_intensity": float(row["Global_intensity"]),
                    "sub_metering_1": float(row["Sub_metering_1"]),
                    "sub_metering_2": float(row["Sub_metering_2"]),
                    "sub_metering_3": float(row["Sub_metering_3"]),
                })
        return rows

    def next_payload(self) -> dict:
        """
        Returns the next payload from the dataset, cycling through rows.
        """
        row = self.data_rows[self.row_index % len(self.data_rows)]
        self.row_index += 1
        payload = {"device_id": self.meter_id}
        payload.update(row)
        return payload

    def peek_payload(self) -> dict:
        """
        Returns what the next payload would be WITHOUT advancing the index.
        """
        row = self.data_rows[self.row_index % len(self.data_rows)]
        payload = {"device_id": self.meter_id}
        payload.update(row)
        return payload

    def has_active_session(self) -> bool:
        """
        Checks if the meter currently has a valid, non-expired session.
        """
        if self.current_session is None:
            return False
        return time.time() <= self.current_session["expiry_time"]

    def clear_session(self):
        """
        Clears the current session and informs attack manager.
        """
        if self.current_session:
            self.attack_manager.end_session(
                self.current_session["session_id"]
            )
        self.current_session = None

    async def authenticate(self, control_center) -> bool:
        """
        Performs Dilithium5 authentication and Kyber1024 key exchange.

        Dilithium5 sign (via build_auth_packet) and Kyber1024 decrypt
        are offloaded to the ProcessPoolExecutor.
        """
        try:
            # Offload Dilithium5 sign to ProcessPoolExecutor
            if self.executor is not None:
                loop = asyncio.get_event_loop()
                auth_packet = await loop.run_in_executor(
                    self.executor,
                    _build_auth_packet_sync,
                    self.meter_id,
                    self.dilithium_private_key
                )
            else:
                auth_packet = build_auth_packet(
                    self.meter_id, self.dilithium_private_key
                )

            response = await control_center.process_auth_request(auth_packet)

            if not response.get("success", False):
                self.clear_session()
                return False

            encrypted_aes_key = response["encrypted_aes_key"]

            # Offload Kyber1024 decrypt to ProcessPoolExecutor
            if self.executor is not None:
                loop = asyncio.get_event_loop()
                aes_key = await loop.run_in_executor(
                    self.executor,
                    _decrypt_aes_key_sync,
                    self.kyber_private_key,
                    encrypted_aes_key
                )
            else:
                aes_key = decrypt_aes_key(self.kyber_private_key, encrypted_aes_key)

            self.current_session = {
                "session_id": response["session_id"],
                "aes_key": aes_key,
                "nonce": response["nonce"],
                "sequence_number": 0,
                "expiry_time": time.time() + 900,
            }

            self.session_count += 1

            # Register session with attack manager
            self.attack_manager.register_session(
                session_id=self.current_session["session_id"],
                meter_id=self.meter_id
            )

            return True

        except Exception:
            self.clear_session()
            return False

    def _stamp_and_resign(self, packet: dict) -> dict:
        """
        FIX 4: Stamps a fresh timestamp on the packet at send time
        and recomputes the HMAC with the new timestamp.

        This ensures the timestamp reflects actual send time,
        not build time, eliminating stale_timestamp false positives.
        """
        fresh_ts = time.time()
        packet["timestamp"] = fresh_ts

        # Recompute HMAC with fresh timestamp
        new_hmac = compute_hmac(
            aes_key=self.current_session["aes_key"],
            session_id=bytes.fromhex(packet["session_id"]),
            nonce=bytes.fromhex(packet["nonce"]),
            sequence_number=packet["sequence_number"],
            timestamp=fresh_ts,
            cipher_data=bytes.fromhex(packet["cipher_data"]),
            aes_auth_tag=bytes.fromhex(packet["aes_auth_tag"])
        )
        packet["hmac_tag"] = new_hmac.hex()
        return packet

    async def send_packet(self, control_center, payload: dict = None) -> dict:
        """
        Builds and sends packets (may inject attacks).

        FIX 4: Non-attack packets get a fresh timestamp + HMAC
        immediately before sending to prevent stale_timestamp
        false positives under load.
        """
        if not self.has_active_session():
            return {"valid": False, "reason": "no_active_session"}

        try:
            if payload is None:
                payload = self.next_payload()

            # 1. Build the valid packet (incrementing sequence)
            self.current_session["sequence_number"] += 1
            packet = build_data_packet(
                self.meter_id, self.current_session, payload
            )

            # 2. Decide whether to inject an attack
            packets_to_send, is_attack, attack_type = inject_attack(
                meter_id=self.meter_id,
                session_id=self.current_session["session_id"],
                valid_packet=packet,
                session=self.current_session,
                attack_session_manager=self.attack_manager,
                packet_number=self.packet_count
            )

            # 3. Revert the sequence increment for attacks that the CC will reject
            #    without calling session.increment_sequence():
            #    - replay: CC rejects with replay_detected (stale seq)
            #    - mitm:   CC rejects with hmac_failed (tampered data)
            #    In both cases the CC's expected sequence does NOT advance,
            #    so the meter must revert to stay in sync.
            if is_attack and attack_type in ("replay", "mitm"):
                self.current_session["sequence_number"] -= 1

            results = []
            if is_attack and attack_type == "flood":
                # Save sequence BEFORE flood starts
                seq_before_flood = self.current_session["sequence_number"]
                for p in packets_to_send:
                    send_pkt = {k: v for k, v in p.items() if not k.startswith("_")}
                    self.total_attacks_injected += 1
                    self.attack_packets_sent += 1
                    result = await control_center.process_data_packet(send_pkt)
                    results.append(result)
                    await asyncio.sleep(0.02)
                # After flood: CC's last_sequence_number is at the highest accepted seq.
                # Flood packets use seq: base_seq, base_seq+1, ..., base_seq+N-1
                # CC accepted some → its last_sequence = base_seq + accepted_count - 1
                # Next send_packet() call increments by 1 first, giving base_seq + accepted_count
                # So set meter seq to base_seq + accepted_count - 1
                flood_accepted_count = sum(1 for r in results if r.get("valid", False))
                if flood_accepted_count > 0:
                    self.current_session["sequence_number"] = seq_before_flood + flood_accepted_count - 1
                else:
                    # All flood packets rejected — CC didn't advance, revert to before flood
                    self.current_session["sequence_number"] = seq_before_flood - 1
            else:
                for p in packets_to_send:
                    # Strip internal metadata before sending
                    send_pkt = {k: v for k, v in p.items() if not k.startswith("_")}

                    # FIX 4: Stamp fresh timestamp at send time for non-attack packets
                    if not is_attack:
                        send_pkt = self._stamp_and_resign(send_pkt)

                    if is_attack:
                        self.total_attacks_injected += 1
                        self.attack_packets_sent += 1

                    result = await control_center.process_data_packet(send_pkt)
                    results.append(result)

            # Update stats
            self.last_packet_time = time.time()
            self.packet_count += 1

            final_result = results[-1]
            # Attach flood burst metadata so the runner can broadcast each sub-packet
            if is_attack and attack_type == "flood" and len(results) > 1:
                final_result["_flood_results"] = results
                final_result["_flood_count"] = len(results)
            if is_attack:
                final_result["_attack_type"] = attack_type

            return final_result

        except Exception as e:
            return {"valid": False, "reason": "send_error: " + str(e)}

    async def send_next(self, control_center) -> dict:
        """
        Convenience method: sends the next dataset row as a packet.
        """
        return await self.send_packet(control_center)

    async def run_session(self, control_center,
                          data_rows: list = None,
                          stop_event=None,
                          interval: float = 1.0,
                          max_packets: int = None) -> dict:
        """
        Runs a complete session loop for this meter.
        """
        original_rows = None
        original_index = None
        if data_rows is not None:
            original_rows = self.data_rows
            original_index = self.row_index
            self.data_rows = data_rows
            self.row_index = 0

        if stop_event is None:
            stop_event = asyncio.Event()

        auth_ok = await self.authenticate(control_center)
        if not auth_ok:
            if original_rows is not None:
                self.data_rows = original_rows
                self.row_index = original_index
            return {
                "meter_id": self.meter_id,
                "packets_sent": 0,
                "sessions_used": 0,
            }

        packets_this_run = 0
        while not stop_event.is_set():
            if max_packets is not None and packets_this_run >= max_packets:
                break

            if not self.has_active_session():
                auth_ok = await self.authenticate(control_center)
                if not auth_ok:
                    break

            await self.send_next(control_center)
            packets_this_run += 1

            if max_packets is not None and packets_this_run >= max_packets:
                break
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass

        if original_rows is not None:
            self.data_rows = original_rows
            self.row_index = original_index

        return {
            "meter_id": self.meter_id,
            "packets_sent": self.packet_count,
            "sessions_used": self.session_count,
            "attacks_injected": self.total_attacks_injected
        }


print("[MODULE LOADED] smart_meter.py ready")
