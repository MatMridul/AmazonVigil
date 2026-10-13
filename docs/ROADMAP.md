# Project Vigil+: Roadmap, Engineering Standards & Hackathon Submission Blueprint

> **Reference Specification:** [`SPEC.md`](../SPEC.md) • [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md) • [`UI_UX_SPECIFICATION.md`](UI_UX_SPECIFICATION.md)  
> **Target:** 1st Place Alexa+ Track ($25,000) + AWS Builder ($5,000) + Open Source ($5,000) = **$35,000 Cash + $20,000 AWS Credits** (+10% Friction Log Bonus)  
> **Document Status:** Active Engineering Roadmap & Submission Architecture  

---

## 1. Development Cycle & SemVer Milestones

Vigil+ follows strict **Semantic Versioning 2.0.0** (`v0.1.0` $\to$ `v1.0.0`). Every milestone is gated by automated CI checks, zero-hardware simulator reproducibility, and task phases defined in [`tasks.md`](../tasks.md):

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  v0.1.0-α    ├────►│  v0.2.0-α    ├────►│  v0.3.0-β    ├────►│  v0.4.0-β    ├────►│   v1.0.0     │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │                    │                    │
  Phases 1 & 2         Phases 3 & 8.1       Phases 4 & 5         Phases 6 & 7         Phases 8 & 9
  Core Types,          FSM Engine,          Adapters &           Bedrock AI,          100% Tests,
  Φ Ingestion,         DMP Degradation      FastMCP HTTP,        Mission Control      Friction Log,
  Math Engine          Rule Tables          Boot-Bridge          Web & TV UI          180s Video
```

### Milestone Breakdown

* **`v0.1.0-alpha` — Ingestion, Telemetry Types & Sensor Integrity Engine**
  * Strict Pydantic models for $\vec{\Phi}$, `PerimeterTelemetry`, `HostState`, and `CadManifest` (`src/core/types.py`).
  * Mathematical $\vec{\Phi}$ integrity calculation based on variance, saturation, SNR, and optical occlusion.
  * Degraded Mode Protocol (DMP) failure handlers (A1 through E2).
  * Automated unit tests for integrity calculation (`pytest tests/test_integrity.py`).

* **`v0.2.0-alpha` — Deterministic State Machine & Edge Rule Engine**
  * Finite State Machine transitioning through strictly bounded states (`L0_SAFE`, `L1_AMBIGUOUS`, `L2_SUSPICIOUS`, `L3_CRITICAL`).
  * Four operational modes (Daytime Ambient, Night Sentry, Vacation/Away, Silent Duress).
  * Zero-latency local fallback rule engine executing physical reflexes in $<50\text{ms}$ during network unobservability.
  * Canned scenario definitions (`src/simulator/canned_scenarios.json`) encoding Scenarios 01 through 10.

* **`v0.3.0-beta` — Multi-Device Hardware Adapters & FastMCP Core**
  * `RingAdapter`: WebRTC/webhook ingestion + client-side `VideoProcessor` plugin for lens occlusion detection + `AudioDuplexMute` flag to prevent audio feedback.
  * `BeeAdapter`: Temporal context parser via `bee now --json` (>1h silence) + accelerometer immobility to infer sleep state ($H_{\text{asleep}}$ vs $H_{\text{awake}}$).
  * `FireTVAdapter`: W3C/Android TV deterrent player; offline bundled `.aac` audio assets; deterrence activation strictly gated to $H_{\text{asleep}}$ and $H_{\text{away}}$ (non-disruptive PIP toast when $H_{\text{awake}}$).
  * `AlexaAdapter`: Bedroom Echo whispered SSML synthesizer + hallway Echo Boot-Bridge (150ms footsteps bridging HDMI-CEC latency).
  * FastMCP Server over Streamable HTTP (`2025-11-25+`) with `idempotency_token` support.

* **`v0.4.0-beta` — AWS Bedrock Cognitive Reasoner & Mission Control UI**
  * Bedrock Claude 3.5 Sonnet multimodal analyzer (`anthropic.claude-3-5-sonnet-20241022`) with structured JSON schema enforcement, JSON repair fallback, and 30s token throttling valve.
  * Web-based Mission Control Console (`src/web/`) built with React + Vite + Tailwind CSS adhering to Architectural Ambient tokens.
  * Interactive components: `SanctuaryCapsule`, `PerimeterBoundaryBadge`, `HardwareMeshStatus`, `ActiveProtectorCard`, `CadDispatchModal`.
  * Fire TV 10-foot HUD with remote D-pad focus styles and 1-click `Back` dismiss.

* **`v1.0.0-rc.1` — Simulator Freeze & Test Suite Verification**
  * 100% automated test pass rate (`pytest tests/`) across all 10 baseline scenarios and 14 degraded modes in $<5\text{s}$.
  * Zero physical hardware dependencies for test execution.
  * CLI simulation runner (`uv run vigil simulate --scenario 02`).

* **`v1.0.0` — Final Contest Release Freeze**
  * Code freeze on `main` branch with clean git commit history.
  * Completed Developer Friction Log ([`docs/FRICTION_LOG.md`](FRICTION_LOG.md)) claiming the +10% bonus.
  * AWS Builder Challenge Dossier ([`docs/AWS_INTEGRATION.md`](AWS_INTEGRATION.md)).
  * 180-second cinematic demo video recorded and uploaded.

---

## 2. Definition of Done (DoD) Hierarchy

Vigil+ enforces a **Three-Tiered Definition of Done** to eliminate AI hallucination, broken edge cases, and incomplete features.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THREE-TIERED DEFINITION OF DONE                      │
├────────────────────┬───────────────────────────────────────────────────┤
│ Tier 1: Task / PR  │ • Zero mypy/ruff/tsc/eslint errors                │
│                    │ • Zero AI slop / TODO placeholders                │
│                    │ • Traceable to SPEC.md mathematical definitions   │
│                    │ • Deterministic unit tests (fixed pseudo-random)  │
│                    │ • Zero secret leaks (.env.example only)           │
├────────────────────┼───────────────────────────────────────────────────┤
│ Tier 2: Subsystem  │ • FastMCP: Streamable HTTP + idempotency tokens   │
│                    │ • Ring: VideoProcessor plugin + duplex mic mute   │
│                    │ • Bee: Sleep inferred from speech silence + motion│
│                    │ • Fire TV: Gated to Hasleep/Haway + 150ms bridge  │
│                    │ • Bedrock: JSON repair parser + 30s rate valve    │
├────────────────────┼───────────────────────────────────────────────────┤
│ Tier 3: Release    │ • uv run vigil simulate runs all 10 scenarios     │
│                    │ • 100% test pass rate in <5 seconds               │
│                    │ • Zero phantom deadbolts / zero 911 robocalls     │
└────────────────────┴───────────────────────────────────────────────────┘
```

