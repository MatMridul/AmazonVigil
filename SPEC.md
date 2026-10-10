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
* **Ring** acts as the high-resolution sensory perimeter (Motion, Vision, Audio).
* **Bee** grounds the system in human state (detecting whether the resident is awake, in deep sleep, or under physiological duress).
* **Alexa+** acts as the central Incident Commander via a self-hosted **Model Context Protocol (MCP)** server, evaluating multi-modal threats with **Amazon Bedrock**.
* **Fire TV & Smart Actuators** deploy active psychological deterrence (the "Home Alone" bluff: simulated living room occupancy, dynamic lighting, acoustic deterrence) before intruders can breach the door.
* **Emergency Dispatch** compiles verified, multi-sensor Computer-Aided Dispatch (CAD) manifests for emergency services if a high-severity threat persists while the resident is vulnerable.

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
│   │ Sensor Integrity Auditor  ├──►│ Bedrock Multimodal Scorer├──►│  Deterministic  │   │
│   │ (Degraded Mode Fallbacks) │   │ (Threat Intent & Level)  │   │  State Machine  │   │
│   └───────────────────────────┘   └──────────────────────────┘   └────────┬────────┘   │
└───────────────────────────────────────────────────────────────────────────┼────────────┘
                                                                            │
                                   ┌────────────────────────────────────────┼────────────────────────────────────────┐
                                   ▼                                        ▼                                        ▼
                             [LEVEL 0: SAFE]                      [LEVEL 1: AMBIGUOUS]                      [LEVEL 2/3: CRITICAL]
                             • Silent Auto-Unlock                 • Query Host gently                       • High-Urgency Escalation
                             • Audit Log                          • Respect Sleep State                     • Bio-Grounding Wake-Up
                                                                  • Ring 2-Way Intercom
                                                                                                                     │
                                                    ┌────────────────────────────────────────────────────────────────┴──────────────────┐
                                                    ▼                                                                                   ▼
                                            [Host is Awake]                                                                     [Host is Asleep]
                                            • Alexa Voice Alert                                                                 • Bee Intense Haptic Pulse
                                            • Fire TV PIP Camera Stream                                                         • Fire TV Acoustic Deterrent
                                            • Manual Resident Control                                                           • Emergency Lighting Strobe
                                                                                                                                • Bedrock 911 CAD Dispatch
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
* $H_{\text{awake}}$: Home and awake (active HRV, physical movement, ambient Alexa interaction).
* $H_{\text{asleep}}$: Home and in deep/circadian sleep (low baseline HR, motionless).
* $H_{\text{away}}$: Away from home (geofence disconnected, BLE beacon out of range).
* $H_{\text{distress}}$: In acute duress (sudden tachycardia spike $>140\text{ BPM}$ at entryway; potential coercion).

---

## 3. The 10-Scenario Baseline Matrix

