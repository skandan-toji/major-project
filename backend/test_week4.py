"""
test_week4.py -- Week 4 Integration Test (Final Clean)
"""

import asyncio
import time
import os
import json
import joblib
import numpy as np
import warnings
from ml.train_model import train_and_save
from ml.isolation_forest import load_detector, AnomalyDetector
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from crypto.packet_builder import build_data_packet

# Update the threshold globally for the test
TEST_THRESHOLD = -0.57

# Ignore sklearn feature name warnings
warnings.filterwarnings("ignore", category=UserWarning)

def separator(title):
    print("\n" + "=" * 64)
    print("  " + title)
    print("=" * 64)

def test_scenario_1_2():
    separator("SCENARIOS 1 & 2: Training and Loading Verification")
    csv_path = os.path.join("dataset_ML", "traffic_features.csv")
    metrics = train_and_save(csv_path)
    detector = load_detector()
    return detector.is_loaded()

def test_scenario_3_4():
    separator("SCENARIOS 3 & 4: Packet Scoring and Flood Detection")
    detector = load_detector()
    detector.threshold = TEST_THRESHOLD
    
    print(f"  Using Calibrated Threshold: {TEST_THRESHOLD}")
    
    print("  Scoring 20 Normal Packets (IAT=0.01)...")
    normal_results = []
    detector.last_packet_time["SM_TEST"] = time.time() - 0.01
    
    for i in range(20):
        res = detector.score_packet("SM_TEST", i+1, 160, time.time(), 0, 1, 1, 1, time.time() - 10)
        normal_results.append(res)
        time.sleep(0.01)
        
    not_flagged = sum(1 for r in normal_results if not r["is_anomaly"])
    print(f"    Normal Score Range: {min(r['score'] for r in normal_results):.4f} to {max(r['score'] for r in normal_results):.4f}")
    print(f"  Normal packets NOT flagged: {not_flagged}/20")
    
    print("\n  Scoring 20 Heavy Flood Packets (IAT=0.001)...")
    flood_results = []
    start_time = time.time()
    detector.last_packet_time["SM_FLOOD"] = start_time - 0.001
    
    for i in range(20):
        res = detector.score_packet("SM_FLOOD", i+1, 160, start_time + (i * 0.001), 0, 1, 1, 1, start_time - 10)
        flood_results.append(res)
        
    flagged = sum(1 for r in flood_results if r["is_anomaly"])
    print(f"    Flood Score Range: {min(r['score'] for r in flood_results):.4f} to {max(r['score'] for r in flood_results):.4f}")
    print(f"  Flood packets flagged: {flagged}/20")
    
    return not_flagged >= 18 and flagged >= 15

async def test_scenario_5_6():
    separator("SCENARIOS 5 & 6: Full Integration and Stats")
    
    cc = ControlCenter()
    cc.anomaly_detector.threshold = TEST_THRESHOLD
    
    dil_pk, dil_sk = generate_dilithium_keypair()
    kyb_pk, kyb_sk = generate_kyber_keypair()
    cc.register_meter("SM_001", dil_pk, kyb_pk)
    sm1 = SmartMeter("SM_001", dil_sk, kyb_sk, cc.get_public_key(), max_rows=100)
    
    # 1. Start a fresh session with flood interval (0.005s)
    print("  Running flood session (interval=0.005s, 50 packets)...")
    await sm1.run_session(cc, interval=0.005, max_packets=50)
    
    # 2. Check stats
    stats = cc.get_stats()
    print(f"  ML Flagged Count: {stats['ml_flagged_count']} / 50 total")
    
    if stats["ml_flagged_count"] > 0:
        print("  [PASS] ML integration verified in stats")
        return True
    return False

async def main():
    s12 = test_scenario_1_2()
    s34 = test_scenario_3_4()
    s56 = await test_scenario_5_6()
        
    separator("WEEK 4 FINAL SUMMARY")
    if s12 and s34 and s56:
        print("  *** ALL SCENARIOS PASSED ***")
    else:
        print("  *** SOME SCENARIOS FAILED ***")

if __name__ == "__main__":
    asyncio.run(main())
