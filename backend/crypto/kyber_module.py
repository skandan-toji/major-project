"""
kyber_module.py — CRYSTALS-Kyber1024 Key Encapsulation Module

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

NIST Security Level : Level 5 (AES-256 equivalent)
Algorithm           : Kyber1024 / ML-KEM-1024 (FIPS 203)
Public key size     : 1,568 bytes
Private key size    : 3,168 bytes
Ciphertext size     : 1,568 bytes
Shared secret size  : 32 bytes

This module provides:
  - generate_kyber_keypair()         -> (public_key, private_key)
  - encrypt_aes_key(pk, aes_key)     -> encrypted_bundle
  - decrypt_aes_key(sk, bundle)      -> aes_key

Kyber is a KEM — it does not directly encrypt arbitrary data.
We use the shared_secret from encapsulation to XOR-wrap the
32-byte AES session key.

Dependencies:
  - pqcrypto (pip install pqcrypto)
    Uses pqcrypto.kem.ml_kem_1024 (standardized name for Kyber1024)
"""

from pqcrypto.kem.ml_kem_1024 import generate_keypair, encrypt, decrypt

KYBER1024_CIPHERTEXT_SIZE = 1568


def generate_kyber_keypair() -> tuple:
    """
    Generates a CRYSTALS-Kyber1024 (ML-KEM-1024) key pair.

    Returns:
        tuple: (public_key: bytes, private_key: bytes)
            - public_key  : 1,568 bytes
            - private_key : 3,168 bytes
    """
    public_key, private_key = generate_keypair()
    return (public_key, private_key)


def _xor_bytes(a: bytes, b: bytes) -> bytes:
    """
    XOR two equal-length byte strings.

    Args:
        a (bytes): First byte string.
        b (bytes): Second byte string (same length).

    Returns:
        bytes: XOR result.

    Raises:
        ValueError: If inputs differ in length.
    """
    if len(a) != len(b):
        raise ValueError(
            f"XOR operands must be equal length: {len(a)} vs {len(b)}"
        )
    return bytes(x ^ y for x, y in zip(a, b))


def encrypt_aes_key(kyber_public_key: bytes, aes_key: bytes) -> bytes:
    """
    Encrypts a 32-byte AES key using Kyber1024 KEM.

    Approach (since Kyber is a KEM, not PKE):
      1. Encapsulate using public key -> (ciphertext, shared_secret)
      2. XOR aes_key with shared_secret -> wrapped_aes_key
      3. Return ciphertext (1568B) || wrapped_aes_key (32B)

    Args:
        kyber_public_key (bytes): 1,568-byte Kyber1024 public key.
        aes_key (bytes): 32-byte AES-256 session key to protect.

    Returns:
        bytes: Encrypted bundle (1,600 bytes total).
    """
    if len(aes_key) != 32:
        raise ValueError(f"AES key must be 32 bytes, got {len(aes_key)}")

    ciphertext, shared_secret = encrypt(kyber_public_key)
    wrapped_aes_key = _xor_bytes(aes_key, shared_secret)
    return ciphertext + wrapped_aes_key


def decrypt_aes_key(kyber_private_key: bytes,
                    encrypted_bundle: bytes) -> bytes:
    """
    Decrypts an encrypted bundle to recover the 32-byte AES key.

    Reverses encrypt_aes_key:
      1. Split bundle into ciphertext (1568B) + wrapped_key (32B)
      2. Decapsulate ciphertext -> shared_secret
      3. XOR wrapped_key with shared_secret -> original aes_key

    Args:
        kyber_private_key (bytes): 3,168-byte Kyber1024 private key.
        encrypted_bundle (bytes): 1,600-byte bundle from encrypt_aes_key.

    Returns:
        bytes: Recovered 32-byte AES-256 session key.
    """
    expected_size = KYBER1024_CIPHERTEXT_SIZE + 32
    if len(encrypted_bundle) != expected_size:
        raise ValueError(
            f"Bundle must be {expected_size} bytes, got {len(encrypted_bundle)}"
        )

    ciphertext = encrypted_bundle[:KYBER1024_CIPHERTEXT_SIZE]
    wrapped_aes_key = encrypted_bundle[KYBER1024_CIPHERTEXT_SIZE:]

    shared_secret = decrypt(kyber_private_key, ciphertext)
    return _xor_bytes(wrapped_aes_key, shared_secret)


print("[kyber_module] Kyber1024 (ML-KEM-1024) key encapsulation module loaded successfully.")
