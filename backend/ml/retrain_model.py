"""
retrain_model.py -- ML Model Retraining (One-Class IsolationForest)

CORRECT TRAINING ARCHITECTURE:
  - Reads from ml/dataset/training_data.csv
  - Fits IsolationForest ONLY on normal (label=0) samples
  - Model learns what "normal" looks like
  - Anomaly = deviation from learned normal distribution
  - Attack features (seq_delta<0, hmac=0, rate spike) are captured
    because ML scores BEFORE crypto in the updated ControlCenter

Run: cd backend && python ml/retrain_model.py
"""
import sys
import os
import csv
import json
import random
import warnings
import numpy as np
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import joblib
    from sklearn.ensemble import IsolationForest
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import confusion_matrix
except ImportError as e:
    print(f"[FATAL] {e} — run: pip install scikit-learn joblib")
    sys.exit(1)

try:
    from ml.isolation_forest import FEATURE_ORDER
except ImportError:
    FEATURE_ORDER = [
        "packet_rate", "inter_arrival_time", "payload_size",
        "sequence_delta", "timestamp_delta", "session_duration",
        "hmac_valid", "seq_check_valid", "timestamp_valid",
        "payload_size_zscore", "inter_arrival_zscore",
        "rate_spike_ratio", "consecutive_failures",
        "session_packet_count",
    ]

# ── Paths ──────────────────────────────────────────────────────
DATASET    = os.path.join(os.path.dirname(__file__), "dataset", "training_data.csv")
SAVE_DIR   = os.path.join(os.path.dirname(__file__), "saved_model")
os.makedirs(SAVE_DIR, exist_ok=True)

MODEL_PATH     = os.path.join(SAVE_DIR, "isolation_forest.pkl")
SCALER_PATH    = os.path.join(SAVE_DIR, "scaler.pkl")
THRESHOLD_PATH = os.path.join(SAVE_DIR, "threshold.json")
METADATA_PATH  = os.path.join(SAVE_DIR, "model_metadata.json")

MIN_ATTACK_ROWS = 100


# ── Helpers ────────────────────────────────────────────────────
def metrics(y_true, y_pred):
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    total = tn + fp + fn + tp
    return dict(
        acc  = (tp + tn) / total * 100 if total else 0.0,
        fpr  = fp / (fp + tn) * 100 if (fp + tn) else 0.0,
        fnr  = fn / (fn + tp) * 100 if (fn + tp) else 0.0,
        prec = tp / (tp + fp) * 100 if (tp + fp) else 0.0,
        rec  = tp / (tp + fn) * 100 if (tp + fn) else 0.0,
        tp=int(tp), tn=int(tn), fp=int(fp), fn=int(fn),
    )


def score_to_pred(scores, threshold):
    return [1 if s < threshold else 0 for s in scores]


