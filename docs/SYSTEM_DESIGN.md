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
     * Fire TV: Smooth Heads-Up System Toast / Picture-in-Picture (PIP) camera overlay on currently playing media.
     * Phone: Low-priority status notification.

2. **Mode 2: Night Sentry (Autonomous Sleep Protection)**
   * **Activation:** Engaged automatically when Bee telemetry confirms $H_{\text{asleep}}$ (conversational silence $>1\text{h}$ in `bee now --json` + accelerometer stillness) or scheduled curfew.
   * **Dwell Grace Period:** $15\text{ seconds}$ for unverified unmasked individuals; $0\text{ seconds}$ for masked, armed, or tampering subjects.
   * **Actuator Protocol:**
     * Ring: Suppress loud exterior chimes; record high-resolution infrared video.
     * Alexa+: **Tactical Interior Whisper:** Low-frequency pitch-shifted whispered SSML on bedroom Echo Dot at bedside.
     * Phone: **Nightstand Mode:** Low-frequency rising 40Hz hum bypassing DND via Critical Alerts.
     * Echo Boot-Bridge: Hallway Echo emits immediate low-latency footstep audio in $150\text{ms}$ while TV wakes.
     * Fire TV: **"Home Alone" Deterrence Bluff:** TV powers on via HDMI-CEC, blasting high-volume offline bundled audio (conversational chatter, barking German Shepherd, footsteps).
     * Smart Home: Floodlights illuminate entryway; exterior smart lights cycle to alert neighbors.

3. **Mode 3: Vacation / Perimeter Hardened (Vacant Home)**
   * **Activation:** Geofence / BLE disconnect confirming all authorized residents are $H_{\text{away}}$.
   * **Dwell Grace Period:** $10\text{ seconds}$.
   * **Actuator Protocol:**
     * Ring: Automated synthetic concierge: *"The homeowner is unavailable. Please state your business."*
     * Mobile: High-priority push notification with 5-second video snippet.
     * Deterrence: If subject lingers $>30\text{s}$ or approaches doorway threshold, Fire TV occupancy simulation and exterior sirens trigger.

4. **Mode 4: Silent Duress (Armed Coercion / Hostage Entry)**
   * **Activation:** Triggered when a resident enters with an unverified individual while speaking a pre-configured duress voice passphrase, or when Tier B wearable records acute distress.
   * **Dwell Grace Period:** $0\text{ seconds}$.
   * **Actuator Protocol:**
     * Ring: Exterior alarms suppressed; normal silent arrival simulated to protect the resident's physical safety.
     * Audible Actuators: **Complete silence.** Zero sirens, zero Alexa chimes, zero Fire TV displays.
     * Emergency Escalation: Silent Level 3 NENA Digital Computer-Aided Dispatch (CAD) packet transmitted with live GPS, entry timestamp, and active audio feed.

---

## 2. Threat Classification & Dwell-Time Dynamics

$$\text{ThreatScore} = f\left(\mathbf{Ring}_{\text{Sensors}} \odot \vec{\Phi}_{\text{Integrity}}, \mathbf{Subject}_{\text{Class}}, \mathbf{Host}_{\text{State}}, T_{\text{dwell}}\right) \in [0.0, 1.0]$$

