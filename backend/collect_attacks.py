"""
collect_attacks.py -- Realistic Attack Data Collection with Jittered Baseline
"""

import asyncio
import sys
import os
import pandas as pd
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter

POWER_DATA_PATH = os.path.join("..", "dataset_traffic", "power_dataset_clean_100k.csv")

async def collect_attacks():
    cc = ControlCenter()
    # DO NOT clear log - we append to the normal data
    
    meters = []
    print("Setting up 10 Smart Meters for Attack Injection...")

    for i in range(10):
        meter_id = f"SM_A{str(i+1).zfill(2)}"
        dil_pub, dil_priv = generate_dilithium_keypair()
        kyb_pub, kyb_priv = generate_kyber_keypair()
        cc.register_meter(meter_id, dil_pub, kyb_pub)
        meter = SmartMeter(meter_id, dil_priv, kyb_priv, cc.get_public_key())
        # Enable probabilistic attacks
        meter.attack_manager.should_attack_this_packet = lambda sid, mid, pn: random.random() < 0.1
        meters.append(meter)

    stop_event = asyncio.Event()
    start_stats = cc.traffic_feature_extractor.get_stats()
    start_attack_count = start_stats["attack_rows"]

    async def run_meter(meter, idx):
        if not await meter.authenticate(cc): return
        while not stop_event.is_set():
            await meter.send_next(cc)
            jitter = random.uniform(-0.2, 0.2)
            await asyncio.sleep(max(0.1, 1.0 + jitter))

    async def monitor():
        while not stop_event.is_set():
            await asyncio.sleep(5)
            stats = cc.traffic_feature_extractor.get_stats()
            current_attacks = stats["attack_rows"]
            new_attacks = current_attacks - start_attack_count
            print(f"  Progress: {new_attacks} / 3000 attack rows collected")
            if new_attacks >= 3000:
                print("  Target reached! Stopping simulation...")
                stop_event.set()

    tasks = [run_meter(m, i) for i, m in enumerate(meters)]
    tasks.append(monitor())
    
    await asyncio.gather(*tasks, return_exceptions=True)
    print("\n[SUCCESS] Attack collection complete.")

if __name__ == "__main__":
    asyncio.run(collect_attacks())
