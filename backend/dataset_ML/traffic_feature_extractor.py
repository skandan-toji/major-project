"""
traffic_feature_extractor.py -- Traffic Feature Extractor for ML Dataset Generation

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Records traffic features for every packet processed during simulation.
Writes one row per packet to a CSV file that serves as the ML training
dataset.

Feature Columns (14 ML features + metadata + label):
    meter_id, session_id, sequence_number,
    packet_rate, inter_arrival_time, payload_size,
    sequence_delta, timestamp_delta, session_duration,
    hmac_valid, seq_check_valid, timestamp_valid,
    payload_size_zscore, inter_arrival_zscore,
    rate_spike_ratio, consecutive_failures,
    session_packet_count,
    label

CRITICAL: The 14 ML feature columns MUST match FEATURE_ORDER in
ml/isolation_forest.py exactly. Any mismatch causes scaler dimension
errors and garbage ML scores at runtime.
"""

import csv
import os
import time


# ── These columns must match FEATURE_ORDER in isolation_forest.py ──
FEATURE_COLUMNS = [
    "meter_id",
    "session_id",
    "sequence_number",
    # ── 14 ML features (match isolation_forest.py FEATURE_ORDER) ──
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
    # ── Ground-truth label ─────────────────────────────────────────
    "label",
]

