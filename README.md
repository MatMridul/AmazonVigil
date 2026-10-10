# Vigil+

**Autonomous Multi-Device Perimeter Defense & Deterrence Mesh**  
*Built for the Amazon Developer Hackathon 2026 (Alexa+ Track, AWS Builder Challenge, Open Source Challenge)*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP Spec 2025-11-25](https://img.shields.io/badge/MCP-2025--11--25-green.svg)](https://modelcontextprotocol.io/)
[![AWS Bedrock](https://img.shields.io/badge/AWS-Bedrock%20Claude%203.5-orange.svg)](https://aws.amazon.com/bedrock/)

---

## What Vigil+ Is

Vigil+ is a multi-device home defense and deterrence mesh that connects the front door, the living room, personal wearables, and the cloud into an ambient, coordinated security response.

Instead of sending passive smartphone notifications that get ignored when residents are asleep, Vigil+:
1. **Perimeter Awareness (Ring):** Analyzes motion, camera imagery, and outdoor audio.
2. **Human Bio-Grounding (Bee Wearable):** Assesses whether the resident is awake, in deep sleep, away, or under acute duress.
3. **Ambient Incident Commander (Alexa+ via FastMCP):** Evaluates multi-modal threat intent with **Amazon Bedrock (Claude 3.5 Sonnet)**.
4. **Active Environmental Deterrence (Fire TV):** Deploys acoustic and visual deception (simulated occupancy, barking dogs, dynamic lights) before an intruder attempts breach.
5. **Fail-Safe Emergency Dispatch:** Prepares structured, verified 911 Computer-Aided Dispatch (CAD) evidentiary manifests when critical threats occur while the resident is vulnerable.

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
│       Perimeter Ingest (Ring)   │     │    Bio-Context (Bee Wearable)   │
│       • PIR Motion Detection    │     │    • Sleep / Circadian State    │
│       • Camera Pose & Face      │     │    • Heart Rate / Distress      │
│       • Ambient Audio Stream    │     │    • Haptic Wake-Up Actuator    │
└────────────────┬────────────────┘     └────────────────┬────────────────┘
                 │                                       │
                 └───────────────────┬───────────────────┘
                                     ▼
                   ┌───────────────────────────────────┐
                   │    Alexa+ Core FastMCP Server     │
                   │    • Sensor Integrity Auditor (Φ) │
                   │    • Bedrock Multi-Modal Scorer   │
                   │    • Deterministic State Machine  │
                   └─────────────────┬─────────────────┘
                                     │
         ┌───────────────────────────┼───────────────────────────┐
         ▼                           ▼                           ▼
  [Level 0: Safe]             [Level 1: Ambiguous]        [Level 2/3: Critical]
  • Silent Door Unlock        • Alexa Voice Check         • Bee Haptic Pulse (Wake)
  • Suppressed Alerts         • Respect Sleep State       • Fire TV Deterrence ("Home Alone")
                              • Fire TV PIP Camera Feed   • Structured 911 CAD Dispatch
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