### 2.1 Tier 1: Task & Pull Request DoD (Engineers & Kiro Pro)
A task or PR is **ONLY marked complete** when:
1. **Zero Type Errors & Lints:** Python passes `mypy --strict` and `ruff check`; frontend passes `tsc --noEmit` and `eslint`.
2. **Zero AI Slop / Placeholders:** Zero `// TODO`, `# FIXME`, or placeholder pass-through functions. Every branch is fully implemented.
3. **Spec Traceability:** Every function or class links directly to its mathematical definition or schema in [`SPEC.md`](../SPEC.md) or [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md).
4. **Deterministic Unit Tests:** Accompanied by unit tests asserting state transitions against fixed pseudo-random seeds.
5. **No Secret Leaks:** Zero hardcoded API keys, tokens, or AWS credentials (`.env.example` strictly used).

### 2.2 Tier 2: Subsystem & Component DoD
* **FastMCP Server (Alexa+ Core):**
  * Complies with MCP Spec `2025-11-25+` over Streamable HTTP.
  * Verified via `@modelcontextprotocol/inspector`.
  * Every tool call accepts an `idempotency_token` and `incident_id` to prevent stuttered duplicate execution.
  * Exposes conversational tools: `explain_incident_reasoning(incident_id)` and `set_mesh_guard_profile(mode, duration)`.
* **Ring Adapter & Plugin:**
  * Client-side `VideoProcessor` plugin detects lens occlusion ($\Phi_V=0$) and triggers acoustic-motion fallback.
  * Ring speaker bluff includes `AudioDuplexMute` flag to prevent Ring mic from hearing its own audio.
  * Burst snapshot mode available to preserve battery-powered doorbells.
* **Fire TV Adapter:**
  * TV acoustic bluff strictly gated to $H_{\text{asleep}}$ and $H_{\text{away}}$. When $H_{\text{awake}}$, displays *only* a non-disruptive PIP toast with 1-click remote `Back` dismissal.
  * Bundled offline `.aac` audio assets verified playable without cloud internet.
