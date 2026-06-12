"""
collect_dataset.py -- ML Training Dataset Collection

Collects feature rows with correct labels using REALISTIC traffic distribution
that matches real deployment conditions (~92% normal / ~8% attack).

Phase 1 -- Pure Normal Traffic:
  Meters   : 20
  Duration : 120 seconds
  Attacks  : NONE (attack_probability = 0.0)
  Target   : minimum 2,000 normal rows (label=0)

Phase 2 -- Realistic Mixed Traffic:
  Meters   : 20
  Duration : 120 seconds
  Attacks  : ON (attack_probability = 0.08 -- matches CLAUDE.md ATTACK_PROBABILITY)
  Labels   : ALL packets get their correct label (normal=0, attack=1)
  Target   : minimum 180 attack rows (label=1), ~92% normal naturally

Final dataset distribution:
  Normal rows  : ~2,150 to 2,400  (label=0) from Phase 1 + Phase 2 normal
  Attack rows  : ~180  to 250     (label=1) from Phase 2 attacks only
  Ratio        : ~92/8 -- matches real deployment traffic exactly

Output: ml/dataset/training_data.csv

Run: cd backend && python ml/collect_dataset.py
"""
import asyncio
import sys
import os
import csv
import time
import random
import warnings
from concurrent.futures import ProcessPoolExecutor

warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from config import MAX_EXECUTOR_WORKERS, METER_STARTUP_STAGGER
    from crypto.dilithium_module import generate_dilithium_keypair
    from crypto.kyber_module import generate_kyber_keypair
    from server.control_center import ControlCenter
    from client.smart_meter import SmartMeter
    from ml.isolation_forest import FEATURE_ORDER
except ImportError as e:
    print(f"[FATAL] {e}")
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────
DATASET_DIR  = os.path.join(os.path.dirname(__file__), "dataset")
DATASET_PATH = os.path.join(DATASET_DIR, "training_data.csv")
os.makedirs(DATASET_DIR, exist_ok=True)

CSV_COLUMNS = FEATURE_ORDER + ["label"]

# ── Simulation parameters ──────────────────────────────────────
PHASE1_METERS   = 20
PHASE1_DURATION = 120   # seconds
PHASE1_ATTACKS  = False # no attacks -- pure normal baseline

PHASE2_METERS   = 20
PHASE2_DURATION = 120   # seconds
PHASE2_ATTACKS  = True  # realistic 8% attack probability (matches CLAUDE.md)

TARGET_NORMAL_ROWS = 2000
TARGET_ATTACK_ROWS = 180

# ── Synthetic payload rows (meter data content) ────────────────
def make_rows(n=300):
    rows = []
    for _ in range(n):
        rows.append({
            "date": "01/01/2026", "time": "00:00:00",
            "global_active_power"  : round(random.uniform(0.5, 25.0), 3),
            "global_reactive_power": round(random.uniform(0.0,  5.0), 3),
            "voltage"              : round(random.uniform(218.0, 242.0), 2),
            "global_intensity"     : round(random.uniform(1.0, 15.0), 2),
            "sub_metering_1"       : round(random.uniform(0.0, 40.0), 1),
            "sub_metering_2"       : round(random.uniform(0.0, 40.0), 1),
            "sub_metering_3"       : round(random.uniform(0.0, 20.0), 1),
        })
    return rows


# ── Shared dataset rows (appended by all meter coroutines) ─────
collected_rows = []   # list of dicts: FEATURE_ORDER keys + "label"


# ── Per-meter runner ───────────────────────────────────────────
async def run_meter(meter, cc, duration, stagger, label_mode):
    """
    Run one meter for `duration` seconds.

    label_mode:
        "normal"  -- all packets are label=0 (pure normal phase)
        "mixed"   -- label assigned based on actual attack injection intent.
                     Correctly labels EVERY packet in the mixed phase:
                       attack packets  -> label=1
                       normal packets  -> label=0
    """
    await asyncio.sleep(stagger)
    if not await meter.authenticate(cc):
        return

    t_end = time.time() + duration

    while time.time() < t_end:
        attacks_before = meter.total_attacks_injected
        result = await meter.send_packet(cc)
        was_attack = meter.total_attacks_injected > attacks_before

        # Label based on injection intent, not crypto outcome.
        # This is critical: attack packets must be label=1 even when
        # the ML model scores them before crypto rejects them.
        if label_mode == "mixed":
            label = 1 if was_attack else 0
        else:
            label = 0  # pure normal phase -- no attacks injected

        # ML features: CC returns them in result dict
        # (ml_features key populated by the ML-before-crypto architecture)
        ml_features = result.get("ml_features", {})
        if not ml_features:
            ml_features = {f: result.get(f, 0.0) for f in FEATURE_ORDER}

        row = {f: ml_features.get(f, 0.0) for f in FEATURE_ORDER}
        row["label"] = label
        collected_rows.append(row)

        await asyncio.sleep(1.0)


# ── Progress printer ───────────────────────────────────────────
async def progress_printer(stop_event, phase_name):
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            n0 = sum(1 for r in collected_rows if r["label"] == 0)
            n1 = sum(1 for r in collected_rows if r["label"] == 1)
            print(f"  [{phase_name}] label=0: {n0} | label=1: {n1} | total: {n0+n1}")


