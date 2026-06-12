"""
verify_backend.py -- Comprehensive Backend Verification & Benchmarking

100 Smart Meters | 300 Second (5 Minute) Simulation
Real crypto stack -- no mocking, no shortcuts.

Run: cd backend && python verify_backend.py
"""
import asyncio
import sys
import os
import time
import json
import warnings
import random
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict

warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Validate imports ────────────────────────────────────────────
try:
    from config import MAX_EXECUTOR_WORKERS, METER_STARTUP_STAGGER, TIMESTAMP_WINDOW
    from crypto.dilithium_module import generate_dilithium_keypair
    from crypto.kyber_module import generate_kyber_keypair
    from server.control_center import ControlCenter
    from client.smart_meter import SmartMeter
    from verify_helpers import (generate_synthetic_rows, benchmark_crypto,
                                compute_percentile, safe_div, safe_pct,
                                print_report, build_json)
except ImportError as e:
    print(f"[FATAL] Missing module: {e}")
    print("Make sure you are running from the backend/ directory.")
    sys.exit(1)

# ── Simulation Parameters ──────────────────────────────────────
NUM_METERS = 100
DURATION = 300          # 5 minutes
INTERVAL = 1.0
STAGGER = 0.1
ATTACK_PROB = 0.08

PARAMS = {
    "num_meters": NUM_METERS, "duration": DURATION, "interval": INTERVAL,
    "stagger": STAGGER, "attack_prob": ATTACK_PROB,
    "ts_window": TIMESTAMP_WINDOW, "executor_workers": MAX_EXECUTOR_WORKERS,
}

# ── Shared State (protected by asyncio — single thread) ────────
pkt_stats = {"sent": 0, "accepted": 0, "rejected": 0}
atk_stats = {"injected": 0, "tp": 0, "fn": 0, "tn": 0, "fp": 0}
rej_stats = defaultdict(int)
ml_stats = {"loaded": False, "scored": 0, "flagged": 0, "tp": 0, "fp": 0,
            "tn": 0, "fn": 0, "avg_score": 0.0, "score_sum": 0.0}
total_latencies = []   # end-to-end including queue wait
crypto_latencies = []  # pure crypto ops only (from CC result)
meter_data = {}  # meter_id -> stats dict
peak_windows = []  # (window_start, count) for throughput peaks

# ── Per-Meter Tracker ──────────────────────────────────────────
def get_meter_stats(mid):
    if mid not in meter_data:
        meter_data[mid] = {"meter_id": mid, "packets_sent": 0,
            "packets_accepted": 0, "packets_rejected": 0,
            "attacks_injected": 0, "attacks_detected": 0, "false_positives": 0}
    return meter_data[mid]

# ── Classify rejection reason ──────────────────────────────────
REASON_MAP = {
    "hmac_failed": "hmac_failed", "replay_detected": "replay_detected",
    "stale_timestamp": "stale_timestamp", "session_expired": "session_expired",
    "session_not_found_or_expired": "session_expired",
    "blacklisted_session": "blacklisted_session",
    "decryption_failed": "decryption_failed",
}

def classify_reason(reason):
    if not reason:
        return "other"
    for key, val in REASON_MAP.items():
        if key in reason:
            return val
    return "other"