* **Bee Bio-Grounding:**
  * Derives sleep state purely from conversational recency (`bee now --json` >1h silence) + accelerometer immobility.
  * Routes tactical wake to bedside Echo whispered SSML and phone Nightstand Alert.
* **AWS Bedrock Reasoner:**
  * Uses `anthropic.claude-3-5-sonnet-20241022` via `boto3`.
  * Structured JSON schema enforcement with automatic markdown strip & repair fallback.
  * 30-second token throttling cooldown to prevent API flooding.

### 2.3 Tier 3: Release Level DoD (`v1.0.0` Hackathon Candidate)
1. **Zero-Hardware Reproducibility:** A judge with zero physical Amazon devices can run:
   ```bash
   uv run vigil simulate --scenario 02
   ```
   and watch the entire multi-device mesh (Ring event $\to$ Bedrock reasoning $\to$ Echo boot-bridge $\to$ Fire TV deterrent $\to$ CAD staging) execute in terminal and web UI.
2. **100% Test Pass Rate:** `pytest tests/` passes all 24 test vectors (10 baseline + 14 degradation) in under 5 seconds.
3. **Audit Integrity:** Zero phantom deadbolts, zero illegal robocalls, zero fake CLI haptics anywhere in the tree.

---

## 3. The Final Hackathon Submission Package

