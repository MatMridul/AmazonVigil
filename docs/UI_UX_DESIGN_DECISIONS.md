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
| **DR-03** | 10-Foot Living Room Display (Fire TV) | **DISCUSSING** | In Review (Ambient PIP vs. Tiered Interruption) |
| **DR-04** | Wearable Interface & Haptics (Bee) | **QUEUED** | Upcoming |
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
