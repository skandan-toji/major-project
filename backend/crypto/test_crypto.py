"""
test_crypto.py — Full Cryptographic Stack End-to-End Test

Traces one complete message from birth to death through the entire
crypto pipeline of the Hybrid Quantum-Resilient Security Framework.

Test sequence:
  1.  Generate Dilithium5 key pair for SM_001
  2.  Generate Kyber1024 key pair for SM_001
  3.  Build and verify authentication packet
  4.  Create session material
  5.  Encrypt AES key with Kyber and decrypt it back
  6.  Build a data packet with meter readings
  7.  Verify the data packet (should be valid)
  8.  Replay attack -- resend same packet
  9.  Show replay is detected
  10. HMAC tampering -- modify cipher_data, verify again
  11. Show tampering is detected
"""

import sys
import copy

# --- Import all crypto modules ---
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import (
    generate_kyber_keypair,
    encrypt_aes_key,
    decrypt_aes_key,
)
from crypto.session_crypto import create_session_material
from crypto.packet_builder import (
    build_auth_packet,
    verify_auth_packet,
    build_data_packet,
    verify_data_packet,
)


def separator(title):
    """Print a section separator."""
    print("\n" + "=" * 60)
    print("  " + title)
    print("=" * 60)


def main():
    print("=" * 60)
    print("  HYBRID QUANTUM-RESILIENT SECURITY FRAMEWORK")
    print("  Full Cryptographic Stack -- End-to-End Test")
    print("=" * 60)

    device_id = "SM_001"

    # ----------------------------------------------------------
    # STEP 1: Generate Dilithium5 key pair
    # ----------------------------------------------------------
    separator("STEP 1: Generate Dilithium5 Key Pair")
    dil_pk, dil_sk = generate_dilithium_keypair()
    print("  Device ID        : " + device_id)
    print("  Public key size  : " + str(len(dil_pk)) + " bytes")
    print("  Private key size : " + str(len(dil_sk)) + " bytes")
    print("  Status           : [PASS] Key pair generated")

    # ----------------------------------------------------------
    # STEP 2: Generate Kyber1024 key pair
    # ----------------------------------------------------------
    separator("STEP 2: Generate Kyber1024 Key Pair")
    kyb_pk, kyb_sk = generate_kyber_keypair()
    print("  Public key size  : " + str(len(kyb_pk)) + " bytes")
    print("  Private key size : " + str(len(kyb_sk)) + " bytes")
    print("  Status           : [PASS] Key pair generated")

    # ----------------------------------------------------------
    # STEP 3: Build and verify authentication packet
    # ----------------------------------------------------------
    separator("STEP 3: Build & Verify Authentication Packet")
    auth_packet = build_auth_packet(device_id, dil_sk)
    print("  Auth message     : " + str(auth_packet['auth_message']))
    sig_len = len(auth_packet['signature']) // 2
    print("  Signature length : " + str(sig_len) + " bytes")

    auth_valid = verify_auth_packet(auth_packet, dil_pk)
    status = "[PASS] Signature verified" if auth_valid else "[FAIL] Signature invalid"
    print("  Verification     : " + status)
    assert auth_valid, "Authentication packet verification failed!"

    # ----------------------------------------------------------
    # STEP 4: Create session material
    # ----------------------------------------------------------
    separator("STEP 4: Create Session Material")
    session = create_session_material()
    print("  Session ID       : " + session['session_id'].hex())
    print("  AES key size     : " + str(len(session['aes_key'])) + " bytes")
    print("  Nonce size       : " + str(len(session['nonce'])) + " bytes")
    print("  Sequence number  : " + str(session['sequence_number']))
    print("  Status           : [PASS] Session created")

    # ----------------------------------------------------------
    # STEP 5: Encrypt AES key with Kyber and decrypt it back
    # ----------------------------------------------------------
    separator("STEP 5: Kyber1024 Key Encapsulation")
    original_key = session["aes_key"]
    encrypted_bundle = encrypt_aes_key(kyb_pk, original_key)
    print("  Original AES key : " + original_key.hex()[:32] + "...")
    print("  Bundle size      : " + str(len(encrypted_bundle)) + " bytes")

    recovered_key = decrypt_aes_key(kyb_sk, encrypted_bundle)
    keys_match = original_key == recovered_key
    print("  Recovered key    : " + recovered_key.hex()[:32] + "...")
    status = "[PASS] Keys match" if keys_match else "[FAIL] Keys differ"
    print("  Keys match       : " + status)
    assert keys_match, "Kyber key encapsulation round-trip failed!"

    # ----------------------------------------------------------
    # STEP 6: Build a data packet
    # ----------------------------------------------------------
    separator("STEP 6: Build Data Packet")
    payload = {
        "device_id": "SM_001",
        "power_usage": 120.5,
        "voltage": 230.1,
    }
    # Clone session for sender (sender increments seq)
    sender_session = copy.deepcopy(session)
    packet = build_data_packet(device_id, sender_session, payload)
    print("  Payload          : " + str(payload))
    print("  Sequence number  : " + str(packet['sequence_number']))
    cipher_len = len(packet['cipher_data']) // 2
    print("  Cipher data len  : " + str(cipher_len) + " bytes")
    print("  HMAC tag         : " + packet['hmac_tag'][:32] + "...")
    print("  Status           : [PASS] Packet built")

    # ----------------------------------------------------------
    # STEP 7: Verify data packet -- should succeed
    # ----------------------------------------------------------
    separator("STEP 7: Verify Data Packet (Legitimate)")
    # Clone session for receiver (starts at seq 0)
    receiver_session = copy.deepcopy(session)
    result = verify_data_packet(packet, receiver_session)
    print("  Valid            : " + str(result['valid']))
    print("  Reason           : " + result['reason'])
    if result['valid']:
        print("  Decrypted payload: " + str(result['payload']))
    assert result["valid"], "Legitimate packet verification failed!"
    print("  Status           : [PASS] Packet accepted")

    # ----------------------------------------------------------
    # STEP 8 & 9: Replay attack -- resend exact same packet
    # ----------------------------------------------------------
    separator("STEP 8-9: Replay Attack Detection")
    print("  Resending the exact same packet again...")
    replay_result = verify_data_packet(packet, receiver_session)
    print("  Valid            : " + str(replay_result['valid']))
    print("  Reason           : " + replay_result['reason'])
    assert not replay_result["valid"], "Replay was not detected!"
    assert replay_result["reason"] == "replay_detected", \
        "Wrong reason: " + replay_result["reason"]
    print("  Status           : [PASS] Replay attack detected and rejected")

    # ----------------------------------------------------------
    # STEP 10 & 11: HMAC tampering -- modify cipher_data
    # ----------------------------------------------------------
    separator("STEP 10-11: HMAC Tampering Detection")
    tampered_packet = copy.deepcopy(packet)
    # Flip a byte in cipher_data to simulate tampering
    original_hex = tampered_packet["cipher_data"]
    tampered_bytes = bytearray(bytes.fromhex(original_hex))
    tampered_bytes[0] ^= 0xFF  # Flip all bits of first byte
    tampered_packet["cipher_data"] = tampered_bytes.hex()
    # Set sequence to what receiver expects next
    tampered_packet["sequence_number"] = receiver_session["sequence_number"] + 1

    print("  Modified cipher_data (flipped first byte)...")
    # Use a fresh copy of receiver session for tamper test
    tamper_session = copy.deepcopy(receiver_session)
    tamper_result = verify_data_packet(tampered_packet, tamper_session)
    print("  Valid            : " + str(tamper_result['valid']))
    print("  Reason           : " + tamper_result['reason'])
    assert not tamper_result["valid"], "Tampering was not detected!"
    assert tamper_result["reason"] == "hmac_failed", \
        "Wrong reason: " + tamper_result["reason"]
    print("  Status           : [PASS] HMAC tampering detected and rejected")

    # ----------------------------------------------------------
    # FINAL SUMMARY
    # ----------------------------------------------------------
    separator("TEST SUMMARY")
    print("  [PASS] Step 1  : Dilithium5 key pair generated")
    print("  [PASS] Step 2  : Kyber1024 key pair generated")
    print("  [PASS] Step 3  : Auth packet built & verified")
    print("  [PASS] Step 4  : Session material created")
    print("  [PASS] Step 5  : Kyber key encapsulation round-trip")
    print("  [PASS] Step 6  : Data packet built")
    print("  [PASS] Step 7  : Data packet verified & decrypted")
    print("  [PASS] Steps 8-9 : Replay attack detected")
    print("  [PASS] Steps 10-11: HMAC tampering detected")
    print("")
    print("  ALL TESTS PASSED -- Crypto stack fully operational")
    print("=" * 60)


if __name__ == "__main__":
    main()
