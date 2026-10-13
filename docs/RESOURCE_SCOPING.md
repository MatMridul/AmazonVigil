# Project Vigil+: Official Resources & SDK Scoping Guide

**Reference Source:** [Amazon Developer Hackathon 2026 Resources Portal](https://amazonappdev2026.devpost.com/resources)  
**Document Status:** Approved & Integrated into Architecture  

---

## 1. Overview of Scoped Ecosystems

Vigil+ unifies four Amazon device ecosystems and AWS cloud intelligence into a single ambient security mesh. Below is the mapping of official starter codebases, SDKs, APIs, and developer tooling:

```
┌───────────────────┬───────────────────────────────────────────┬────────────────────────────────────────────┐
│ Ecosystem         │ Official Tool / Starter Repository        │ Scoped Role in Vigil+                      │
├───────────────────┼───────────────────────────────────────────┼────────────────────────────────────────────┤
│ **Alexa+**        │ MCP Spec 2025-11-25+ (Streamable HTTP)    │ Central Incident Commander & FastMCP Hub   │
│ **Ring**          │ `AmazonAppDev/ring-api-helloworld`        │ Perimeter Sentry (Motion, WebRTC, Audio)   │
│ **Bee**           │ `docs.bee.computer` / `bee-cli` / Skill   │ Bio-Grounding (Sleep/Awake Context via Voice & Motion)│
│ **Fire TV**       │ `AmazonAppDev/react-native-multi-tv-app`  │ Active Deterrence Player (Vega/Web Player) │
│ **AWS Cloud**     │ Amazon Bedrock (Claude 3.5 Sonnet via SDK)│ Multimodal Threat Scorer & 911 CAD Engine  │
│ **Dev Tooling**   │ `@amazon-devices/amazon-devices-builder`  │ ADBT MCP Server & Agent Skills for Kiro    │
└───────────────────┴───────────────────────────────────────────┴────────────────────────────────────────────┘
```

---

## 2. Deep Dive by Component

### 2.1 Alexa+ Core (Model Context Protocol Engine)
* **Specification Requirement:** Model Context Protocol (MCP) version `2025-11-25` or later over **Streamable HTTP**.
* **Framework Choice:** Python `FastMCP` (or Node.js `@modelcontextprotocol/sdk`).
* **Simulation Allowance:** Amazon officially permits simulating the Alexa+ experience in a web app using agentic tooling.
* **Exposed Tool Contracts:**
  * `audit_perimeter_event(event_payload: dict) -> dict`
  * `query_wearer_state(user_id: str) -> dict`
  * `trigger_tactical_wake(user_id: str, channel: str) -> dict`
  * `trigger_firetv_deterrence(mode: str, volume_percent: int) -> dict`
  * `format_emergency_cad_packet(incident_id: str) -> dict`

### 2.2 Ring Ingest & Perimeter API
* **Reference Starter:** [`AmazonAppDev/ring-api-helloworld`](https://github.com/AmazonAppDev/ring-api-helloworld) (TypeScript / React).
* **Key Capabilities Scoped:**
  * **OAuth Token Flow:** Auth flow via Ring Developer Playground.
  * **Webhook Subscriptions:** Receiving real-time event triggers (`motion_detected`, `ding`) over SSE.
  * **WebRTC Live Streaming:** Low-latency video and audio stream initialization via WHEP.
  * **VideoProcessor Plugin Architecture (`lib/video-processors/`):** Client-side frame analysis interface (`process(frame: ImageData)`) powering our Optical Integrity Auditor ($\Phi_V$) to detect lens spray-paint and laser blinding directly on live frames.
  * **Device Health:** Battery levels, Wi-Fi RSSI, camera online/offline status.

### 2.3 Bee Wearable AI (Bio-Grounding & Context)
* **Official Docs:** [`docs.bee.computer`](https://docs.bee.computer)
* **Reference Starter:** [`github.com/bee-computer/bee-skill`](https://github.com/bee-computer/bee-skill)
* **Key Capabilities Scoped:**
  * **`bee-cli`:** Local CLI interface that exports raw context, conversations, and temporal metadata.
  * **Real-Time Context (`bee now --json`):** Reads the last 10 hours of ambient audio utterances to calculate speech recency.
  * **Daily Summary (`bee today --context`):** Reads daily notes, todos, and calendar facts.
  * **Dual-Tier Hardware UX Contract:**
    * **Tier A (Bee Pioneer Clip):** Sleep inferred from conversational silence (>1h) + accelerometer stillness. Zero fake CLI vibration dependencies.
    * **Tier B (Apple Watch via Bee App):** HealthKit optical PPG heart rate and sleep stages.
  * **Wake Actuation Route:** Interior tactical wake is executed by the bedroom **Echo Dot via low-frequency whisper SSML** and the smartphone **Nightstand Critical Alert**.

### 2.4 Fire TV & Echo Boot-Bridge (Living Room Deterrence)
* **Reference Starter:** [`AmazonAppDev/react-native-multi-tv-app-sample`](https://github.com/AmazonAppDev/react-native-multi-tv-app-sample)
* **Key Capabilities Scoped:**
  * **Cross-Platform Target:** Builds for **Vega OS, Android TV, AND Web** from one codebase.
  * **The "Home Alone" Deterrence Player:**
    * When Level 2 threat is triggered, Alexa+ signals the TV via WebSocket/MQTT.
    * **The Echo Boot-Bridge:** Hallway Echo fires 150ms footstep audio while Fire TV negotiates 3-4s HDMI-CEC screen power-on.
    * Fire TV powers on and plays **offline bundled `.aac` audio** (loud conversation, barking German Shepherd, movement shadows).
  * **Heads-Up System Toast & Fullscreen Stream:**
    * Uses native Android / Vega system notifications for couriers, and foreground intents for active Level 2/3 breach video feeds.

### 2.5 AWS Cloud & Bedrock Intelligence (AWS Builder Challenge)
* **Runtime Service:** Amazon Bedrock (`anthropic.claude-3-5-sonnet-20241022` via `boto3`).
* **Development Tool:** Kiro Crew with Claude models.
* **Key Capabilities Scoped:**
  * **Multimodal Threat Scorer:** Accepts base64 camera stills + audio transcripts + host state, returning structured JSON with threat scores $[0.0, 1.0]$.
  * **Emergency CAD Manifest Generator:** Formats 911 Computer-Aided Dispatch payloads containing timestamped incident logs, GPS coordinates, evidentiary frames, and threat justifications.

### 2.6 Amazon Devices Builder Tools (ADBT)
* **NPM Package:** `@amazon-devices/amazon-devices-buildertools-mcp`
* **Initialization:** `npx -y @amazon-devices/amazon-devices-buildertools-mcp@latest init-context`
* **Scoped Role:** Provides AI coding agents with ground-truth documentation, crash profiling, and 10-foot TV UX patterns.

---

## 3. Directory Layout for Scoped References

Reference repositories are pulled into `references/` (excluded from git via `.gitignore` to prevent nested submodule bloat):

```
references/
├── ring-api-helloworld/           # Ring API WebRTC & webhook sample
├── react-native-multi-tv-app/     # Vega / Fire TV cross-platform starter
└── bee-skill/                     # Bee wearable AI integration sample
```
