# Vigil+

**Autonomous Multi-Device Perimeter Defense & Deterrence Mesh**  
*Built for the Amazon Developer Hackathon 2026 (Alexa+ Track, AWS Builder Challenge, Open Source Challenge)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Spec 2025-11-25](https://img.shields.io/badge/MCP-2025--11--25-green.svg)](https://modelcontextprotocol.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude%203.5-orange.svg)](https://aws.amazon.com/bedrock/)

---

## What Vigil+ Is

Vigil+ is an autonomous, 100% software home defense and deterrence mesh that connects the front door, the living room, personal wearables, and the cloud into an ambient, coordinated security response.

Instead of sending passive smartphone notifications that get ignored when residents are asleep, Vigil+:
1. **Perimeter Awareness (Ring):** Ingests motion, WebRTC camera video, and audio; runs client-side `VideoProcessor` plugins to detect lens tampering and spray-paint sabotage.
2. **Human Bio-Grounding (Bee Wearable):** Assesses whether the resident is awake or in deep sleep via conversation recency (`bee now`) and accelerometer stillness.
3. **Ambient Incident Commander (Alexa+ via FastMCP):** Acts as the central coordinator, orchestrating low-latency local edge reflexes (<50ms) and cognitive multimodal threat analysis via **Amazon Bedrock (Claude 3.5 Sonnet)**.
4. **Active Psychological Deterrence (Fire TV & Echo Boot-Bridge):** Deploys the "Home Alone" bluff—using hallway Echo speakers for instant 150ms footstep audio while Fire TV wakes over HDMI-CEC to blast high-decibel barking dogs, dialogue, and movement shadows before an intruder breaches the entryway.
5. **Fail-Safe Digital CAD Dispatch:** Stages structured, NENA-compliant Digital Computer-Aided Dispatch (CAD) manifests (RapidSOS format) with cryptographic hashes for 1-tap resident transmission.

---

## Key Documentation

* 📖 **[Master System Specification](docs/SPEC.md)** — Mathematical sensor triad formulation, the 10-Scenario baseline matrix, and the 14-Edge-Case Degraded Mode Protocol (DMP).
* 📋 **[Implementation Tasks & Roadmap](tasks.md)** — Phase-by-phase execution plan for autonomous agents and developers.
* ☁️ **[AWS Integration Guide](docs/AWS_INTEGRATION.md)** — Amazon Bedrock and Kiro Crew architecture for the AWS Builder Challenge.
* 🛠️ **[Developer Friction Log](docs/FRICTION_LOG.md)** — Tooling telemetry and feedback for the Amazon developer ecosystem (+10% judging bonus).

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

### Prerequisites
* Python 3.11+
* `uv` package manager (`pip install uv`)
* AWS credentials with Amazon Bedrock access (`anthropic.claude-3-5-sonnet-20241022`)

### Installation & Test Suite
```bash
# Clone the repository
git clone https://github.com/your-username/vigil.git
cd vigil

# Install dependencies with uv
uv sync

# Run the full 10-Scenario and 14-Edge-Case resilience test suite
uv run pytest tests/ -v
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