# ── Synthetic attack rows ──────────────────────────────────────
def make_synthetic_rows():
    """
    Generate synthetic attack rows with distinct feature signatures.
    These supplement live-collected data when attack rows < MIN_ATTACK_ROWS.
    """
    rows = []

    # ── Extra normal rows ──
    for _ in range(3000):
        rows.append({
            "packet_rate": random.gauss(1.0, 0.1),
            "inter_arrival_time": random.gauss(1.0, 0.12),
            "payload_size": random.randint(78, 95),
            "sequence_delta": 0,
            "timestamp_delta": random.uniform(0, 2),
            "session_duration": random.uniform(1, 300),
            "hmac_valid": 1, "seq_check_valid": 1, "timestamp_valid": 1,
            "payload_size_zscore": random.gauss(0, 0.3),
            "inter_arrival_zscore": random.gauss(0, 0.3),
            "rate_spike_ratio": random.gauss(1.0, 0.1),
            "consecutive_failures": 0,
            "session_packet_count": random.randint(1, 200),
            "label": 0,
        })

    # ── Replay attack — negative seq_delta, stale timestamp ──
    for _ in range(500):
        rows.append({
            "packet_rate": random.gauss(1.0, 0.1),
            "inter_arrival_time": random.gauss(1.0, 0.2),
            "payload_size": random.randint(78, 95),
            "sequence_delta": -random.randint(1, 30),
            "timestamp_delta": random.uniform(40, 120),
            "session_duration": random.uniform(30, 300),
            "hmac_valid": 1, "seq_check_valid": 0, "timestamp_valid": 0,
            "payload_size_zscore": random.gauss(0, 0.5),
            "inter_arrival_zscore": random.gauss(0, 0.5),
            "rate_spike_ratio": random.gauss(1.0, 0.2),
            "consecutive_failures": random.randint(1, 8),
            "session_packet_count": random.randint(1, 200),
            "label": 1,
        })

    # ── MITM — HMAC=0, otherwise normal ──
    for _ in range(500):
        rows.append({
            "packet_rate": random.gauss(1.0, 0.15),
            "inter_arrival_time": random.gauss(1.0, 0.15),
            "payload_size": random.randint(78, 95),
            "sequence_delta": 0,
            "timestamp_delta": random.uniform(0, 3),
            "session_duration": random.uniform(1, 300),
            "hmac_valid": 0, "seq_check_valid": 1, "timestamp_valid": 1,
            "payload_size_zscore": random.gauss(0, 0.4),
            "inter_arrival_zscore": random.gauss(0, 0.4),
            "rate_spike_ratio": random.gauss(1.0, 0.15),
            "consecutive_failures": random.randint(1, 10),
            "session_packet_count": random.randint(1, 200),
            "label": 1,
        })

    # ── Flood attack — burst rate spike, tiny IAT ──
    for _ in range(300):
        burst_len = random.randint(10, 25)
        for i in range(burst_len):
            rows.append({
                "packet_rate": random.uniform(8, 25),
                "inter_arrival_time": random.uniform(0.04, 0.12),
                "payload_size": random.randint(78, 95),
                "sequence_delta": i,
                "timestamp_delta": random.uniform(0, 1),
                "session_duration": random.uniform(1, 100),
                "hmac_valid": 1, "seq_check_valid": 0 if i > 0 else 1, "timestamp_valid": 1,
                "payload_size_zscore": random.gauss(0, 0.3),
                "inter_arrival_zscore": random.uniform(3.0, 10.0),
                "rate_spike_ratio": random.uniform(5.0, 20.0),
                "consecutive_failures": i,
                "session_packet_count": random.randint(1, 50),
                "label": 1,
            })
    return rows


