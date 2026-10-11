# Project Vigil+: UI/UX Design Decisions Log

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
| **DR-04** | Wearable Interface & Haptics (Bee) | **DISCUSSING** | In Review (Tactile Language & Glanceable Micro-UI) |
| **DR-05** | Acoustic & Voice Persona (Alexa+) | **QUEUED** | Upcoming |

---

## DR-01: Visual Tone, Aesthetic Direction & Crisis Psychology

### 1. Context & Problem
Security interfaces frequently fail in one of two extremes: either they resemble cold, militaristic cyber-terminals that alienate non-technical family members, or they look like generic, bubbly SaaS templates with low-contrast gray text. Furthermore, when threats occur, typical alarms induce blinding panic by shouting for the user to resolve the problem.

### 2. Locked Direction: High-End Architectural Ambient (Bang & Olufsen meets Apple Home)
* **Visual Materiality:** Soft volcanic charcoal (`#161618`), warm bone/off-white typography (`#EDEDED`), calibrated warm amber indicators (`#F59E0B`), and deep obsidian surfaces (`#0D0D0E`). Zero gratuitous purple gradients or card-inside-card bloat.
* **Legibility & Accessibility:** High optical contrast, generous negative space, and large, clear touch targets designed for comfortable readability by elderly parents or multi-generational households.

### 3. Crisis Interaction Model: "The Active Protector"
* **Psychological Principle:** Vigil+ is an active guardian that bears the operational burden, not an alarmist bell that panics the resident.
* **Execution:** During an active perimeter threat, the interface remains calm, dark, and composed. Instead of flashing sirens, it presents a clear, step-by-step guidance card:
  > *"Unknown individual at front door. Front deadbolt secured. Deterrence active. Police notified. Stay inside."*
* Reassures the resident that the system is actively protecting the home while keeping them informed.

---

## DR-02: Information Architecture, Hero Object & Anti-Surveillance Family Model

### 1. Context & Problem
Smart home security apps often become accidental domestic surveillance tools—logging every movement, tracking which family member is in which room, and snitching on teenagers returning late. This breeds domestic friction and leads rebellious family members to tamper with or disable security hardware.

### 2. Locked Direction: The Sanctuary State Capsule (Boundary Protection, Zero Internal Tracking)
* **The Hero Object:** The central focal point is the **Sanctuary State Capsule**. It communicates boundary integrity without internal surveillance:
  * Shows external perimeter status (*"All entrances sealed • Grounds quiet"*).
  * Shows physical mechanical deadbolt seal confirmation (*"Front Deadbolt Latch Confirmed & Re-Locked"*).
  * Displays an aggregate household presence count (*"3 of 3 Residents on Premises"*), with zero forensic movement timelines or room-by-room snooping.

### 3. Arrival Model: Multi-Entity Zero-Trace Protocol
* **The Principle:** Authorized household members returning home (solo or in groups) are treated as quiet, self-clearing non-events.
* **Multi-Entity Set Resolution:**
  $$\text{Zero-Trace Entry:} \quad \forall p \in \text{Scene}, \quad \text{Identity}(p) \in \text{Household\_Whitelist}$$
  * If all individuals in the camera threshold are verified family/friends, the door unlatches silently with **zero trace** on shared screens.
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
