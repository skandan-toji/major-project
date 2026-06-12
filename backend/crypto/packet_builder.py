"""
packet_builder.py — Packet Construction and Verification Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

This module ties all crypto modules together for building and
verifying authentication and data packets.

Provides:
  - build_auth_packet(device_id, private_key) -> dict
  - verify_auth_packet(packet, public_key) -> bool
  - build_data_packet(device_id, session, payload) -> dict
  - verify_data_packet(packet, session) -> dict
"""

import json
import time

from crypto.dilithium_module import sign_message, verify_signature
from crypto.aes_module import encrypt_payload, decrypt_payload
from crypto.hmac_module import compute_hmac, verify_hmac
from crypto.session_crypto import (
    is_session_expired,
    is_timestamp_fresh,
    is_sequence_valid,
)


def build_auth_packet(device_id: str, private_key: bytes) -> dict:
    """
    Builds the authentication packet for session initiation.

    Steps:
      1. Create auth_message dict with device_id, timestamp, intent
      2. Serialize auth_message to JSON bytes (canonical form)
      3. Sign the serialized bytes with Dilithium5
      4. Return packet dict with signature as hex string

    Args:
        device_id (str): The smart meter identifier (e.g. "SM_001").
        private_key (bytes): The Dilithium5 private key (4,864 bytes).

    Returns:
        dict: Authentication packet:
            {
                "device_id": str,
                "auth_message": dict,
                "signature": str (hex)
            }
    """
    # Step 1: Create the authentication message
    auth_message = {
        "device_id": device_id,
        "timestamp": time.time(),
        "intent": "session_request",
    }

    # Step 2: Serialize to canonical JSON bytes
    message_bytes = json.dumps(
        auth_message, separators=(',', ':'), sort_keys=True
    ).encode('utf-8')

    # Step 3: Sign with Dilithium5
    signature = sign_message(private_key, message_bytes)

    # Step 4: Build and return the packet
    return {
        "device_id": device_id,
        "auth_message": auth_message,
        "signature": signature.hex(),
    }


def verify_auth_packet(packet: dict, public_key: bytes) -> bool:
    """
    Verifies an authentication packet's Dilithium5 signature.

    Args:
        packet (dict): The authentication packet from build_auth_packet.
        public_key (bytes): The Dilithium5 public key (2,592 bytes).

    Returns:
        bool: True if the signature is valid, False otherwise.
    """
    try:
        auth_message = packet["auth_message"]
        signature = bytes.fromhex(packet["signature"])

        # Reconstruct the exact bytes that were signed
        message_bytes = json.dumps(
            auth_message, separators=(',', ':'), sort_keys=True
        ).encode('utf-8')

        return verify_signature(public_key, message_bytes, signature)
    except Exception:
        return False


def build_data_packet(device_id: str,
                      session: dict,
                      payload: dict) -> dict:
    """
    Builds a complete encrypted data packet for transmission.

    Steps:
      1. Increment session sequence_number by 1
      2. Record current timestamp
      3. Encrypt payload with AES-256-GCM
      4. Compute HMAC-SHA256 over packet fields
      5. Return packet dict with all byte fields as hex strings

    Args:
        device_id (str): The smart meter identifier.
        session (dict): The session material dict (mutated in place —
                        sequence_number is incremented).
        payload (dict): The data to encrypt (e.g. meter readings).

    Returns:
        dict: Complete data packet:
            {
                "device_id": str,
                "session_id": str (hex),
                "nonce": str (hex),
                "sequence_number": int,
                "timestamp": float,
                "cipher_data": str (hex),
                "aes_auth_tag": str (hex),
                "hmac_tag": str (hex)
            }
    """
    # Step 1: Use current sequence number
    seq_num = session["sequence_number"]

    # Step 2: Record current timestamp
    timestamp = time.time()

    # Step 3: Encrypt payload with AES-256-GCM
    ciphertext, auth_tag = encrypt_payload(
        session["aes_key"],
        session["nonce"],
        payload
    )

    # Step 4: Compute HMAC-SHA256
    hmac_tag = compute_hmac(
        aes_key=session["aes_key"],
        session_id=session["session_id"],
        nonce=session["nonce"],
        sequence_number=seq_num,
        timestamp=timestamp,
        cipher_data=ciphertext,
        aes_auth_tag=auth_tag
    )

    # Step 5: Build and return packet with hex-encoded byte fields
    return {
        "device_id": device_id,
        "session_id": session["session_id"].hex(),
        "nonce": session["nonce"].hex(),
        "sequence_number": seq_num,
        "timestamp": timestamp,
        "cipher_data": ciphertext.hex(),
        "aes_auth_tag": auth_tag.hex(),
        "hmac_tag": hmac_tag.hex(),
    }


