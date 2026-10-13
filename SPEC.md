# Project Vigil+: Master System & Architecture Specification

**System Name:** Vigil+  
**Target Competition:** [Build, Ship, Shape: Amazon Developer Hackathon 2026](https://amazonappdev2026.devpost.com/)  
**Primary Track:** Alexa+ (Agent Skills / Self-Hosted MCP Server over Streamable HTTP)  
**Layered Mini-Challenges:** AWS Builder Challenge & Open Source Challenge  
**Target Prize Pool:** $25,000 (1st Place Alexa+) + $5,000 (AWS Builder) + $5,000 (Open Source) = **$35,000 Cash + $20,000 AWS Credits**  
**Engineering Methodology:** Creative System Architecture & Specification via Antigravity; Autonomous Implementation via Kiro Pro (Claude Models)  
**License:** MIT License (Open Source)  
**Status:** Architecture Frozen & Ready for Implementation  

---

## 1. Executive Summary & Core Thesis

Current smart home security suffers from a **fundamental decoupling**:
1. **The Sensor Sentry (Ring)** detects movement and records video, but acts purely passively—dumping push notifications onto sleeping homeowners whose phones are set to "Do Not Disturb".
2. **The Ambient Brain (Alexa+)** controls lighting and media, but lacks real-time perimeter threat awareness.
3. **The Personal Wearable (Bee)** tracks real-time biometrics and circadian state, but lives in a silo disconnected from home automation.
4. **The Living Room Screen (Fire TV)** sits dark and idle while security events unfold outside the door.

**Vigil+** bridges this gap into an **autonomous multi-device perimeter defense and deterrence mesh**:
* **Ring** acts as the high-resolution sensory perimeter (Motion, Vision, Audio) with client-side frame processing to detect physical lens tampering ($\Phi_V$).
* **Bee** grounds the system in human context (detecting whether the resident is awake or in deep sleep via conversation recency `bee now` and accelerometer stillness).
* **Alexa+** acts as the central Incident Commander via a self-hosted **Model Context Protocol (MCP)** server, coordinating **System 1 local edge reflexes (<50ms)** with **System 2 cognitive multimodal reasoning (Amazon Bedrock)**.
* **Fire TV & Echo Boot-Bridge** deploy active psychological deterrence (the "Home Alone" bluff: simulated living room occupancy, dynamic lighting, high-decibel acoustic deterrence) before intruders can breach the entryway.
* **Emergency Dispatch** compiles verified, NENA-compliant Digital Computer-Aided Dispatch (CAD) manifests (RapidSOS format) staged for 1-tap resident transmission when critical threats persist.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 PERIMETER INGEST (Ring)                                │
│                     [PIR Motion]      [Camera / Vision]      [Microphone]              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Telemetry Packet (M, V, A, Φ)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ALEXA+ INCIDENT COMMANDER (FastMCP Server)                      │
│                                                                                        │
│   ┌───────────────────────────┐   ┌──────────────────────────┐   ┌─────────────────┐   │
│   │ Sensor Integrity Auditor  ├──►│ System 1: Local Reflexes ├──►│  Deterministic  │   │
│   │ (Degraded Mode Fallbacks) │   │ (Zero-Latency Rule Table)│   │  State Machine  │   │
│   └───────────────────────────┘   └─────────────┬────────────┘   └────────┬────────┘   │
│                                                 ▼                         │            │
│                                   ┌──────────────────────────┐            │            │
│                                   │ System 2: Bedrock Scorer │◄───────────┘            │
│                                   │ (Claude 3.5 Sonnet / CAD)│                         │
│                                   └──────────────────────────┘                         │
└───────────────────────────────────────────────────────────────────────────┼────────────┘
                                                                            │
                                   ┌────────────────────────────────────────┼────────────────────────────────────────┐
                                   ▼                                        ▼                                        ▼
                             [LEVEL 0: SAFE]                      [LEVEL 1: AMBIGUOUS]                      [LEVEL 2/3: CRITICAL]
                             • Silent Arrival Clearance           • Query Host gently                       • High-Urgency Escalation
                             • Audit Log                          • Respect Sleep State                     • Dual-Brain Deterrence Trigger
                             • Disarm Exterior Alert              • Ring Doorbell Intercom
                                                                                                                     │
                                                    ┌────────────────────────────────────────────────────────────────┴──────────────────┐
                                                    ▼                                                                                   ▼
                                            [Host is Awake]                                                                     [Host is Asleep]
                                            • Alexa Voice Alert                                                                 • Low-Frequency Bedroom Whisper
                                            • Fire TV System Toast / PIP                                                        • Phone Nightstand Critical Alert
                                            • Manual Resident Control                                                           • Echo Boot-Bridge (150ms Footsteps)
                                                                                                                                • Fire TV "Home Alone" Bluff
                                                                                                                                • NENA Digital CAD Staged (1-Tap)
```

---

## 2. Mathematical Formalization & Signal Ingestion

A perimeter event is defined as a tensor product across three orthogonal state spaces:

$$\mathbf{ObservedEvent} = \left( \mathbf{Ring}_{\text{Sensors}} \odot \vec{\Phi}_{\text{Integrity}} \right) \times \mathbf{Subject}_{\text{Class}} \times \mathbf{Host}_{\text{State}}$$

### 2.1 The Ring Sensor Triad ($\mathbf{Ring}_{\text{Sensors}}$)
* **Motion ($M \in \{0, 1\}$):** Binary PIR trip or optical flow delta.
* **Vision ($V \in \mathcal{V}$):**
  $$\mathcal{V} = \{ V_{\text{face\_known}}, V_{\text{face\_unv}}, V_{\text{masked}}, V_{\text{weapon}}, V_{\text{package}}, V_{\text{animal}}, V_{\text{tampered}} \}$$
* **Audio ($A \in \mathcal{A}$):**
  $$\mathcal{A} = \{ A_{\text{voice\_known}}, A_{\text{speech\_benign}}, A_{\text{speech\_hostile}}, A_{\text{breach\_noise}}, A_{\text{ambient\_quiet}}, A_{\text{jammed}} \}$$

### 2.2 The Signal Integrity Vector ($\vec{\Phi}_{\text{Integrity}}$)
To ensure zero crashes during hardware faults, physical tampering, or bad weather:

$$\vec{\Phi} = \begin{bmatrix} \Phi_M \\ \Phi_V \\ \Phi_A \end{bmatrix}, \quad \Phi_k \in \{1.0 \text{ (Nominal)}, 0.5 \text{ (Degraded)}, 0.0 \text{ (Failed / Tampered)}\}$$

### 2.3 Subject Classification ($\mathbf{Subject}_{\text{Class}}$)
* $S_{\text{family}}$: Authorized resident / family / whitelisted guest.
* $S_{\text{benign}}$: Unharmful stranger (delivery driver, postman, utility worker, lost neighbor).
* $S_{\text{suspicious}}$: Ambiguous stranger (loitering $>90\text{s}$, casing windows, testing gates).
* $S_{\text{hostile}}$: Hostile intruder (masked, carrying pry tools/weapons, aggressive banging).
* $S_{\text{env}}$: Environmental false trigger (stray animal, windblown foliage, headlight sweep).

### 2.4 Host State ($\mathbf{Host}_{\text{State}}$ via Bee Wearable)
* $H_{\text{awake}}$: Home and awake (active conversational speech in `bee now`, physical movement).
* $H_{\text{asleep}}$: Home and in deep/circadian sleep (temporal speech silence $>1\text{h}$ in `bee now` + accelerometer stillness).
* $H_{\text{away}}$: Away from home (geofence disconnected, BLE beacon out of range).
* $H_{\text{distress}}$: In acute duress (spoken duress codeword or Tier B Apple Watch tachycardia spike $>140\text{ BPM}$).

---

## 3. The 10-Scenario Baseline Matrix

| ID | Scenario | Ingest Triad ($M, V, A$) | Subject | Host State | Severity | Coordinated Mesh Response |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **01** | **Late-Night Family Arrival** | $M=1$<br>$V=V_{\text{face\_known}}$<br>$A=A_{\text{voice\_known}}$ | $S_{\text{family}}$ | $H_{\text{asleep}}$ | **L0** | • **Ring:** Silent arrival clearance; perimeter alerts disarmed.<br>• **Bee & Fire TV:** Zero disruption.<br>• **Alexa+:** Silent event log. |
| **02** | **Midnight Stealth Delivery** | $M=1$<br>$V=V_{\text{package}} + V_{\text{face\_unv}}$<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{benign}}$ | $H_{\text{asleep}}$ | **L1** | • **Ring:** Video recorded.<br>• **Bedroom Echo:** Suppressed (preserves sleep).<br>• **Alexa+:** Enqueues morning notification. |
| **03** | **Daytime Doorbell / Visitor** | $M=1$<br>$V=V_{\text{face\_unv}}$<br>$A=A_{\text{speech\_benign}}$ | $S_{\text{benign}}$ | $H_{\text{awake}}$ | **L1** | • **Alexa+:** Chimes: *"Visitor at the front door."*<br>• **Fire TV:** Heads-up system notification / PIP stream.<br>• **Phone:** Low-priority push notification. |
| **04** | **Curious Neighbor (Host Away)** | $M=1$<br>$V=V_{\text{face\_unv}}$<br>$A=A_{\text{speech\_benign}}$ | $S_{\text{benign}}$ | $H_{\text{away}}$ | **L1** | • **Ring:** Automated voice concierge: *"Host is away, please leave a message."*<br>• **Mobile:** Summary alert pushed. |
| **05** | **Environmental Anomaly** | $M=1$<br>$V=V_{\text{animal}}$<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{env}}$ | $H_{\text{asleep}}$ | **L0** | • **Engine:** Vision model filters animal.<br>• **All Devices:** Pure silent drop. Zero false alarm penalty. |
| **06** | **Covert Entry Breach (Prowler)** | $M=1$<br>$V=V_{\text{masked}}$<br>$A=A_{\text{breach\_noise}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ | **L2** | • **Alexa+:** Low-frequency whispered alert at bedside.<br>• **Echo Boot-Bridge:** Hallway Echo fires 150ms footsteps.<br>• **Fire TV:** Deterrent trigger — simulated conversation & dog barking.<br>• **Smart Home:** Exterior floodlight on.<br>• **Ring:** Outdoor speaker: *"Hold on, coming to the door!"* |
| **07** | **Violent Forced Entry / Invasion** | $M=1$<br>$V=V_{\text{weapon}}$<br>$A=A_{\text{speech\_hostile}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ / $H_{\text{awake}}$ | **L3** | • **Ring:** Siren triggered.<br>• **Smart Lights:** Interior/exterior strobe.<br>• **Fire TV:** Full-screen Ring camera live feed takeover.<br>• **Alexa+:** Broadcasts: *"Emergency services alerted."*<br>• **AWS Bedrock:** Compiles NENA Digital CAD manifest. |
| **08** | **Lens Tamper Breach** | $M=1$<br>$V=V_{\text{tampered}}$<br>$A=A_{\text{breach\_noise}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ | **L2** | • **Engine:** Flags optical tamper fault ($\Phi_V=0$).<br>• **Alexa+:** Bedside whispered alert of compromised sensor.<br>• **Echo Boot-Bridge & Fire TV:** Instant acoustic deterrence.<br>• **Phone:** Nightstand alert card displayed. |
| **09** | **Loitering / Perimeter Casing** | $M=1$<br>$V=V_{\text{face\_unv}}$ ($>90\text{s}$)<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{suspicious}}$ | $H_{\text{awake}}$ | **L1** | • **Ring:** Activates courtesy spotlight.<br>• **Alexa+:** Asks: *"Individual lingering at front gate. View feed?"*<br>• **Phone:** Notification card. |
| **10** | **Host Duress / Armed Coercion** | $M=1$<br>$V=V_{\text{face\_known}} + V_{\text{weapon}}$<br>$A=A_{\text{speech\_hostile}}$ | $S_{\text{hostile}}$ | $H_{\text{distress}}$ | **L3** | • **Silent Protocol:** Exterior/interior sirens suppressed (preserves host life).<br>• **Perimeter:** Normal silent clearance.<br>• **Emergency:** Silent NENA Digital CAD alert dispatched with live telemetry. |

---

## 4. The Degraded-Mode Protocol (DMP): 14 Edge Cases & Failure Adaptations

The core engineering distinction of Vigil+ is that **it does not assume ideal telemetry**. If a camera is spray-painted, a wearable is off-wrist, or cloud APIs throttle, the system adapts deterministically:

### Category A: Optical & Vision Failures
1. **A1. Lens Tamper / Total Blinding ($\Phi_V = 0.0$):**
   * *Detection:* Luminance variance drops to $\approx 0$; edge-detector gradient collapse while PIR confirms proximity.
   * *Adaptation:* **Acoustic-Motion Triangulation (AMT)**. Audio promoted to primary evidence. Any breach sound (scraping/prying) triggers Level 2 escalation.
2. **A2. High-Beam Laser / IR Saturation ($\Phi_V = 0.0$):**
   * *Detection:* Overexposure with pixel saturation $>95\%$; histogram clamped at 255 with zero spatial contours.
   * *Adaptation:* Classified as intentional human tampering attempt. Automatic Level 2 alarm: Turn on porch floodlight and trigger Alexa interior chime.
3. **A3. Facial Masking / Concealment ($\Phi_V = 0.5$):**
   * *Detection:* Human body/pose confidence $>0.80$, but Facial Landmark confidence $<0.15$.
   * *Adaptation:* Subject marked as $S_{\text{suspicious}}$ with elevated threat multiplier. If dwell time $>30\text{s}$ at door $\to$ Level 2 escalation.
4. **A4. 2D Facial Spoofing Attack ($\Phi_V = 0.0$):**
   * *Detection:* 2D liveness check failure (no micro-saccades, static IR reflection, zero parallax).
   * *Adaptation:* Rejection. Suppress perimeter clearance. Trigger dynamic two-way voice challenge via Ring speaker.

### Category B: Acoustic & Microphone Failures
5. **B1. Acoustic Jamming / High Ambient Noise ($\Phi_A = 0.0$):**
   * *Detection:* SNR drops $<0\text{ dB}$; audio frequency spectrum shows flat high-power saturation (pink/white noise or heavy storm).
   * *Adaptation:* **Optical-Dominant Fallback**. Audio muted in pipeline. Threat assessment driven purely by visual pose and object detection (tracking hands, crowbars, gestures).
6. **B2. Sub-Vocal / Whisper Breach ($\Phi_A = 0.5$):**
   * *Detection:* Voice Activity Detector (VAD) triggers on noise floor shifts; spectral energy in human whisper band ($2\text{kHz} - 4\text{kHz}$).
   * *Adaptation:* **Spectral Audio Zoom**. Dynamic range boosted; targeted acoustic transcription correlated with lingering motion.
7. **B3. Voice Replay / Deepfake Attack ($\Phi_A = 0.0$):**
   * *Detection:* Acoustic Room Impulse Response (RIR) anomaly; outdoor porch reverberation mismatch; speaker proximity distortion.
   * *Adaptation:* Voice alone denied authority to disarm perimeter alert without simultaneous 3D facial liveness match.

### Category C: Motion Sensor Edge Cases
8. **C1. Stealth Crawl / PIR Blindspot ($\Phi_M = 0.0$):**
   * *Detection:* PIR reads $M=0$, but Camera Optical Flow or VAD detects subtle pixel movement or floor friction noise.
   * *Adaptation:* **Continuous Optical Watchdog**. When host is $H_{\text{asleep}}$, low-power vision watchdog triggers on optical flow $>5\%$ even if PIR is cold.
9. **C2. PIR Flapping / Environmental False Fire ($\Phi_M = 0.5$):**
   * *Detection:* Rapid repetitive $M=1$ triggers every $2\text{s}$; vision detects no human anatomy (only trees/leaves).
   * *Adaptation:* Dynamic sensor damping: apply 60s cooldown; require positive Human Visual Classification before waking Alexa or Bee.

### Category D: Host Biometrics & Wearable Failures
10. **D1. Bee Off-Wrist / Charging ($H = \text{unknown}$):**
    * *Detection:* Bee telemetry reports `device_state = off_wrist` or `charging = true` with zero audio logging.
    * *Adaptation:* **Conservative Fail-Safe Default**. System defaults to $H_{\text{asleep}}$ (safest assumption). Wake alerts routed directly to **Alexa bedroom whisper/chime** and phone nightstand hum.
11. **D2. Host Sedated / Unresponsive ($H = \text{unresponsive}$):**
    * *Detection:* Zero vocal acknowledgement or motion after $30\text{s}$ of bedroom whisper and phone nightstand alert.
    * *Adaptation:* **Actuator Escalation**. Fire TV deterrent volume increased by $+6\text{dB}$; smart bedroom lights turn on softly; Alexa voice alert escalates volume.
12. **D3. Host Sleepwalking / Parasomnia ($H = \text{parasomnia}$):**
    * *Detection:* Erratic nocturnal movement without normal interactive responsiveness.
    * *Adaptation:* Alexa prompts: *"Confirm status."* If no verbal response received, perimeter alert remains armed.

### Category E: Multi-Subject & Adversarial Edge Cases
13. **E1. The Piggyback (Family Member + Stranger):**
    * *Detection:* Bounding box scene graph identifies 1 Known Face + 1 Unverified Person in the same threshold frame.
    * *Adaptation:* **Conditional Disarm**. Exterior alert clears, but chime alerts household: *"Welcome home. Guest detected."* Bedroom console notified silently.
14. **E2. Host Duress / Armed Coercion:**
    * *Detection:* Host at door accompanied by unverified person speaking a pre-configured duress codeword or exhibiting distress.
    * *Adaptation:* **Silent Duress Protocol**. Normal arrival simulated (preserving physical safety). All audible sirens suppressed. Silent Level 3 NENA Digital CAD emergency manifest compiled and staged for dispatch.

---

## 5. System Architecture & MCP Tool Contracts

Vigil+ is implemented as a **FastMCP Server** exposing standard tools over **Streamable HTTP** (MCP Specification 2025-11-25+):

### 5.1 MCP Tools Exposed to Alexa+
```python
@mcp.tool()
async def audit_perimeter_event(event_payload: dict) -> dict:
    """Ingests raw Ring telemetry, evaluates signal integrity vector (Φ),
    and returns normalized event with degradation flags."""

@mcp.tool()
async def query_wearer_state(user_id: str) -> dict:
    """Queries Bee context via bee-cli (`bee now --json`) and wearable status:
    returns {
        is_awake: bool,
        inference_basis: str,           # 'speech_recency_and_stillness' or 'apple_watch_healthkit'
        minutes_since_last_speech: int,  # Derived from bee now utterance timestamps
        device_tier: str,                # 'bee_pioneer' or 'apple_watch'
        heart_rate: Optional[int],       # Available only on Tier B Apple Watch
        on_wrist: bool
    }"""

@mcp.tool()
async def trigger_tactical_wake(user_id: str, channel: str = "echo_whisper") -> dict:
    """Executes private interior wake-up: triggers bedroom Echo low-frequency whisper
    and nightstand phone Critical Alert hum without outdoor acoustic spillage."""

@mcp.tool()
async def trigger_firetv_deterrence(mode: str, volume_percent: int) -> dict:
    """Launches Fire TV deterrent player: 'simulated_party', 'dog_bark', or 'camera_feed',
    preceded by 150ms hallway Echo Boot-Bridge footstep audio."""

@mcp.tool()
async def format_emergency_cad_packet(incident_id: str) -> dict:
    """Compiles NENA-compliant Digital CAD manifest (RapidSOS format) with cryptographic
    SHA-256 hash, evidence timeline, photographic stills, and coordinates."""
```

### 5.2 Amazon Bedrock Multimodal Threat Assessment Schema
When a suspicious event occurs, the Ring snapshot and audio transcript are evaluated by **Amazon Bedrock (Claude 3.5 Sonnet)** using structured JSON outputs:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ThreatAssessment",
  "type": "object",
  "properties": {
    "threat_level": { "type": "string", "enum": ["L0_SAFE", "L1_AMBIGUOUS", "L2_SUSPICIOUS", "L3_CRITICAL"] },
    "threat_score": { "type": "number", "minimum": 0.0, "maximum": 1.0 },
    "detected_subject": { "type": "string", "enum": ["FAMILY", "BENIGN_STRANGER", "SUSPICIOUS_STRANGER", "HOSTILE_INTRUDER", "ANIMAL_ENVIRONMENTAL"] },
    "visual_findings": { "type": "array", "items": { "type": "string" } },
    "audio_sentiment": { "type": "string", "enum": ["BENIGN", "NEUTRAL", "HOSTILE", "BREACH_NOISE", "INDETERMINATE"] },
    "recommended_mesh_action": { "type": "string", "enum": ["SILENT_PASS", "NOTIFY_HOST", "WAKE_HOST_AND_DETER", "DISPATCH_EMERGENCY"] },
    "justification": { "type": "string" }
  },
  "required": ["threat_level", "threat_score", "detected_subject", "recommended_mesh_action", "justification"]
}
```

---

## 6. Implementation Roadmap for Kiro Pro

The repository is organized cleanly for automated execution using Kiro Pro:

```
Vigil/
├── README.md                      # Overview, setup, architecture diagram, license
├── LICENSE                        # MIT License (Open Source Challenge requirement)
├── pyproject.toml                 # uv/Python dependencies (mcp, boto3, pydantic, pytest)
├── docs/
│   ├── SPEC.md                    # System specification & mathematical formulations
│   ├── SYSTEM_DESIGN.md           # Operational modes, dwell dynamics & personas
│   ├── UI_UX_SPECIFICATION.md     # Design tokens, wireframes & anti-slop rules
│   ├── UI_UX_DESIGN_DECISIONS.md  # DR-01 to DR-06 design rationale
│   ├── AWS_INTEGRATION.md         # Bedrock & Kiro usage documentation (AWS Builder requirement)
│   └── FRICTION_LOG.md            # Developer friction log for 10% judging bonus
├── src/
│   ├── __init__.py
│   ├── server.py                  # FastMCP Streamable HTTP server entrypoint
│   ├── core/
│   │   ├── types.py               # Strict Pydantic models (Φ, Telemetry, State, CAD)
│   │   ├── state_machine.py       # Deterministic threat level state machine (L0 - L3)
│   │   ├── integrity_auditor.py   # Φ vector evaluator and degraded-mode logic
│   │   └── cad_dispatcher.py      # Emergency services NENA CAD payload generator
│   ├── adapters/
│   │   ├── ring_adapter.py        # Ring API, WebRTC & VideoProcessor plugin bridge
│   │   ├── bee_adapter.py         # Bee CLI `bee now` wrapper & sleep inference
│   │   ├── firetv_adapter.py      # Fire TV WebSocket bridge & bundled .aac deterrence
│   │   ├── alexa_adapter.py       # Bedroom whisper SSML & Echo Boot-Bridge trigger
│   │   └── bedrock_analyzer.py    # AWS Bedrock Claude 3.5 Sonnet integration
│   └── simulator/
│       ├── scenario_runner.py     # Deterministic multi-device scenario simulator
│       └── canned_scenarios.json  # Definitions for Scenarios 01-10 and Failures A1-E2
└── tests/
    ├── test_scenarios_baseline.py # Tests verifying Scenarios 01-10
    └── test_resilience_matrix.py  # Tests verifying all 14 Degraded Mode Protocol adaptations
```

### Execution Milestones for Kiro Pro:
1. **Milestone 1:** Scaffold project, dependencies (`pyproject.toml`), and core Pydantic types (`src/core/types.py`).
2. **Milestone 2:** Implement `IntegrityAuditor` and `ScenarioRunner` with the 10 baseline scenarios.
3. **Milestone 3:** Implement Degraded Mode Protocol (DMP) handling all 14 edge cases.
4. **Milestone 4:** Build FastMCP server endpoints and AWS Bedrock adapter with schema enforcement.
5. **Milestone 5:** Connect device simulators (Ring, Bee, Fire TV) and pass 100% of automated tests.
6. **Milestone 6:** Finalize documentation (`AWS_INTEGRATION.md`, `FRICTION_LOG.md`) and verify open-source license.

---

## 7. The Ground-Truth Reality & Assumption Transformation Matrix

To guarantee that Vigil+ is built upon engineering reality rather than vaporware, every initial design assumption was subjected to a Devil's Advocate audit and tested against the official APIs and physical hardware:

| Domain | False / Naive Assumption | Ground-Truth Reality | The Hardened Vigil Feature / Moat |
| :--- | :--- | :--- | :--- |
| **Physical Security** | Ring doorbells can lock/unlock physical deadbolts. | Ring doorbells have zero mechanical motors or latch sensors. "Software cannot save you from a crowbar." | **Asymmetric Psychological Deterrence:** The "Home Alone" bluff (Fire TV + Echo) convinces prowlers the house is awake and occupied. Verified arrivals clear perimeter alerts with zero-trace. |
| **Bee Wearable Actuation** | `bee-cli` has a command to trigger haptic vibrations (`bee vibrate`). | `bee-cli` is strictly a read-only memory and context interface. No actuation endpoint exists. | **Tactical Bedroom Wake-Up:** The bedroom **Echo Dot** delivers pitch-shifted whispered SSML at bedside; the smartphone delivers a low-frequency nightstand hum. |
| **Bee Biometrics** | Bee Pioneer outputs heart rate (BPM) and REM sleep stages. | The Bee Pioneer clip contains microphones and an accelerometer; it has no optical PPG sensor. | **Temporal Bio-Grounding:** Sleep is inferred from **conversational silence in `bee now --json` (>1h) + accelerometer stillness**. Heart rate is strictly scoped to Tier B (Apple Watch via HealthKit). |
| **Fire TV Wake Latency** | Fire TV can wake instantly from standby and blast audio in 0ms. | HDMI-CEC handshake takes 3 to 4 seconds to power on a TV display from cold standby. | **The Echo Boot-Bridge:** The hallway Echo Dot fires low-latency footstep audio in **150ms** to bridge the 3-second HDMI-CEC negotiation window. |
| **Fire TV Display HUD** | Fire TV can draw arbitrary floating web overlays over running DRM streaming video. | Android TV / Fire OS strictly prevents third-party apps from overlaying Widevine L1 video. | **Native Heads-Up Toasts & Foreground Intents:** Uses native system notifications for couriers and foreground intents for active Level 2/3 breach feeds. |
| **Emergency Telephony** | Software can automatically place robocalls to 911 dispatch. | Automated 911 robocalls are illegal under US Federal law (FCC / 47 U.S.C. § 227). | **NENA-Compliant Digital CAD Manifest:** Formatted JSON payload (RapidSOS format) staged for 1-tap resident SOS transmission with cryptographic SHA-256 hash. |
| **AI Decision Latency** | AWS Bedrock Claude 3.5 Sonnet can make sub-second safety reflexes. | Base64 image upload + multimodal LLM inference takes 1.5s to 3.0s round-trip. | **Dual-Brain Architecture:** System 1 local deterministic state machine fires immediate physical reflexes (<50ms); System 2 Bedrock handles cognitive threat attribution (~2s). |
| **Network Loss** | Network drops should be treated as an alarm state / invasion. | Home Wi-Fi drops regularly (router reboots, DHCP leases). False alarms destroy user trust. | **Local Hardening & Silent Containment:** Internet loss ($\Phi_{\text{net}} = 0$) engages local edge sentry, illuminates courtesy light, and sends a contained local phone notice. Zero false 911 dispatches. |
| **Acoustic Duplexing Loop** | Blasting deterrent audio through Ring intercom while listening for intrusion sounds. | Ring mic and speaker are co-located (1.5 inches apart); outbound bluff creates an acoustic feedback loop triggering false breach escalation. | **Acoustic Duplex Mute Gate:** `RingAdapter` sets an `AudioDuplexMute` lock that suppresses inbound mic intake during outbound bluff playback plus 500ms acoustic dampening. |
| **Living Room Disruption** | Blasting high-decibel barking dogs on Fire TV on any nighttime motion ambiguity. | If the family is watching a movie at 9 PM ($H_{\text{awake}}$), blasting 85dB dog barks causes customer panic and return. | **HostState Context Gating:** Fire TV acoustic deterrence is strictly gated to $H_{\text{asleep}}$ and $H_{\text{away}}$. When $H_{\text{awake}}$, Fire TV renders *only* a subtle PIP toast with 1-click remote `Back` dismissal. |
| **Municipal False Alarm Fines** | 1-tap 911 dispatch card without cancellation buffer or authorization code. | Groggy residents woken up at 3 AM risk panic-tapping 911 on false alarms, incurring $100–$500 municipal police fines. | **Safe Cancellation & Disarm PIN:** 10-second cancel countdown window + 4-digit voice/touch Disarm PIN (*"Alexa, disarm 1-2-3-4"*) to safely abort dispatch staging. |
| **Agentic Alexa+ Surface** | Alexa+ FastMCP server exposes only raw RPC actuation endpoints. | Judges test Alexa+ for conversational agency, event reasoning, and configuration. | **Conversational Agent Tools:** Exposes `explain_incident_reasoning(incident_id)` and `set_mesh_guard_profile(mode, duration)` with `idempotency_token` deduplication. |
| **Hardware Dependency in Testing** | Requiring judges to own and configure physical Ring, Fire TV, and Bee hardware. | Judges evaluate projects in 3 minutes on their laptop without external hardware. | **Zero-Hardware Canned Simulator:** `src/simulator/canned_scenarios.json` and CLI runner (`uv run vigil simulate --scenario 02`) executes all 10 scenarios and 14 failure vectors in $<5\text{s}$. |