# ── Phase runner ───────────────────────────────────────────────
async def run_phase(phase_name, num_meters, duration, enable_attacks,
                    label_mode, executor):
    atk_str = f"ON (probability=0.08)" if enable_attacks else "OFF"
    print(f"\n[{phase_name}] {num_meters} meters | {duration}s | attacks={atk_str}")

    syn = make_rows(300)
    cc  = ControlCenter(executor=executor)

    meters = []
    for i in range(num_meters):
        mid      = f"{phase_name[:4]}_{str(i+1).zfill(3)}"
        d_pk, d_sk = generate_dilithium_keypair()
        k_pk, k_sk = generate_kyber_keypair()
        cc.register_meter(mid, d_pk, k_pk)
        m = SmartMeter(mid, d_sk, k_sk, cc.get_public_key(),
                       data_rows=syn, executor=executor)
        if not enable_attacks:
            # Disable attack injection entirely for the normal phase
            m.attack_manager.should_attack_this_packet = lambda s, i2, p: False
        meters.append(m)

    stop_event = asyncio.Event()
    asyncio.create_task(progress_printer(stop_event, phase_name))

    tasks = [
        run_meter(m, cc, duration, i * METER_STARTUP_STAGGER, label_mode)
        for i, m in enumerate(meters)
    ]
    await asyncio.gather(*tasks)
    stop_event.set()
    await asyncio.sleep(0.1)


# ── Main ───────────────────────────────────────────────────────
async def main():
    print("\n" + "=" * 65)
    print("  ML DATASET COLLECTION")
    print("  Realistic distribution: ~92% normal / ~8% attack")
    print("=" * 65)

    executor = ProcessPoolExecutor(max_workers=MAX_EXECUTOR_WORKERS)

    # ── Phase 1: Pure normal traffic ──
    before_phase1 = len(collected_rows)
    await run_phase(
        phase_name    = "NORMAL",
        num_meters    = PHASE1_METERS,
        duration      = PHASE1_DURATION,
        enable_attacks= PHASE1_ATTACKS,
        label_mode    = "normal",
        executor      = executor,
    )
    phase1_normal = len(collected_rows) - before_phase1
    print(f"  Phase 1 done: {phase1_normal} normal rows (label=0)")

    # ── Phase 2: Realistic mixed traffic (8% attack probability) ──
    before_phase2 = len(collected_rows)
    await run_phase(
        phase_name    = "MIXED",
        num_meters    = PHASE2_METERS,
        duration      = PHASE2_DURATION,
        enable_attacks= PHASE2_ATTACKS,
        label_mode    = "mixed",
        executor      = executor,
    )
    phase2_rows   = collected_rows[before_phase2:]
    phase2_normal = sum(1 for r in phase2_rows if r["label"] == 0)
    phase2_attack = sum(1 for r in phase2_rows if r["label"] == 1)
    print(f"  Phase 2 done: {phase2_normal} normal rows + {phase2_attack} attack rows")

    # ── Final counts ──
    total_label0 = sum(1 for r in collected_rows if r["label"] == 0)
    total_label1 = sum(1 for r in collected_rows if r["label"] == 1)
    total        = len(collected_rows)
    pct_normal   = total_label0 / total * 100 if total else 0.0
    pct_attack   = total_label1 / total * 100 if total else 0.0

    print(f"\n  Dataset summary:")
    print(f"    Total rows   : {total}")
    print(f"    Normal (0)   : {total_label0}  ({pct_normal:.1f}%)")
    print(f"    Attack (1)   : {total_label1}  ({pct_attack:.1f}%)")
    print(f"    Distribution : {pct_normal:.0f}% normal / {pct_attack:.0f}% attack")

    # ── Save ──
    print(f"\n  Writing to: {DATASET_PATH}")
    with open(DATASET_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(collected_rows)
    print(f"  Saved successfully.")

    # ── Validation warnings ──
    if total_label0 < TARGET_NORMAL_ROWS:
        print(f"\n  [WARN] Only {total_label0} normal rows (target: {TARGET_NORMAL_ROWS}).")
        print("  retrain_model.py will add synthetic rows automatically.")
    if total_label1 < TARGET_ATTACK_ROWS:
        print(f"\n  [WARN] Only {total_label1} attack rows (target: {TARGET_ATTACK_ROWS}).")
        print("  retrain_model.py will add synthetic attack rows automatically.")
    if total_label0 >= TARGET_NORMAL_ROWS and total_label1 >= TARGET_ATTACK_ROWS:
        print(f"\n  [OK] Both targets met. Run: python ml/retrain_model.py")

    executor.shutdown(wait=False)


if __name__ == "__main__":
    print("ML Dataset Collection")
    print(f"  Phase 1: Normal traffic only  ({PHASE1_METERS} meters, {PHASE1_DURATION}s)")
    print(f"  Phase 2: Mixed traffic (8% attacks) ({PHASE2_METERS} meters, {PHASE2_DURATION}s)")
    print(f"  Total runtime: ~{(PHASE1_DURATION + PHASE2_DURATION) // 60 + 1}-5 minutes")
    print()
    asyncio.run(main())