# ── ML features used for training — order must match FEATURE_ORDER ─
ML_FEATURE_COLUMNS = [
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

WINDOW_SIZE = 50   # rolling window for per-meter baseline (matches MeterBaseline)


class _MeterBaseline:
    """
    Minimal per-meter rolling baseline for feature extraction.
    Mirrors MeterBaseline in ml/meter_baseline.py so deviation
    features logged to CSV match what the runtime detector computes.
    """

    def __init__(self):
        self.payload_sizes: list       = []
        self.inter_arrival_times: list = []
        self.last_packet_time: float   = None
        self.packet_count: int         = 0
        self.consecutive_failures: int = 0
        self.baseline_rate: float      = 1.0

    def update(self, payload_size: int, packet_time: float,
               crypto_passed: bool) -> None:
        if self.last_packet_time is not None:
            iat = packet_time - self.last_packet_time
            if iat > 0:
                self.inter_arrival_times.append(iat)
                if len(self.inter_arrival_times) > WINDOW_SIZE:
                    self.inter_arrival_times.pop(0)
        self.last_packet_time = packet_time
        self.packet_count += 1

        self.payload_sizes.append(payload_size)
        if len(self.payload_sizes) > WINDOW_SIZE:
            self.payload_sizes.pop(0)

        if not crypto_passed:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        recent = self.inter_arrival_times[-10:]
        if len(recent) >= 5:
            avg_iat = sum(recent) / len(recent)
            if avg_iat > 0:
                self.baseline_rate = 1.0 / avg_iat

    def payload_zscore(self, payload_size: int) -> float:
        if len(self.payload_sizes) < 5:
            return 0.0
        mean = sum(self.payload_sizes) / len(self.payload_sizes)
        var  = sum((x - mean) ** 2 for x in self.payload_sizes) / len(self.payload_sizes)
        std  = var ** 0.5
        return 0.0 if std == 0 else abs(payload_size - mean) / std

    def iat_zscore(self, iat: float) -> float:
        if len(self.inter_arrival_times) < 5:
            return 0.0
        mean = sum(self.inter_arrival_times) / len(self.inter_arrival_times)
        var  = sum((x - mean) ** 2 for x in self.inter_arrival_times) / len(self.inter_arrival_times)
        std  = var ** 0.5
        return 0.0 if std == 0 else abs(iat - mean) / std

    def rate_spike_ratio(self, current_rate: float) -> float:
        if self.baseline_rate <= 0:
            return 1.0
        return current_rate / self.baseline_rate


class TrafficFeatureExtractor:
    """
    Logs all 14 ML traffic features + metadata for every packet to CSV.
    Used to generate the ML training dataset automatically while the
    simulation runs.

    The 5 behavioral deviation features (payload_size_zscore,
    inter_arrival_zscore, rate_spike_ratio, consecutive_failures,
    session_packet_count) are computed by an internal per-meter rolling
    baseline that mirrors ml/meter_baseline.py, ensuring the logged
    values reflect exactly what the runtime IsolationForestDetector sees.

    Attributes:
        log_file_path (str):  Path to the CSV output file.
        row_count (int):      Total rows written so far.
    """

    def __init__(self, log_file_path: str = "dataset_ML/traffic_features.csv"):
        self.log_file_path = log_file_path
        self.row_count     = 0
        self._baselines: dict[str, _MeterBaseline] = {}

        log_dir = os.path.dirname(self.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        if not os.path.exists(self.log_file_path):
            with open(self.log_file_path, "w", newline="") as f:
                csv.writer(f).writerow(FEATURE_COLUMNS)
        else:
            try:
                with open(self.log_file_path, "r") as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    self.row_count = sum(1 for _ in reader)
            except Exception:
                self.row_count = 0

    # ── Public API ────────────────────────────────────────────────

    def log_packet(self,
                   meter_id: str,
                   session_id: str,
                   sequence_number: int,
                   payload_size: int,
                   packet_timestamp: float,
                   sequence_delta: int,
                   hmac_valid: int,
                   seq_check_valid: int,
                   timestamp_valid: int,
                   session_start_time: float,
                   label: int,
                   ml_score: float = 0.0) -> None:
        """
        Records one row of traffic features to the CSV file.

        Computes inter_arrival_time from actual per-meter timestamps
        (not a fixed value) so the logged IAT reflects true jitter
        from async scheduling + PQC overhead.
        """
        packet_time = time.time()
        baseline    = self._baselines.setdefault(meter_id, _MeterBaseline())

        # ── Timing features ──────────────────────────────────────
        if baseline.last_packet_time is not None:
            iat = packet_time - baseline.last_packet_time
            if iat <= 0:
                iat = 0.001
        else:
            iat = 0.0

        packet_rate      = (1.0 / iat) if iat > 0 else 0.0
        timestamp_delta  = abs(packet_time - packet_timestamp)
        session_duration = packet_timestamp - session_start_time

        # ── Deviation features (computed BEFORE baseline.update) ─
        # Mirrors the order in control_center.py where deviation
        # features are read before the baseline is updated.
        pz = baseline.payload_zscore(payload_size)
        iz = baseline.iat_zscore(iat)
        rr = baseline.rate_spike_ratio(packet_rate)
        cf = float(baseline.consecutive_failures)
        sp = float(baseline.packet_count)          # session_packet_count before increment

        # Update baseline with this packet's outcome
        crypto_passed = (hmac_valid == 1 and seq_check_valid == 1
                         and timestamp_valid == 1)
        baseline.update(payload_size, packet_time, crypto_passed)

        # ── Write row ────────────────────────────────────────────
        row = [
            meter_id,
            session_id,
            sequence_number,
            round(packet_rate, 6),
            round(iat, 6),
            payload_size,
            sequence_delta,
            round(timestamp_delta, 6),
            round(session_duration, 6),
            hmac_valid,
            seq_check_valid,
            timestamp_valid,
            round(pz, 6),
            round(iz, 6),
            round(rr, 6),
            cf,
            sp,
            label,
        ]

        try:
            with open(self.log_file_path, "a", newline="") as f:
                csv.writer(f).writerow(row)
            self.row_count += 1
        except Exception:
            pass

    def get_stats(self) -> dict:
        normal_count = 0
        attack_count = 0
        try:
            if os.path.exists(self.log_file_path):
                with open(self.log_file_path, "r") as f:
                    for row in csv.DictReader(f):
                        lbl = int(row.get("label", 0))
                        if lbl == 0:
                            normal_count += 1
                        else:
                            attack_count += 1
        except Exception:
            pass
        return {
            "total_rows": normal_count + attack_count,
            "normal_rows": normal_count,
            "attack_rows": attack_count,
            "log_file": self.log_file_path,
        }

    def clear_log(self) -> None:
        """Wipes the CSV and resets in-memory state."""
        with open(self.log_file_path, "w", newline="") as f:
            csv.writer(f).writerow(FEATURE_COLUMNS)
        self.row_count  = 0
        self._baselines = {}


print("[MODULE LOADED] traffic_feature_extractor.py ready")