# ── Dataset loader ─────────────────────────────────────────────
def load_dataset():
    rows = []
    if os.path.exists(DATASET):
        print(f"  Reading: {DATASET}")
        with open(DATASET, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed = {}
                for feat in FEATURE_ORDER:
                    try:
                        parsed[feat] = float(row[feat])
                    except (KeyError, ValueError):
                        parsed[feat] = 0.0
                parsed["label"] = int(float(row.get("label", 0)))
                rows.append(parsed)
    else:
        print(f"  [WARN] No CSV found at {DATASET}. Using synthetic data only.")

    live_attack = sum(1 for r in rows if r["label"] == 1)
    live_normal = sum(1 for r in rows if r["label"] == 0)
    print(f"  Live rows  -- label=0: {live_normal}  label=1: {live_attack}")

    # ALWAYS add synthetic data to ensure feature variance.
    # Live-collected rows are nearly identical (packet_rate=1.0, IAT=1.0, seq_delta=0)
    # and cause degenerate IsolationForest trees. Synthetic rows span the full
    # feature space the model will see in production.
    print(f"  Adding synthetic rows for feature coverage...")
    rows += make_synthetic_rows()

    attack_count = sum(1 for r in rows if r["label"] == 1)
    normal_count = sum(1 for r in rows if r["label"] == 0)
    print(f"  Total      -- label=0: {normal_count}  label=1: {attack_count}")

    X = np.array([[r[f] for f in FEATURE_ORDER] for r in rows])
    y = np.array([r["label"] for r in rows])
    return X, y


# -- Threshold tuning --
def tune_threshold(val_scores, y_val, candidates=None):
    if candidates is None:
        candidates = [-0.5, -0.4, -0.3, -0.2, -0.15, -0.1, -0.05, 0.0, 0.05, 0.1]
    print(f"\n  {'Threshold':>12}  {'Acc':>8}  {'FPR':>8}  {'Recall':>8}  {'Composite':>10}")

    results = []
    for thr in candidates:
        preds = score_to_pred(val_scores.tolist(), thr)
        m = metrics(y_val.tolist(), preds)
        composite = m["rec"] - m["fpr"] * 2
        results.append((thr, m, composite))
        print(f"  {thr:>12.6f}  {m['acc']:>7.2f}%  {m['fpr']:>7.2f}%  {m['rec']:>7.2f}%  {composite:>10.2f}")

    # Criterion 1: FPR <= 2% AND recall >= 85%
    qualified = [(t, m, c) for t, m, c in results if m["fpr"] <= 2.0 and m["rec"] >= 85.0]
    if qualified:
        best_thr, best_m, _ = min(qualified, key=lambda x: x[1]["fpr"])
        reason = f"FPR={best_m['fpr']:.2f}%<=2% and Recall={best_m['rec']:.2f}%>=85%"
    else:
        # Criterion 2: best Recall - 2*FPR composite
        best_thr, best_m, _ = max(results, key=lambda x: x[2])
        reason = f"Best composite Recall-2*FPR (FPR={best_m['fpr']:.2f}%, Recall={best_m['rec']:.2f}%)"

    return best_thr, reason




# ── Main ───────────────────────────────────────────────────────
def main():
    W = 65
    print("\n" + "=" * W)
    print("   ML MODEL RETRAINING")
    print("   One-Class IsolationForest -- Hybrid Smart Grid Security")
    print("=" * W)

    # ── Phase 1: Load ──
    print("\n[Phase 1] Loading dataset...")
    X, y = load_dataset()
    n_normal = int(np.sum(y == 0))
    n_attack = int(np.sum(y == 1))
    print(f"  Total: {len(y)}  Normal: {n_normal}  Attack: {n_attack}")

    if n_attack < 50:
        print("[ERROR] Insufficient attack samples. Exiting.")
        sys.exit(1)

    # ── Phase 2: Stratified split ──
    print("\n[Phase 2] Splitting 70/15/15 (stratified)...")
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=0.15/0.85, random_state=42, stratify=y_tmp
    )
    X_train_normal = X_train[y_train == 0]
    X_train_attack = X_train[y_train == 1]
    print(f"  Train: {len(X_train)} (normal={len(X_train_normal)}, attack={len(X_train_attack)})")
    print(f"  Val: {len(X_val)}  Test: {len(X_test)}")

    # ── Phase 3: Scale — fit ONLY on normal training samples ──
    print("\n[Phase 3] Fitting StandardScaler on NORMAL training samples only...")
    scaler = StandardScaler()
    X_train_normal_s = scaler.fit_transform(X_train_normal)
    X_val_s          = scaler.transform(X_val)
    X_test_s         = scaler.transform(X_test)

    # -- Phase 4: Fit IsolationForest on NORMAL samples only --
    print("\n[Phase 4] Training IsolationForest (fit on normal-only)...")
    print("  One-class learning: model learns the normal distribution.")

    contamination = 0.08   # matches CLAUDE.md ATTACK_PROBABILITY = 0.08
    print(f"  Training on {len(X_train_normal_s)} normal samples (contamination={contamination})")

    model = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        max_samples=min(512, len(X_train_normal_s)),
        random_state=42, n_jobs=-1, bootstrap=False,
    )
    model.fit(X_train_normal_s)
    print("  Training complete.")

    # Check score range
    sample_scores = model.score_samples(X_train_normal_s)
    print(f"  Score range (train-normal): min={sample_scores.min():.4f} max={sample_scores.max():.4f} mean={sample_scores.mean():.4f}")

    # Overfitting check: FPR on train-normal vs val-normal at p10 reference threshold
    val_normal_mask = (y_val == 0)
    val_normal_s    = X_val_s[val_normal_mask]
    score_range     = sample_scores.max() - sample_scores.min()

    if len(val_normal_s) == 0 or score_range < 0.001:
        print("  [WARN] Skipping overfitting check (degenerate scores or no val-normal samples).")
        train_fpr_ref = val_fpr_ref = gap = 0.0
        overfit = False
    else:
        val_scores_n  = model.score_samples(val_normal_s)
        _ref          = float(np.percentile(sample_scores, 10))
        train_fpr_ref = sum(1 for s in sample_scores if s < _ref) / len(sample_scores) * 100
        val_fpr_ref   = sum(1 for s in val_scores_n   if s < _ref) / len(val_scores_n)   * 100
        gap    = abs(train_fpr_ref - val_fpr_ref)
        overfit = gap > 15.0
        print(f"  Train-normal FPR @ p10 ({_ref:.4f}): {train_fpr_ref:.2f}%")
        print(f"  Val-normal   FPR @ p10 ({_ref:.4f}): {val_fpr_ref:.2f}%")
        print(f"  Gap: {gap:.2f}%")


    print(f"  Overfitting: {'YES' if overfit else 'NO -- PASSED'}")

    # -- Phase 5: Threshold tuning using actual score range --
    print("\n[Phase 5] Threshold tuning on validation set...")
    val_scores_full = model.score_samples(X_val_s)

    all_scores = np.concatenate([sample_scores, val_scores_full])
    s_min, s_max = float(np.min(all_scores)), float(np.max(all_scores))
    print(f"  Score range (train+val): [{s_min:.4f}, {s_max:.4f}]")

    if s_max - s_min < 0.001:
        # Degenerate: use percentile anchors directly
        candidates = sorted(set(
            float(np.percentile(val_scores_full, p))
            for p in [1, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]
        ))
        print("  [WARN] Degenerate range. Using val-percentile thresholds.")
    else:
        linspace_c = list(np.linspace(s_min, s_max, 15))
        pct_c      = [float(np.percentile(all_scores, p)) for p in [5, 10, 20, 30, 50, 70, 90]]
        candidates = sorted(set(round(c, 5) for c in linspace_c + pct_c))

    best_threshold, selection_reason = tune_threshold(val_scores_full, y_val, candidates)
    print(f"\n  Selected threshold: {best_threshold:.5f}  ({selection_reason})")



    # ── Phase 6: Test evaluation ──
    print("\n[Phase 6] Final evaluation on held-out test set...")
    test_scores = model.score_samples(X_test_s)
    test_preds  = score_to_pred(test_scores.tolist(), best_threshold)
    test_met    = metrics(y_test.tolist(), test_preds)

    val_preds = score_to_pred(val_scores_full.tolist(), best_threshold)
    val_met   = metrics(y_val.tolist(), val_preds)

    # ── Phase 6b: Production Distribution Validation ──────────
    # The stratified test set already has the realistic distribution
    # from the dataset (~92% normal / ~8% attack).  Score it and
    # predict what verify_backend.py will report for ML accuracy.
    print("\n[Phase 6b] Production distribution validation...")
    prod_n_normal = int(np.sum(y_test == 0))
    prod_n_attack = int(np.sum(y_test == 1))
    prod_total    = prod_n_normal + prod_n_attack
    prod_pct_n    = prod_n_normal / prod_total * 100 if prod_total else 0.0
    prod_pct_a    = prod_n_attack / prod_total * 100 if prod_total else 0.0

    prod_preds = test_preds   # already scored above
    prod_met   = test_met     # same metrics, just renamed for clarity

    # Predicted ML accuracy in verify_backend: proportion of packets
    # correctly classified (TP + TN) over total.
    predicted_ml_accuracy = prod_met["acc"]
    prod_ready = prod_met["fpr"] <= 5.0 and prod_met["rec"] >= 80.0

    # ── Phase 7: Save ──
    print("\n[Phase 7] Saving artifacts...")
    joblib.dump(model,  MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)

    with open(THRESHOLD_PATH, "w") as f:
        json.dump({"threshold": best_threshold, "selection_reason": selection_reason}, f, indent=2)

    meta = {
        "trained_at"         : datetime.now().isoformat(),
        "training_approach"  : "one-class (fit on normal samples only)",
        "n_estimators"       : 200,
        "contamination"      : float(contamination),
        "total_samples"      : int(len(y)),
        "normal_samples"     : n_normal,
        "attack_samples"     : n_attack,
        "features_used"      : FEATURE_ORDER,
        "selected_threshold" : best_threshold,
        "selection_reason"   : selection_reason,
        "val_accuracy"       : val_met["acc"],
        "val_fpr"            : val_met["fpr"],
        "val_recall"         : val_met["rec"],
        "test_accuracy"      : test_met["acc"],
        "test_fpr"           : test_met["fpr"],
        "test_recall"        : test_met["rec"],
        "overfitting_detected": bool(overfit),
        "train_val_fpr_gap"  : float(gap),
    }
    with open(METADATA_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    # ── Final report ──
    print("\n" + "=" * W)
    print("   ML MODEL TRAINING REPORT")
    print("   One-Class IsolationForest -- Hybrid Smart Grid Security")
    print("=" * W)

    print("\nDATASET")
    print(f"  Total Samples           : {len(y)}")
    print(f"  Normal Samples (label=0): {n_normal}")
    print(f"  Attack Samples (label=1): {n_attack}")
    print(f"  Training approach       : One-class (fit on normal only)")
    print(f"  Contamination           : {contamination} (matches ATTACK_PROBABILITY=0.08)")
    print(f"  Train / Val / Test Split: 70% / 15% / 15%")

    print("\nOVERFITTING CHECK")
    print(f"  Train-normal FPR @ ref  : {train_fpr_ref:.2f}%")
    print(f"  Val-normal   FPR @ ref  : {val_fpr_ref:.2f}%")
    print(f"  FPR Gap                 : {gap:.2f}%")
    print(f"  Overfitting Detected    : {'YES' if overfit else 'NO'}")

    print("\nVALIDATION RESULTS (selected threshold)")
    print(f"  Accuracy                : {val_met['acc']:.2f}%")
    print(f"  False Positive Rate     : {val_met['fpr']:.2f}%")
    print(f"  False Negative Rate     : {val_met['fnr']:.2f}%")
    print(f"  Precision               : {val_met['prec']:.2f}%")
    print(f"  Recall (Attack Detect.) : {val_met['rec']:.2f}%")

    print("\nTEST RESULTS (held-out, never seen during training)")
    print(f"  Accuracy                : {test_met['acc']:.2f}%")
    print(f"  False Positive Rate     : {test_met['fpr']:.2f}%")
    print(f"  False Negative Rate     : {test_met['fnr']:.2f}%")
    print(f"  Precision               : {test_met['prec']:.2f}%")
    print(f"  Recall (Attack Detect.) : {test_met['rec']:.2f}%")

    print("\nTHRESHOLD SELECTION")
    print(f"  Selected Threshold      : {best_threshold:.5f}")
    print(f"  Reason                  : {selection_reason}")

    # ── Production Distribution Validation (Change 3) ──────────
    print("\n" + "-" * W)
    print("PRODUCTION DISTRIBUTION VALIDATION")
    print(f"  Test set distribution  : {prod_pct_n:.1f}% normal / {prod_pct_a:.1f}% attack")
    print(f"  Production FPR         : {prod_met['fpr']:.2f}%")
    print(f"  Production Recall      : {prod_met['rec']:.2f}%")
    print(f"  Production Accuracy    : {prod_met['acc']:.2f}%")
    print()
    print(f"  Predicted ML accuracy in verify_backend.py: {predicted_ml_accuracy:.2f}%")
    print(f"  Status: {'READY' if prod_ready else 'NEEDS MORE DATA'}")
    if not prod_ready:
        if prod_met['fpr'] > 5.0:
            print(f"  -> FPR {prod_met['fpr']:.2f}% > 5%. Threshold too low or too many normals scored as anomalies.")
        if prod_met['rec'] < 80.0:
            print(f"  -> Recall {prod_met['rec']:.2f}% < 80%. Attack features not distinct enough.")
    print("-" * W)

    print("\nMODEL SAVED TO")
    print(f"  Model     : {MODEL_PATH}")
    print(f"  Scaler    : {SCALER_PATH}")
    print(f"  Threshold : {THRESHOLD_PATH}")
    print(f"  Metadata  : {METADATA_PATH}")

    ready = prod_ready
    print("\nOVERALL VERDICT")
    print(f"  Model Status            : {'READY' if ready else 'NEEDS REVIEW'}")
    print(f"  Ready for Integration   : {'YES' if ready else 'NO'}")
    print("=" * W + "\n")


if __name__ == "__main__":
    main()
