"""
config.py -- Centralized Configuration for Smart Grid Simulation

Part of the Hybrid Quantum-Resilient Security Framework for
Man-in-the-Middle Attack Detection in Smart Grid Systems.

All tunable parameters live here. No magic numbers elsewhere.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MODE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SIMULATION_MODE = True

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# TIMESTAMP WINDOW
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TIMESTAMP_WINDOW_PRODUCTION = 30    # seconds — strict for real deployment
TIMESTAMP_WINDOW_SIMULATION = 60    # seconds — relaxed for single-machine sim
TIMESTAMP_WINDOW = (
    TIMESTAMP_WINDOW_SIMULATION
    if SIMULATION_MODE
    else TIMESTAMP_WINDOW_PRODUCTION
)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CONCURRENCY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MAX_EXECUTOR_WORKERS = 4            # ProcessPoolExecutor worker count

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SIMULATION PARAMETERS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
METER_STARTUP_STAGGER = 0.1         # seconds between meter starts
PACKET_INTERVAL = 1.0               # seconds between packets per meter
MAX_METERS = 500                    # maximum concurrent meters
SESSION_LIFETIME = 900              # seconds (15 minutes)
MAX_SEQUENCE_NUMBER = 4294967295    # 32-bit unsigned integer max


print("[MODULE LOADED] config.py ready")
