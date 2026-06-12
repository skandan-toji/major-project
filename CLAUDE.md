# CLAUDE.md — Project Intelligence File
# Read this entire file before writing a single line of code.
# This file is the single source of truth for this project.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PROJECT IDENTITY

Title:
"A Hybrid Quantum-Resilient Security Framework for 
Man-in-the-Middle Attack Detection in Smart Grid Systems"

Type:
Major Project — Simulation-based web application.
NOT a research paper implementation.
NOT a real hardware deployment.
A working simulation that demonstrates the architecture.

Developer:
Skandan — undergraduate engineering student.
Windows machine. 8 GB RAM.
Python backend. React frontend.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT THIS PROJECT DOES

Simulates secure communication between Smart Meters and a 
Control Center in a smart grid environment.

Every simulated message goes through a complete cryptographic 
security pipeline involving:

1. Post-Quantum Device Authentication  (Dilithium5)
2. Post-Quantum Key Protection         (Kyber1024)
3. Symmetric Data Encryption           (AES-256-GCM)
4. Message Integrity Verification      (HMAC-SHA256)
5. Replay Attack Prevention            (Sequence Numbers + Timestamps)
6. Session Management                  (Session IDs + Nonces)
7. Anomaly Detection                   (Isolation Forest ML)

The system also simulates attacks in the background automatically
using a probability engine. Attacks are NEVER triggered manually
from the frontend. They happen randomly and the system detects them.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FOLDER STRUCTURE
MAJOR PROJECT/
├── CLAUDE.md                    ← this file
├── requirements.txt
│
├── backend/
│   ├── main.py                  ← entry point
│   │
│   ├── crypto/                  ← WEEK 1 — COMPLETE. DO NOT MODIFY.
│   │   ├── __init__.py
│   │   ├── dilithium_module.py
│   │   ├── kyber_module.py
│   │   ├── aes_module.py
│   │   ├── hmac_module.py
│   │   ├── session_crypto.py
│   │   ├── packet_builder.py
│   │   └── test_crypto.py       ← all 11 tests passing
│   │
│   ├── session/                 ← WEEK 2 — COMPLETE
│   │   ├── __init__.py
│   │   └── session_manager.py
│   │
│   ├── client/                  ← WEEK 2 — COMPLETE
│   │   ├── __init__.py
│   │   └── smart_meter.py
│   │
│   ├── server/                  ← WEEK 2 — COMPLETE
│   │   ├── __init__.py
│   │   └── control_center.py
│   │
│   ├── dataset/                 ← WEEK 2 — COMPLETE
│   │   ├── __init__.py
│   │   ├── traffic_logger.py
│   │   └── traffic_data.csv     ← auto-generated during simulation
│   │
│   ├── attacks/                 ← WEEK 3 — COMPLETE
│   │   ├── __init__.py
│   │   └── attack_injector.py
│   │
│   ├── ml/                      ← WEEK 4 — COMPLETE
│   │   ├── __init__.py
│   │   ├── train_model.py
│   │   ├── isolation_forest.py
│   │   └── saved_model/
│   │       └── isolation_forest.pkl
│   │
│   ├── api/                     ← WEEK 5 — COMPLETE
│   │   ├── __init__.py
│   │   ├── fastapi_server.py
│   │   └── websocket_manager.py
│   │
│   └── test_week2.py
│
└── frontend/                    ← WEEK 6 — IN PROGRESS
    └── src/
        ├── App.jsx
        ├── index.css
        ├── main.jsx
        ├── pages/
        │   ├── HomePage.jsx
        │   ├── LiveOperationsPage.jsx
        │   ├── AnalyticsPage.jsx
        │   ├── AttackIntelPage.jsx
        │   ├── PerformancePage.jsx
        │   └── SystemInfoPage.jsx
        ├── components/
        │   ├── Navbar.jsx
        │   ├── GlassCard.jsx
        │   ├── GlowButton.jsx
        │   ├── StatCard.jsx
        │   ├── NetworkMap.jsx
        │   ├── PacketFeed.jsx
        │   ├── AttackLog.jsx
        │   ├── SessionList.jsx
        │   ├── CryptoLatency.jsx
        │   ├── ConfusionMatrix.jsx
        │   ├── LiveCharts.jsx
        │   ├── PipelineDiagram.jsx
        │   └── BackgroundEffect.jsx
        ├── context/
        │   └── SimulationContext.jsx
        ├── websocket/
        │   └── useWebSocket.js
        └── utils/
            ├── formatters.js
            └── api.js

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SECURITY PARAMETERS — NEVER CHANGE THESE

| Parameter              | Value                        |
|------------------------|------------------------------|
| NIST Security Level    | Level 5 (AES-256 equivalent) |
| Dilithium Variant      | Dilithium5                   |
| Kyber Variant          | Kyber1024                    |
| AES Mode               | AES-256-GCM                  |
| HMAC Algorithm         | HMAC-SHA256                  |
| Session Lifetime       | 900 seconds (15 minutes)     |
| Timestamp Window       | 30 seconds                   |
| Session ID Size        | 16 bytes (os.urandom)        |
| Nonce Size             | 12 bytes (os.urandom)        |
| AES Key Size           | 32 bytes (256-bit)           |
| Sequence Number Type   | 32-bit unsigned integer      |
| ML Model               | Isolation Forest             |
| ML Contamination       | 0.05                         |
| ML Estimators          | 200                          |
| Anomaly Threshold      | -0.1                         |

