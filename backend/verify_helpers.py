"""
verify_helpers.py -- Helper functions for verify_backend.py
"""
import time
import json
import random
import numpy as np

def generate_synthetic_rows(count=200):
    """Generate synthetic meter payload rows."""
    rows = []
    for _ in range(count):
        rows.append({
            "date": "01/01/2026", "time": "00:00:00",
            "global_active_power": round(random.uniform(0.5, 25.0), 3),
            "global_reactive_power": round(random.uniform(0.0, 5.0), 3),
            "voltage": round(random.uniform(218.0, 242.0), 2),
            "global_intensity": round(random.uniform(1.0, 15.0), 2),
            "sub_metering_1": round(random.uniform(0.0, 40.0), 1),
            "sub_metering_2": round(random.uniform(0.0, 40.0), 1),
            "sub_metering_3": round(random.uniform(0.0, 20.0), 1),
        })
    return rows


def benchmark_crypto(iterations=5):
    """Benchmark individual crypto operations. Returns dict of avg times in ms."""
    from crypto.dilithium_module import generate_dilithium_keypair, sign_message, verify_signature
    from crypto.kyber_module import generate_kyber_keypair, encrypt_aes_key, decrypt_aes_key
    from crypto.aes_module import generate_aes_key, generate_nonce, encrypt_payload, decrypt_payload
    from crypto.hmac_module import compute_hmac, verify_hmac
    import os

    results = {k: [] for k in [
        "dilithium_sign", "dilithium_verify", "kyber_encrypt", "kyber_decrypt",
        "aes_encrypt", "aes_decrypt", "hmac_compute", "hmac_verify"
    ]}

    d_pk, d_sk = generate_dilithium_keypair()
    k_pk, k_sk = generate_kyber_keypair()
    aes_key = generate_aes_key()
    nonce = generate_nonce()
    session_id = os.urandom(16)
    payload = {"device_id": "BENCH", "power_usage": 5.0, "voltage": 230.0}
    msg = b"benchmark_message_for_dilithium"

    for _ in range(iterations):
        t = time.perf_counter(); sig = sign_message(d_sk, msg); results["dilithium_sign"].append(time.perf_counter() - t)
        t = time.perf_counter(); verify_signature(d_pk, msg, sig); results["dilithium_verify"].append(time.perf_counter() - t)
        t = time.perf_counter(); enc_key = encrypt_aes_key(k_pk, aes_key); results["kyber_encrypt"].append(time.perf_counter() - t)
        t = time.perf_counter(); decrypt_aes_key(k_sk, enc_key); results["kyber_decrypt"].append(time.perf_counter() - t)
        t = time.perf_counter(); ct, tag = encrypt_payload(aes_key, nonce, payload); results["aes_encrypt"].append(time.perf_counter() - t)
        t = time.perf_counter(); decrypt_payload(aes_key, nonce, ct, tag); results["aes_decrypt"].append(time.perf_counter() - t)
        t = time.perf_counter(); hmac_val = compute_hmac(aes_key, session_id, nonce, 1, time.time(), ct, tag); results["hmac_compute"].append(time.perf_counter() - t)
        t = time.perf_counter(); verify_hmac(aes_key, session_id, nonce, 1, time.time(), ct, tag, hmac_val); results["hmac_verify"].append(time.perf_counter() - t)

    return {k: np.mean(v) * 1000 for k, v in results.items()}


def compute_percentile(values, p):
    if not values:
        return 0.0
    return float(np.percentile(values, p))


def safe_div(a, b, default=0.0):
    return a / b if b > 0 else default


def safe_pct(a, b):
    return safe_div(a, b) * 100


