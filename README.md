# Amazon Vigil

**Autonomous Multi-Device Perimeter Defense & Deterrence Mesh**  
*Built for the Amazon Developer Hackathon 2026 (Alexa+ Track, AWS Builder Challenge, Open Source Challenge)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Spec 2025-11-25](https://img.shields.io/badge/MCP-2025--11--25-green.svg)](https://modelcontextprotocol.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude%203.5-orange.svg)](https://aws.amazon.com/bedrock/)

---

## What Amazon Vigil Is

Amazon Vigil is an autonomous, 100% software home defense and deterrence mesh that connects the front door, the living room, personal wearables, and the cloud into an ambient, coordinated security response.

Instead of sending passive smartphone notifications that get ignored when residents are asleep, Amazon Vigil:
1. **Perimeter Awareness (Ring):** Ingests motion, WebRTC camera video, and audio; runs client-side `VideoProcessor` plugins to detect lens tampering and spray-paint sabotage.
2. **Human Bio-Grounding (Bee Wearable):** Assesses whether the resident is awake or in deep sleep via conversation recency (`bee now`) and accelerometer stillness.
3. **Ambient Incident Commander (Alexa+ via FastMCP):** Acts as the central coordinator, orchestrating low-latency local edge reflexes (<50ms) and cognitive multimodal threat analysis via **Amazon Bedrock (Claude 3.5 Sonnet)**.
4. **Active Psychological Deterrence (Fire TV & Echo Boot-Bridge):** Deploys the "Home Alone" bluff—using hallway Echo speakers for instant 150ms footstep audio while Fire TV wakes over HDMI-CEC to blast high-decibel barking dogs, dialogue, and movement shadows before an intruder breaches the entryway.
5. **Fail-Safe Digital CAD Dispatch:** Stages structured, NENA-compliant Digital Computer-Aided Dispatch (CAD) manifests (RapidSOS format) with cryptographic hashes for 1-tap resident transmission.

---

## Key Documentation

* 📖 **[Master System Specification](SPEC.md)** — Mathematical sensor triad formulation, the 10-Scenario baseline matrix, and the 14-Edge-Case Degraded Mode Protocol (DMP).
* 📋 **[Implementation Tasks & Roadmap](tasks.md)** — Phase-by-phase execution plan for autonomous agents and developers.
* 🧭 **[Decision Records](docs/decisions/)** — `DR-00` … `DR-10`, the durable architecture decisions (spec authority, state machine, MCP eligibility, smartphone mesh organ). Product/UI decisions live in **[UI/UX Decisions](docs/UI_UX_DESIGN_DECISIONS.md)** (`UX-01` … `UX-06`).
* 🛠️ **[Developer Friction Log](docs/FRICTION_LOG.md)** — Tooling feedback for the Amazon developer ecosystem (+10% judging bonus).

---

## Mesh Nodes — real vs. MODELED (honesty split)

Every integration is coded to the **real** vendor interface and runs **device-optional**: live with credentials/hardware, clearly-badged simulated mode without. Nothing fabricates a live feed.

| Organ | Role | Status | How it runs |
| :-- | :-- | :-- | :-- |
| **Alexa+ (MCP)** | incident commander / brain | **REAL** | `src/server.py` — official `mcp` SDK, 8 tools over Streamable HTTP (spec 2025-11-25+). Live with an Echo + linked Alexa+ account. |
| **Ring** | perimeter eyes/ears | **REAL API** | `src/adapters/ring_adapter.py` — Bearer-token auth, HMAC webhook verify, WHEP WebRTC. Simulated without a token. |
| **Fire TV** | deterrence actuator | **REAL (sideload)** | `src/web/static/firetv.html` surface + adapter logic. Live on a Fire TV Stick. |
| **Phone** | human CAD authorization | **REAL** | `src/web/static/phone.html` — renders on any Android/iOS browser (Samsung A35 tested). |
| **Bee** | resident bio-state | **MODELED** | `src/adapters/bee_adapter.py` — coded to the real `@beeai/cli` contract, but **no Bee device/data**, so MODELED. Vigil does **not** claim the Bee track. |

---

## Architecture Flow

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     Perimeter Ingest (Ring)     │     │    Bio-Context (Bee Wearable)   │
│     • PIR Motion Detection      │     │    • Conversation Recency (now) │
│     • WebRTC Live Video Stream  │     │    • Locomotion / Stillness     │
│     • VideoProcessor Plugin (Φ) │     │    • Sleep Context via bee CLI  │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │    Alexa+ Core FastMCP Server     │
                   │    • System 1: Local Reflex (<50ms)│
                   │    • System 2: Bedrock Multimodal │
                   │    • Sensor Integrity Auditor (Φ) │
                   └─────────────────┬─────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
  [Level 0: Safe]             [Level 1: Ambiguous]        [Level 2/3: Critical]
  • Verified Arrival Clearance• Alexa Voice Check         • Bedroom Whisper & Nightstand Hum
  • Muted Perimeter Alerts    • Respect Sleep State       • Echo Boot-Bridge (150ms Footsteps)
  • Zero-Trace Family Entry   • Fire TV System Toast/PIP  • Fire TV "Home Alone" Deterrence
                              • Ring Doorbell Greeting    • NENA 911 Digital CAD Staged
```

---

## Quickstart

Vigil runs **fully offline** out of the box — the deterministic engine and all
three console surfaces work with **no AWS account and no devices**. Credentials
and hardware only upgrade MODELED/simulated nodes to live.

### Prerequisites
* Python 3.11+
* `uv` package manager (`pip install uv`)
* *(optional)* AWS credentials with Amazon Bedrock access, for live multimodal
  reasoning — the offline deterministic path needs none.

### Install & test
```bash
git clone https://github.com/MatMridul/AmazonVigil.git
cd AmazonVigil
uv sync --extra dev        # dev group carries pytest + pytest-asyncio
uv run pytest -q           # full suite, deterministic, offline (150 passing)
```
*(Runtime-only install is `uv sync`; the `--extra dev` group adds the test tools.)*

### Run the scenario engine (no deps beyond uv sync)
```bash
uv run python -m src.simulator.scenario_runner --scenario 06   # one scenario
uv run python -m src.simulator.scenario_runner --all           # all 10 baselines
```

### Run the Web Console (three hero surfaces)
```bash
uv run python -m src.web.server            # http://127.0.0.1:5176
```
Then open the console and use the Surface Switcher:
* **Mission Control** (`/`) — the brain correlating the mesh (Φ-vector, Bedrock attribution, Fire TV deterrence)
* **Nightstand Phone** (`/phone.html`) — the human crisis surface: staged CAD manifest, 10s countdown, PIN-disarm
* **Fire TV** (`/firetv.html`) — the 10-foot deterrence display

### Run the Alexa+ MCP server (primary track)
```bash
uv run python -m src.server                # Streamable HTTP MCP endpoint
```
Link the endpoint to an Alexa+ developer account to drive it from a real Echo.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