# ── Meter Simulation Coroutine ─────────────────────────────────
async def run_meter(meter, cc, duration, stagger_delay):
    await asyncio.sleep(stagger_delay)
    mid = meter.meter_id
    ms = get_meter_stats(mid)

    auth_ok = await meter.authenticate(cc)
    if not auth_ok:
        return

    start = time.time()
    while time.time() - start < duration:
        initial_atk = meter.total_attacks_injected
        t0 = time.perf_counter()
        result = await meter.send_packet(cc)
        total_elapsed_ms = (time.perf_counter() - t0) * 1000
        total_latencies.append(total_elapsed_ms)
        # Crypto latency is separately reported by the CC result field
        if "crypto_latency_ms" in result:
            crypto_latencies.append(result["crypto_latency_ms"])

        was_attack = meter.total_attacks_injected > initial_atk
        valid = result.get("valid", False)
        reason = result.get("reason", "")
        ml_flagged = result.get("ml_flagged", False)
        ml_score = result.get("ml_score", 0.0)
        crypto_rejected = not valid

        pkt_stats["sent"] += 1
        ms["packets_sent"] += 1

        if was_attack:
            atk_stats["injected"] += 1
            ms["attacks_injected"] += 1
            if crypto_rejected or ml_flagged:
                atk_stats["tp"] += 1
                ms["attacks_detected"] += 1
            else:
                atk_stats["fn"] += 1
        else:
            if crypto_rejected:
                atk_stats["fp"] += 1
                ms["false_positives"] += 1
                rej_stats[classify_reason(reason)] += 1
            else:
                atk_stats["tn"] += 1

        if valid:
            pkt_stats["accepted"] += 1
            ms["packets_accepted"] += 1
        else:
            pkt_stats["rejected"] += 1
            ms["packets_rejected"] += 1
            if was_attack:
                rej_stats[classify_reason(reason)] += 1

        # ML tracking
        if valid and ml_score != 0.0:
            ml_stats["scored"] += 1
            ml_stats["score_sum"] += ml_score
            if ml_flagged:
                ml_stats["flagged"] += 1
                if was_attack:
                    ml_stats["tp"] += 1
                else:
                    ml_stats["fp"] += 1
            else:
                if was_attack:
                    ml_stats["fn"] += 1
                else:
                    ml_stats["tn"] += 1

        await asyncio.sleep(INTERVAL)

# ── Progress Printer ───────────────────────────────────────────
async def progress_printer(stop_event, sim_start):
    interval = 5
    last_count = 0
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
            break
        except asyncio.TimeoutError:
            elapsed = int(time.time() - sim_start)
            s = pkt_stats
            a = atk_stats
            norm = a['tn'] + a['fp']
            fpr = safe_pct(a['fp'], norm)
            pps = safe_div(s['sent'], elapsed) if elapsed > 0 else 0
            # Track peak throughput per 5s window
            window_count = s['sent'] - last_count
            peak_windows.append(window_count / interval if interval > 0 else 0)
            last_count = s['sent']
            print(f"[T+{elapsed:03d}s] Meters: {NUM_METERS} | Sent: {s['sent']} | "
                  f"Accepted: {s['accepted']} | Rejected: {s['rejected']} | "
                  f"Attacks: {a['injected']} | Detected: {a['tp']} | "
                  f"FPR: {fpr:.2f}% | Pkt/s: {pps:.1f}")

