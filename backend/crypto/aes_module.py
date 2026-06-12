"""
aes_module.py — AES-256-GCM Authenticated Encryption Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

AES Mode        : AES-256-GCM (Galois/Counter Mode)
Key size        : 256 bits / 32 bytes
Nonce size      : 96 bits / 12 bytes (one per session)
Auth tag size   : 128 bits / 16 bytes (per message)

This module provides:
  - generate_aes_key()  -> 32 bytes
  - generate_nonce()    -> 12 bytes
  - encrypt_payload(key, nonce, payload, aad) -> (ciphertext, auth_tag)
  - decrypt_payload(key, nonce, ciphertext, auth_tag, aad) -> dict

The nonce is generated once per session. Per-message uniqueness is
ensured by the sequence number which is passed as associated data
by the packet_builder layer.

Dependencies:
  - pycryptodome (pip install pycryptodome)
"""

import os
import json
from Crypto.Cipher import AES


def generate_aes_key() -> bytes:
    """
    Generates a cryptographically secure 256-bit AES key.

    Returns:
        bytes: 32 bytes of cryptographically secure random data,
               generated using os.urandom() which sources from the
               OS CSPRNG (e.g., /dev/urandom on Linux, CryptGenRandom
               on Windows).

    Security:
        NEVER uses Python's random module. Always uses os.urandom()
        for cryptographic key generation.
    """
    return os.urandom(32)


def generate_nonce() -> bytes:
    """
    Generates a 96-bit nonce for AES-GCM.

    Returns:
        bytes: 12 bytes of cryptographically secure random data.

    Usage:
        One nonce is generated per session and reused within that
        session. The sequence number (incremented per message) provides
        per-message uniqueness and is included as associated data.
        The session lifetime is 900 seconds (15 minutes), limiting
        nonce reuse exposure.
    """
    return os.urandom(12)


def encrypt_payload(aes_key: bytes,
                    nonce: bytes,
                    payload: dict,
                    associated_data: bytes = None) -> tuple:
    """
    Encrypts a payload dictionary using AES-256-GCM.

    Steps:
      1. Serialize the payload dict to JSON bytes (UTF-8 encoded).
      2. Create an AES-GCM cipher with the provided key and nonce.
      3. If associated_data is provided, update the cipher with it
         as Additional Authenticated Data (AAD).
      4. Encrypt the JSON bytes to produce ciphertext.
      5. Generate the 16-byte authentication tag.

    Args:
        aes_key (bytes):          The 32-byte AES-256 session key.
        nonce (bytes):            The 12-byte session nonce.
        payload (dict):           The data to encrypt (e.g., meter readings).
        associated_data (bytes):  Optional AAD for additional authentication.
                                  Not encrypted, but authenticated.

    Returns:
        tuple: (ciphertext: bytes, auth_tag: bytes)
            - ciphertext : Variable-length encrypted payload bytes.
            - auth_tag   : 16 bytes AES-GCM authentication tag.

    Note:
        Both return values are raw bytes, NOT hex-encoded.
        Hex conversion is done at the packet_builder layer.
    """
    # Step 1: Serialize payload to JSON bytes
    plaintext = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    # Step 2: Create AES-GCM cipher
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)

    # Step 3: Add associated data if provided
    if associated_data is not None:
        cipher.update(associated_data)

    # Step 4-5: Encrypt and generate auth tag
    ciphertext, auth_tag = cipher.encrypt_and_digest(plaintext)

    return (ciphertext, auth_tag)


def decrypt_payload(aes_key: bytes,
                    nonce: bytes,
                    ciphertext: bytes,
                    auth_tag: bytes,
                    associated_data: bytes = None) -> dict:
    """
    Decrypts and authenticates AES-256-GCM encrypted payload.

    Steps:
      1. Create an AES-GCM cipher with the provided key and nonce.
      2. If associated_data was used during encryption, it must be
         provided here as well for authentication to succeed.
      3. Decrypt the ciphertext.
      4. Verify the authentication tag — if tampered, ValueError is raised.
      5. Deserialize JSON bytes back to a Python dict.

    Args:
        aes_key (bytes):          The 32-byte AES-256 session key.
        nonce (bytes):            The 12-byte session nonce.
        ciphertext (bytes):       The encrypted payload bytes.
        auth_tag (bytes):         The 16-byte AES-GCM authentication tag.
        associated_data (bytes):  Optional AAD (must match encryption).

    Returns:
        dict: The original payload dictionary.

    Raises:
        ValueError: If the authentication tag verification fails,
                    indicating the ciphertext or AAD has been tampered
                    with, or the wrong key/nonce was used.
    """
    # Step 1: Create AES-GCM cipher for decryption
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)

    # Step 2: Add associated data if provided
    if associated_data is not None:
        cipher.update(associated_data)

    # Step 3-4: Decrypt and verify authentication tag
    plaintext = cipher.decrypt_and_verify(ciphertext, auth_tag)

    # Step 5: Deserialize JSON bytes to dict
    payload = json.loads(plaintext.decode('utf-8'))

    return payload


print("[aes_module] AES-256-GCM authenticated encryption module loaded successfully.")
