"""
session_crypto.py — Session Management Module

Part of the Hybrid Quantum-Resilient Security Framework.

Session Parameters:
  Session ID       : 128 bits / 16 bytes
  Session lifetime : 900 seconds (15 minutes)
  Timestamp window : 30 seconds
  Sequence number  : 32-bit unsigned int, starts at 0
"""

import os
import time

from crypto.aes_module import generate_aes_key, generate_nonce

SESSION_LIFETIME = 900
TIMESTAMP_WINDOW = 30
SESSION_ID_SIZE = 16


def create_session_material() -> dict:
    """
    Generates all material needed for a new session.

    Returns:
        dict with keys:
            session_id (bytes): 16 bytes os.urandom
            aes_key (bytes): 32 bytes from generate_aes_key()
            nonce (bytes): 12 bytes from generate_nonce()
            expiry_time (float): time.time() + 900
            sequence_number (int): starts at 0
    """
    return {
        "session_id": os.urandom(SESSION_ID_SIZE),
        "aes_key": generate_aes_key(),
        "nonce": generate_nonce(),
        "expiry_time": time.time() + SESSION_LIFETIME,
        "sequence_number": 0,
    }


def is_session_expired(session: dict) -> bool:
    """
    Checks if current time exceeds session expiry_time.

    Args:
        session (dict): Session material with 'expiry_time' key.

    Returns:
        bool: True if expired, False if still valid.
    """
    return time.time() > session["expiry_time"]


def is_timestamp_fresh(packet_timestamp: float) -> bool:
    """
    Checks if packet timestamp is within 30 second window.

    Args:
        packet_timestamp (float): Unix timestamp from the packet.

    Returns:
        bool: True if fresh, False if stale.
    """
    return abs(time.time() - packet_timestamp) <= TIMESTAMP_WINDOW


def is_sequence_valid(expected_seq: int, received_seq: int) -> bool:
    """
    Checks if received sequence number equals expected.

    Args:
        expected_seq (int): last_sequence_number + 1
        received_seq (int): sequence number from packet

    Returns:
        bool: True if valid, False otherwise.
    """
    return expected_seq == received_seq


print("[session_crypto] Session management module loaded successfully.")
