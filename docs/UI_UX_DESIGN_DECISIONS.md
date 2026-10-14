# Amazon Vigil: UI/UX Design Decisions Log

> **Document Status:** Active Living Design Record  
> **Repository:** [MatMridul/AmazonVigil](https://github.com/MatMridul/AmazonVigil)  
> **Design Lead:** Freelance UI/UX Creative Director & Systems Architect  
> **Client:** Mridul (Creative Engineer)  

---

## Decision Status Matrix

| ID | Decision Focus | Status | Locked Choice / Summary |
| :---: | :--- | :---: | :--- |
| **DR-01** | Visual Tone & Crisis Psychology | **LOCKED** | High-End Architectural Ambient; "The Active Protector" Model |
| **DR-02** | Hero Object & Family Privacy Model | **LOCKED** | Sanctuary State Capsule; Multi-Entity Zero-Trace Arrival |
| **DR-03** | 10-Foot Living Room Display (Fire TV) | **LOCKED** | Combinatorial Matrix; Headless Daemon; Bundled Offline Audio Library |
| **DR-04** | Wearable Interface & Haptics (Bee) | **LOCKED** | Dual-Tier Hardware Contract (Screenless Bee vs Apple Watch); 6s Overdrive; 30s Dispatch Countdown |
| **DR-05** | Acoustic & Voice Persona (Alexa+) | **LOCKED** | Low-Frequency Whisper Mode; Hierarchical Day/Night Deception Logic |
| **DR-06** | Smartphone Node, Network Resilience & RBAC | **LOCKED** | Contained Critical Alerts; Local Hardening on Network Loss; 3-Tier Household RBAC |

---

## DR-01: Visual Tone, Aesthetic Direction & Crisis Psychology

### 1. Context & Problem
Security interfaces frequently fail in one of two extremes: either they resemble cold, militaristic cyber-terminals that alienate non-technical family members, or they look like generic, bubbly SaaS templates with low-contrast gray text. Furthermore, when threats occur, typical alarms induce blinding panic by shouting for the user to resolve the problem.

### 2. Locked Direction: High-End Architectural Ambient (Bang & Olufsen meets Apple Home)
* **Visual Materiality:** Soft volcanic charcoal (`#161618`), warm bone/off-white typography (`#EDEDED`), calibrated warm amber indicators (`#F59E0B`), and deep obsidian surfaces (`#0D0D0E`). Zero gratuitous purple gradients or card-inside-card bloat.
* **Legibility & Accessibility:** High optical contrast, generous negative space, and large, clear touch targets designed for comfortable readability by elderly parents or multi-generational households.

### 3. Crisis Interaction Model: "The Active Protector"
* **Psychological Principle:** Amazon Vigil is an active guardian that bears the operational burden, not an alarmist bell that panics the resident.
* **Execution:** During an active perimeter threat, the interface remains calm, dark, and composed. Instead of flashing sirens, it presents a clear, step-by-step guidance card:
  > *"Unknown individual at front door. Front entryway monitored. Active deterrence running. Stay inside."*
* Reassures the resident that the system is actively protecting the home while keeping them informed.

---

## DR-02: Information Architecture, Hero Object & Anti-Surveillance Family Model

### 1. Context & Problem
Smart home security apps often become accidental domestic surveillance tools—logging every movement, tracking which family member is in which room, and snitching on teenagers returning late. This breeds domestic friction and leads rebellious family members to tamper with or disable security hardware.

### 2. Locked Direction: The Sanctuary State Capsule (Boundary Protection, Zero Internal Tracking)
* **The Hero Object:** The central focal point is the **Sanctuary State Capsule**. It communicates boundary integrity without internal surveillance:
  * Shows external perimeter status (*"All entrances monitored • Grounds quiet"*).
  * Shows perimeter boundary security confirmation (*"Front Entrance Monitored • Grounds Quiet"*).
  * Displays an aggregate household presence count (*"3 of 3 Residents on Premises"*), with zero forensic movement timelines or room-by-room snooping.

### 3. Arrival Model: Multi-Entity Zero-Trace Protocol
* **The Principle:** Authorized household members returning home (solo or in groups) are treated as quiet, self-clearing non-events.
* **Multi-Entity Set Resolution:**
  $$\text{Zero-Trace Entry:} \quad \forall p \in \text{Scene}, \quad \text{Identity}(p) \in \text{Household\_Whitelist}$$
  * If all individuals in the camera threshold are verified family/friends, perimeter alerts disarm silently with **zero trace** on shared screens.
  * If an unverified individual is detected alongside an authorized resident ($\exists p \in \text{Scene} \text{ where } \text{Identity}(p) \notin \text{Whitelist}$), the system immediately engages the **Tailgating / Piggyback Protocol** to protect against forced coercion.

---

## DR-03: 10-Foot Living Room Display & Headless Deterrence (Fire TV / Vega OS)

### 1. Context & Problem
Traditional smart TV apps fail as security systems because users must manually open them from an app drawer. Moreover, sudden loud bluffs on a TV can cause resident panic attacks, stream buffering can cause failure, and Bluetooth headphones can swallow the deterrent audio.

### 2. Locked Architecture: Combinatorial State Matrix & Headless Daemon
The Fire TV client runs as a **headless background daemon** reacting to the state tensor:
$$\mathbf{FireTV}_{\text{Response}} = \mathbf{Power}_{\text{TV}} \times \mathbf{Playback}_{\text{TV}} \times \mathbf{Subject}_{\text{Class}}$$

#### Combinatorial Behavior Table
1. **Watching Movie + Verified Household:** Zero interruption. Optional 3s subtle toast: *"Welcome home, Jordan"*, auto-clearing.
2. **Watching Movie + Benign Visitor (Courier):** Ambient Heads-Up PIP slides into top-right corner for 8s; movie continues playing uninterrupted.
3. **Watching Movie + Hostile Intruder:** Media pauses; smooth full-screen transition to Ring live feed with "Active Protector" guidance card.
4. **TV Standby (Screen Off) + Verified Household:** Complete silence. Screen stays black and off (preserves sleep and zero-trace).
5. **TV Standby (Screen Off) + Benign Visitor:** Screen stays black and off (preserves energy; logged silently).
6. **TV Standby (Screen Off) + Hostile Intruder:** **The HDMI-CEC Ambush.** Wakes TV via HDMI-CEC, blasting local "Home Alone" deterrent audio.
7. **TV Cold / Unplugged at Wall:** **Actuator Redundancy Fallback (DMP F1).** Automatically reroutes all deterrent audio to the local Echo smart speaker.

### 3. Hardened Engineering Countermeasures
* **Offline-First Bundled Acoustic Library:** The deterrence audio assets (multi-person conversation, footsteps, aggressive dog barks) are **packaged locally inside the app bundle**. Zero dependency on cloud streaming, YouTube, or external CDNs.
* **Ramping Decibel Curve:** Deterrent audio begins with a 3-second natural ramp (conversational murmur at 40% volume, escalating to footsteps and barking at 75%) to avoid triggering cardiac panic in residents sleeping on the couch.
* **Audio Sink Force-Override:** Issues `FORCE_AUDIO_SPEAKER` and unbinds active Bluetooth headsets upon Level 2 threat escalation, forcing audio to the primary TV speakers.
* **One-Touch Auto-Resume:** Pressing any remote button (or 15s post-threat clearance) immediately resumes media playback from the exact paused timestamp.
* **Echo Speaker Boot-Bridge:** While Fire TV negotiates HDMI-CEC power-on (~3-4s), the hallway Echo Dot emits low-latency footsteps within 150ms to bridge the gap.

---

## DR-04: Wearable Interface, Bio-Grounding & Dual-Tier Hardware Model (Bee Wearable)

### 1. Context & Hardware Reality
The physical Bee Pioneer wearable is a minimalist, screenless "Zero-UI" clip with only a dual-mic array, an accelerometer, an LED, and a single physical button. Crucially, `bee-cli` is strictly a read-only memory and context tool without remote vibration endpoints, and the hardware lacks an optical PPG heart rate sensor. Sleep state is inferred from conversational recency (`bee now --json` >1h silence) combined with accelerometer stillness. In contrast, an Apple Watch running Bee software provides a high-resolution OLED display, HealthKit PPG heart-rate tracking, and Apple's precision Taptic Engine.

### 2. Locked Architecture: The Dual-Tier Hardware UX Contract
* **Tier A: Screenless Bee Device (Pioneer Clip):**
  * Operates with zero visual display or CLI haptic dependencies.
  * **Bio-Grounding:** Sleep inferred from conversational silence (>1h) + accelerometer immobility.
  * **Wake Actuation:** Delegated to the bedroom Echo speaker (calibrated whispered SSML) and smartphone (contained 40Hz Nightstand hum).
  * **Single Click:** Acknowledge alert / Cancel emergency CAD dispatch staging countdown.
  * **Long Press:** Silent Duress trigger / Manual emergency confirmation.
* **Tier B: Apple Watch (Running Bee Software):**
  * Reads native optical PPG heart rate and sleep stages via HealthKit.
  * Renders full glanceable micro-UI threat capsule: `[L2: FRONT DOOR] • Prowler Detected • [DISMISS] / [CONFIRM 911]`.
  * Multi-frequency tactile haptics via Apple Taptic Engine.

### 3. Automatic Discovery & Zero-Friction Setup
* **Telemetry Auto-Detect:** The system checks `bee status --json` at runtime to detect `device_model: "bee_pioneer"` vs `"apple_watch"`.
* **Explicit Setup Confirmation:** Displays a single clear confirmation card in Mission Control during initial onboarding:
  > *"Wearable Detected: Apple Watch (via Bee). Haptics and on-wrist emergency confirmation cards active."*  
  *(One-tap override toggle to Screenless Bee Pioneer if needed).*

### 4. Deterministic Wake Ramp & The 6-Second Overdrive Tripwire
* **Phase 1: Contained Interior Wake (0s to 5s):**
  * **Tier A (Screenless Bee Pioneer):** Bedroom Echo Dot delivers low-frequency whispered SSML (*"Maya. Someone is outside. Stay quiet. Active deterrence running."*); smartphone emits rising 40Hz nightstand hum.
  * **Tier B (Apple Watch via Bee):** Rhythmic 30Hz gentle double-taps via Taptic Engine.
* **Phase 2: Emergency Overdrive (Trips at T = 6s):**
  * If after **6 seconds** resident exhibits zero movement (still asleep), OR if Ring detects forced entry noise ($A_{\text{breach}}$) / weapons ($V_{\text{weapon}}$):
  * Tier A: Bedroom Echo voice escalates: *"Maya, wake up. Perimeter breach at front door."* Living room Echo Boot-Bridge and Fire TV deterrent bluff launch at maximum volume.
  * Tier B: Apple Watch haptics jump to 100% continuous resonant vibration.
* **Phase 3: The 30-Second CAD Staging & 1-Tap SOS Transmission Window:**
  * When Overdrive engages while resident is asleep, the system compiles a NENA-compliant Digital CAD Manifest (RapidSOS format) and stages it on the resident's lock screen and Apple Watch.
  * An urgent 30-second countdown runs with a prominent **[TRANSMIT TO 911 / CAD]** button and voice authorization prompt (*"Say 'Alexa, confirm 911' or press transmit"*).
  * If the resident clicks the Bee button once or says *"Alexa, cancel alarm"*, the staging is safely aborted.
  * This guarantees compliance with FCC / 47 U.S.C. § 227 (no automated robocalls) while reducing resident panic-time to a single touch or word.

---

## DR-05: Acoustic Persona & Audio Architecture (Alexa+ & Ring Intercom)

### 1. Context & Problem
Commercial voice assistants sound cheerful, overly conversational, and apologetic (*"Hi there! I'm sorry, but I see motion at the door..."*). In a real defense system, this sounds absurd and undermines authority. Additionally, high-frequency audio from bedroom speakers can bleed outside, alerting intruders to the resident's location.

### 2. Interior Voice: Calibrated Low-Frequency Whisper Mode
* **Acoustic Physics:** Lower-frequency, pitch-calibrated sound stays contained inside the bedroom, preventing outdoor acoustic spillage.
* **Execution:** When the resident is asleep (Night Sentry mode), Alexa+ synthesizes low-pitch whispered speech directly on the bedroom Echo:
  ```xml
  <amazon:effect name="whispered">
    <prosody pitch="-15%" rate="92%">
      Maya. Someone is outside the door. Stay inside and stay quiet. Active deterrence running.
    </prosody>
  </amazon:effect>
  ```
* **Calm Authority:** Eliminates conversational pleasantries; communicates pure actionable state.

### 3. Exterior Voice: Hierarchical Day/Night Deception Logic
To prevent overconfident facial recognition failures from ruining user experience, Vigil utilizes a **Two-Tiered Hierarchical Resolution Flow**:
* **Tier 1 (Whitelist Resolution):** Binary check for verified resident.
* **Tier 2 (Ambiguity Resolution for Unverified):**
  * **Daytime Hours:** Deploys the **Firm Synthetic Sentry** (*"Notice: Resident is currently unavailable. This area is monitored. Deliveries may be placed on the mat."*).
  * **Night Sentry Hours:** Deploys the **Deceptive Ambient Bluff** (*"Hold on, coming to the door right now!"* + footsteps on wood). Intruders panic and flee; late couriers simply drop the parcel and depart.

---

## DR-06: Smartphone Node, Network Resilience & Household RBAC

### 1. Context & Problem
The smartphone is the resident's most powerful personal computer, but smart security systems often mishandle it—either spamming annoying push notifications that get tuned out, or blindly calling emergency services when home internet drops, causing catastrophic false alarm rates.

### 2. Contained Critical Alerts (Nightstand UX)
* **Bypassing Do Not Disturb Safely:** The smartphone utilizes native Apple/Android Critical Alerts on Level 2/3 threats.
* **Containment-First Audio:** Does not scream with an explosive siren. Emits a soft, rising 40Hz acoustic hum with high-contrast screen wake, acting as an intimate secondary safety net if the resident is not wearing the Bee watch.

### 3. Network Unobservability & "Fail-Safe Locally"
* **The Principle:** Loss of network $\neq$ Home invasion. High unobservability must never trigger automated external 911 dispatches.
* **Local Hardening Protocol:**
  1. Local edge sentry engages; sensor integrity evaluator drops cloud weighting and executes local rule table.
  2. Exterior and entryway floodlights illuminate.
  3. Echo bedroom speaker and smartphone emit localized alert: *"Notice: Home network offline. Local edge sentry active."*
  4. Cellular 5G on the phone acts as an emergency witness for the resident, preserving manual SOS capabilities without automated false dispatch.

### 4. Household Role-Based Access Control (RBAC)
* **Primary Admin (Head of Household):** Full governance, whitelist management, sensitivity mode configuration, and diagnostic audit review.
* **Verified Resident (Family Members / Teenagers):** Full view of Sanctuary status capsule, 1-tap "Call for Help" SOS, 2-way intercom, self-disarming, but zero snooping on other residents or audit log modification.
* **Trusted Guest / Caretaker (Babysitter / Neighbor):** Time-bounded access window during active shift; perimeter disarm permissions; zero visibility into household occupancy or historical records.
