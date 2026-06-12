"""
collect_normal.py -- Realistic Normal Data Collection with Jitter
"""

import asyncio
import sys
import os
import pandas as pd
import random

# Add the backend directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter

POWER_DATA_PATH = os.path.join("..", "dataset_traffic", "power_dataset_clean_100k.csv")
OUTPUT_FEATURES_PATH = os.path.join("dataset_ML", "traffic_features.csv")

async def collect_normal():
    cc = ControlCenter()
    
    meters = []
    print("Setting up 10 Smart Meters for Jittered Collection...")

    for i in range(10):
        meter_id = f"SM_{str(i+1).zfill(3)}"
        dil_pub, dil_priv = generate_dilithium_keypair()
        kyb_pub, kyb_priv = generate_kyber_keypair()
        cc.register_meter(meter_id, dil_pub, kyb_pub)
        meter = SmartMeter(meter_id, dil_priv, kyb_priv, cc.get_public_key())
        meter.attack_manager.should_attack_this_packet = lambda sid, mid, pn: False
        meters.append(meter)

    stop_event = asyncio.Event()

    async def run_meter(meter, idx):
        if not await meter.authenticate(cc): return
        while not stop_event.is_set():
            await meter.send_next(cc)
            # Add 20% jitter around the 1.0s interval
            jitter = random.uniform(-0.2, 0.2)
            await asyncio.sleep(max(0.1, 1.0 + jitter))

    async def monitor():
        while not stop_event.is_set():
            await asyncio.sleep(5)
            stats = cc.traffic_feature_extractor.get_stats()
            count = stats["normal_rows"]
            print(f"  Progress: {count} / 10000 normal rows collected")
            if count >= 10000:
                print("  Target reached! Stopping simulation...")
                stop_event.set()

    tasks = [run_meter(m, i) for i, m in enumerate(meters)]
    tasks.append(monitor())
    
    await asyncio.gather(*tasks, return_exceptions=True)
    print("\n[SUCCESS] Normal collection complete.")

if __name__ == "__main__":
    asyncio.run(collect_normal())
