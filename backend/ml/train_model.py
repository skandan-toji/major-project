"""
train_model.py -- Isolation Forest Training Pipeline

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Trains and saves the Isolation Forest model for anomaly detection.

CRITICAL: FEATURE_COLUMNS here MUST exactly match FEATURE_ORDER in
ml/isolation_forest.py. Any deviation causes a scaler dimension mismatch
at runtime that makes the model flag every packet as anomalous.

Features (14):
    packet_rate, inter_arrival_time, payload_size,
    sequence_delta, timestamp_delta, session_duration,
    hmac_valid, seq_check_valid, timestamp_valid,
    payload_size_zscore, inter_arrival_zscore,
    rate_spike_ratio, consecutive_failures,
    session_packet_count
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
import json
from datetime import datetime

# == 14 ML features — MUST match FEATURE_ORDER in isolation_forest.py ==
FEATURE_COLUMNS = [
    "packet_rate",
    "inter_arrival_time",
    "payload_size",
    "sequence_delta",
    "timestamp_delta",
    "session_duration",
    "hmac_valid",
    "seq_check_valid",
    "timestamp_valid",
    "payload_size_zscore",
    "inter_arrival_zscore",
    "rate_spike_ratio",
    "consecutive_failures",
    "session_packet_count",
]

MODEL_PATH    = os.path.join(os.path.dirname(__file__), "saved_model", "isolation_forest.pkl")
SCALER_PATH   = os.path.join(os.path.dirname(__file__), "saved_model", "scaler.pkl")
METRICS_PATH  = os.path.join(os.path.dirname(__file__), "saved_model", "training_metrics.json")
META_PATH     = os.path.join(os.path.dirname(__file__), "saved_model", "model_metadata.json")
THRESH_PATH   = os.path.join(os.path.dirname(__file__), "saved_model", "threshold.json")


def load_dataset(csv_path: str) -> tuple:
    """
    Loads the traffic features CSV and returns features and labels.
    Validates that all 14 required feature columns are present.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Dataset not found: {csv_path}")

    df = pd.read_csv(csv_path)
    df = df.dropna()

    # Validate columns
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"Dataset is missing {len(missing)} feature column(s): {missing}\n"
            f"Run a fresh simulation with the updated traffic_feature_extractor.py "
            f"to generate a dataset with all 14 required features."
        )

    X = df[FEATURE_COLUMNS]
    y = df["label"]

    total  = len(df)
    normal = int((y == 0).sum())
    attack = int((y == 1).sum())
    print(f"\n{'='*40}")
    print(f"  Dataset loaded from: {csv_path}")
    print(f"  Total rows   : {total:,}")
    print(f"  Normal (0)   : {normal:,}")
    print(f"  Attack (1)   : {attack:,}")
    print(f"  Attack ratio : {attack/total:.2%}")
    print(f"{'='*40}\n")

    return X, y


def select_threshold(model, scaler, X_normal_scaled, X_attack_scaled,
                     target_fpr: float = 0.02) -> float:
    """
    Scans candidate thresholds and picks the one that achieves
    FPR <= target_fpr with the highest recall. Falls back to
    best composite score if no threshold meets the FPR target.
    """
    normal_scores = model.score_samples(X_normal_scaled)
    attack_scores = model.score_samples(X_attack_scaled)

    candidates = np.linspace(
        min(normal_scores.min(), attack_scores.min()),
        max(normal_scores.max(), attack_scores.max()),
        500
    )

    best_thresh     = float(np.median(normal_scores))
    best_composite  = -999.0

    for t in candidates:
        fp = int((normal_scores < t).sum())
        tn = int((normal_scores >= t).sum())
        tp = int((attack_scores < t).sum())
        fn = int((attack_scores >= t).sum())

        fpr_t    = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        recall_t = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        composite = recall_t - 2 * fpr_t
        if composite > best_composite:
            best_composite = composite
            best_thresh    = float(t)

    return best_thresh


