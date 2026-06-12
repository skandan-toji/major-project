"""
full_simulation_report.py -- Full Simulation Performance Report (Scalable)

Uses ProcessPoolExecutor + per-meter queues + staggered startup.
Produces a Confusion Matrix and performance metrics.

IMPORTANT: On Windows, this MUST be run via: python full_simulation_report.py
"""

import asyncio
import time
import warnings
import sys
import os
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_EXECUTOR_WORKERS, METER_STARTUP_STAGGER, PACKET_INTERVAL
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair

# Results storage
simulation_data = {
    "total_packets": 0,
    "actual_attacks": 0,
    "detected_attacks": 0,
    "true_positives": 0,
    "false_positives": 0,
    "true_negatives": 0,
    "false_negatives": 0,
    "detections": {"crypto": 0, "ml": 0}
}

async def run_meter_sim(meter, cc, duration, stats_ref, stagger_delay):
    # FIX 5: Stagger startup
    await asyncio.sleep(stagger_delay)

    start_time = time.time()
    if not await meter.authenticate(cc):
        return

    while time.time() - start_time < duration:
        payload = meter.next_payload()
        initial_attack_count = meter.total_attacks_injected
        result = await meter.send_packet(cc, payload)
        
        was_attack = meter.total_attacks_injected > initial_attack_count
        is_detected = (not result.get("valid", True)) or result.get("ml_flagged", False)
        
        stats_ref["total_packets"] += 1
        if was_attack:
            stats_ref["actual_attacks"] += 1
            if is_detected:
                stats_ref["true_positives"] += 1
                stats_ref["detected_attacks"] += 1
                if not result.get("valid"): stats_ref["detections"]["crypto"] += 1
                else: stats_ref["detections"]["ml"] += 1
            else:
                stats_ref["false_negatives"] += 1
        else:
            if is_detected:
                stats_ref["false_positives"] += 1
            else:
                stats_ref["true_negatives"] += 1
        
        await asyncio.sleep(PACKET_INTERVAL)

async def main():
    print("\n" + "="*60)
    print("   HYBRID SECURITY FRAMEWORK — PERFORMANCE REPORT")
    print("="*60)
    
    warnings.filterwarnings("ignore", category=UserWarning)

    # Create executor inside main() — Windows-safe
    executor = ProcessPoolExecutor(max_workers=MAX_EXECUTOR_WORKERS)
    cc = ControlCenter(executor=executor)
    
    num_meters = 20
    duration = 30
    
    print(f"Initializing {num_meters} Smart Meters...")
    meters = []
    for i in range(num_meters):
        m_id = f"SM_{str(i+1).zfill(3)}"
        d_pk, d_sk = generate_dilithium_keypair()
        k_pk, k_sk = generate_kyber_keypair()
        cc.register_meter(m_id, d_pk, k_pk)
        meters.append(SmartMeter(
            m_id, d_sk, k_sk, cc.get_public_key(),
            max_rows=1000, executor=executor
        ))

    print(f"Running simulation for {duration} seconds...")
    
    # Progress tracker
    async def tracker():
        for i in range(0, duration, 10):
            print(f"  [SIM] Time: {i}s/{duration}s | Packets: {simulation_data['total_packets']}")
            await asyncio.sleep(10)
            
    await asyncio.gather(
        tracker(),
        *[run_meter_sim(m, cc, duration, simulation_data, i * METER_STARTUP_STAGGER)
          for i, m in enumerate(meters)]
    )

    print("\n" + "="*60)
    print("              FINAL PERFORMANCE REPORT")
    print("="*60)
    
    sd = simulation_data
    total = sd["total_packets"]
    accuracy = (sd["true_positives"] + sd["true_negatives"]) / total if total > 0 else 0
    recall = sd["true_positives"] / sd["actual_attacks"] if sd["actual_attacks"] > 0 else 0
    precision = sd["true_positives"] / (sd["true_positives"] + sd["false_positives"]) if (sd["true_positives"] + sd["false_positives"]) > 0 else 0
    normal_total = sd["false_positives"] + sd["true_negatives"]
    fpr = sd["false_positives"] / normal_total * 100 if normal_total > 0 else 0

    print(f"Total Packets Transmitted : {total}")
    print(f"Total Attacks Injected    : {sd['actual_attacks']}")
    print(f"Total Attacks Detected    : {sd['detected_attacks']}")
    print(f"  - Caught by Crypto      : {sd['detections']['crypto']}")
    print(f"  - Caught by ML          : {sd['detections']['ml']}")
    print(f"\n--- PERFORMANCE METRICS ---")
    print(f"Overall System Accuracy   : {accuracy*100:.2f}%")
    print(f"Attack Detection Rate     : {recall*100:.2f}%")
    print(f"Detection Precision       : {precision*100:.2f}%")
    print(f"False Positive Rate       : {fpr:.2f}%")

    print("\n--- CONFUSION MATRIX ---")
    print(f"                 Actual: Normal   Actual: Attack")
    print(f"Predicted: Normal     {sd['true_negatives']:<10}      {sd['false_negatives']:<10}")
    print(f"Predicted: Attack     {sd['false_positives']:<10}      {sd['true_positives']:<10}")
    print("="*60 + "\n")

    executor.shutdown(wait=False)

if __name__ == "__main__":
    asyncio.run(main())