# ── Main ───────────────────────────────────────────────────────
async def main():
    print("\n" + "=" * 65)
    print("   BACKEND VERIFICATION SCRIPT")
    print(f"   {NUM_METERS} Smart Meters | {DURATION}s (5 min) Simulation")
    print("=" * 65)

    executor = ProcessPoolExecutor(max_workers=MAX_EXECUTOR_WORKERS)

    # Phase 1: Crypto Benchmark
    print("\n[Phase 1] Benchmarking individual crypto operations...")
    crypto_bench = benchmark_crypto(iterations=5)
    for op, ms in crypto_bench.items():
        print(f"  {op:24s}: {ms:.2f}ms")

    # Phase 2: Create meters
    print(f"\n[Phase 2] Creating {NUM_METERS} meters and generating keypairs...")
    cc = ControlCenter(executor=executor)
    ml_stats["loaded"] = cc.anomaly_detector is not None

    synthetic_rows = generate_synthetic_rows(500)
    meters = []
    for i in range(NUM_METERS):
        mid = f"SM_{str(i+1).zfill(3)}"
        d_pk, d_sk = generate_dilithium_keypair()
        k_pk, k_sk = generate_kyber_keypair()
        cc.register_meter(mid, d_pk, k_pk)
        meters.append(SmartMeter(
            mid, d_sk, k_sk, cc.get_public_key(),
            data_rows=synthetic_rows, executor=executor
        ))
    print(f"  {NUM_METERS} meters created and registered.")

    # Phase 3: Run simulation
    print(f"\n[Phase 3] Starting {DURATION}s simulation...")
    print("-" * 65)

    stop_event = asyncio.Event()
    sim_start = time.time()

    progress_task = asyncio.create_task(progress_printer(stop_event, sim_start))

    try:
        tasks = [run_meter(m, cc, DURATION, i * STAGGER) for i, m in enumerate(meters)]
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Stopping simulation gracefully...")
    finally:
        stop_event.set()
        await progress_task

    sim_elapsed = time.time() - sim_start

    # Phase 4: Compute results
    print(f"\n[Phase 4] Computing results...")

    total_arr  = np.array(total_latencies)  if total_latencies  else np.array([0.0])
    crypto_arr = np.array(crypto_latencies) if crypto_latencies else np.array([0.0])
    lat_data = {
        "duration"     : sim_elapsed,
        # End-to-end (includes queue wait under flood storms)
        "avg"          : float(np.mean(total_arr)),
        "min"          : float(np.min(total_arr)),
        "max"          : float(np.max(total_arr)),
        "p95"          : float(np.percentile(total_arr, 95)),
        "p99"          : float(np.percentile(total_arr, 99)),
        # Pure crypto only
        "crypto_avg"   : float(np.mean(crypto_arr)),
        "crypto_min"   : float(np.min(crypto_arr)),
        "crypto_max"   : float(np.max(crypto_arr)),
        "crypto_p95"   : float(np.percentile(crypto_arr, 95)),
        "crypto_p99"   : float(np.percentile(crypto_arr, 99)),
    }

    sess_data = {
        "created": cc.auth_success_count,
        "active": len(cc.session_manager.list_active_sessions()),
    }

    if ml_stats["scored"] > 0:
        ml_stats["avg_score"] = ml_stats["score_sum"] / ml_stats["scored"]

    meter_list = sorted(meter_data.values(), key=lambda m: m['meter_id'])

    # Verdict — uses CRYPTO P99, not total P99
    norm_total = atk_stats['tn'] + atk_stats['fp']
    total_classified = atk_stats['tp'] + atk_stats['fn'] + atk_stats['tn'] + atk_stats['fp']
    acceptance_normal = safe_pct(atk_stats['tn'], norm_total)
    fpr = safe_pct(atk_stats['fp'], norm_total)
    accuracy = safe_pct(atk_stats['tp'] + atk_stats['tn'], total_classified)
    crypto_p99 = lat_data['crypto_p99']
    total_p99  = lat_data['p99']

    reasons = []
    if acceptance_normal < 99.5:
        reasons.append(f"Normal acceptance rate {acceptance_normal:.2f}% < 99.5%")
    if fpr > 0.5:
        reasons.append(f"False positive rate {fpr:.2f}% > 0.5%")
    if accuracy < 90.0:
        reasons.append(f"Detection accuracy {accuracy:.2f}% < 90.0%")
    if crypto_p99 > 10.0:
        reasons.append(f"Crypto P99 {crypto_p99:.2f}ms > 10ms")
    if total_p99 > 15000.0:
        reasons.append(f"Total P99 {total_p99:.2f}ms > 15000ms (extreme flood congestion)")

    verdict = {"status": "PASS" if not reasons else "FAIL",
               "ready": len(reasons) == 0, "reasons": reasons,
               "latency_note": (
                   "Crypto P99 measures pure PQC+AES+HMAC operations only. "
                   "Total P99 includes queue wait during coordinated flood attacks "
                   "and is expected to be high under intentional burst load."
               )}

    # Phase 5: Print report
    print_report(PARAMS, pkt_stats, atk_stats, dict(rej_stats),
                 lat_data, sess_data, ml_stats, meter_list, verdict, crypto_bench)

    # Phase 6: Save JSON
    results = build_json(PARAMS, pkt_stats, atk_stats, dict(rej_stats),
                         lat_data, sess_data, ml_stats, meter_list, verdict, crypto_bench)
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verification_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results saved to: {out_path}")

    executor.shutdown(wait=False)


if __name__ == "__main__":
    print("Starting Backend Verification...")
    print(f"{NUM_METERS} Smart Meters | {DURATION} Second (5 min) Simulation")
    print("This will take approximately 5-6 minutes to complete.")
    print("Press Ctrl+C to stop early and get partial results.")
    print()
    asyncio.run(main())