Our final submission on [Devpost](https://amazonappdev2026.devpost.com/) (before Oct 23, 2026 @ 12:00 PM PDT) consists of **Six Concrete Deliverables**:

```
                              THE FINAL SUBMISSION PACKAGE
 ┌───────────────────────────────────────┬───────────────────────────────────────┐
 │ 1. Public GitHub Repository (MIT)     │ 2. 180-Second Cinematic Demo Video    │
 │    • Tagged v1.0.0, Zero-Hardware Sim │    • 1080p/4K YouTube/Vimeo Walkthrough│
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ 3. Devpost Project Dossier & Narrative│ 4. AWS Builder Challenge Architecture │
 │    • Problem, Architecture, Impact    │    • Bedrock Claude 3.5 Sonnet Specs  │
 ├───────────────────────────────────────┼───────────────────────────────────────┤
 │ 5. Developer Friction Log (+10% Bonus)│ 6. Interactive Web & TV Mission Ctrl  │
 │    • High-value upstream PR patches   │    • Architectural Ambient UI Studio  │
 └───────────────────────────────────────┴───────────────────────────────────────┘
```

### Deliverable 1: Public GitHub Repository (`MatMridul/AmazonVigil`)
* **Branch & Tag:** Clean `main` branch tagged `v1.0.0`.
* **License:** OSI-approved **MIT License** for the **Open Source Challenge ($5,000)**.
* **Documentation Suite:** [`README.md`](../README.md), [`SPEC.md`](../SPEC.md), [`SYSTEM_DESIGN.md`](SYSTEM_DESIGN.md), [`UI_UX_SPECIFICATION.md`](UI_UX_SPECIFICATION.md), [`RESOURCE_SCOPING.md`](RESOURCE_SCOPING.md), [`ROADMAP.md`](ROADMAP.md).
* **One-Line Quickstart:** Clear instructions for judges to run the simulator locally in under 60 seconds.

### Deliverable 2: 180-Second Demo Video (Strictly $\le 3$ Minutes)
* **Hosting:** Public / Unlisted YouTube or Vimeo in 1080p/60fps or 4K with clear English voiceover and closed captions.
* **Strict Timeline Breakdown:**
  * **0:00 – 0:35 (The Problem & The Lie):** Smart homes today spam push notifications, ring bells, and claim to lock phantom deadbolts while residents sleep through invasions. Software cannot stop a crowbar—only psychological deterrence can.
  * **0:35 – 1:10 (The 4-Device Solution):** Introduce Vigil+ mesh: Ring perimeter, Bee bio-grounding, Alexa+ FastMCP incident commander, Echo Boot-Bridge (150ms footsteps), and Fire TV "Home Alone" bluff.
  * **1:10 – 2:05 (Live Multi-Device Execution — Scenario 02):** Prowler approaches at 3 AM. System 1 edge reflex mutes porch chime $\to$ bedroom Echo delivers low-frequency whisper $\to$ hallway Echo plays 150ms footsteps $\to$ Fire TV blasts barking German Shepherd $\to$ Bedrock Claude 3.5 Sonnet analyzes camera still $\to$ 911 CAD manifest staged on resident lock screen.
  * **2:05 – 2:35 (Adversarial Stress Test):** Prowler spray-paints the Ring camera lens ($\Phi_V \to 0.0$). VideoProcessor plugin flags occlusion; mesh automatically shifts to Acoustic-Motion Triangulation without blind-spot failure.
  * **2:35 – 3:00 (AWS Builder & Open Source Impact):** Showcase Bedrock token budgeting, Kiro Pro development artifacts, and open-source contribution to the Amazon developer ecosystem.

### Deliverable 3: Devpost Written Narrative
* **Title:** **Vigil+: Multi-Device Ambient Defense & Psychological Deterrence Mesh**
* **Tagline:** *Transforming off-the-shelf Ring, Alexa+, Fire TV, Bee Wearables, and AWS Bedrock into an autonomous residential perimeter defense system.*
* **Tracks Targeted:**
  1. **Alexa+ Track ($25,000 First Place):** Leading use of MCP Streamable HTTP and multi-device agentic coordination.
  2. **AWS Builder Challenge ($5,000):** Multimodal Bedrock Claude 3.5 Sonnet cognitive reasoning and structured CAD generation.
  3. **Open Source Challenge ($5,000):** Modular, permissible MIT codebase with complete simulator suite.
  4. **+10% Judging Bonus:** Submission of comprehensive developer friction log.

### Deliverable 4: AWS Builder Challenge Dossier ([`docs/AWS_INTEGRATION.md`](AWS_INTEGRATION.md))
* Detailed architecture diagram showing AWS Bedrock invocation lifecycle via `boto3`.
* Pydantic schema validation and prompt engineering techniques.
* Cloud token budgeting (65% reduction via WebP downscaling) and least-privilege IAM policies.
* Documentation of Kiro Pro's role in spec-driven autonomous implementation.

### Deliverable 5: Official Developer Friction Log ([`docs/FRICTION_LOG.md`](FRICTION_LOG.md))
* A high-value technical critique that Amazon’s Developer Relations team can directly use:
  1. **Ring API:** Limitations in client-side WebRTC frame intercept (`VideoProcessor` plugin interface) and lack of programmatic two-way audio mute hooks.
  2. **Fire TV Multi-TV Sample:** Vega vs Android TV build discrepancies and overlay rendering restrictions under Widevine L1 DRM.
  3. **FastMCP Streamable HTTP:** Edge connection keep-alive behavior and agentic session recovery.
  4. **Bee CLI:** Structured JSON parsing edge cases in `bee now --json`.
  5. Actionable PR recommendations and code snippets for Amazon upstream maintainers.

### Deliverable 6: Interactive Mission Control & TV HUD
* Single-page web console matching the **Architectural Ambient** design system ([`docs/UI_UX_SPECIFICATION.md`](UI_UX_SPECIFICATION.md)):
  * `SanctuaryCapsule` (Perimeter status, `PerimeterBoundaryBadge`, resident count).
  * `HardwareMeshStatus` (real-time $\vec{\Phi}$ sensor health gauges).
  * `CadDispatchModal` (cryptographic NENA incident manifest with SHA-256 hash).
  * Interactive scenario switcher letting judges simulate Scenarios 01 through 10 with a single click.

---

## 4. Testing Standards: Hardware vs. Zero-Hardware Simulator

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

## 5. AWS Cloud Planning (AWS Builder Challenge)

### 5.1 Architectural Integration
* **Amazon Bedrock:**
  * Primary Model: `anthropic.claude-3-5-sonnet-20241022` for multi-modal visual reasoning and structured JSON threat extraction.
  * Fallback Model: `anthropic.claude-3-5-haiku-20241022` for low-latency acoustic sentiment parsing.
* **Kiro Crew:**
  * Used as the autonomous engineering environment during the hackathon window, satisfying the development-tool criteria for the AWS Builder track.
* **Identity & Access Management (IAM):**
  * Minimal IAM policy granting `bedrock:InvokeModel` strictly scoped to the required Claude foundation models.

### 5.2 Cost & Budget Optimization
* **Token Efficiency:** Ring snapshots are downscaled to $1024 \times 768$ and compressed with WebP before base64 encoding, reducing input tokens by $65\%$.
* **Rate-Limiting Valve:** Enforces maximum 1 Bedrock call per 30 seconds per zone to prevent API flooding and token exhaustion.
* **Estimated Evaluation Cost:** $< \$3.50$ total across 500+ test runs and live demonstrations (easily covered by free tier or promotional credits).
