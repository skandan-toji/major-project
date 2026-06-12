"""
meter_baseline.py -- Per-Meter Behavioral Baseline Tracker

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

Tracks rolling behavioral statistics per meter so the ML model
can compute deviation features: z-scores, rate spike ratios, and
consecutive failure counts.
"""


class MeterBaseline:
    """
    Tracks rolling behavioral baseline for one smart meter.
    Updated for EVERY packet (accepted and rejected) so the baseline
    reflects true normal behavior and deviations are meaningful.
    """

    WINDOW_SIZE = 50

    def __init__(self, meter_id: str):
        self.meter_id             = meter_id
        self.payload_sizes        = []
        self.inter_arrival_times  = []
        self.last_packet_time     = None
        self.packet_count         = 0
        self.consecutive_failures = 0
        self.baseline_rate        = 1.0  # packets/sec

    def update(self, payload_size: int, packet_time: float, crypto_passed: bool):
        """
        Called for EVERY packet including rejected ones.
        Updates rolling history and consecutive failure count.
        """
        if self.last_packet_time is not None:
            iat = packet_time - self.last_packet_time
            if iat > 0:
                self.inter_arrival_times.append(iat)
                if len(self.inter_arrival_times) > self.WINDOW_SIZE:
                    self.inter_arrival_times.pop(0)

        self.last_packet_time = packet_time
        self.packet_count += 1

        self.payload_sizes.append(payload_size)
        if len(self.payload_sizes) > self.WINDOW_SIZE:
            self.payload_sizes.pop(0)

        if not crypto_passed:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        # Update rolling baseline rate
        recent = self.inter_arrival_times[-10:]
        if len(recent) >= 5:
            avg_iat = sum(recent) / len(recent)
            if avg_iat > 0:
                self.baseline_rate = 1.0 / avg_iat

    def get_payload_zscore(self, payload_size: int) -> float:
        """Z-score of payload_size vs rolling history. 0.0 if < 5 samples."""
        if len(self.payload_sizes) < 5:
            return 0.0
        mean = sum(self.payload_sizes) / len(self.payload_sizes)
        variance = sum((x - mean) ** 2 for x in self.payload_sizes) / len(self.payload_sizes)
        std = variance ** 0.5
        if std == 0:
            return 0.0
        return abs(payload_size - mean) / std

    def get_iat_zscore(self, iat: float) -> float:
        """Z-score of inter_arrival_time vs rolling history. 0.0 if < 5 samples."""
        if len(self.inter_arrival_times) < 5:
            return 0.0
        mean = sum(self.inter_arrival_times) / len(self.inter_arrival_times)
        variance = sum((x - mean) ** 2 for x in self.inter_arrival_times) / len(self.inter_arrival_times)
        std = variance ** 0.5
        if std == 0:
            return 0.0
        return abs(iat - mean) / std

    def get_rate_spike_ratio(self, current_rate: float) -> float:
        """Ratio of current rate to baseline. 1.0=normal, >5=flood, <0.1=probe."""
        if self.baseline_rate <= 0:
            return 1.0
        return current_rate / self.baseline_rate


class MeterBaselineTracker:
    """
    Manages MeterBaseline objects for all meters in the Control Center.
    One instance is shared across all packet processing.
    """

    def __init__(self):
        self.baselines = {}   # meter_id -> MeterBaseline

    def get_or_create(self, meter_id: str) -> MeterBaseline:
        if meter_id not in self.baselines:
            self.baselines[meter_id] = MeterBaseline(meter_id)
        return self.baselines[meter_id]

    def update_meter(self, meter_id: str, payload_size: int,
                     packet_time: float, crypto_passed: bool):
        self.get_or_create(meter_id).update(payload_size, packet_time, crypto_passed)

    def get_deviation_features(self, meter_id: str, payload_size: int,
                               current_iat: float, current_rate: float) -> dict:
        b = self.get_or_create(meter_id)
        return {
            "payload_size_zscore" : b.get_payload_zscore(payload_size),
            "inter_arrival_zscore": b.get_iat_zscore(current_iat),
            "rate_spike_ratio"    : b.get_rate_spike_ratio(current_rate),
            "consecutive_failures": b.consecutive_failures,
            "session_packet_count": b.packet_count,
        }
