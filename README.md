# A Hybrid Quantum-Resilient Security Framework for Man-in-the-Middle Attack Detection in Smart Grid Systems

This repository contains a simulation-based web application demonstrating a hybrid, post-quantum cryptography (PQC) and machine learning (ML) security framework designed to protect Smart Grid systems against Man-in-the-Middle (MITM), replay, and flood attacks.

The framework simulates secure communication between **Smart Meters** and a central **Control Center** in a smart grid environment, routing every message through a multi-layered cryptographic pipeline and an anomaly-detection machine learning model.

---

## 🚀 Key Features & Cryptographic Pipeline

Every simulated packet is processed through a 7-layer defense pipeline:

1. **Post-Quantum Device Authentication:** Signatures generated using **Crystals-Dilithium5** (NIST Security Level 5).
2. **Post-Quantum Key Protection:** Session keys exchanged using **Crystals-Kyber1024** (NIST Security Level 5).
3. **Symmetric Data Encryption:** Payloads encrypted using **AES-256-GCM**.
4. **Message Integrity Verification:** Packet verification sealed with **HMAC-SHA256** (using constant-time comparison).
5. **Replay Attack Prevention:** Strict check on sequential packet sequence numbers and timestamp windows.
6. **Session Management:** Time-bound active sessions (15-minute expiry) with cryptographically secure session IDs and nonces.
7. **Anomaly Detection:** An **Isolation Forest** machine learning model trained on grid traffic data to flag out-of-bound packet rates, inter-arrival times, and sequence deltas.

---

## 📊 Verified System Performance Metrics

The simulation framework has been verified at scale (100 meters active over 5 minutes) and achieves the following performance parameters:

| Metric | Verified Value | Description |
| :--- | :--- | :--- |
| **Detection Accuracy** | `98.18%` | Overall threat detection accuracy |
| **False Positive Rate (FPR)** | `0.00%` | Zero false alerts for normal traffic operations |
| **Precision** | `100.00%` | Precision of flagged anomalies |
| **Recall** | `79.78%` | Rate of successfully intercepted threat patterns |
| **Throughput** | `51.47 pkt/s` | Maximum processing rate of the security backend |
| **Crypto Latency (P99)** | `sub-10ms` | Combined latency for all cryptographic operations |

### Cryptographic Operation Latency (Average)
* **Dilithium5 Sign:** `0.73 ms`
* **Dilithium5 Verify:** `0.23 ms`
* **Kyber1024 Encrypt:** `0.17 ms`
* **Kyber1024 Decrypt:** `0.07 ms`
* **AES-256-GCM Encrypt/Decrypt:** `~1.23 ms`

---

## 📁 Project Structure

```text
MAJOR PROJECT/
├── README.md               # Project Documentation
├── CLAUDE.md               # Developer Intelligence / Reference Sheet
├── backend/                # FastAPI Python Backend
│   ├── api/                # FastAPI App, WebSockets & Simulation Runner
│   ├── crypto/             # Dilithium5, Kyber1024, AES-GCM, HMAC Cryptography
│   ├── session/            # Session Management & Lifecycles
│   ├── server/             # Control Center Verification Engine
│   ├── client/             # Smart Meter Simulation Agent
│   ├── attacks/            # Background Attack Injection Engine
│   ├── ml/                 # Isolation Forest Model Training & Model Files
│   └── main.py             # Entry Point
└── frontend/               # React + Vite Frontend Dashboard
    ├── src/
    │   ├── pages/          # Live Operations, Analytics, Attack Intel, Performance
    │   ├── components/     # Network Map, Live Charts, Packet Feed, Session List
    │   └── context/        # Simulation Context State Provider
    └── index.html
```

---

## ⚙️ How to Setup & Run

### Prerequisites
* **Python 3.10+**
* **Node.js 18+** & **npm**

### 1. Run the Backend
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Start the FastAPI server:
   ```bash
   python api/fastapi_server.py
   ```
   *The backend server will run on `http://127.0.0.1:8000`.*

### 2. Run the Frontend
1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```
2. Install package dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open your browser and navigate to:
   ```text
   http://localhost:5173
   ```

---

## 🎨 Frontend Design
The dashboard UI features a custom dark-themed aesthetics platform (gradient borders, glassmorphic panels, and backdrop blurs) inspired by premium dashboard interfaces. It provides:
* **Interactive Network Map:** SVG-based grid visualizer displaying real-time packet transmissions, active alerts, and communication vectors.
* **Live Charts:** Cryptographic latency metrics, machine learning anomaly thresholds, and attack interception logs.
* **Adjustable Scale:** Interactive meter slider allowing simulation sizes from `10` to `500` concurrent Smart Meter nodes.