def verify_data_packet(packet: dict, session: dict) -> dict:
    """
    Verifies and decrypts a data packet at the Control Center.

    Verification steps in EXACT order (never skip or reorder):
      1. Check session not expired
      2. Verify HMAC — reject if invalid
      3. Check sequence number — reject if replay
      4. Check timestamp freshness — reject if stale
      5. Decrypt payload with AES-256-GCM
      6. Update session sequence_number
      7. Return success with decrypted payload

    Args:
        packet (dict): The data packet from build_data_packet.
        session (dict): The session material dict (mutated on success).

    Returns:
        dict: Verification result:
            On success: {"valid": True,  "payload": dict, "reason": "accepted"}
            On failure: {"valid": False, "payload": None, "reason": str}
            
            Possible failure reasons:
              - "session_expired"
              - "hmac_failed"
              - "replay_detected"
              - "stale_timestamp"
              - "decryption_failed"
    """
    try:
        # Extract byte fields from hex
        pkt_session_id = bytes.fromhex(packet["session_id"])
        pkt_nonce = bytes.fromhex(packet["nonce"])
        pkt_cipher_data = bytes.fromhex(packet["cipher_data"])
        pkt_auth_tag = bytes.fromhex(packet["aes_auth_tag"])
        pkt_hmac = bytes.fromhex(packet["hmac_tag"])
        pkt_seq = packet["sequence_number"]
        pkt_ts = packet["timestamp"]

        # Step 1: Check session expiry
        if is_session_expired(session):
            return {"valid": False, "payload": None, "reason": "session_expired"}

        # Step 2: Verify HMAC (constant-time comparison)
        hmac_valid = verify_hmac(
            aes_key=session["aes_key"],
            session_id=pkt_session_id,
            nonce=pkt_nonce,
            sequence_number=pkt_seq,
            timestamp=pkt_ts,
            cipher_data=pkt_cipher_data,
            aes_auth_tag=pkt_auth_tag,
            received_hmac=pkt_hmac
        )
        if not hmac_valid:
            return {"valid": False, "payload": None, "reason": "hmac_failed"}

        # Step 3: Check sequence number
        expected_seq = session["sequence_number"] + 1
        if not is_sequence_valid(expected_seq, pkt_seq):
            return {"valid": False, "payload": None, "reason": "replay_detected"}

        # Step 4: Check timestamp freshness
        if not is_timestamp_fresh(pkt_ts):
            return {"valid": False, "payload": None, "reason": "stale_timestamp"}

        # Step 5: Decrypt payload
        decrypted = decrypt_payload(
            aes_key=session["aes_key"],
            nonce=session["nonce"],
            ciphertext=pkt_cipher_data,
            auth_tag=pkt_auth_tag
        )

        # Step 6: Update session sequence number
        session["sequence_number"] = pkt_seq

        # Step 7: Return success
        return {"valid": True, "payload": decrypted, "reason": "accepted"}

    except Exception as e:
        return {"valid": False, "payload": None, "reason": f"decryption_failed: {e}"}


print("[packet_builder] Packet construction/verification module loaded successfully.")