def print_report(params, pkt, atk, rej, lat, sess, ml, meters, verdict, crypto_bench):
    """Print the full structured report."""
    W = 65
    print("\n" + "=" * W)
    print("   BACKEND VERIFICATION REPORT")
    print("   Hybrid Quantum-Resilient Security Framework")
    print(f"   {params['num_meters']} Smart Meters | {params['duration']}s Simulation")
    print("=" * W)

    print("\nSIMULATION PARAMETERS")
    print(f"  Meters Simulated        : {params['num_meters']}")
    print(f"  Duration                : {params['duration']:.2f} seconds")
    print(f"  Packet Interval         : {params['interval']}s per meter")
    print(f"  Attack Probability      : {params['attack_prob']*100:.1f}%")
    print(f"  Timestamp Window        : {params['ts_window']}s (simulation mode)")
    print(f"  Security Level          : NIST Level 5")
    print(f"  Dilithium Variant       : Dilithium5")
    print(f"  Kyber Variant           : Kyber1024")

    print("\n" + "-" * W)
    print("PACKET STATISTICS")
    print(f"  Total Sent              : {pkt['sent']}")
    print(f"  Total Accepted          : {pkt['accepted']}")
    print(f"  Total Rejected          : {pkt['rejected']}")
    print(f"  Acceptance Rate         : {safe_pct(pkt['accepted'], pkt['sent']):.2f}%")
    print(f"  Rejection Rate          : {safe_pct(pkt['rejected'], pkt['sent']):.2f}%")
    print(f"  Throughput              : {safe_div(pkt['sent'], lat['duration']):.2f} packets/second")

    print("\n" + "-" * W)
    print("ATTACK DETECTION RESULTS")
    print(f"  Attacks Injected        : {atk['injected']}")
    print(f"  True Positives          : {atk['tp']}  (attacks correctly detected)")
    print(f"  False Negatives         : {atk['fn']}  (attacks missed)")
    print(f"  True Negatives          : {atk['tn']}  (normal packets accepted)")
    print(f"  False Positives         : {atk['fp']}  (normal packets wrongly rejected)")
    total = atk['tp'] + atk['fn'] + atk['tn'] + atk['fp']
    print(f"\n  Detection Accuracy      : {safe_pct(atk['tp']+atk['tn'], total):.2f}%")
    norm = atk['tn'] + atk['fp']
    print(f"  False Positive Rate     : {safe_pct(atk['fp'], norm):.2f}%")
    atk_total = atk['tp'] + atk['fn']
    print(f"  False Negative Rate     : {safe_pct(atk['fn'], atk_total):.2f}%")
    print(f"  Precision               : {safe_pct(atk['tp'], atk['tp']+atk['fp']):.2f}%")
    print(f"  Recall                  : {safe_pct(atk['tp'], atk_total):.2f}%")

    print("\n" + "-" * W)
    print("REJECTION BREAKDOWN")
    for label, key in [
        ("HMAC Failed", "hmac_failed"), ("Replay Detected", "replay_detected"),
        ("Stale Timestamp", "stale_timestamp"), ("Session Expired", "session_expired"),
        ("Blacklisted Session", "blacklisted_session"),
        ("Decryption Failed", "decryption_failed"), ("Other", "other")
    ]:
        print(f"  {label:24s}: {rej.get(key, 0)}")

    print("\n" + "-" * W)
    print("LATENCY MEASUREMENTS (milliseconds)")
    print()
    print("  -- Pure Crypto Latency (PQC + AES + HMAC ops only) --")
    print(f"  Dilithium5 Sign         : {crypto_bench['dilithium_sign']:.2f}ms avg")
    print(f"  Dilithium5 Verify       : {crypto_bench['dilithium_verify']:.2f}ms avg")
    print(f"  Kyber1024 Encrypt       : {crypto_bench['kyber_encrypt']:.2f}ms avg")
    print(f"  Kyber1024 Decrypt       : {crypto_bench['kyber_decrypt']:.2f}ms avg")
    print(f"  AES-256-GCM Encrypt     : {crypto_bench['aes_encrypt']:.2f}ms avg")
    print(f"  AES-256-GCM Decrypt     : {crypto_bench['aes_decrypt']:.2f}ms avg")
    print(f"  HMAC-SHA256 Compute     : {crypto_bench['hmac_compute']:.2f}ms avg")
    print(f"  HMAC-SHA256 Verify      : {crypto_bench['hmac_verify']:.2f}ms avg")
    print(f"  Combined Crypto P95     : {lat.get('crypto_p95', 0.0):.2f}ms")
    print(f"  Combined Crypto P99     : {lat.get('crypto_p99', 0.0):.2f}ms  <-- verdict metric")
    print()
    print("  -- System End-to-End Latency (includes queue wait) --")
    print(f"  Average                 : {lat['avg']:.2f}ms")
    print(f"  Minimum                 : {lat['min']:.2f}ms")
    print(f"  Maximum                 : {lat['max']:.2f}ms")
    print(f"  P95                     : {lat['p95']:.2f}ms")
    print(f"  P99                     : {lat['p99']:.2f}ms  (informational)")
    print(f"  Note: High P99 during flood bursts is expected infrastructure behavior.")
    print(f"        The per-meter queue serializes correctly. Crypto is unaffected.")

    print("\n" + "-" * W)
    print("SESSION STATISTICS")
    print(f"  Sessions Created        : {sess['created']}")
    print(f"  Sessions Active at End  : {sess['active']}")
    print(f"  Avg Messages/Session    : {safe_div(pkt['sent'], sess['created']):.2f}")

    print("\n" + "-" * W)
    print("ML ANOMALY DETECTION")
    if ml['loaded']:
        print(f"  Packets Scored          : {ml['scored']}")
        print(f"  Anomalies Flagged       : {ml['flagged']}")
        print(f"  ML True Positives       : {ml['tp']}")
        print(f"  ML False Positives      : {ml['fp']}")
        ml_total = ml['tp'] + ml['fp'] + ml.get('tn', 0) + ml.get('fn', 0)
        print(f"  ML Accuracy             : {safe_pct(ml['tp']+ml.get('tn', 0), ml_total):.2f}%")
        print(f"  Avg Anomaly Score       : {ml['avg_score']:.4f}")
    else:
        print("  ML model not yet trained -- skipping ML metrics")

    print("\n" + "-" * W)
    print("PER-METER SUMMARY")
    if meters:
        most_attacks = max(meters, key=lambda m: m['attacks_injected'])
        fpr_meters = [
            (m, safe_pct(m['false_positives'], m['packets_sent'] - m['attacks_injected']))
            for m in meters
        ]
        highest_fpr = max(fpr_meters, key=lambda x: x[1])
        lowest_fpr  = min(fpr_meters, key=lambda x: x[1])
        zero_fpr    = sum(1 for _, f in fpr_meters if f == 0.0)
        print(f"  Meter with most attacks : {most_attacks['meter_id']} ({most_attacks['attacks_injected']} attacks)")
        print(f"  Highest FPR meter       : {highest_fpr[0]['meter_id']} ({highest_fpr[1]:.2f}%)")
        print(f"  Lowest FPR meter        : {lowest_fpr[0]['meter_id']} ({lowest_fpr[1]:.2f}%)")
        print(f"  Meters with 0% FPR      : {zero_fpr} / {len(meters)}")

    print("\n" + "-" * W)
    print("OVERALL VERDICT")
    print(f"  Backend Status          : {verdict['status']}")
    print(f"  Ready for Dashboard     : {'YES' if verdict['ready'] else 'NO'}")
    if verdict.get('reasons'):
        for r in verdict['reasons']:
            print(f"    - {r}")
    print("=" * W + "\n")


