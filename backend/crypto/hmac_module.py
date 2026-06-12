"""
hmac_module.py — HMAC-SHA256 Message Authentication Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

HMAC Algorithm  : HMAC-SHA256
Output size     : 256 bits / 32 bytes
Key used        : AES session key (32 bytes)

This module provides:
  - compute_hmac(key, session_id, nonce, seq, ts, data, tag) -> 32 bytes
  - verify_hmac(key, session_id, nonce, seq, ts, data, tag, received) -> bool

HMAC is computed over the exact concatenation:
  session_id + nonce + sequence_number (4-byte big-endian)
  + timestamp (8-byte IEEE 754 big-endian double)
  + cipher_data + aes_auth_tag

Dependencies:
  - Python standard library: hmac, hashlib, struct
"""

import hmac
import hashlib
import struct


def compute_hmac(aes_key: bytes,
                 session_id: bytes,
                 nonce: bytes,
                 sequence_number: int,
                 timestamp: float,
                 cipher_data: bytes,
                 aes_auth_tag: bytes) -> bytes:
    """
    Computes HMAC-SHA256 over the packet fields.

    The data to be authenticated is constructed by concatenating
    the packet fields in this EXACT order:
      1. session_id     (16 bytes)
      2. nonce          (12 bytes)
      3. sequence_number encoded as 4-byte big-endian unsigned int
      4. timestamp       encoded as 8-byte big-endian IEEE 754 double
      5. cipher_data    (variable length — AES-GCM ciphertext)
      6. aes_auth_tag   (16 bytes — AES-GCM authentication tag)

    Args:
        aes_key (bytes):        The 32-byte AES session key used as HMAC key.
        session_id (bytes):     The 16-byte session identifier.
        nonce (bytes):          The 12-byte session nonce.
        sequence_number (int):  The 32-bit unsigned integer sequence number.
        timestamp (float):      The 64-bit Unix timestamp (float).
        cipher_data (bytes):    The AES-GCM encrypted ciphertext.
        aes_auth_tag (bytes):   The 16-byte AES-GCM authentication tag.

    Returns:
        bytes: 32-byte HMAC-SHA256 digest.
    """
    # Build the data to authenticate in strict concatenation order
    data = (
        session_id
        + nonce
        + sequence_number.to_bytes(4, 'big')
        + struct.pack('>d', timestamp)
        + cipher_data
        + aes_auth_tag
    )

    # Compute HMAC-SHA256
    mac = hmac.new(aes_key, data, hashlib.sha256)
    return mac.digest()


def verify_hmac(aes_key: bytes,
                session_id: bytes,
                nonce: bytes,
                sequence_number: int,
                timestamp: float,
                cipher_data: bytes,
                aes_auth_tag: bytes,
                received_hmac: bytes) -> bool:
    """
    Verifies an HMAC-SHA256 tag using constant-time comparison.

    Recomputes the HMAC over the same packet fields and compares
    the result with the received HMAC tag. Uses hmac.compare_digest()
    for constant-time comparison to prevent timing side-channel attacks.

    Args:
        aes_key (bytes):        The 32-byte AES session key used as HMAC key.
        session_id (bytes):     The 16-byte session identifier.
        nonce (bytes):          The 12-byte session nonce.
        sequence_number (int):  The 32-bit unsigned integer sequence number.
        timestamp (float):      The 64-bit Unix timestamp (float).
        cipher_data (bytes):    The AES-GCM encrypted ciphertext.
        aes_auth_tag (bytes):   The 16-byte AES-GCM authentication tag.
        received_hmac (bytes):  The 32-byte HMAC tag received in the packet.

    Returns:
        bool: True if the HMAC is valid, False otherwise.

    Security:
        MUST use hmac.compare_digest() — NEVER the == operator.
        The == operator can leak information about how many bytes
        match through timing differences.
    """
    expected_hmac = compute_hmac(
        aes_key, session_id, nonce,
        sequence_number, timestamp,
        cipher_data, aes_auth_tag
    )
    return hmac.compare_digest(expected_hmac, received_hmac)


print("[hmac_module] HMAC-SHA256 message authentication module loaded successfully.")
