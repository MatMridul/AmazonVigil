# Project Vigil+: Roadmap, Engineering Standards & AWS Plan

> **Reference Specification:** [`SPEC.md`](../SPEC.md) • [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md)  
> **Target:** 1st Place Alexa+ Track ($25,000) + AWS Builder ($5,000) + Open Source ($5,000)  
> **Document Status:** Active Engineering Roadmap  

---

## 1. Development Cycle & SemVer Milestones

To ensure enterprise-grade reliability, Vigil+ follows strict Semantic Versioning (`v0.1.0` $\to$ `v1.0.0`):

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐      ┌─────────┐
│ v0.1.0  ├─────►│ v0.2.0  ├─────►│ v0.3.0  ├─────►│ v0.4.0  ├─────►│ v0.5.0  ├─────►│ v1.0.0  │
└────┬────┘      └────┬────┘      └────┬────┘      └────┬────┘      └────┬────┘      └────┬────┘
     │                │                │                │                │                │
 Ingest & Φ       FSM & Rules      Adapters        Bedrock & CAD    FastMCP & UI      RELEASE
```

### Milestone Breakdown

* **`v0.1.0` — Ingestion & Sensor Integrity Engine**
  * Pydantic telemetry models (`PerimeterEvent`, `SensorIntegrityVector`, `HostState`).
  * Mathematical $\vec{\Phi}$ calculation based on variance, saturation, and signal-to-noise ratio.
  * Unit test suite for sensor health checks.

* **`v0.2.0` — Deterministic State Machine & Local Rule Engine**
  * Finite State Machine (`L0_SAFE`, `L1_AMBIGUOUS`, `L2_SUSPICIOUS`, `L3_CRITICAL`).
  * Operational mode switching (Daytime Ambient, Night Sentry, Away, Duress).
  * Zero-latency local fallback rule engine for edge execution during network latency.

* **`v0.3.0` — Multi-Device Hardware Adapters & Simulators**
  * `RingAdapter`: Ingesting webhooks and WebRTC streams (using `references/ring-api-helloworld`).
  * `BeeAdapter`: Polling sleep and biometric state via local `bee-cli` / Bee MCP (using `references/bee-skill`).
  * `FireTVAdapter`: Launching W3C deterrence audio/video on Vega TV / Web player (using `references/react-native-multi-tv-app-sample`).

* **`v0.4.0` — AWS Bedrock Multimodal & CAD Dispatcher**
  * AWS SDK integration calling `anthropic.claude-3-5-sonnet-20241022`.
  * Multi-modal prompt evaluating Ring camera base64 images + audio transcripts with structured JSON schemas.
  * Structured 911 CAD manifest generator with cryptographic hash for chain-of-custody.

* **`v0.5.0` — FastMCP Server & Operator Mission Control**
  * FastMCP server running over Streamable HTTP (spec `2025-11-25+`).
  * Web-based simulated Alexa+ agent console for live judge interaction.
  * Real-time telemetry dashboard (showing device mesh health, incident timeline, and deterrence status).

* **`v1.0.0` — Contest Freeze & Final Polish**
  * Automated test runner passing 100% of the 10 baseline scenarios and 14 failure adaptations.
  * Verified physical hardware pluggability.
  * Completed Developer Friction Log (`docs/FRICTION_LOG.md`) claiming the **10% judging bonus**.
  * 2.5-minute demo video recorded and uploaded to YouTube/Vimeo.

---

## 2. Definition of Done (DoD) & Definition of Success (DoS)

### 2.1 Definition of Done (DoD) for Any Pull Request / Module
1. **Zero Type Errors:** Strict typing with Python `mypy` or TypeScript `tsc` (zero `any`).
2. **Comprehensive Test Coverage:** $\ge 90\%$ test coverage on all state machine and degradation logic.
3. **Deterministic Simulation:** All unit tests execute against fixed pseudo-random seeds with zero flaky network dependencies.
4. **Zero AI Slop:** No placeholder comments (`// TODO: implement later`), no unused imports, no dummy hardcoded mocks that break in live mode.
5. **Architectural Traceability:** Code changes must reference specific sections in `SPEC.md` or `SYSTEM_DESIGN.md`.

### 2.2 Definition of Success (DoS) for the Hackathon
1. **Rule Compliance:** Meets all Devpost requirements:
   * Demo video strictly under 3 minutes (in English, public).
   * GitHub repository public with MIT license (or private with Amazon reviewer permissions).
   * Verified code calls to Alexa+ MCP, Ring APIs, and Bee CLI.
2. **Zero Failures under Adversarial Stress:** System passes all 14 degradation edge cases without crashing or throwing unhandled exceptions.
3. **Flawless Multi-Device Story:** Live video demonstrates all 4 endpoints cooperating in under 180 seconds.
4. **Judging Bonus Earned:** Structured friction log submitted with actionable feedback for the Amazon engineering team.

---

## 3. Testing Standards: Hardware vs. Simulator

```
┌─────────────────────────────────┐     ┌─────────────────────────────────┐
│     PHYSICAL HARDWARE SUITE     │     │   DETERMINISTIC SIMULATOR SUITE │
├─────────────────────────────────┤     ├─────────────────────────────────┤
│ • Ring Video Doorbell Pro 2     │     │ • `canned_scenarios.json`       │
│ • Bee AI Wearable / Apple Watch │     │ • Synthetic Biometric Mock      │
│ • Fire TV Stick 4K / Omni TV    │     │ • Web-based W3C Media Player    │
│ • Amazon Echo Dot (5th Gen)     │     │ • Local FastMCP Inspector       │
└─────────────────────────────────┘     └─────────────────────────────────┘
```

* **Simulator Testing (`pytest tests/`):**
  * Runs in CI/CD without requiring external credentials or physical devices.
  * Simulates sensor telemetry down to the millisecond.
  * Judges can run `uv run pytest tests/` and watch all scenarios pass in $<5\text{ seconds}$.
* **Hardware Plug-and-Play Verification:**
  * Setting `VIGIL_MODE=live` connects directly to real LAN devices and cloud endpoints.
  * Live verification scripts located in `scripts/test_live_ring.py`, `scripts/test_live_bee.py`, `scripts/test_live_firetv.py`.

---

## 4. AWS Cloud Planning (AWS Builder Challenge)

### 4.1 Architectural Integration
* **Amazon Bedrock:**
  * Primary Model: `anthropic.claude-3-5-sonnet-20241022` for multi-modal visual reasoning and structured JSON threat extraction.
  * Fallback Model: `anthropic.claude-3-5-haiku-20241022` for low-latency acoustic sentiment parsing.
* **Kiro Crew:**
  * Used as the autonomous engineering environment during the hackathon window, satisfying the development-tool criteria for the AWS Builder track.
* **Identity & Access Management (IAM):**
  * Minimal IAM policy granting `bedrock:InvokeModel` strictly scoped to the required Claude foundation models.

### 4.2 Cost & Budget Optimization
* **Token Efficiency:** Ring snapshots are downscaled to $1024 \times 768$ and compressed with WebP before base64 encoding, reducing input tokens by $65\%$.
* **Estimated Evaluation Cost:** $< \$3.50$ total across 500+ test runs and live demonstrations (easily covered by free tier or promotional credits).
