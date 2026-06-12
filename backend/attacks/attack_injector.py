"""
attack_injector.py -- Background Attack Injection Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

This module automates the generation of malicious traffic for ML training.
It includes a probability engine and builders for Replay, MITM (Tampering),
and Flood attacks.
"""

import random
import time
import copy
import struct
import hmac as hmac_lib
import hashlib
from crypto.hmac_module import compute_hmac

# Probability Constants
ATTACK_PROBABILITY = 0.08      # 8% of individual packets in normal sessions
SESSION_ATTACK_PROB = 0.15     # 15% of sessions are "Attack Sessions" (high frequency)

def should_inject_attack(attack_probability: float = 0.08) -> bool:
    """
    Rolls against attack_probability using random.random().
    Returns True if this packet should be an attack.
    """
    return random.random() < attack_probability

def pick_attack_type() -> str:
    """
    Randomly picks attack type based on distribution:
      roll < 0.50  -> "replay"
      roll < 0.80  -> "mitm"
      roll >= 0.80 -> "flood"
    """
    roll = random.random()
    if roll < 0.50:
        return "replay"
    elif roll < 0.80:
        return "mitm"
    else:
        return "flood"

def is_attack_session(session_attack_prob: float = 0.15) -> bool:
    """
    Decides at session creation time whether this entire session
    will be an attack session with elevated frequency.
    """
    return random.random() < session_attack_prob

def build_replay_attack(valid_packet: dict, session: dict) -> dict:
    """
    Constructs a replay attack packet from a previously valid packet.
    Updates sequence and timestamp to be stale, then recomputes HMAC.
    """
    packet = copy.deepcopy(valid_packet)
    
    # Get current sequence for reference
    current_seq = session.get("sequence_number", 1)
    
    # Set sequence to a deliberately old value
    replayed_seq = max(1, current_seq - random.randint(5, 20))
    
    # Set timestamp to a stale value (outside 30s window)
    replayed_timestamp = time.time() - random.uniform(35, 120)
    
    # Recompute HMAC with replayed values to make it "consistent" but stale
    new_hmac = compute_hmac(
        aes_key=session["aes_key"],
        session_id=bytes.fromhex(packet["session_id"]),
        nonce=bytes.fromhex(packet["nonce"]),
        sequence_number=replayed_seq,
        timestamp=replayed_timestamp,
        cipher_data=bytes.fromhex(packet["cipher_data"]),
        aes_auth_tag=bytes.fromhex(packet["aes_auth_tag"])
    )
    
    packet["sequence_number"] = replayed_seq
    packet["timestamp"] = replayed_timestamp
    packet["hmac_tag"] = new_hmac.hex()
    packet["_attack_type"] = "replay"
    
    return packet

def build_mitm_attack(valid_packet: dict) -> dict:
    """
    Constructs a MITM/tampering attack packet by flipping a bit in cipher_data.
    Does NOT recompute HMAC, causing immediate verification failure.
    """
    packet = copy.deepcopy(valid_packet)
    cipher_bytes = bytearray(bytes.fromhex(packet["cipher_data"]))
    
    if len(cipher_bytes) > 0:
        # Flip all bits in one random byte
        pos = random.randint(0, len(cipher_bytes) - 1)
        cipher_bytes[pos] ^= 0xFF
        
    packet["cipher_data"] = cipher_bytes.hex()
    packet["_attack_type"] = "mitm"
    
    return packet

def build_flood_packets(valid_packet: dict, session: dict, count: int = 20, base_seq: int = None) -> list:
    """
    Constructs a burst of valid packets with rapid sequence increments.
    Passed cryptographic checks but detected by ML rate analysis.
    """
    packets = []
    if base_seq is None:
        base_seq = session.get("sequence_number", 0)
    
    for i in range(count):
        packet = copy.deepcopy(valid_packet)
        seq = base_seq + i
        ts = time.time()
        
        # Recompute HMAC for each flood packet so they pass crypto checks
        new_hmac = compute_hmac(
            aes_key=session["aes_key"],
            session_id=bytes.fromhex(packet["session_id"]),
            nonce=bytes.fromhex(packet["nonce"]),
            sequence_number=seq,
            timestamp=ts,
            cipher_data=bytes.fromhex(packet["cipher_data"]),
            aes_auth_tag=bytes.fromhex(packet["aes_auth_tag"])
        )
        
        packet["sequence_number"] = seq
        packet["timestamp"] = ts
        packet["hmac_tag"] = new_hmac.hex()
        packet["_attack_type"] = "flood"
        packets.append(packet)
        
    return packets