### Key Sizes (Dilithium5)
- Public Key  : 2,592 bytes
- Private Key : 4,864 bytes
- Signature   : 4,595 bytes

### Key Sizes (Kyber1024)
- Public Key  : 1,568 bytes
- Private Key : 3,168 bytes
- Ciphertext  : 1,568 bytes
- Shared Secret: 32 bytes

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## EXACT PACKET STRUCTURE

### Authentication Packet (Smart Meter → Control Center)
```json
{
  "device_id"    : "SM_001",
  "auth_message" : {
      "device_id" : "SM_001",
      "timestamp" : 1712903400.0,
      "intent"    : "session_request"
  },
  "signature"    : "hex string of Dilithium5 signature"
}
```

### Session Response (Control Center → Smart Meter)
```json
{
  "success"           : true,
  "session_id"        : "hex string — 16 bytes",
  "nonce"             : "hex string — 12 bytes",
  "encrypted_aes_key" : "hex string — Kyber1024 ciphertext"
}
```

### Data Packet (Smart Meter → Control Center, every message)
```json
{
  "device_id"       : "SM_001",
  "session_id"      : "hex string",
  "nonce"           : "hex string",
  "sequence_number" : 1,
  "timestamp"       : 1712903401.0,
  "cipher_data"     : "hex string — AES-GCM ciphertext",
  "aes_auth_tag"    : "hex string — 16 bytes GCM tag",
  "hmac_tag"        : "hex string — 32 bytes HMAC-SHA256"
}
```

### Verification Result (Control Center → Smart Meter)
```json
{
  "valid"   : true,
  "reason"  : "accepted",
  "payload" : { "device_id": "SM_001", "power_usage": 120.5, "voltage": 230.1 }
}
```

### Rejection Result
```json
{
  "valid"  : false,
  "reason" : "hmac_failed | replay_detected | stale_timestamp | 
              session_not_found_or_expired | blacklisted_session |
              decryption_failed | invalid_signature | unregistered_device"
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## VERIFICATION ORDER — SACRED. NEVER CHANGE.

    Check session_id not blacklisted
    Retrieve session — confirm active and not expired
    Convert hex fields to bytes
    VERIFY HMAC          → fail = hmac_failed
    CHECK sequence number → fail = replay_detected
    CHECK timestamp       → fail = stale_timestamp
    DECRYPT payload       → fail = decryption_failed
    Update session sequence number
    Log traffic features
    Return accepted

HMAC is always verified first. Always. No exceptions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## HMAC COMPUTATION — EXACT CONCATENATION

```python
session_id                              # bytes
+ nonce                                 # bytes
+ sequence_number.to_bytes(4, 'big')    # 4 bytes big-endian
+ struct.pack('>d', timestamp)          # 8 bytes big-endian double
+ cipher_data                           # bytes
+ aes_auth_tag                          # bytes
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## SESSION LIFECYCLE

    REGISTRATION (one time before simulation):
        Smart Meter generates Dilithium5 keypair
        Smart Meter generates Kyber1024 keypair
        Control Center stores both public keys in device_registry

    SESSION START (every 15 minutes):
        Smart Meter sends auth packet with Dilithium signature
        Control Center verifies signature
        Control Center generates AES key + nonce + session_id
        Control Center encrypts AES key with meter's Kyber public key
        Smart Meter decrypts AES key with its Kyber private key
        Both sides store session — sequence number starts at 0

    ACTIVE SESSION (every message):
        Sequence number increments by 1 before each send
        AES-GCM encrypts payload
        HMAC seals the packet
        Control Center verifies HMAC → seq → timestamp → decrypts

    SESSION EXPIRY:
        Smart Meter detects expiry from stored expiry_timestamp
        Smart Meter re-authenticates automatically
        Control Center moves session to expired_sessions blacklist
        AES key deleted from memory on both sides
        Old session_id permanently blacklisted

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ATTACK INJECTION — BACKGROUND ONLY

Attacks are NEVER triggered from the frontend.
Attacks are injected automatically by the backend probability engine.

