"""
test_week2.py -- Week 2 End-to-End Integration Test

Tests the complete Week 2 system using REAL dataset data only.
No hardcoded payload values anywhere -- all data comes from
dataset_traffic/power_dataset_clean_100k.csv

Scenarios:
  1: Single Meter Full Session (5 packets from dataset)
  2: Replay Attack Detection
  3: HMAC Tampering Detection
  4: Stale Timestamp Detection
  5: Multiple Meters Simultaneously (real data)
  6: Traffic Logger Verification

Run from: MAJOR PROJECT/backend/
Command:  python test_week2.py
"""

import asyncio
import time
import copy

from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from crypto.aes_module import encrypt_payload
from crypto.hmac_module import compute_hmac
from crypto.packet_builder import build_data_packet
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter


def separator(title):
    """Print a section separator."""
    print("\n" + "=" * 64)
    print("  " + title)
    print("=" * 64)


scenario_results = []


async def scenario_1(cc, sm1):
    """
    SCENARIO 1 -- Single Meter Full Session
    Authenticate SM_001 and send 5 packets from real dataset.
    """
    separator("SCENARIO 1: Single Meter Full Session (Real Dataset)")
    passed = True

    # Authenticate
    print("  Authenticating SM_001...")
    auth_ok = await sm1.authenticate(cc)
    print("  Auth result     : " + ("SUCCESS" if auth_ok else "FAILED"))
    if not auth_ok:
        print("  [FAIL] Authentication failed")
        scenario_results.append(False)
        return
    print("  Session ID      : " + sm1.current_session["session_id"].hex())
    print("  Session count   : " + str(sm1.session_count))

    # Send 5 data packets -- all from the real dataset
    print("\n  Sending 5 data packets (from real dataset)...")
    for i in range(5):
        # Peek to show what will be sent
        upcoming = sm1.peek_payload()
        pwr = upcoming["global_active_power"]
        volts = upcoming["voltage"]

        # send_next() pulls from the dataset automatically
        result = await sm1.send_next(cc)
        valid = result.get("valid", False)
        reason = result.get("reason", "unknown")
        status = "ACCEPTED" if valid else "REJECTED"
        print("    Packet " + str(i + 1) + ": " + status
              + " | power=" + str(pwr) + " voltage=" + str(volts)
              + " (" + reason + ")")

        if not valid:
            passed = False

    # Print CC stats
    stats = cc.get_stats()
    print("\n  Control Center Stats after 5 packets:")
    print("    Packets received : " + str(stats["packets_received"]))
    print("    Packets accepted : " + str(stats["packets_accepted"]))
    print("    Packets rejected : " + str(stats["packets_rejected"]))
    print("    Auth success     : " + str(stats["auth_success"]))

    print("\n  Scenario 1: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def scenario_2(cc, sm1):
    """
    SCENARIO 2 -- Replay Attack Detection
    Send a fresh dataset packet, then replay it.
    """
    separator("SCENARIO 2: Replay Attack Detection")
    passed = True

    if not sm1.has_active_session():
        print("  [FAIL] No active session for SM_001")
        scenario_results.append(False)
        return

    # Build a fresh packet from the dataset (next row automatically)
    payload = sm1.next_payload()
    fresh_packet = build_data_packet(
        sm1.meter_id, sm1.current_session, payload
    )
    sm1.packet_count += 1

    print("  Sent fresh dataset packet (power="
          + str(payload["global_active_power"])
          + " voltage=" + str(payload["voltage"]) + ")")

    # Process it normally first
    result1 = await cc.process_data_packet(fresh_packet)
    print("  Fresh packet     : " + result1["reason"])
    if not result1["valid"]:
        passed = False

    # Replay the exact same packet
    print("  Replaying exact same packet...")
    replay_result = await cc.process_data_packet(fresh_packet)
    print("  Replay result    : valid=" + str(replay_result["valid"]))
    print("  Replay reason    : " + replay_result["reason"])

    if replay_result["valid"]:
        passed = False
        print("  [FAIL] Replay was NOT detected!")
    elif replay_result["reason"] != "replay_detected":
        passed = False
        print("  [FAIL] Wrong rejection reason: " + replay_result["reason"])
    else:
        print("  [PASS] Replay attack correctly detected")

    print("\n  Scenario 2: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def scenario_3(cc, sm1):
    """
    SCENARIO 3 -- HMAC Tampering Detection
    Build a fresh dataset packet, tamper with cipher_data, send it.
    """
    separator("SCENARIO 3: HMAC Tampering Detection")
    passed = True

    if not sm1.has_active_session():
        print("  [FAIL] No active session for SM_001")
        scenario_results.append(False)
        return

    # Build a fresh packet from the dataset
    payload = sm1.next_payload()
    packet = build_data_packet(
        sm1.meter_id, sm1.current_session, payload
    )
    sm1.packet_count += 1

    print("  Built dataset packet (power="
          + str(payload["global_active_power"])
          + " voltage=" + str(payload["voltage"]) + ")")

    # Tamper with cipher_data
    tampered_packet = copy.deepcopy(packet)
    original_hex = tampered_packet["cipher_data"]
    tampered_bytes = bytearray(bytes.fromhex(original_hex))
    tampered_bytes[0] ^= 0xFF  # Flip first byte
    tampered_packet["cipher_data"] = tampered_bytes.hex()

    print("  Sending tampered packet (cipher_data modified)...")
    tamper_result = await cc.process_data_packet(tampered_packet)
    print("  Tamper result    : valid=" + str(tamper_result["valid"]))
    print("  Tamper reason    : " + tamper_result["reason"])

    if tamper_result["valid"]:
        passed = False
        print("  [FAIL] Tampering was NOT detected!")
    elif tamper_result["reason"] != "hmac_failed":
        passed = False
        print("  [FAIL] Wrong rejection reason: " + tamper_result["reason"])
    else:
        print("  [PASS] HMAC tampering correctly detected")

    # Send the ORIGINAL packet to keep session in sync
    original_result = await cc.process_data_packet(packet)
    print("  Original packet  : " + original_result["reason"])

    print("\n  Scenario 3: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def scenario_4(cc, sm1):
    """
    SCENARIO 4 -- Stale Timestamp Detection
    Build a dataset packet with timestamp 60 seconds in the past.
    Recompute HMAC with the stale timestamp so HMAC still passes.
    """
    separator("SCENARIO 4: Stale Timestamp Detection")
    passed = True

    if not sm1.has_active_session():
        print("  [FAIL] No active session for SM_001")
        scenario_results.append(False)
        return

    session = sm1.current_session

    # Get next payload from dataset
    payload = sm1.next_payload()
    sm1.packet_count += 1

    print("  Using dataset row (power="
          + str(payload["global_active_power"])
          + " voltage=" + str(payload["voltage"]) + ")")

    # Build packet manually with stale timestamp
    session["sequence_number"] += 1
    seq_num = session["sequence_number"]
    stale_timestamp = time.time() - 60  # 60 seconds old

    ciphertext, auth_tag = encrypt_payload(
        session["aes_key"], session["nonce"], payload
    )

    # Recompute HMAC with the stale timestamp
    hmac_tag = compute_hmac(
        aes_key=session["aes_key"],
        session_id=session["session_id"],
        nonce=session["nonce"],
        sequence_number=seq_num,
        timestamp=stale_timestamp,
        cipher_data=ciphertext,
        aes_auth_tag=auth_tag,
    )

    stale_packet = {
        "device_id": sm1.meter_id,
        "session_id": session["session_id"].hex(),
        "nonce": session["nonce"].hex(),
        "sequence_number": seq_num,
        "timestamp": stale_timestamp,
        "cipher_data": ciphertext.hex(),
        "aes_auth_tag": auth_tag.hex(),
        "hmac_tag": hmac_tag.hex(),
    }

    print("  Sending packet with timestamp 60s in the past...")
    print("  Delta            : ~60 seconds (beyond 30s window)")

    stale_result = await cc.process_data_packet(stale_packet)
    print("  Stale result     : valid=" + str(stale_result["valid"]))
    print("  Stale reason     : " + stale_result["reason"])

    if stale_result["valid"]:
        passed = False
        print("  [FAIL] Stale timestamp was NOT detected!")
    elif stale_result["reason"] != "stale_timestamp":
        passed = False
        print("  [FAIL] Wrong rejection reason: " + stale_result["reason"])
    else:
        print("  [PASS] Stale timestamp correctly detected")

    print("\n  Scenario 4: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def scenario_5(cc, dataset_rows):
    """
    SCENARIO 5 -- Multiple Meters Simultaneously
    Register SM_002 and SM_003, run all 3 meters sending 3 packets
    each from different slices of the real dataset.
    """
    separator("SCENARIO 5: Multiple Meters Simultaneously (Real Dataset)")
    passed = True

    meters = []
    # Give each meter a different slice of the dataset
    slices = {
        "SM_002": dataset_rows[10:50],
        "SM_003": dataset_rows[50:90],
        "SM_001_v2": dataset_rows[0:40],
    }

    for mid in ["SM_002", "SM_003"]:
        dil_pk, dil_sk = generate_dilithium_keypair()
        kyb_pk, kyb_sk = generate_kyber_keypair()
        cc.register_meter(mid, dil_pk, kyb_pk)
        meter = SmartMeter(mid, dil_sk, kyb_sk, cc.get_public_key(),
                           data_rows=slices[mid])
        meters.append(meter)
        print("  Registered " + mid + " with "
              + str(len(slices[mid])) + " dataset rows")

    # Fresh SM_001_v2
    dil_pk1, dil_sk1 = generate_dilithium_keypair()
    kyb_pk1, kyb_sk1 = generate_kyber_keypair()
    cc.register_meter("SM_001_v2", dil_pk1, kyb_pk1)
    meter1 = SmartMeter("SM_001_v2", dil_sk1, kyb_sk1, cc.get_public_key(),
                        data_rows=slices["SM_001_v2"])
    meters.append(meter1)
    print("  Registered SM_001_v2 with "
          + str(len(slices["SM_001_v2"])) + " dataset rows")

    # Each meter sends 3 packets using its dataset slice
    async def run_meter(meter):
        """Run a meter for 3 packets from its own dataset."""
        auth_ok = await meter.authenticate(cc)
        if not auth_ok:
            return {"meter_id": meter.meter_id, "packets_sent": 0}

        for _ in range(3):
            await meter.send_next(cc)

        return {
            "meter_id": meter.meter_id,
            "packets_sent": meter.packet_count,
            "sessions_used": meter.session_count,
        }

    # Run all meters concurrently
    print("\n  Running 3 meters concurrently (3 packets each, real data)...")
    results = await asyncio.gather(*[run_meter(m) for m in meters])

    for r in results:
        print("    " + r["meter_id"] + ": sent " + str(r["packets_sent"]) + " packets")
        if r["packets_sent"] < 3:
            passed = False

    stats = cc.get_stats()
    print("\n  Control Center Stats (cumulative):")
    print("    Packets received : " + str(stats["packets_received"]))
    print("    Packets accepted : " + str(stats["packets_accepted"]))
    print("    Auth success     : " + str(stats["auth_success"]))
    print("    Active sessions  : " + str(len(stats["active_sessions"])))

    print("\n  Scenario 5: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def scenario_6(cc):
    """
    SCENARIO 6 -- Traffic Feature Verification
    Check that traffic_features.csv has been populated.
    """
    separator("SCENARIO 6: Traffic Feature Verification")
    passed = True

    log_stats = cc.traffic_feature_extractor.get_stats()
    print("  Log file         : " + log_stats["log_file"])
    print("  Total rows       : " + str(log_stats["total_rows"]))
    print("  Normal rows      : " + str(log_stats["normal_rows"]) + " (label=0)")
    print("  Attack rows      : " + str(log_stats["attack_rows"]) + " (label=1)")

    if log_stats["total_rows"] == 0:
        passed = False
        print("  [FAIL] No rows written to CSV!")
    else:
        print("  [PASS] Traffic features CSV populated")

    if log_stats["normal_rows"] == 0:
        passed = False
        print("  [FAIL] No normal traffic rows!")
    else:
        print("  [PASS] Normal traffic rows present")

    print("\n  Scenario 6: " + ("[PASS]" if passed else "[FAIL]"))
    scenario_results.append(passed)


async def main():
    print("=" * 64)
    print("  HYBRID QUANTUM-RESILIENT SECURITY FRAMEWORK")
    print("  Week 2 Integration Test -- All Data From Real Dataset")
    print("=" * 64)

    # --- Setup ---
    separator("SETUP: Key Generation & Registration")

    # Generate keys for SM_001
    print("  Generating Dilithium5 key pair for SM_001...")
    dil_pk, dil_sk = generate_dilithium_keypair()
    print("    Dilithium PK   : " + str(len(dil_pk)) + " bytes")

    print("  Generating Kyber1024 key pair for SM_001...")
    kyb_pk, kyb_sk = generate_kyber_keypair()
    print("    Kyber PK       : " + str(len(kyb_pk)) + " bytes")

    # Create Control Center
    print("  Creating Control Center...")
    cc = ControlCenter()
    print("    CC Kyber PK    : " + str(len(cc.get_public_key())) + " bytes")

    # Register SM_001
    cc.register_meter("SM_001", dil_pk, kyb_pk)
    print("  Registered SM_001 in device registry")

    # Load real dataset
    separator("DATASET: Loading power_dataset_clean_100k.csv")
    dataset_rows = SmartMeter.load_dataset_from_csv(max_rows=100)
    print("  Loaded " + str(len(dataset_rows)) + " rows from real dataset")
    print("  Sample row 0     : power=" + str(dataset_rows[0]["global_active_power"])
          + " voltage=" + str(dataset_rows[0]["voltage"]))
    print("  Sample row 1     : power=" + str(dataset_rows[1]["global_active_power"])
          + " voltage=" + str(dataset_rows[1]["voltage"]))
    print("  Columns per row  : " + str(list(dataset_rows[0].keys())))

    # Create Smart Meter with real dataset loaded
    sm1 = SmartMeter("SM_001", dil_sk, kyb_sk, cc.get_public_key(),
                     data_rows=dataset_rows)
    print("  SmartMeter SM_001 created with " + str(len(sm1.data_rows)) + " dataset rows")

    # Clear any existing CSV for a clean test
    cc.traffic_feature_extractor.clear_log()
    print("  Traffic feature extractor cleared for clean test run")

    # --- Run Scenarios ---
    await scenario_1(cc, sm1)
    await scenario_2(cc, sm1)
    await scenario_3(cc, sm1)
    await scenario_4(cc, sm1)
    await scenario_5(cc, dataset_rows)
    await scenario_6(cc)

    # --- Final Summary ---
    separator("FINAL SUMMARY")
    scenario_names = [
        "Scenario 1: Single Meter Full Session",
        "Scenario 2: Replay Attack Detection",
        "Scenario 3: HMAC Tampering Detection",
        "Scenario 4: Stale Timestamp Detection",
        "Scenario 5: Multiple Meters Simultaneously",
        "Scenario 6: Traffic Logger Verification",
    ]

    all_passed = True
    for i, (name, result) in enumerate(zip(scenario_names, scenario_results)):
        status = "[PASS]" if result else "[FAIL]"
        print("  " + status + " " + name)
        if not result:
            all_passed = False

    print("")
    if all_passed:
        print("  *** ALL 6 SCENARIOS PASSED ***")
        print("  Week 2 system is fully operational.")
        print("  All packet data sourced from real dataset -- zero hardcoded values.")
    else:
        print("  *** SOME SCENARIOS FAILED ***")
        print("  Review output above for details.")
    print("=" * 64)


if __name__ == "__main__":
    asyncio.run(main())
