"""
test_week3.py -- Week 3 Integration Test

Verifies the automated attack injection system and confirms
that the ML dataset (traffic_features.csv) is being populated
with labeled attack rows.
"""

import asyncio
import time
import os
import csv
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter
from attacks.attack_injector import (
    should_inject_attack, is_attack_session,
    build_replay_attack, build_mitm_attack, build_flood_packets
)

def separator(title):
    print("\n" + "=" * 64)
    print("  " + title)
    print("=" * 64)

async def scenario_1(cc, sm1):
    """SCENARIO 1 -- Replay Attack Injection and Detection"""
    separator("SCENARIO 1: Replay Attack Injection and Detection")
    
    await sm1.authenticate(cc)
    print("  SM_001 Authenticated")
    
    # Send 10 normal packets to build history
    print("  Sending 10 normal packets to build history...")
    for _ in range(10):
        await sm1.send_next(cc)
    
    # Manually build a replay attack
    candidate = sm1.attack_manager.get_replay_candidate(sm1.meter_id)
    replay_pkt = build_replay_attack(candidate, sm1.current_session)
    
    # Strip internal metadata
    send_pkt = {k: v for k, v in replay_pkt.items() if not k.startswith("_")}
    
    print("  Sending Replay Attack packet...")
    result = await cc.process_data_packet(send_pkt)
    print("  CC Result: " + result["reason"])
    
    if result["reason"] in ["replay_detected", "stale_timestamp"]:
        print("  [PASS] Replay attack correctly detected")
        return True
    else:
        print("  [FAIL] Replay attack was NOT detected correctly")
        return False

async def scenario_2(cc, sm1):
    """SCENARIO 2 -- MITM Tampering Detection"""
    separator("SCENARIO 2: MITM Tampering Detection")
    
    # Build a valid packet
    payload = sm1.peek_payload()
    from crypto.packet_builder import build_data_packet
    valid_pkt = build_data_packet(sm1.meter_id, sm1.current_session, payload)
    
    # Build MITM attack
    tampered_pkt = build_mitm_attack(valid_pkt)
    send_pkt = {k: v for k, v in tampered_pkt.items() if not k.startswith("_")}
    
    print("  Sending Tampered (MITM) packet...")
    result = await cc.process_data_packet(send_pkt)
    print("  CC Result: " + result["reason"])
    
    if result["reason"] == "hmac_failed":
        print("  [PASS] MITM tampering correctly detected by HMAC")
        return True
    else:
        print("  [FAIL] MITM attack was NOT detected")
        return False

async def scenario_3(cc, sm1):
    """SCENARIO 3 -- Flood Attack Traffic Features"""
    separator("SCENARIO 3: Flood Attack Traffic Features")
    
    # Re-authenticate to sync sequence numbers after scenario 2 rejection
    await sm1.authenticate(cc)
    
    payload = sm1.peek_payload()
    from crypto.packet_builder import build_data_packet
    # Note: build_data_packet increments seq
    valid_pkt = build_data_packet(sm1.meter_id, sm1.current_session, payload)
    
    # Build 20 flood packets starting from the incremented sequence
    flood_pkts = build_flood_packets(valid_pkt, sm1.current_session, count=20)
    print(f"  Sending {len(flood_pkts)} flood packets in rapid succession...")
    
    accepted_count = 0
    first_fail_reason = None
    for p in flood_pkts:
        send_pkt = {k: v for k, v in p.items() if not k.startswith("_")}
        result = await cc.process_data_packet(send_pkt)
        if result["valid"]:
            accepted_count += 1
        elif first_fail_reason is None:
            first_fail_reason = result["reason"]
        await asyncio.sleep(0.01)
        
    print(f"  Accepted: {accepted_count}/{len(flood_pkts)}")
    if first_fail_reason:
        print(f"  First Failure Reason: {first_fail_reason}")
    
    # Flood should pass crypto but trigger ML later
    if accepted_count == len(flood_pkts):
        print("  [PASS] Flood packets passed crypto checks as intended")
        return True
    else:
        print(f"  [FAIL] Flood packets were rejected ({first_fail_reason})")
        return False

def scenario_4():
    """SCENARIO 4 -- Probability Engine Verification"""
    separator("SCENARIO 4: Probability Engine Verification")
    
    # 1000 iterations of 8% roll
    attack_rolls = sum(1 for _ in range(1000) if should_inject_attack(0.08))
    print(f"  Individual Attack Rolls (Target ~80): {attack_rolls}")
    
    # 1000 iterations of 15% roll
    session_rolls = sum(1 for _ in range(1000) if is_attack_session(0.15))
    print(f"  Session Attack Rolls (Target ~150): {session_rolls}")
    
    checks = []
    checks.append(50 <= attack_rolls <= 120)
    checks.append(100 <= session_rolls <= 200)
    
    if all(checks):
        print("  [PASS] Probability engine is within statistical range")
        return True
    else:
        print("  [FAIL] Probability engine distribution is off")
        return False

async def scenario_5(cc):
    """SCENARIO 5 -- Full Simulation Run with Mixed Traffic"""
    separator("SCENARIO 5: Full Simulation Run with Mixed Traffic")
    
    # Register 3 meters
    meters = []
    for mid in ["SM_004", "SM_005", "SM_006"]: # Use fresh IDs
        dil_pk, dil_sk = generate_dilithium_keypair()
        kyb_pk, kyb_sk = generate_kyber_keypair()
        cc.register_meter(mid, dil_pk, kyb_pk)
        m = SmartMeter(mid, dil_sk, kyb_sk, cc.get_public_key(), max_rows=100)
        meters.append(m)
        
    print("  Running 3 meters, 30 packets each, random attacks enabled...")
    results = await asyncio.gather(*[m.run_session(cc, max_packets=30, interval=0.1) for m in meters])
    
    total_attacks = sum(r.get("attacks_injected", 0) for r in results)
    ext_stats = cc.traffic_feature_extractor.get_stats()
    
    print(f"\n  Final Stats:")
    print(f"    Total Attacks Injected : {total_attacks}")
    print(f"    Dataset Normal Rows    : {ext_stats['normal_rows']}")
    print(f"    Dataset Attack Rows    : {ext_stats['attack_rows']}")
    
    if ext_stats['attack_rows'] > 0:
        print("  [PASS] Labeled attack data generated in CSV")
        return True
    else:
        print("  [FAIL] No attack data generated")
        return False

async def main():
    cc = ControlCenter()
    cc.traffic_feature_extractor.clear_log()
    
    # Setup SM_001 for unit tests
    dil_pk, dil_sk = generate_dilithium_keypair()
    kyb_pk, kyb_sk = generate_kyber_keypair()
    cc.register_meter("SM_001", dil_pk, kyb_pk)
    sm1 = SmartMeter("SM_001", dil_sk, kyb_sk, cc.get_public_key(), max_rows=100)

    results = []
    results.append(await scenario_1(cc, sm1))
    results.append(await scenario_2(cc, sm1))
    results.append(await scenario_3(cc, sm1))
    results.append(scenario_4())
    results.append(await scenario_5(cc))
    
    separator("FINAL SUMMARY")
    if all(results):
        print("  *** ALL 5 SCENARIOS PASSED ***")
        print("  Week 3: Automated Attack Injection is fully operational.")
    else:
        print("  *** SOME SCENARIOS FAILED ***")

if __name__ == "__main__":
    asyncio.run(main())