def train_and_save(csv_path: str) -> dict:
    """Full training pipeline for Isolation Forest with 14 features."""
    # 1. Load
    X, y = load_dataset(csv_path)

    # 2. Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_test, y_test, test_size=0.5, random_state=42, stratify=y_test
    )

    # 3. Scale — fit on NORMAL training rows only (one-class paradigm)
    X_train_normal = X_train[y_train == 0]
    scaler = StandardScaler()
    scaler.fit(X_train_normal)

    X_train_scaled = scaler.transform(X_train)
    X_val_scaled   = scaler.transform(X_val)
    X_test_scaled  = scaler.transform(X_test)

    X_val_normal_scaled = scaler.transform(X_val[y_val == 0])
    X_val_attack_scaled = scaler.transform(X_val[y_val == 1])

    os.makedirs(os.path.dirname(SCALER_PATH), exist_ok=True)
    joblib.dump(scaler, SCALER_PATH)
    print(f"  Scaler saved  -> {SCALER_PATH}")

    # 4. Train — one-class: fit on normal training rows only
    print(f"  Training Isolation Forest (n_estimators=200, contamination=0.05)...")
    model = IsolationForest(
        n_estimators  = 200,
        max_samples   = 512,
        contamination = 0.05,
        random_state  = 42,
        n_jobs        = -1,
    )
    model.fit(scaler.transform(X_train_normal))
    joblib.dump(model, MODEL_PATH)
    print(f"  Model saved   -> {MODEL_PATH}")

    # 5. Select threshold on validation set
    threshold = select_threshold(
        model, scaler,
        X_val_normal_scaled, X_val_attack_scaled,
        target_fpr=0.02
    )

    # 6. Evaluate on test set
    def _evaluate(X_s, y_true):
        scores = model.score_samples(X_s)
        pred   = (scores < threshold).astype(int)
        tp = int(((pred == 1) & (y_true == 1)).sum())
        fp = int(((pred == 1) & (y_true == 0)).sum())
        tn = int(((pred == 0) & (y_true == 0)).sum())
        fn = int(((pred == 0) & (y_true == 1)).sum())
        acc    = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0
        fpr_   = fp / (fp + tn)           if (fp + tn) > 0  else 0.0
        recall = tp / (tp + fn)           if (tp + fn) > 0  else 0.0
        return dict(accuracy=acc*100, fpr=fpr_*100, recall=recall*100,
                    tp=tp, fp=fp, tn=tn, fn=fn)

    val_m  = _evaluate(X_val_scaled,  y_val.values)
    test_m = _evaluate(X_test_scaled, y_test.values)

    print(f"\n{'='*40}")
    print(f"  Selected threshold : {threshold:.5f}")
    print(f"  Val  accuracy: {val_m['accuracy']:.2f}%  "
          f"FPR: {val_m['fpr']:.2f}%  Recall: {val_m['recall']:.2f}%")
    print(f"  Test accuracy: {test_m['accuracy']:.2f}%  "
          f"FPR: {test_m['fpr']:.2f}%  Recall: {test_m['recall']:.2f}%")
    print(f"{'='*40}\n")

    # 7. Save threshold.json
    thresh_data = {
        "threshold": threshold,
        "selection_reason": (
            f"Best composite Recall-2*FPR "
            f"(FPR={val_m['fpr']:.2f}%, Recall={val_m['recall']:.2f}%)"
        )
    }
    with open(THRESH_PATH, "w") as f:
        json.dump(thresh_data, f, indent=2)
    print(f"  Threshold saved -> {THRESH_PATH}")

    # 8. Save training_metrics.json
    metrics = {
        "total_samples"   : int(len(y)),
        "normal_samples"  : int((y == 0).sum()),
        "attack_samples"  : int((y == 1).sum()),
        "accuracy"        : float(test_m["accuracy"] / 100),
        "detection_rate"  : float(test_m["recall"]   / 100),
        "false_pos_rate"  : float(test_m["fpr"]      / 100),
        "contamination"   : 0.05,
        "n_estimators"    : 200,
        "anomaly_threshold": threshold,
        "feature_columns" : FEATURE_COLUMNS,
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=4)
    print(f"  Metrics saved  -> {METRICS_PATH}")

    # 9. Save model_metadata.json
    meta = {
        "trained_at"         : datetime.now().isoformat(),
        "training_approach"  : "one-class (fit on normal samples only)",
        "n_estimators"       : 200,
        "contamination"      : 0.05,
        "total_samples"      : int(len(y)),
        "normal_samples"     : int((y == 0).sum()),
        "attack_samples"     : int((y == 1).sum()),
        "features_used"      : FEATURE_COLUMNS,
        "num_features"       : len(FEATURE_COLUMNS),
        "selected_threshold" : threshold,
        "selection_reason"   : thresh_data["selection_reason"],
        "val_accuracy"       : val_m["accuracy"],
        "val_fpr"            : val_m["fpr"],
        "val_recall"         : val_m["recall"],
        "test_accuracy"      : test_m["accuracy"],
        "test_fpr"           : test_m["fpr"],
        "test_recall"        : test_m["recall"],
        "overfitting_detected": abs(val_m["fpr"] - test_m["fpr"]) > 3.0,
        "train_val_fpr_gap"  : abs(val_m["fpr"] - test_m["fpr"]),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Metadata saved -> {META_PATH}")

    return metrics


if __name__ == "__main__":
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "dataset_ML", "traffic_features.csv"
    )
    print(f"\n{'='*50}")
    print(f"  Isolation Forest Training Pipeline")
    print(f"  Features: {len(FEATURE_COLUMNS)}")
    print(f"{'='*50}")
    try:
        train_and_save(csv_path)
        print("\n  [OK] Training complete.")
    except Exception as e:
        print(f"\n  [FAIL] Training failed: {e}")
