# Project Vigil+: Detailed System Design, Features & Personas

**System Name:** Vigil+  
**Target Submission:** Amazon Developer Hackathon 2026 (Alexa+ Track)  
**Document Status:** Master Architecture & Engineering Design  

---

## 1. Feature Specification & Operational Modes

Vigil+ supports 4 distinct operational modes that dynamically govern sensor thresholds, dwell grace periods, and actuator responses:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              THE 4 VIGIL OPERATIONAL MODES                             │
├─────────────────────┬───────────────────┬──────────────────────┬───────────────────────┤
│ 1. DAYTIME AMBIENT  │ 2. NIGHT SENTRY   │ 3. VACATION / AWAY   │ 4. SILENT DURESS      │
│  Host: Home & Awake │  Host: Deep Sleep │  Host: Geofenced Out │  Host: In Coercion    │
│  Dwell Grace: 45s   │  Dwell Grace: 15s │  Dwell Grace: 10s    │  Dwell Grace: 0s      │
│  Actuation: Chimes  │  Actuation: Wake  │  Actuation: Cloud    │  Actuation: Silent    │
│   & TV PIP stream   │   & Deterrence    │   Concierge & Alarm  │   911 CAD Dispatch    │
└─────────────────────┴───────────────────┴──────────────────────┴───────────────────────┘
```

### 1.1 Mode Definitions

1. **Mode 1: Daytime Ambient (Home & Active)**
   * **Activation:** Triggered when the resident is home and Bee reports $H_{\text{awake}}$ between 07:00 and 22:00.
   * **Dwell Grace Period:** $45\text{ seconds}$.
   * **Actuator Protocol:**
     * Ring: Polite chime on doorbell ding.
     * Alexa+: Subtle audio announcement: *"Delivery driver at the front door."*
     * Fire TV: Smooth Picture-in-Picture (PIP) camera overlay on currently playing media.
     * Bee: Low-priority single wrist tap.

2. **Mode 2: Night Sentry (Autonomous Sleep Protection)**
   * **Activation:** Engaged automatically when Bee telemetry confirms $H_{\text{asleep}}$ (circadian resting heart rate and zero locomotion) or scheduled curfew.
   * **Dwell Grace Period:** $15\text{ seconds}$ for unverified unmasked individuals; $0\text{ seconds}$ for masked, armed, or tampering subjects.
   * **Actuator Protocol:**
     * Ring: Suppress loud exterior chimes; record high-resolution infrared video.
     * Bee: **Progressive Tactile Arousal:** Continuous $80\text{Hz}$ haptic vibration pulsing until wrist motion confirms the resident is awake.
     * Fire TV: **"Home Alone" Acoustic/Visual Deterrent:** TV powers on instantly, playing high-volume simulated indoor occupancy (conversational audio, barking guard dogs, movement shadows).
     * Smart Home: Floodlights illuminate entryway; exterior smart lights cycle to alert neighbors.

3. **Mode 3: Vacation / Perimeter Hardened (Vacant Home)**
   * **Activation:** Geofence / BLE disconnect confirming all authorized residents are $H_{\text{away}}$.
   * **Dwell Grace Period:** $10\text{ seconds}$.
   * **Actuator Protocol:**
     * Ring: Automated synthetic concierge: *"The homeowner is unavailable. Please state your business."*
     * Mobile: High-priority push notification with 5-second video snippet.
     * Deterrence: If subject lingers $>30\text{s}$ or approaches deadbolt, Fire TV occupancy simulation and exterior sirens trigger.

4. **Mode 4: Silent Duress (Armed Coercion / Hostage Entry)**
   * **Activation:** Triggered when a resident enters with an unverified individual while Bee records acute tachycardia ($>140\text{ BPM}$) with static posture, or when a pre-configured duress voice passphrase is spoken.
   * **Dwell Grace Period:** $0\text{ seconds}$.
   * **Actuator Protocol:**
     * Ring: Door unlocks normally to protect the resident's physical safety.
     * Audible Actuators: **Complete silence.** Zero sirens, zero Alexa chimes, zero Fire TV displays.
     * Emergency Escalation: Silent Level 3 Computer-Aided Dispatch (CAD) packet transmitted to 911 with live GPS, door entry timestamp, and active audio feed.

---

## 2. Threat Classification & Dwell-Time Dynamics

$$\text{ThreatScore} = f\left(\mathbf{Ring}_{\text{Sensors}} \odot \vec{\Phi}_{\text{Integrity}}, \mathbf{Subject}_{\text{Class}}, \mathbf{Host}_{\text{State}}, T_{\text{dwell}}\right) \in [0.0, 1.0]$$

```
Threat Score:  0.0 ──────────── 0.25 ──────────────── 0.65 ──────────────── 0.85 ──────────── 1.0
Severity:      [ LEVEL 0: SAFE ]    [ LEVEL 1: AMBIGUOUS ]    [ LEVEL 2: SUSPICIOUS ]    [ LEVEL 3: CRITICAL ]
Action:        Silent Auto-Unlock   Gentle Query / Check      Haptic Wake & Deterrent   Sirens & 911 CAD
```

### 2.1 Zero-Grace Overrides
The system immediately bypasses all dwell timers and escalates to Level 2/3 when any of the following occur:
1. Optical Tamper Flag: $\Phi_V = 0.0$ (spray paint, tape, or sensor saturation).
2. Forced Entry Acoustics: $A = A_{\text{breach}}$ (metal scraping, glass breaking, lock jiggling).
3. Concealed Identity: $V = V_{\text{masked}}$ within $1.5\text{m}$ of entryway.
4. Weapon Detection: $V = V_{\text{weapon}}$ (crowbar, firearm, blade).

---

## 3. Personas & End-to-End User Stories

### Persona 1: Dr. Maya Lin (Deep-Sleeping Resident)
* **Profile:** Pediatric surgeon, erratic shift schedule, sleeps deeply with earplugs, phone on "Do Not Disturb".
* **Hardware:** Wears Bee wearable to bed, Ring Video Doorbell Pro 2 at entrance, Fire TV Omni Series in living room, Echo Dot in bedroom.
* **Journey (Covert Intrusion Attempt):**
  1. *03:14:20 UTC:* Masked prowler steps onto porch carrying a pry bar.
  2. *03:14:22 UTC:* Ring PIR trips ($M=1$); camera detects masked face ($V_{\text{masked}}$); audio detects lock scraping ($A_{\text{breach}}$).
  3. *03:14:23 UTC:* Alexa+ FastMCP server queries Bee via local MCP. Bee confirms Maya is in REM sleep ($H_{\text{asleep}}$, HR: 58 BPM).
  4. *03:14:24 UTC:* **Tactile Wake-Up:** Maya's Bee wearable pulses with sharp haptic vibrations. Maya awakens without intruder knowing she is awake.
  5. *03:14:25 UTC:* **Psychological Deterrent:** Living room Fire TV powers on via HDMI-CEC, blasting high-volume simulated living room chatter and barking dogs. Porch floodlight turns on.
  6. *03:14:28 UTC:* Prowler panics and flees the porch.
  7. *03:14:30 UTC:* Bedroom Echo whispers: *"Perimeter secure. Prowler deterred at front entrance. Telemetry recorded."*

### Persona 2: Jordan Lin (17-Year-Old Son)
* **Profile:** High school senior, returns home late after curfew, battery at 2%.
* **Hardware:** Enrolled in household voice and face whitelist.
* **Journey (Late-Night Silent Entry):**
  1. *02:22:10 UTC:* Jordan steps onto porch. Motion trips ($M=1$).
  2. *02:22:12 UTC:* Camera captures facial frame; 3D facial liveness passes ($V_{\text{face\_known}}$). Jordan whispers: *"Hey, it's Jordan."* ($A_{\text{voice\_known}}$).
  3. *02:22:13 UTC:* Threat score calculated as $0.02$ (Level 0 Safe).
  4. *02:22:14 UTC:* Smart deadbolt unlocks silently. Maya's Bee wearable experiences zero vibrations. Silent audit logged.

### Persona 3: Dave (Courier / Delivery Driver)
* **Profile:** Amazon Logistics delivery driver delivering same-day packages at night.
* **Journey (Midnight Parcel Drop):**
  1. *23:15:02 UTC:* Dave walks up to porch holding a cardboard box.
  2. *23:15:05 UTC:* Camera identifies box ($V_{\text{package}}$) and unmasked face ($V_{\text{face\_unv}}$). Audio captures footstep rustle ($A_{\text{ambient}}$).
  3. *23:15:14 UTC:* Dave sets package down, photographs delivery, and leaves. Total dwell time: $12\text{ seconds}$ ($< 15\text{s}$ threshold).
  4. *23:15:15 UTC:* System tags event as **Level 1 Safe Delivery**. Suppresses Bee vibrations. Enqueues parcel summary for morning briefing.

### Persona 4: The Covert Prowler (Adversary)
* **Profile:** Professional burglar attempting sensor sabotage.
* **Journey (Camera Sabotage Attempt):**
  1. *03:45:00 UTC:* Prowler approaches edge of porch and sprays black paint over Ring camera lens.
  2. *03:45:02 UTC:* Camera luminance drops to zero with edge collapse ($\Phi_V = 0.0$); PIR confirms human presence ($M=1$); mic hears aerosol hiss.
  3. *03:45:03 UTC:* Integrity Auditor triggers **Tamper Degraded Mode Protocol**. Shifting trust to acoustics.
  4. *03:45:04 UTC:* Exterior floodlight turns on, Fire TV deterrence blasts occupancy sounds, Maya's Bee vibrates, and emergency CAD dispatch prepares.

### Persona 5: Officer Davis (911 Emergency Dispatcher)
* **Profile:** Public Safety Communications Officer at county 911 dispatch.
* **Journey (Verified Digital Dispatch):**
  1. *03:45:30 UTC:* Unverified threat persists for $>25\text{s}$ while resident is in deep sleep.
  2. *03:45:32 UTC:* AWS Bedrock compiles structured 911 CAD payload.
  3. *03:45:33 UTC:* Dispatch terminal receives verified CAD manifest:
     * *Incident:* Active Residential Breach Attempt
     * *Address:* 1428 Elmhurst Lane (verified GPS)
     * *Evidence:* Masked male with crowbar, timestamped still frames, audio spectrogram of forced entry.
     * *Resident Status:* Confirmed asleep on premises.
  4. *03:45:45 UTC:* Police patrol dispatched with priority code 10-33.

---

## 4. Hardware Pluggability & Environment Abstraction

To ensure instant evaluation on physical hardware or zero-hardware simulators, all devices implement the **Abstract Hardware Provider Pattern**:

```
                       ┌────────────────────────────────────────┐
                       │          VIGIL CORE ENGINE             │
                       └───────────────────┬────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
       [VIGIL_MODE = 'live']                         [VIGIL_MODE = 'simulation']
       • Ring Partner API (WebRTC/OAuth)             • Canned JSON Event Stream
       • Real `bee-cli` & Bee MCP                    • Synthetic Biometric Generator
       • LAN WebSocket to Vega Fire TV               • Web-Based Deterrence Player
       • Live AWS Bedrock Cloud API                  • Mock Bedrock Fixture Replay
```

### 4.1 Environment Configuration (`.env`)
```bash
# System Mode: 'live' or 'simulation'
VIGIL_MODE=simulation

# Ring Configuration (Live Mode)
RING_REFRESH_TOKEN=mock_ring_token
RING_DEVICE_ID=mock_doorbell_01

# Bee Wearable Configuration
BEE_ENDPOINT=http://127.0.0.1:4000/mcp

# Fire TV Configuration
FIRETV_WS_HOST=192.168.1.150
FIRETV_WS_PORT=8080

# AWS Credentials (AWS Builder Challenge)
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022
```