```
Threat Score:  0.0 ──────────── 0.25 ──────────────── 0.65 ──────────────── 0.85 ──────────── 1.0
Severity:      [ LEVEL 0: SAFE ]    [ LEVEL 1: AMBIGUOUS ]    [ LEVEL 2: SUSPICIOUS ]    [ LEVEL 3: CRITICAL ]
Action:        Silent Clearance     Gentle Query / Check      Whisper Wake & Bluff       Sirens & CAD Staged
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
  3. *03:14:23 UTC:* Alexa+ FastMCP server queries Bee via `bee now --json`. Bee confirms Maya's last spoken utterance was 3h 12m ago and accelerometer is motionless: confirms deep sleep ($H_{\text{asleep}}$).
  4. *03:14:24 UTC:* **Tactical Bedroom Wake-Up:** Bedroom Echo whispers in low-pitch SSML: *"Maya. Someone is on the porch. Stay inside. Deterrence active."* Maya's phone wakes in Nightstand Mode with contained 40Hz hum. Maya awakens in quiet privacy without intruder knowing she is awake.
  5. *03:14:25 UTC:* **Psychological Deterrent & Boot-Bridge:** Hallway Echo emits low-latency 150ms footsteps while living room Fire TV powers on via HDMI-CEC, blasting high-volume simulated living room chatter and barking dogs. Porch floodlight turns on. Ring doorbell speaker states: *"Hold on, coming to the door right now!"*
  6. *03:14:28 UTC:* Prowler panics and flees the porch.
  7. *03:14:30 UTC:* Bedroom Echo whispers: *"Perimeter secure. Prowler deterred at front entrance. Telemetry recorded."*

### Persona 2: Jordan Lin (17-Year-Old Son)
* **Profile:** High school senior, returns home late after curfew, battery at 2%.
* **Hardware:** Enrolled in household voice and face whitelist.
* **Journey (Late-Night Silent Entry):**
  1. *02:22:10 UTC:* Jordan steps onto porch. Motion trips ($M=1$).
  2. *02:22:12 UTC:* Camera captures facial frame; 3D facial liveness passes ($V_{\text{face\_known}}$). Jordan whispers: *"Hey, it's Jordan."* ($A_{\text{voice\_known}}$).
  3. *02:22:13 UTC:* Threat score calculated as $0.02$ (Level 0 Safe).
  4. *02:22:14 UTC:* Verified Arrival Clearance logged. Ring suppresses motion chimes; Maya's bedroom experiences zero disturbance. Zero-trace entry logged.

### Persona 3: Dave (Courier / Delivery Driver)
* **Profile:** Amazon Logistics delivery driver delivering same-day packages at night.
* **Journey (Midnight Parcel Drop):**
  1. *23:15:02 UTC:* Dave walks up to porch holding a cardboard box.
  2. *23:15:05 UTC:* Camera identifies box ($V_{\text{package}}$) and unmasked face ($V_{\text{face\_unv}}$). Audio captures footstep rustle ($A_{\text{ambient}}$).
  3. *23:15:14 UTC:* Dave sets package down, photographs delivery, and leaves. Total dwell time: $12\text{ seconds}$ ($< 15\text{s}$ threshold).
  4. *23:15:15 UTC:* System tags event as **Level 1 Safe Delivery**. Suppresses bedroom alerts. Enqueues parcel summary for morning briefing.

### Persona 4: The Covert Prowler (Adversary)
* **Profile:** Professional burglar attempting sensor sabotage.
* **Journey (Camera Sabotage Attempt):**
  1. *03:45:00 UTC:* Prowler approaches edge of porch and sprays black paint over Ring camera lens.
  2. *03:45:02 UTC:* Camera luminance drops to zero with edge collapse ($\Phi_V = 0.0$); PIR confirms human presence ($M=1$); mic hears aerosol hiss.
  3. *03:45:03 UTC:* Integrity Auditor triggers **Tamper Degraded Mode Protocol**. Shifting trust to acoustics.
  4. *03:45:04 UTC:* Exterior floodlight turns on, Echo Boot-Bridge fires footsteps, Fire TV deterrence blasts occupancy sounds, Maya's bedroom Echo whispers alert, and emergency CAD dispatch stages.

### Persona 5: Officer Davis (911 Emergency Dispatcher)
* **Profile:** Public Safety Communications Officer at county 911 dispatch.
* **Journey (Verified Digital Dispatch):**
  1. *03:45:30 UTC:* Unverified threat persists for $>25\text{s}$ while resident is in deep sleep.
  2. *03:45:32 UTC:* AWS Bedrock compiles structured NENA Digital CAD payload.
  3. *03:45:33 UTC:* RapidSOS / Dispatch terminal receives verified CAD manifest with SHA-256 cryptographic hash:
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

---

## 5. Architectural Decisions & Devil's Advocate Reality Check

Vigil+ was systematically audited against ground truth, physical acoustics, and the official Amazon Hackathon SDKs. The results of this Devil's Advocate audit directly informed our hardened architecture:

1. **Pure Software Perimeter (No Phantom Deadbolts):**
   * *The Myth:* Ring doorbells can mechanically lock or unlock doors.
   * *The Reality:* Ring doorbells have zero motorized deadbolt actuators. Software cannot physically block a crowbar.
   * *The Grounded Feature:* Vigil leverages **Asymmetric Psychological Deterrence**. The moment an unverified subject lingers, the living room and entryway simulate an alert, awake, and occupied home ("Home Alone" engine), causing burglars to flee before attempting breach.

2. **Bio-Grounding via Conversation Recency (No Fake CLI Haptics):**
   * *The Myth:* `bee-cli` can trigger remote vibration motors, and Bee Pioneer outputs optical heart rate.
   * *The Reality:* `bee-cli` is a read-only memory and utterance logger. Bee Pioneer has microphones and an accelerometer, but no optical PPG sensor.
   * *The Grounded Feature:* Sleep is inferred from **temporal conversational silence in `bee now` (>1h) + accelerometer stillness**. Tactile and acoustic wake is executed by the bedroom **Echo Dot via low-frequency whisper SSML** and the smartphone **Nightstand Critical Alert**.

3. **Latency-Bridged Living Room Ambush (The Echo Boot-Bridge):**
   * *The Myth:* Fire TV can turn on instantly from standby (0ms).
   * *The Reality:* HDMI-CEC handshakes take 3 to 4 seconds to power on a TV display.
   * *The Grounded Feature:* The **Echo Boot-Bridge** fires low-latency footstep audio on the nearest hallway Echo within **150ms**, bridging the gap until Fire TV's high-decibel surround-sound bluffs engage.

4. **Two-Tier Cognitive Processing:**
   * *The Myth:* Cloud foundation models can handle instantaneous real-time safety reflexes.
   * *The Reality:* Multi-modal Bedrock inference over 1080p images takes 1.5s to 3.0s.
   * *The Grounded Feature:* **System 1 (Local Edge Rules, <50ms)** handles immediate physical reflexes (chime muting, light triggers, boot-bridge). **System 2 (AWS Bedrock Claude 3.5 Sonnet, ~2s)** performs deep cognitive intent evaluation and NENA Digital CAD manifest compilation.

5. **NENA-Compliant Digital CAD Manifest (No Illegal Robocalls):**
   * *The Myth:* Software should dial 911 directly via automated voice.
   * *The Reality:* Automated 911 robocalls are illegal under US Federal law (FCC).
   * *The Grounded Feature:* Vigil formats a cryptographic **NENA-Compliant Digital CAD Incident Manifest (RapidSOS format)** staged for 1-tap resident transmission, complete with GPS, evidentiary stills, and Bedrock reasoning justification.

6. **Acoustic Duplex Cancellation (No Microphone Self-Feedback Loop):**
   * *The Myth:* Ring two-way intercom can blast loud sound while simultaneously analyzing ambient audio without interference.
   * *The Reality:* Ring mic and speaker are 1.5 inches apart; outbound bluff audio loops directly into the mic, triggering false breach escalation.
   * *The Grounded Feature:* `RingAdapter` sets an `AudioDuplexMute` lock that suppresses inbound mic intake during outbound bluff playback plus 500ms acoustic dampening.

7. **Living Room Context Gating (No False Alarms on Movie Night):**
   * *The Myth:* Blasting barking dogs on Fire TV whenever an unverified person lingers at the door is always desirable.
   * *The Reality:* If the family is sitting on the couch at 9 PM watching a movie ($H_{\text{awake}}$), blasting 85dB dog barks causes customer panic and return.
   * *The Grounded Feature:* Fire TV acoustic deterrence is strictly gated to $H_{\text{asleep}}$ and $H_{\text{away}}$. When $H_{\text{awake}}$, Fire TV renders *only* a subtle PIP toast with 1-click remote `Back` dismissal.

8. **Cloud Token Budgeting & LLM JSON Resilience:**
   * *The Myth:* We can send raw 1080p images to Bedrock on every motion event and expect guaranteed valid JSON back.
   * *The Reality:* Flapping sensors cause rate limits ($ThrottlingException$), high token costs, and LLMs occasionally return markdown code fences ````json ... ````.
   * *The Grounded Feature:* WebP compression (65% token cut), 30-second token throttling valve, and Pydantic JSON repair fallback.

9. **Municipal False Alarm Mitigation & Safe Disarm PIN:**
   * *The Myth:* 1-tap 911 dispatch cards require no authorization safeguards.
   * *The Reality:* Groggy residents woken up at 3 AM risk panic-tapping 911 on false alarms, incurring $100–$500 municipal police fines.
   * *The Grounded Feature:* 10-second cancel countdown window + 4-digit voice/touch Disarm PIN (*"Alexa, disarm 1-2-3-4"*) to safely abort dispatch staging.

10. **Agentic Conversational Surface (Not a Dumb RPC Server):**
    * *The Myth:* Alexa+ only needs low-level emergency actuation tools.
    * *The Reality:* Hackathon judges evaluate Alexa+ on agentic interaction, event reasoning, and configuration.
    * *The Grounded Feature:* FastMCP exposes conversational tools (`explain_incident_reasoning`, `set_mesh_guard_profile`) with `idempotency_token` deduplication.

11. **Zero-Hardware Evaluation Sandbox:**
    * *The Myth:* Judges will set up physical Ring doorbells, Fire TV sticks, and Bee clips to test the project.
    * *The Reality:* Judges have 3 minutes to evaluate on their laptop.
    * *The Grounded Feature:* `src/simulator/` with `canned_scenarios.json` and CLI runner (`uv run vigil simulate --scenario 02`) executes all 10 scenarios and 14 failure vectors in $<5\text{s}$ with zero hardware dependencies.