| ID | Scenario | Ingest Triad ($M, V, A$) | Subject | Host State | Severity | Coordinated Mesh Response |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **01** | **Late-Night Family Arrival** | $M=1$<br>$V=V_{\text{face\_known}}$<br>$A=A_{\text{voice\_known}}$ | $S_{\text{family}}$ | $H_{\text{asleep}}$ | **L0** | • **Ring:** Silent deadbolt unlock.<br>• **Bee & Fire TV:** Zero disruption.<br>• **Alexa+:** Silent event log. |
| **02** | **Midnight Stealth Delivery** | $M=1$<br>$V=V_{\text{package}} + V_{\text{face\_unv}}$<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{benign}}$ | $H_{\text{asleep}}$ | **L1** | • **Ring:** Video recorded.<br>• **Bee:** Suppressed (preserves sleep).<br>• **Alexa+:** Enqueues morning notification. |
| **03** | **Daytime Doorbell / Visitor** | $M=1$<br>$V=V_{\text{face\_unv}}$<br>$A=A_{\text{speech\_benign}}$ | $S_{\text{benign}}$ | $H_{\text{awake}}$ | **L1** | • **Alexa+:** Chimes: *"Visitor at the front door."*<br>• **Fire TV:** Picture-in-picture stream overlay.<br>• **Bee:** Gentle wrist tap. |
| **04** | **Curious Neighbor (Host Away)** | $M=1$<br>$V=V_{\text{face\_unv}}$<br>$A=A_{\text{speech\_benign}}$ | $S_{\text{benign}}$ | $H_{\text{away}}$ | **L1** | • **Ring:** Automated voice concierge: *"Host is away, please leave a message."*<br>• **Mobile:** Summary alert pushed. |
| **05** | **Environmental Anomaly** | $M=1$<br>$V=V_{\text{animal}}$<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{env}}$ | $H_{\text{asleep}}$ | **L0** | • **Engine:** Vision model filters animal.<br>• **All Devices:** Pure silent drop. Zero false alarm penalty. |
| **06** | **Covert Lock Picking (Prowler)** | $M=1$<br>$V=V_{\text{masked}}$<br>$A=A_{\text{breach\_noise}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ | **L2** | • **Bee:** Continuous haptic vibration until awake.<br>• **Fire TV:** **Deterrence Trigger** — activates simulated indoor noise (loud conversation/barking dog).<br>• **Smart Home:** Exterior floodlight on.<br>• **Alexa+:** Whispers status to host upon waking. |
| **07** | **Violent Forced Entry / Invasion** | $M=1$<br>$V=V_{\text{weapon}}$<br>$A=A_{\text{speech\_hostile}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ / $H_{\text{awake}}$ | **L3** | • **Ring:** Siren triggered.<br>• **Smart Lights:** Interior/exterior strobe.<br>• **Fire TV:** Full-screen Ring camera live feed.<br>• **Alexa+:** Broadcasts: *"Emergency services contacted."*<br>• **AWS Bedrock:** Compiles 911 CAD dispatch manifest. |
| **08** | **Lens Tamper Breach** | $M=1$<br>$V=V_{\text{tampered}}$<br>$A=A_{\text{breach\_noise}}$ | $S_{\text{hostile}}$ | $H_{\text{asleep}}$ | **L2** | • **Engine:** Flags optical tamper fault ($\Phi_V=0$).<br>• **Bee:** Emergency haptic pulse.<br>• **Fire TV:** Instant acoustic deterrence.<br>• **Alexa+:** Alerts host of compromised door sensor. |
| **09** | **Loitering / Perimeter Casing** | $M=1$<br>$V=V_{\text{face\_unv}}$ ($>90\text{s}$)<br>$A=A_{\text{ambient\_quiet}}$ | $S_{\text{suspicious}}$ | $H_{\text{awake}}$ | **L1** | • **Ring:** Activates courtesy spotlight.<br>• **Alexa+:** Asks: *"Individual lingering at front gate. View feed?"*<br>• **Bee:** Subtle vibration alert. |
| **10** | **Host Duress / Armed Coercion** | $M=1$<br>$V=V_{\text{face\_known}} + V_{\text{weapon}}$<br>$A=A_{\text{speech\_hostile}}$ | $S_{\text{hostile}}$ | $H_{\text{distress}}$ (Tachycardia spike) | **L3** | • **Ring:** Normal door unlock (preserves host life).<br>• **Silent Escalation:** All audible sirens suppressed.<br>• **Emergency:** Silent 911 CAD alert dispatched with live telemetry. |

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
   * *Adaptation:* Rejection. Suppress auto-unlock. Require dynamic two-way voice challenge.

### Category B: Acoustic & Microphone Failures
5. **B1. Acoustic Jamming / High Ambient Noise ($\Phi_A = 0.0$):**
   * *Detection:* SNR drops $<0\text{ dB}$; audio frequency spectrum shows flat high-power saturation (pink/white noise or heavy storm).
   * *Adaptation:* **Optical-Dominant Fallback**. Audio muted in pipeline. Threat assessment driven purely by visual pose and object detection (tracking hands, crowbars, gestures).
6. **B2. Sub-Vocal / Whisper Breach ($\Phi_A = 0.5$):**
   * *Detection:* Voice Activity Detector (VAD) triggers on noise floor shifts; spectral energy in human whisper band ($2\text{kHz} - 4\text{kHz}$).
   * *Adaptation:* **Spectral Audio Zoom**. Dynamic range boosted; targeted acoustic transcription correlated with lingering motion.
7. **B3. Voice Replay / Deepfake Attack ($\Phi_A = 0.0$):**
   * *Detection:* Acoustic Room Impulse Response (RIR) anomaly; outdoor porch reverberation mismatch; speaker proximity distortion.
   * *Adaptation:* Voice alone denied authority to unlock without simultaneous 3D facial liveness match.

### Category C: Motion Sensor Edge Cases
8. **C1. Stealth Crawl / PIR Blindspot ($\Phi_M = 0.0$):**
   * *Detection:* PIR reads $M=0$, but Camera Optical Flow or VAD detects subtle pixel movement or floor friction noise.
   * *Adaptation:* **Continuous Optical Watchdog**. When host is $H_{\text{asleep}}$, low-power vision watchdog triggers on optical flow $>5\%$ even if PIR is cold.
9. **C2. PIR Flapping / Environmental False Fire ($\Phi_M = 0.5$):**
   * *Detection:* Rapid repetitive $M=1$ triggers every $2\text{s}$; vision detects no human anatomy (only trees/leaves).
   * *Adaptation:* Dynamic sensor damping: apply 60s cooldown; require positive Human Visual Classification before waking Alexa or Bee.

### Category D: Host Biometrics & Wearable Failures
10. **D1. Bee Off-Wrist / Charging ($H = \text{unknown}$):**
    * *Detection:* Bee telemetry reports `device_state = off_wrist` or `charging = true` ($\text{HeartRate} = \text{null}$).
    * *Adaptation:* **Conservative Fail-Safe Default**. System defaults to $H_{\text{asleep}}$ (safest assumption). Haptic wake is rerouted to **Alexa bedroom whisper/chime** at progressive volume.
11. **D2. Host Sedated / Unresponsive to Haptics ($H = \text{unresponsive}$):**
    * *Detection:* Bee accelerometer records zero movement or dismissal after $30\text{s}$ of continuous haptic pulsing.
    * *Adaptation:* **Actuator Escalation**. Fire TV deterrent volume increased by $+6\text{dB}$; smart bedroom lights turn on softly; Alexa voice alert triggered.
12. **D3. Host Sleepwalking / Parasomnia ($H = \text{parasomnia}$):**
    * *Detection:* Low HRV + erratic nocturnal movement without normal interactive responsiveness.
    * *Adaptation:* Alexa prompts: *"Confirm status."* If no verbal or wearable input received, exterior doors remain locked.

### Category E: Multi-Subject & Adversarial Edge Cases
13. **E1. The Piggyback (Family Member + Stranger):**
    * *Detection:* Bounding box scene graph identifies 1 Known Face + 1 Unverified Person in the same threshold frame.
    * *Adaptation:* **Conditional Disarm**. Door unlocks, but chime alerts household: *"Welcome home. Guest detected."* Bedroom console notified silently.
14. **E2. Host Duress / Armed Coercion:**
    * *Detection:* Host at door exhibiting extreme tachycardia ($>140\text{ BPM}$) while accompanied by an unverified person; or host speaks a pre-configured duress codeword.
    * *Adaptation:* **Silent Duress Protocol**. Door unlocks normally (preserving physical safety). All audible sirens are suppressed. Silent Level 3 CAD emergency dispatch sent immediately to 911.

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
    """Queries Bee wearable for current physiological state:
    returns {is_awake: bool, sleep_stage: str, heart_rate: int, on_wrist: bool}"""

@mcp.tool()
async def trigger_wearer_haptic(user_id: str, intensity: str, duration_sec: int) -> bool:
    """Triggers haptic wake-up vibration on the resident's Bee wearable."""

@mcp.tool()
async def trigger_firetv_deterrence(mode: str, volume_percent: int) -> dict:
    """Launches Fire TV deterrent player: 'simulated_party', 'dog_bark', or 'camera_feed'."""

@mcp.tool()
async def format_emergency_cad_packet(incident_id: str) -> dict:
    """Compiles AWS Bedrock-verified 911 CAD manifest with evidence timeline and coordinates."""
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
│   ├── AWS_INTEGRATION.md         # Bedrock & Kiro usage documentation (AWS Builder requirement)
│   └── FRICTION_LOG.md            # Developer friction log for 10% judging bonus
├── src/
│   ├── __init__.py
│   ├── server.py                  # FastMCP Streamable HTTP server entrypoint
│   ├── core/
│   │   ├── state_machine.py       # Deterministic threat level state machine (L0 - L3)
│   │   ├── integrity_auditor.py   # Φ vector evaluator and degraded-mode logic
│   │   └── cad_dispatcher.py      # Emergency services payload generator
│   ├── adapters/
│   │   ├── ring_adapter.py        # Ring API & simulator bridge
│   │   ├── bee_adapter.py         # Bee CLI / MCP wrapper
│   │   ├── firetv_adapter.py      # Fire TV WebSocket / MQTT deterrence launcher
│   │   └── bedrock_analyzer.py    # AWS Bedrock Claude 3.5 Sonnet integration
│   └── simulator/
│       ├── scenario_runner.py     # Deterministic multi-device scenario simulator
│       └── canned_scenarios.json  # Definitions for Scenarios 01-10 and Failures A1-E2
└── tests/
    ├── test_scenarios_baseline.py # Tests verifying Scenarios 01-10
    └── test_resilience_matrix.py  # Tests verifying all 14 Degraded Mode Protocol adaptations
```

### Execution Milestones for Kiro Pro:
1. **Milestone 1:** Scaffold project, dependencies (`pyproject.toml`), and core state machine.
2. **Milestone 2:** Implement `IntegrityAuditor` and `ScenarioRunner` with the 10 baseline scenarios.
3. **Milestone 3:** Implement Degraded Mode Protocol (DMP) handling all 14 edge cases.
4. **Milestone 4:** Build FastMCP server endpoints and AWS Bedrock adapter with schema enforcement.
5. **Milestone 5:** Connect device simulators (Ring, Bee, Fire TV) and pass 100% of automated tests.
6. **Milestone 6:** Finalize documentation (`AWS_INTEGRATION.md`, `FRICTION_LOG.md`) and verify open-source license.