class AttackSessionManager:
    """
    Tracks session-level attack states and packet history for replay simulation.
    """
    def __init__(self):
        self.attack_sessions = {}  # session_id (hex) -> bool
        self.packet_history = {}   # meter_id -> list of valid packets
        
    def register_session(self, session_id: bytes, meter_id: str):
        """Called on session creation to determine session type."""
        sid_hex = session_id.hex()
        self.attack_sessions[sid_hex] = is_attack_session(SESSION_ATTACK_PROB)
        if meter_id not in self.packet_history:
            self.packet_history[meter_id] = []

    def is_attack_session(self, session_id: bytes) -> bool:
        """Returns True if the session is an elevated attack frequency session."""
        return self.attack_sessions.get(session_id.hex(), False)

    def record_valid_packet(self, meter_id: str, packet: dict):
        """Stores a valid packet for future replay candidates."""
        if meter_id not in self.packet_history:
            self.packet_history[meter_id] = []
        
        # Keep only the last 5 packets
        self.packet_history[meter_id].append(copy.deepcopy(packet))
        if len(self.packet_history[meter_id]) > 5:
            self.packet_history[meter_id].pop(0)

    def get_replay_candidate(self, meter_id: str):
        """Returns a random historical packet from the specific meter."""
        history = self.packet_history.get(meter_id, [])
        if not history:
            return None
        return random.choice(history)

    def should_attack_this_packet(self, session_id: bytes, 
                                   meter_id: str, 
                                   packet_number: int) -> bool:
        """Decides if the current packet should be converted to an attack."""
        if self.is_attack_session(session_id):
            # Attack session logic: attack every 5th to 10th packet
            return packet_number > 0 and (packet_number % random.randint(5, 10) == 0)
        else:
            # Normal session logic: standard 8% roll
            return should_inject_attack(ATTACK_PROBABILITY)

    def end_session(self, session_id: bytes):
        """Cleans up session tracking."""
        sid_hex = session_id.hex()
        if sid_hex in self.attack_sessions:
            del self.attack_sessions[sid_hex]

def inject_attack(meter_id: str,
                  session_id: bytes,
                  valid_packet: dict,
                  session: dict,
                  attack_session_manager: AttackSessionManager,
                  packet_number: int) -> tuple:
    """
    Master function to decide and build attack packets.
    Returns: (packets_to_send: list, is_attack: bool, attack_type: str)
    """
    # 1. Record valid packet for future replays
    attack_session_manager.record_valid_packet(meter_id, valid_packet)
    
    # 2. Check if attack should be injected
    if not attack_session_manager.should_attack_this_packet(session_id, meter_id, packet_number):
        return ([valid_packet], False, "none")
    
    # 3. Pick type and build
    attack_type = pick_attack_type()
    
    if attack_type == "replay":
        candidate = attack_session_manager.get_replay_candidate(meter_id)
        if candidate is None:
            return ([valid_packet], False, "none")
        attack_packet = build_replay_attack(candidate, session)
        return ([attack_packet], True, "replay")
        
    elif attack_type == "mitm":
        attack_packet = build_mitm_attack(valid_packet)
        return ([attack_packet], True, "mitm")
        
    elif attack_type == "flood":
        flood_count = random.randint(15, 25)
        flood_packets = build_flood_packets(
            valid_packet, session, flood_count,
            base_seq=session.get("sequence_number", 0)
        )
        return (flood_packets, True, "flood")
        
    return ([valid_packet], False, "none")

print("[MODULE LOADED] attack_injector.py ready")