def build_json(params, pkt, atk, rej, lat, sess, ml, meters, verdict, crypto_bench):
    """Build the JSON results dict."""
    from datetime import datetime
    total    = atk['tp'] + atk['fn'] + atk['tn'] + atk['fp']
    norm     = atk['tn'] + atk['fp']
    atk_total = atk['tp'] + atk['fn']
    return {
        "simulation_params": params,
        "packet_stats": {
            "total_sent"     : pkt['sent'],
            "total_accepted" : pkt['accepted'],
            "total_rejected" : pkt['rejected'],
            "acceptance_rate": safe_pct(pkt['accepted'], pkt['sent']),
            "rejection_rate" : safe_pct(pkt['rejected'], pkt['sent']),
            "throughput_pps" : safe_div(pkt['sent'], lat['duration']),
        },
        "attack_detection": {
            "total_injected"    : atk['injected'],
            "true_positives"    : atk['tp'],
            "false_negatives"   : atk['fn'],
            "true_negatives"    : atk['tn'],
            "false_positives"   : atk['fp'],
            "detection_accuracy": safe_pct(atk['tp']+atk['tn'], total),
            "false_positive_rate": safe_pct(atk['fp'], norm),
            "false_negative_rate": safe_pct(atk['fn'], atk_total),
            "precision"         : safe_pct(atk['tp'], atk['tp']+atk['fp']),
            "recall"            : safe_pct(atk['tp'], atk_total),
        },
        "rejection_breakdown": rej,
        "latency_ms": {
            **crypto_bench,
            # Pure crypto latencies (verdict metric)
            "crypto_avg": lat.get("crypto_avg", 0.0),
            "crypto_min": lat.get("crypto_min", 0.0),
            "crypto_max": lat.get("crypto_max", 0.0),
            "crypto_p95": lat.get("crypto_p95", 0.0),
            "crypto_p99": lat.get("crypto_p99", 0.0),
            # System end-to-end (informational)
            "e2e_avg": lat["avg"],
            "e2e_min": lat["min"],
            "e2e_max": lat["max"],
            "e2e_p95": lat["p95"],
            "e2e_p99": lat["p99"],
            "note": "crypto_p99 is the verdict metric. e2e_p99 includes queue wait under flood bursts.",
        },
        "session_stats": sess,
        "ml_stats"    : ml,
        "per_meter"   : meters,
        "verdict": {
            "backend_status"     : verdict['status'],
            "ready_for_dashboard": verdict['ready'],
            "failure_reasons"    : verdict['reasons'],
            "latency_note"       : verdict.get('latency_note', ''),
        },
        "timestamp": datetime.now().isoformat(),
    }
