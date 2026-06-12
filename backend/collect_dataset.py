"""
collect_dataset.py -- Clean Dataset Collection Script

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Runs a headless simulation (no FastAPI, no WebSocket) to collect
exactly TARGET_NORMAL normal rows and TARGET_ATTACK attack rows,
then stops automatically.

Usage:
    cd backend
    python collect_dataset.py

Target:
    10,000 normal rows (label=0)
    2,000  attack rows (label=1)

IAT:
    Packet interval is driven by asyncio scheduling + real PQC
    crypto overhead (Dilithium5, Kyber1024, AES-256-GCM).
    Natural jitter comes from OS scheduler and crypto timing.
    No artificial IAT manipulation.

Attack mix (from attack_injector.py defaults):
    replay : 50%
    mitm   : 30%
    flood  : 20%
"""

import asyncio
import os
import sys
import time
import random
import csv
from concurrent.futures import ProcessPoolExecutor

# Ensure backend/ is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import MAX_EXECUTOR_WORKERS, PACKET_INTERVAL, METER_STARTUP_STAGGER
from crypto.dilithium_module import generate_dilithium_keypair
from crypto.kyber_module import generate_kyber_keypair
from server.control_center import ControlCenter
from client.smart_meter import SmartMeter
from dataset_ML.traffic_feature_extractor import TrafficFeatureExtractor

# ── Targets ───────────────────────────────────────────────────────
TARGET_NORMAL = 10_000
TARGET_ATTACK =  2_000
NUM_METERS    =    50     # 50 concurrent meters for balanced collection
CSV_PATH      = os.path.join(os.path.dirname(__file__),
                             "dataset_ML", "traffic_features.csv")

# ── Counters (shared across coroutines via asyncio — no threads) ──
_normal_count = 0
_attack_count = 0
_stop_event   = None


def _make_rows(n: int = 300) -> list:
    """Synthetic power payload rows — realistic value ranges."""
    rows = []
    for _ in range(n):
        rows.append({
            "date": "01/01/2026", "time": "00:00:00",
            "global_active_power"   : round(random.uniform(0.5,  25.0), 3),
            "global_reactive_power" : round(random.uniform(0.0,   5.0), 3),
            "voltage"               : round(random.uniform(218.0, 242.0), 2),
            "global_intensity"      : round(random.uniform(1.0,   15.0), 2),
            "sub_metering_1"        : round(random.uniform(0.0,   40.0), 1),
            "sub_metering_2"        : round(random.uniform(0.0,   40.0), 1),
            "sub_metering_3"        : round(random.uniform(0.0,   20.0), 1),
        })
    return rows


async def _run_meter(meter: SmartMeter, control_center: ControlCenter,
                     extractor: TrafficFeatureExtractor,
                     meter_index: int, lock: asyncio.Lock) -> None:
    """
    Runs one meter continuously until the global stop event fires.
    After each packet, logs its features directly via the extractor.
    """
    global _normal_count, _attack_count, _stop_event

    await asyncio.sleep(meter_index * METER_STARTUP_STAGGER)

    if not await meter.authenticate(control_center):
        return

    mid = meter.meter_id

    while not _stop_event.is_set():
        # Re-authenticate on session expiry
        if not meter.has_active_session():
            meter.clear_session()
            if not await meter.authenticate(control_center):
                await asyncio.sleep(1.0)
                continue

        initial_atk = meter.total_attacks_injected
        result      = await meter.send_packet(control_center)
        was_attack  = meter.total_attacks_injected > initial_atk

        valid           = result.get("valid", False)
        reason          = result.get("reason", "")
        ml_flagged      = result.get("ml_flagged", False)

        if reason == "no_active_session":
            continue

        # ── Determine label and seq_delta ────────────────────────
        label     = 1 if was_attack else 0
        seq_delta = 0
        hmac_ok   = 1
        seq_ok    = 1
        ts_ok     = 1

        if not valid:
            r = reason.lower()
            if "hmac" in r:
                hmac_ok   = 0
                seq_delta = 0
            elif "replay" in r or "sequence" in r:
                seq_ok    = 0
                seq_delta = -1   # replay = repeated/old sequence
            elif "stale" in r or "timestamp" in r:
                ts_ok     = 0

        # For flood: packets pass crypto (hmac/seq/ts = 1)
        seq_num      = (meter.current_session or {}).get("sequence_number", 0)
        payload_size = len(str(result.get("payload", "")))
        session_start = 0.0
        if meter.current_session:
            # Estimate session start from expiry (expiry = start + 900)
            session_start = meter.current_session.get("expiry_time", time.time() + 900) - 900

        session_id_raw = (meter.current_session or {}).get("session_id", b"")
        session_id_hex = (session_id_raw.hex()
                         if isinstance(session_id_raw, bytes)
                         else str(session_id_raw))

        # ── Handle flood bursts: log each sub-packet ─────────────
        flood_results = result.get("_flood_results")
        if flood_results and len(flood_results) > 1:
            for fi, fr in enumerate(flood_results):
                fr_valid = fr.get("valid", False)
                fr_seq   = int(seq_num) - len(flood_results) + fi + 1
                extractor.log_packet(
                    meter_id        = mid,
                    session_id      = session_id_hex,
                    sequence_number = fr_seq,
                    payload_size    = payload_size,
                    packet_timestamp= time.time(),
                    sequence_delta  = 0,
                    hmac_valid      = 1,
                    seq_check_valid = 1,
                    timestamp_valid = 1,
                    session_start_time = session_start,
                    label           = 1,
                )
        else:
            extractor.log_packet(
                meter_id        = mid,
                session_id      = session_id_hex,
                sequence_number = int(seq_num),
                payload_size    = payload_size,
                packet_timestamp= time.time(),
                sequence_delta  = seq_delta,
                hmac_valid      = hmac_ok,
                seq_check_valid = seq_ok,
                timestamp_valid = ts_ok,
                session_start_time = session_start,
                label           = label,
            )

        # ── Update shared counters and check stop condition ───────
        async with lock:
            if label == 0:
                _normal_count += 1
            else:
                _attack_count += 1

            if _normal_count >= TARGET_NORMAL and _attack_count >= TARGET_ATTACK:
                _stop_event.set()

        # ── Respect PACKET_INTERVAL with natural jitter ───────────
        try:
            await asyncio.wait_for(_stop_event.wait(), timeout=PACKET_INTERVAL)
        except asyncio.TimeoutError:
            pass


