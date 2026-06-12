"""
dilithium_module.py — CRYSTALS-Dilithium5 Digital Signature Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

NIST Security Level : Level 5 (AES-256 equivalent)
Algorithm           : Dilithium5 / ML-DSA-87 (FIPS 204)
Public key size     : 2,592 bytes
Private key size    : 4,896 bytes
Signature size      : 4,627 bytes
Hash used internally: SHAKE-256

This module provides:
  - generate_dilithium_keypair() -> (public_key, private_key)
  - sign_message(private_key, message) -> signature
  - verify_signature(public_key, message, signature) -> bool

Dependencies:
  - pqcrypto (pip install pqcrypto)
    Uses pqcrypto.sign.ml_dsa_87 (standardized name for Dilithium5)
"""

from pqcrypto.sign.ml_dsa_87 import generate_keypair, sign, verify


def generate_dilithium_keypair() -> tuple:
    """
    Generates a CRYSTALS-Dilithium5 (ML-DSA-87) key pair.

    Returns:
        tuple: (public_key: bytes, private_key: bytes)
            - public_key  : 2,592 bytes — used by verifier
            - private_key : 4,896 bytes — used by signer, kept secret
    """
    public_key, private_key = generate_keypair()
    return (public_key, private_key)


def sign_message(private_key: bytes, message: bytes) -> bytes:
    """
    Signs a message using a Dilithium5 private key.

    Args:
        private_key (bytes): The Dilithium5 private key.
        message (bytes):     The message to sign (must be bytes).

    Returns:
        bytes: The digital signature (~4,627 bytes).
    """
    signature = sign(private_key, message)
    return signature


def verify_signature(public_key: bytes,
                     message: bytes,
                     signature: bytes) -> bool:
    """
    Verifies a Dilithium5 digital signature.

    Args:
        public_key (bytes): The Dilithium5 public key.
        message (bytes):    The original message that was signed.
        signature (bytes):  The signature bytes from sign_message().

    Returns:
        bool: True if valid, False otherwise.

    Security:
        Never raises an exception on invalid signature —
        catches all exceptions and returns False.
    """
    try:
        return verify(public_key, message, signature)
    except Exception:
        return False


print("[dilithium_module] Dilithium5 (ML-DSA-87) digital signature module loaded successfully.")