```python
ATTACK_PROBABILITY     = 0.08   # 8% of packets are attacks
SESSION_ATTACK_PROB    = 0.15   # 15% of sessions are attack sessions

ATTACK_TYPE_DISTRIBUTION:
  replay  : 50%
  mitm    : 30%
  flood   : 20%
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## TRAFFIC DATASET — ML TRAINING DATA

### CSV Columns (exact order)
meter_id, session_id, sequence_number, packet_rate,
inter_arrival_time, payload_size, sequence_delta,
timestamp_delta, session_duration, hmac_valid,
seq_check_valid, timestamp_valid, label

### Labels
- label = 0 → normal traffic
- label = 1 → attack traffic

### Target Sizes
- Normal rows  : 10,000 (label=0)
- Attack rows  :  2,000 (label=1)
- Total        : 12,000 rows

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CURRENT BUILD STATUS

| Week | Component              | Status                    |
|------|------------------------|---------------------------|
| 1    | Crypto Modules         | COMPLETE — TESTED         |
| 2    | Session Manager        | COMPLETE — TESTED         |
| 2    | Smart Meter Simulator  | COMPLETE — TESTED         |
| 2    | Control Center         | COMPLETE — TESTED         |
| 2    | Traffic Logger         | COMPLETE — TESTED         |
| 3    | Attack Injector        | COMPLETE — TESTED         |
| 4    | ML Module              | COMPLETE — TESTED         |
| 4    | Dataset Generation     | COMPLETE                  |
| 4    | Backend Verification   | COMPLETE — PASS           |
| 5    | FastAPI Server         | COMPLETE — TESTED         |
| 5    | WebSocket Manager      | COMPLETE — TESTED         |
| 6    | React Dashboard        | IN PROGRESS               |
| 6    | Performance Metrics    | NOT STARTED               |

## FINAL VERIFIED BACKEND METRICS (100 meters, 5 minutes)

| Metric                    | Value        |
|---------------------------|--------------|
| Detection Accuracy        | 98.18%       |
| False Positive Rate       | 0.00%        |
| Precision                 | 100.00%      |
| Recall                    | 79.78%       |
| ML Accuracy               | 98.04%       |
| ML False Positives        | 0            |
| Throughput                | 51.47 pkt/s  |
| Meters with 0% FPR        | 100 / 100    |
| Dilithium5 Sign           | 0.73ms avg   |
| Dilithium5 Verify         | 0.23ms avg   |
| Kyber1024 Encrypt         | 0.17ms avg   |
| Kyber1024 Decrypt         | 0.07ms avg   |
| AES-256-GCM Encrypt       | 1.15ms avg   |
| AES-256-GCM Decrypt       | 0.08ms avg   |
| Crypto P99 Latency        | sub-10ms     |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## FRONTEND DESIGN SYSTEM — WOPE-STYLE
## THIS IS THE LOCKED VISUAL REFERENCE. DO NOT DEVIATE.
## Match wope.com pixel-for-pixel in structure and feel.
## Only the text/content changes. Everything else is identical.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### TYPOGRAPHY

Primary font  : 'Sora' (Google Fonts) — used for all headings
Body font     : 'Inter' (Google Fonts) — used for body text only
Mono font     : 'JetBrains Mono'       — used for metric numbers

Import in index.html:
  https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700;800&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;600&display=swap

Heading sizes (match Wope exactly):
  Hero h1        : clamp(42px, 7vw, 72px), weight 800, line-height 1.05
  Section h2     : clamp(28px, 4vw, 42px), weight 700, line-height 1.15
  Card heading   : 18px, weight 600
  Body text      : 15px–16px, weight 400, line-height 1.65
  Badge/label    : 11px–12px, weight 600, letter-spacing 0.08em, uppercase

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### COLOR PALETTE (exact values, define as CSS variables)

```css
:root {
  /* Backgrounds */
  --bg-root        : #08070f;   /* deepest background — almost black-purple */
  --bg-surface     : #0e0c1a;   /* card/panel surfaces */
  --bg-elevated    : #13101f;   /* elevated elements */

  /* Purple brand (dominant accent — matches Wope purple) */
  --purple-core    : #7c3aed;   /* main CTA purple */
  --purple-bright  : #8b5cf6;   /* hover/active states */
  --purple-glow    : #a78bfa;   /* text accents, gradient ends */
  --purple-dim     : rgba(124,58,237,0.15); /* subtle bg tints */

  /* Blue accent (secondary) */
  --blue-core      : #2563eb;
  --blue-bright    : #3b82f6;
  --blue-glow      : #60a5fa;

  /* Status colors */
  --green          : #10b981;
  --green-dim      : rgba(16,185,129,0.15);
  --red            : #ef4444;
  --red-dim        : rgba(239,68,68,0.15);
  --yellow         : #f59e0b;
  --yellow-dim     : rgba(245,158,11,0.15);
  --cyan           : #06b6d4;

  /* Text */
  --text-primary   : #f8f8ff;
  --text-secondary : #a0a0b8;
  --text-muted     : #5a5a78;

  /* Borders */
  --border-subtle  : rgba(255,255,255,0.06);
  --border-purple  : rgba(124,58,237,0.25);
  --border-glow    : rgba(139,92,246,0.4);
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### BACKGROUND — THE MOST CRITICAL VISUAL ELEMENT

The background must look EXACTLY like Wope — deep dark purple-black
with soft glowing orbs bleeding through. No gradients on content.
All glow lives in the background layer.

```css
body {
  background-color: var(--bg-root);
  position: relative;
  overflow-x: hidden;
}

/* Orb 1 — upper left, large purple bloom */
.bg-orb-1 {
  position: fixed;
  top: -200px;
  left: -200px;
  width: 700px;
  height: 700px;
  background: radial-gradient(
    circle at center,
    rgba(124,58,237,0.18) 0%,
    rgba(124,58,237,0.08) 35%,
    transparent 70%
  );
  pointer-events: none;
  animation: orb-drift-1 22s ease-in-out infinite;
  z-index: 0;
}

/* Orb 2 — lower right, blue-purple bloom */
.bg-orb-2 {
  position: fixed;
  bottom: -150px;
  right: -150px;
  width: 600px;
  height: 600px;
  background: radial-gradient(
    circle at center,
    rgba(37,99,235,0.14) 0%,
    rgba(124,58,237,0.07) 40%,
    transparent 70%
  );
  pointer-events: none;
  animation: orb-drift-2 28s ease-in-out infinite;
  z-index: 0;
}

/* Orb 3 — center, very faint, creates depth */
.bg-orb-3 {
  position: fixed;
  top: 40%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 800px;
  height: 400px;
  background: radial-gradient(
    ellipse at center,
    rgba(124,58,237,0.06) 0%,
    transparent 65%
  );
  pointer-events: none;
  z-index: 0;
}

/* Subtle grid overlay — matches Wope grid texture */
.bg-grid {
  position: fixed;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
  z-index: 0;
}

@keyframes orb-drift-1 {
  0%,100% { transform: translate(0,0) scale(1); }
  33%      { transform: translate(60px,-40px) scale(1.05); }
  66%      { transform: translate(-30px,50px) scale(0.97); }
}

@keyframes orb-drift-2 {
  0%,100% { transform: translate(0,0) scale(1); }
  40%      { transform: translate(-50px,30px) scale(1.08); }
  70%      { transform: translate(40px,-60px) scale(0.95); }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### NAVBAR — EXACT WOPE STRUCTURE

Fixed top, full width, height 60px.
Background: rgba(8,7,15,0.8) with backdrop-filter: blur(20px)
Border-bottom: 1px solid var(--border-subtle)
z-index: 1000

Layout (flex, space-between, padding 0 40px):

  LEFT:
    Logo — small shield SVG icon (14px) + text "SecureNet"
    Font: Sora 600, 15px
    Color: white
    No background, no border

  CENTER:
    Nav links (hidden on mobile, flex on desktop):
      [Live Operations] [Analytics] [Attack Intel] [Performance] [System Info]
      Font: Inter 400, 13px
      Color: var(--text-secondary) default
      Hover: var(--text-primary), transition 0.2s
      Active: var(--purple-glow) with 1px bottom border purple

  RIGHT:
    Live status pill:
      If running: green pulsing dot + "LIVE" — green text, 11px Sora 600
      If stopped: gray dot + "OFFLINE"
    Separator line
    Clock — 12px Inter, var(--text-muted)

Navbar must be transparent-to-blur — same as Wope's frosted glass nav.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### HERO SECTION — EXACT WOPE LAYOUT

The hero is centered, full viewport height (100vh minimum).
No sidebars. No split layouts. Pure center-aligned content.
This MUST match Wope's hero proportions exactly.

```
┌─────────────────────────────────────────────────────┐
│                     [NAVBAR]                         │
│                                                      │
│                                                      │
│           ┌──────────────────────────┐               │
│           │  NIST Level 5 · PQC  [pill] │            │
│           └──────────────────────────┘               │
│                                                      │
│         Quantum-Resilient Security                   │  ← h1 line 1
│              Framework                               │  ← h1 line 2
│                                                      │
│    Real-time MITM detection for smart grid systems   │  ← subtitle
│                                                      │
│           [ START SIMULATION ]  ← glow button        │
│                                                      │
│    ┌──────────────────────────────────────────┐      │
│    │  [preview dashboard mockup card]          │      │  ← product screenshot
│    │  semi-transparent, purple border glow     │      │
│    └──────────────────────────────────────────┘      │
│                                                      │
└─────────────────────────────────────────────────────┘
```

Hero specs:
  Badge pill above h1:
    "NIST Level 5  ·  Post-Quantum Cryptography"
    Background: rgba(124,58,237,0.12)
    Border: 1px solid rgba(124,58,237,0.3)
    Border-radius: 100px
    Padding: 6px 16px
    Font: Inter 500, 11px, letter-spacing 0.06em, uppercase
    Color: var(--purple-glow)
    Shimmer animation on border (see below)

  h1 text:
    Line 1: "Quantum-Resilient Security" — white, Sora 800
    Line 2: "Framework" — gradient text (purple to blue)
    clamp(44px, 6vw, 68px), line-height 1.05
    Text-align: center
    Max-width: 700px, margin: 0 auto

  Subtitle:
    "Real-time Man-in-the-Middle attack detection
     for smart grid infrastructure"
    Inter 400, 16px, var(--text-secondary), max-width 480px
    Text-align: center, margin: 0 auto

  CTA button:
    "Start Simulation" — see BUTTON SYSTEM below
    Centered below subtitle, margin-top 36px

  Meter count slider (below button):
    Label: "Smart Meters:" + gradient number
    Slider styled dark purple — range 10 to 500
    Current value shown large in gradient

  Product preview card (CRITICAL — matches Wope's dashboard preview):
    A glassmorphism card showing a mini dashboard preview
    Width: min(700px, 90vw)
    Background: rgba(14,12,26,0.9)
    Border: 1px solid rgba(124,58,237,0.3)
    Border-radius: 16px
    Box-shadow:
      0 0 0 1px rgba(124,58,237,0.1),
      0 40px 80px rgba(0,0,0,0.6),
      0 0 120px rgba(124,58,237,0.08) inset
    Padding: 24px
    Inside: mini stat grid + tiny packet feed table mockup
    This is the visual anchor — make it look like a real product screenshot

  Background behind hero:
    The 3 orbs are most visible here
    Additionally: a soft radial glow directly behind the product card
      background: radial-gradient(ellipse 80% 50% at 50% 120%,
                  rgba(124,58,237,0.12), transparent)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SCROLLABLE HOMEPAGE — SECTION STRUCTURE

The homepage scrolls like wope.com with distinct sections.
Each section fades in on scroll (Framer Motion: fadeInUp).

SECTION ORDER:

  1. Hero            (100vh, described above)
  2. Trust badges    (logo strip — show crypto standard badges)
  3. Features grid   (3 feature cards, alternating layout)
  4. Architecture    (security pipeline diagram)
  5. Metrics preview (6 stat cards)
  6. FAQ accordion   (5 questions about the system)
  7. CTA bottom      (full-width, "Defend Your Grid. Starting Now.")
  8. Footer

─────────────────────────────────────────
SECTION 2 — TRUST BADGE STRIP (matches Wope's partner logos strip)

  Height: 80px, full width
  Background: var(--bg-surface)
  Border-top/bottom: 1px solid var(--border-subtle)
  
  Content: 5 security standard badges in a row, centered
    NIST FIPS 197  |  NIST PQC  |  RFC 2104  |  CRYSTALS  |  ISO 27001
  
  Font: Inter 500, 13px, var(--text-muted)
  Separated by subtle vertical lines
  Gentle horizontal marquee animation (scrolling left, infinite)

─────────────────────────────────────────
SECTION 3 — FEATURES (matches Wope's feature sections)

  3 features, each with alternating layout:
    Odd:  text left, card visual right
    Even: card visual left, text right
  
  Feature 1: "Detailed Cryptographic Analysis"
    Text: "Every packet authenticated with Dilithium5 signatures
           and encrypted with Kyber1024 key exchange — quantum resistant
           at NIST Level 5."
    Visual: Glass card showing crypto operation breakdown
            (mini bar chart of operation latencies)
  
  Feature 2: "Real-Time Attack Detection"  
    Text: "Isolation Forest ML model scores every packet.
           Replay attacks, MITM tampering, and flood attacks
           detected automatically in the background."
    Visual: Glass card with mini attack log table
  
  Feature 3: "Live Session Management"
    Text: "Full session lifecycle — authentication, key exchange,
           expiry, and re-authentication — all automated and
           monitored in real time."
    Visual: Glass card with session timeline visualization

  Each feature section:
    Padding: 100px 0
    Max-width: 1100px, centered
    Feature card (visual side): full glass card treatment
    Text side: h2 (gradient) + body + small metric badge

─────────────────────────────────────────
SECTION 4 — ARCHITECTURE PIPELINE

  Heading: "7-Layer Defense Pipeline" (centered, gradient)
  Subheading: "Every packet survives all 7 checks or gets dropped"
  
  Horizontal scrolling pipeline (7 nodes):
    [Dilithium5] → [Kyber1024] → [AES-256-GCM] → [HMAC-SHA256]
        → [Seq+Timestamp] → [Session Mgmt] → [Isolation Forest]
  
  Node style:
    Glass card, 140px × 180px
    Icon top (SVG, 28px, purple)
    Name (Sora 600, 13px, white)
    One-line description (Inter 400, 11px, muted)
    Bottom badge: key metric (e.g. "0.73ms avg")
  
  Connecting arrows: thin purple lines with animated moving dot
  Animation: dot travels left-to-right, loops, 3s per segment

─────────────────────────────────────────
SECTION 5 — METRICS PREVIEW (matches Wope's feature numbers)

  Heading: "Verified Performance Metrics"
  Subheading: "Measured results from 100-meter simulation"
  
  6-card grid (3×2 desktop, 2×3 mobile):
    Detection Accuracy : 98.18%  (green)
    False Positive Rate: 0.00%   (green)
    Precision          : 100%    (green)
    ML Accuracy        : 98.04%  (blue)
    Throughput         : 51.47 pkt/s (cyan)
    Crypto P99 Latency : <10ms   (purple)
  
  Card style:
    Glass card
    Large number: clamp(28px,4vw,40px), JetBrains Mono 600, gradient
    Label below: Inter 400, 13px, var(--text-secondary)
    Subtle bottom border glow matching metric color
  
  Numbers count up from 0 when scrolled into view (useCountUp hook)

─────────────────────────────────────────
SECTION 6 — FAQ (matches Wope's FAQ section exactly)

  Heading: "Frequently Asked Questions" (centered)
  Link: "Contact us" below heading (purple, underlined)
  
  5 accordion items (expand/collapse on click):
  
    Q1: "What is this system?"
    A: Explain the hybrid PQC framework in 2-3 sentences
    
    Q2: "Why post-quantum cryptography?"
    A: Quantum computers break RSA/ECC. Dilithium5 and Kyber1024
       are NIST-standardized algorithms resistant to quantum attacks.
    
    Q3: "How does attack detection work?"
    A: Isolation Forest ML model trained on 12,000 traffic samples.
       Scores every packet. Crypto layers act as primary defense.
    
    Q4: "What attacks does this detect?"
    A: Replay attacks (sequence+timestamp), MITM tampering (HMAC),
       flood attacks (ML), impersonation (Dilithium signature).
    
    Q5: "What scale does this simulate?"
    A: 10 to 500 smart meters simultaneously on a single machine.
       51.47 packets/second throughput with sub-10ms crypto latency.
  
  Accordion style:
    Full width, max-width 700px, centered
    Each item: border-bottom var(--border-subtle)
    Question: Inter 500, 15px, white
    Answer: Inter 400, 14px, var(--text-secondary)
    +/− icon right side, purple color
    Expand: smooth height transition (max-height trick or Framer Motion)

─────────────────────────────────────────
SECTION 7 — BOTTOM CTA (matches Wope's "Outrank Everyone" section)

  Full width, padding 120px 40px
  Background: subtle purple gradient overlay on dark
    background: linear-gradient(180deg,
      transparent 0%,
      rgba(124,58,237,0.08) 50%,
      transparent 100%)
  
  Large centered icon (shield with lock, 80px, purple glow)
  
  Heading (3 lines, centered):
    Line 1: "Defend Your Grid."    — white, Sora 800
    Line 2: "Starting Now."        — gradient text, Sora 800
    clamp(36px, 5vw, 56px)
  
  Subtext:
    "Quantum-resilient encryption. Real-time threat detection.
     Zero false positives."
    Inter 400, 15px, var(--text-secondary)
  
  Two buttons:
    Primary: "Start Simulation" (glow button)
    Secondary: "View Architecture" (ghost button, purple border)
  
  Below buttons:
    Three small trust badges in a row:
    "No real hardware needed"  |  "NIST Level 5"  |  "Open simulation"

─────────────────────────────────────────
SECTION 8 — FOOTER (matches Wope's footer)

  Background: var(--bg-surface)
  Border-top: 1px solid var(--border-subtle)
  Padding: 60px 40px 40px
  
  Top row (4 columns):
    Col 1: Logo + tagline
      "SecureNet" logo
      "Experience the next generation of smart grid security."
      Inter 400, 13px, var(--text-muted)
    
    Col 2: Platform
      Links: Live Operations, Analytics, Attack Intel,
             Performance, System Info
    
    Col 3: Security Stack
      Dilithium5, Kyber1024, AES-256-GCM, HMAC-SHA256,
      Isolation Forest
    
    Col 4: Project Info
      NIST Level 5
      Major Project 2026
      100% FPR = 0.00%
  
  Bottom bar:
    "©2026 SecureNet. All rights reserved." left
    "98.18% Detection Accuracy" right (subtle, muted)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### BUTTON SYSTEM

Primary glow button (.btn-primary):
```css
.btn-primary {
  background    : linear-gradient(135deg, #7c3aed, #2563eb);
  color         : white;
  border        : none;
  border-radius : 10px;
  padding       : 13px 28px;
  font-family   : 'Sora', sans-serif;
  font-size     : 14px;
  font-weight   : 600;
  cursor        : pointer;
  box-shadow    : 0 0 30px rgba(124,58,237,0.35),
                  0 4px 15px rgba(0,0,0,0.3);
  transition    : all 0.25s ease;
  letter-spacing: 0.02em;
}
.btn-primary:hover {
  transform   : translateY(-2px);
  box-shadow  : 0 0 50px rgba(124,58,237,0.55),
                0 8px 25px rgba(0,0,0,0.4);
}
.btn-primary:active { transform: translateY(0); }
```

Ghost button (.btn-ghost):
```css
.btn-ghost {
  background    : transparent;
  color         : var(--purple-glow);
  border        : 1px solid rgba(124,58,237,0.4);
  border-radius : 10px;
  padding       : 12px 28px;
  font-family   : 'Sora', sans-serif;
  font-size     : 14px;
  font-weight   : 600;
  cursor        : pointer;
  transition    : all 0.25s ease;
}
.btn-ghost:hover {
  background    : rgba(124,58,237,0.1);
  border-color  : rgba(124,58,237,0.6);
  transform     : translateY(-2px);
}
```

STOP button (active simulation state):
  Same as .btn-primary but:
  background: linear-gradient(135deg, #ef4444, #b91c1c)
  box-shadow: 0 0 30px rgba(239,68,68,0.35)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### GLASS CARD SYSTEM

```css
.glass-card {
  background    : rgba(255,255,255,0.025);
  border        : 1px solid var(--border-subtle);
  border-radius : 14px;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  box-shadow    : 0 0 0 1px rgba(255,255,255,0.03) inset,
                  0 20px 50px rgba(0,0,0,0.35);
  transition    : border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
  border-color  : var(--border-purple);
  box-shadow    : 0 0 0 1px rgba(124,58,237,0.1) inset,
                  0 20px 50px rgba(0,0,0,0.4),
                  0 0 40px rgba(124,58,237,0.06);
}

/* Variant: purple tinted card */
.glass-card-purple {
  background  : rgba(124,58,237,0.05);
  border      : 1px solid rgba(124,58,237,0.2);
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### GRADIENT TEXT

```css
.text-gradient {
  background              : linear-gradient(135deg, #a78bfa 0%, #60a5fa 100%);
  -webkit-background-clip : text;
  -webkit-text-fill-color : transparent;
  background-clip         : text;
}

/* Warm variant (for CTAs) */
.text-gradient-warm {
  background              : linear-gradient(135deg, #c084fc 0%, #818cf8 50%, #60a5fa 100%);
  -webkit-background-clip : text;
  -webkit-text-fill-color : transparent;
  background-clip         : text;
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### BADGE / PILL COMPONENTS

Status badge (live indicator):
```css
.badge-live {
  display       : inline-flex;
  align-items   : center;
  gap           : 6px;
  padding       : 4px 10px;
  border-radius : 100px;
  font-size     : 11px;
  font-weight   : 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.badge-live.running {
  background  : rgba(16,185,129,0.12);
  border      : 1px solid rgba(16,185,129,0.3);
  color       : #10b981;
}
.badge-live .dot {
  width         : 6px;
  height        : 6px;
  border-radius : 50%;
  background    : currentColor;
  animation     : live-pulse 2s ease-in-out infinite;
}
@keyframes live-pulse {
  0%,100% { opacity: 1; transform: scale(1); }
  50%     { opacity: 0.5; transform: scale(0.8); }
}
```

Category badge (attack type, etc.):
```css
.badge-purple { background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.3); color: #a78bfa; }
.badge-blue   { background: rgba(37,99,235,0.15);  border: 1px solid rgba(37,99,235,0.3);  color: #60a5fa; }
.badge-red    { background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.3);  color: #f87171; }
.badge-green  { background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.3); color: #34d399; }
.badge-yellow { background: rgba(245,158,11,0.12); border: 1px solid rgba(245,158,11,0.3); color: #fbbf24; }
/* All badges: border-radius 6px, padding 3px 8px, font-size 11px, font-weight 600 */
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SHIMMER ANIMATION (for badge borders — Wope effect)

```css
@keyframes shimmer-border {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}

.shimmer-border {
  background    : linear-gradient(
    90deg,
    rgba(124,58,237,0.3) 0%,
    rgba(167,139,250,0.8) 40%,
    rgba(124,58,237,0.3) 80%
  );
  background-size: 200% auto;
  animation     : shimmer-border 3s linear infinite;
  /* Apply as border using padding trick or outline */
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### FRAMER MOTION ANIMATION PRESETS

Use these consistently across all pages:

```js
// Page container — stagger children
const pageVariants = {
  hidden : { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.08 } }
}

// Individual element — fade up
const itemVariants = {
  hidden : { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: [0.22,1,0.36,1] } }
}

// Section on scroll
const scrollVariants = {
  hidden : { opacity: 0, y: 40 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22,1,0.36,1] } }
}

// Card hover
const cardHover = {
  whileHover : { y: -4, transition: { duration: 0.2 } }
}

// Number counter
// Use useCountUp(targetValue, duration=1500) custom hook
// Triggers when element enters viewport (useInView)

// Attack flash
const attackFlash = {
  animate: { 
    backgroundColor: ['rgba(239,68,68,0.0)', 'rgba(239,68,68,0.12)', 'rgba(239,68,68,0.0)'],
    transition: { duration: 0.8 }
  }
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### RECHARTS THEME (for all charts)

```js
const chartTheme = {
  backgroundColor : 'transparent',
  gridColor       : 'rgba(255,255,255,0.04)',
  axisColor       : 'rgba(255,255,255,0.15)',
  tickColor       : '#5a5a78',
  fontSize        : 11,
  fontFamily      : 'Inter, sans-serif',
  tooltipBg       : 'rgba(14,12,26,0.95)',
  tooltipBorder   : 'rgba(124,58,237,0.3)',
  tooltipRadius   : 10,
  
  // Line colors
  lineColors: {
    primary   : '#8b5cf6',
    secondary : '#3b82f6',
    success   : '#10b981',
    danger    : '#ef4444',
    warning   : '#f59e0b',
    cyan      : '#06b6d4',
  }
}
```

Custom tooltip component (apply to ALL charts):
```jsx
const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background    : 'rgba(14,12,26,0.95)',
      border        : '1px solid rgba(124,58,237,0.3)',
      borderRadius  : '10px',
      padding       : '10px 14px',
      backdropFilter: 'blur(10px)',
      fontSize      : '12px',
      fontFamily    : 'Inter, sans-serif',
    }}>
      <p style={{ color: '#5a5a78', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color }}>{p.name}: {p.value}</p>
      ))}
    </div>
  )
}
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### NETWORK MAP SPECS (NetworkMap.jsx)

SVG-based. No canvas.

Layout:
  Center node: hexagon, 56px, purple fill + glow
    Label: "Control Center", 11px, white, centered below
    Pulsing glow animation always active

  Meter nodes: circles, 20px diameter
    Arranged in concentric rings around center
    Ring 1 (inner): up to 10 meters, radius 140px
    Ring 2 (middle): up to 20 meters, radius 220px
    Ring 3 (outer): up to 30 meters, radius 300px
    If > 50 meters: show 40 representative nodes + "... +N more" label

  Connection lines:
    Thin path from each meter to center: stroke-width 1, opacity 0.3
    Color: matches meter status (green/yellow/red/gray)
    Animated packet dot traveling along path:
      Circle r=3, same color as line
      animateMotion, dur="2s", repeatCount="indefinite"
      Attack packets: red dot, dur="0.5s" (faster = urgent)

  Color states:
    Healthy  : #10b981 (green)
    Suspicious: #f59e0b (yellow)  — ML flagged
    Attack   : #ef4444 (red) + ripple animation
    Inactive : #2a2a40 (dark)

  Ripple on attack:
    Expanding circle from meter node
    stroke: #ef4444, fill: none
    Animate r from 20px to 50px, opacity 1 to 0, 1s, once per attack

  Node labels: show meter ID on hover (tooltip, not permanent)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### LIVE OPERATIONS PAGE LAYOUT

3-column grid, full height, padding 80px top (navbar offset)

LEFT (22%):
  Active Sessions panel (glass card, full height)
  System Health panel (glass card below)

CENTER (52%):
  Network Map (glass card, tall, 60% of height)
  Security Verification Strip (glass card, below map)

RIGHT (26%):
  Packet Feed (glass card, full height, scrollable)

Bottom: full-width stats bar with 5 live counters

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### SCROLLBAR STYLING

```css
::-webkit-scrollbar       { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { 
  background    : rgba(124,58,237,0.3); 
  border-radius : 2px; 
}
::-webkit-scrollbar-thumb:hover { background: rgba(124,58,237,0.5); }
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### REACT DEPENDENCIES (install exactly these)

```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install framer-motion recharts react-router-dom axios
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

Tailwind: used ONLY for layout utilities (flex, grid, spacing, etc.)
ALL visual styling (colors, shadows, borders, animations) goes in
index.css using CSS variables — NOT Tailwind color utilities.
This ensures exact color control matching the design system above.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### STRICT FRONTEND RULES — NEVER VIOLATE

1.  Font stack: Sora for headings, Inter for body, JetBrains Mono
    for numbers. No other fonts.

2.  Background: ALWAYS the 3-orb system + grid overlay.
    Never solid colors. Never different gradients.

3.  Cards: ALWAYS .glass-card class. Never inline glass styles.

4.  Buttons: ALWAYS .btn-primary or .btn-ghost. Never ad-hoc button styles.

5.  Colors: ALWAYS use CSS variables. Never hardcode hex in JSX.

6.  Charts: ALWAYS dark theme with custom tooltip. Never default Recharts theme.

7.  Animations: Framer Motion for component animations.
    CSS keyframes ONLY for background effects and microloops.

8.  No mock data anywhere. "--" or "Waiting..." as placeholders.

9.  NetworkMap must support 10–500 meters.

10. Slider: min=10, max=500, step=10, default=100.

11. Homepage MUST be scrollable exactly like wope.com.
    Each section transitions cleanly on scroll.
    Navbar stays fixed.

12. No attack controls visible anywhere on frontend.

13. All text content adapts the Wope layout exactly —
    just with smart grid security content instead of SEO content.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PYTHON LIBRARIES USED

pqcrypto          → Dilithium5 and Kyber1024
pycryptodome      → AES-256-GCM
fastapi           → backend API server
uvicorn           → ASGI server for FastAPI
websockets        → WebSocket support
scikit-learn      → Isolation Forest
pandas            → dataset handling
numpy             → numerical operations
sqlalchemy        → database ORM
joblib            → save/load ML model
asyncio           → concurrency (built-in)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## PYTHON CODING RULES — NEVER VIOLATE

1.  NEVER use Python random module for cryptographic operations.
    Always use os.urandom() or secrets.token_bytes()

2.  NEVER rewrite anything inside backend/crypto/
    Those modules are complete and tested. Only import from them.

3.  NEVER change the HMAC concatenation order.

4.  NEVER change the verification order. HMAC always first.

5.  NEVER expose attack injection controls on frontend.

6.  NEVER use == for HMAC comparison.
    Always use hmac.compare_digest()

7.  NEVER raise unhandled exceptions from crypto/verification.
    Wrap in try/except, return meaningful error dict.

8.  NEVER hardcode any cryptographic key anywhere.

9.  ALWAYS use asyncio for concurrency. Never threading.

10. ALWAYS convert bytes to hex for JSON/CSV serialization.
    ALWAYS convert hex back to bytes when deserializing.

11. ALWAYS verify HMAC before decryption.

12. Session IDs stored as bytes internally.
    Converted to hex strings only for JSON/CSV.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## HOW TO RUN

Terminal 1 — Backend:
    cd "MAJOR PROJECT/backend"
    python api/fastapi_server.py

Terminal 2 — Frontend:
    cd "MAJOR PROJECT/frontend"
    npm run dev

Open browser: http://localhost:5173

Verify:
    WebSocket connects — LIVE indicator turns green
    Homepage scrolls like wope.com
    Start simulation with 100 meters
    Watch live packet feed update
    Network map nodes animate
    Stop simulation
    Performance page populates with real results

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## WHAT TO DO WHEN ASKED TO BUILD SOMETHING

1. Read this entire CLAUDE.md file first
2. Check Current Build Status table
3. Never modify completed weeks
4. Always import from crypto/ — never reimplement
5. Follow exact packet structure documented above
6. Follow exact verification order documented above
7. Use exact security parameters above
8. Follow frontend design system EXACTLY as documented
9. Match wope.com layout — content changes, structure stays identical