async def main() -> None:
    global _normal_count, _attack_count, _stop_event

    print("\n" + "=" * 60)
    print("  Dataset Collection — Smart Grid Security Framework")
    print(f"  Target: {TARGET_NORMAL:,} normal + {TARGET_ATTACK:,} attack rows")
    print(f"  Meters: {NUM_METERS}")
    print(f"  Output: {CSV_PATH}")
    print("=" * 60)

    # ── Delete existing dataset ───────────────────────────────────
    if os.path.exists(CSV_PATH):
        os.remove(CSV_PATH)
        print(f"\n  [CLEANUP] Deleted existing dataset: {CSV_PATH}")

    extractor = TrafficFeatureExtractor(log_file_path=CSV_PATH)
    print(f"  [INIT] Fresh CSV created with {len(extractor._baselines)} baselines")

    _stop_event   = asyncio.Event()
    _normal_count = 0
    _attack_count = 0
    lock          = asyncio.Lock()

    executor     = ProcessPoolExecutor(max_workers=MAX_EXECUTOR_WORKERS)
    cc           = ControlCenter(executor=executor)

    # ── CRITICAL: Redirect CC's internal extractor to a throw-away path ──
    # ControlCenter.__init__ creates its own TrafficFeatureExtractor that
    # also writes to dataset_ML/traffic_features.csv by default. Without this
    # redirect, every packet is logged TWICE (once by CC, once by this script),
    # resulting in exactly 2x the expected row count.
    _dummy_path = os.path.join(os.path.dirname(__file__), "dataset_ML", "_cc_internal.csv")
    cc.traffic_feature_extractor = cc.traffic_feature_extractor.__class__(log_file_path=_dummy_path)

    syn          = _make_rows(500)
    meters       = []

    print(f"\n  [SETUP] Registering {NUM_METERS} meters...")
    for i in range(NUM_METERS):
        mid     = f"SM_{str(i + 1).zfill(3)}"
        d_pk, d_sk = generate_dilithium_keypair()
        k_pk, k_sk = generate_kyber_keypair()
        cc.register_meter(mid, d_pk, k_pk)
        m = SmartMeter(mid, d_sk, k_sk, cc.kyber_public_key,
                       data_rows=syn, executor=executor)
        meters.append(m)

    print(f"  [RUN] Starting collection (this may take several minutes)...\n")
    start_t = time.time()

    tasks = [
        asyncio.create_task(_run_meter(m, cc, extractor, i, lock))
        for i, m in enumerate(meters)
    ]

    # Progress reporter
    async def _progress():
        while not _stop_event.is_set():
            elapsed = time.time() - start_t
            print(f"  [{elapsed:>6.1f}s] Normal: {_normal_count:>6,} / {TARGET_NORMAL:,}  "
                  f"| Attack: {_attack_count:>5,} / {TARGET_ATTACK:,}",
                  end="\r", flush=True)
            try:
                await asyncio.wait_for(_stop_event.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                pass

    progress_task = asyncio.create_task(_progress())

    # Wait for stop event (targets reached) or 30-minute hard timeout
    try:
        await asyncio.wait_for(_stop_event.wait(), timeout=1800)
    except asyncio.TimeoutError:
        print(f"\n\n  [WARN] Hard timeout reached — stopping early.")
        _stop_event.set()

    # Cancel all tasks
    progress_task.cancel()
    done, pending = await asyncio.wait(tasks, timeout=15)
    for t in pending:
        t.cancel()

    executor.shutdown(wait=False)

    elapsed = time.time() - start_t
    stats   = extractor.get_stats()

    print(f"\n\n{'='*60}")
    print(f"  Collection complete in {elapsed:.1f}s")
    print(f"  Normal rows : {stats['normal_rows']:,}")
    print(f"  Attack rows : {stats['attack_rows']:,}")
    print(f"  Total rows  : {stats['total_rows']:,}")
    print(f"  CSV         : {CSV_PATH}")
    print(f"{'='*60}")

    if stats["normal_rows"] < TARGET_NORMAL or stats["attack_rows"] < TARGET_ATTACK:
        print(f"\n  [WARN] Targets not fully reached. "
              f"You can run collect_dataset.py again to append more rows,\n"
              f"  or run train_model.py on what was collected.")
    else:
        print(f"\n  [OK] Targets reached. Now run:")
        print(f"       python ml/train_model.py")


if __name__ == "__main__":
    asyncio.run(main())
