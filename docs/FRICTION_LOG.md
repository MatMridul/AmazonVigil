# Project Vigil+: Official Developer Friction Log

> **Contest Category:** Amazon Developer Hackathon 2026 (Build, Ship, Shape)  
> **Incentive Target:** +10% Developer Friction Log Judging Bonus  
> **Status:** Active Engineering Telemetry Log  
> **Maintained By:** Vigil+ Systems Engineering Team  

---

## Executive Summary

This document captures actionable engineering feedback, SDK edge cases, and unexpected architectural barriers encountered while developing **Project Vigil+** across five Amazon ecosystem technologies:
1. **Ring Developer API & Starter** (`AmazonAppDev/ring-api-helloworld`)
2. **Fire TV Multi-TV Sample** (`AmazonAppDev/react-native-multi-tv-app-sample`)
3. **Model Context Protocol (MCP)** Spec `2025-11-25+` over Streamable HTTP
4. **Bee Wearable CLI & Ecosystem** (`docs.bee.computer` / `bee-skill`)
5. **Amazon Devices Builder Tools (ADBT)** MCP Server (`@amazon-devices/amazon-devices-buildertools-mcp`)

---

## Friction Matrix

```
┌────┬──────────────────┬──────────────────────────────────────────┬──────────┬────────────────────────┐
│ ID │ Technology       │ Issue Summary                            │ Severity │ Status                 │
├────┼──────────────────┼──────────────────────────────────────────┼──────────┼────────────────────────┤
│ F1 │ Ring WebRTC API  │ Lack of Audio Duplex Muting on Intercom  │ High     │ Solved via Mesh Gate   │
│ F2 │ Ring Video Ingest│ Client-Side Tamper Frame Intercept Hook  │ Medium   │ Solved via Custom Plugin│
│ F3 │ Fire TV OS / DRM │ Overlay Suppression over Widevine L1     │ High     │ Solved via PIP & Toasts│
│ F4 │ Fire TV HDMI-CEC │ 3-Second Cold Standby Power-On Latency   │ High     │ Solved via Boot-Bridge │
│ F5 │ FastMCP HTTP     │ Idempotency Token Omission on Re-trials  │ Medium   │ Solved via Cache Lock  │
│ F6 │ Bee CLI Context  │ Temporal Voice Recency Granularity       │ Medium   │ Solved via Delta Parser│
└────┴──────────────────┴──────────────────────────────────────────┴──────────┴────────────────────────┘
```

---

## Detailed Friction Reports & Upstream Recommendations

### F1: Acoustic Duplexing Feedback Loop on Ring Doorbell Two-Way Intercom

* **Component:** Ring WebRTC Audio Uplink (`AmazonAppDev/ring-api-helloworld`).
* **Expected Behavior:** An application sending simulated speech or deterrent audio to the Ring doorbell speaker should be able to flag outbound audio so the Ring microphone does not treat it as an external ambient sound.
* **Actual Blocker / Edge Case:** Because the Ring microphone and speaker are co-located 1.5 inches apart on the doorbell chassis, blasting deterrent audio (e.g., *"Hold on, coming to the door right now!"* + footsteps) immediately loops back into the microphone. Acoustic analysis engines classify this playback as an escalating intruder breach, creating an acoustic feedback loop.
* **Severity:** **High (Architecture Flaw if Unhandled).**
* **Vigil+ Workaround:** Implemented an internal `AudioDuplexMute` flag in `RingAdapter`: whenever the deterrent speech bluff fires, inbound acoustic ingest ($\Phi_A$) is temporarily gated and ignored for the duration of the audio playback plus 500ms acoustic dampening.
* **Upstream Recommendation for Amazon Ring Team:**
  > *Expose an `is_self_echo: boolean` metadata tag on the WebRTC inbound audio frame stream, or provide an API parameter `suppress_mic_feedback: true` during two-way audio session initialization.*

---

### F2: Lack of Lens Tamper / Occlusion Callbacks in Ring Ingest

* **Component:** Ring API Webhooks & SSE Event Stream.
* **Expected Behavior:** Official Ring webhooks notify when motion is detected (`motion_detected`) or doorbell rings (`ding`). It would be expected to receive camera health alerts when a camera is physically obscured (e.g. spray paint, tape, or laser wash).
* **Actual Blocker:** Ring treats an obscured camera as normal nighttime darkness or silent video; no optical integrity failure is signaled over the standard webhook interface.
* **Severity:** **Medium.**
* **Vigil+ Workaround:** Built a custom client-side `VideoProcessor` plugin (`src/adapters/video_processors/optical_auditor.py`) hooking into the `references/ring-api-helloworld/lib/video-processors/` interface. It analyzes frame saturation, variance, and optical flow locally to derive the Optical Integrity factor ($\Phi_V \in [0.0, 1.0]$) and triggers Degraded Mode Protocol (A1–A4).
* **Upstream Recommendation for Amazon Ring Team:**
  > *Incorporate an on-device edge tamper heuristic into the Ring firmware / API that emits a `camera_tamper_detected` webhook event when luminance variance drops to zero while PIR motion is active.*

---

### F3: Fire TV / Android TV Video Overlay Blocking over Widevine L1 Streams

* **Component:** Fire TV React Native Sample (`AmazonAppDev/react-native-multi-tv-app-sample`).
* **Expected Behavior:** Displaying a security camera HUD overlay on top of whatever media is playing on Fire TV.
* **Actual Blocker:** Android TV and Fire OS hardware DRM security layers (Widevine L1) strictly prevent third-party applications from rendering floating web views or custom React Native modals on top of active, protected video surfaces (e.g., Prime Video, Netflix). The overlay either flickers or renders as a black rectangle.
* **Severity:** **High.**
* **Vigil+ Workaround:** Architected a **Two-Tiered 10-Foot UI Contract**:
  1. For non-critical couriers ($L0/L1$), use native Android System Heads-Up Notifications (`Toast` / PIP API), which Fire OS natively composites over video surfaces.
  2. For critical perimeter breaches ($L2/L3$), explicitly fire a **Foreground Activity Launch Intent** that takes over the screen and pauses background playback cleanly.
* **Upstream Recommendation for Amazon Fire TV Team:**
  > *Provide an official Fire TV `SecurityOverlay` API or system-level PIP template in the Multi-TV starter kit that allows authorized emergency smart-home apps to draw trusted feeds over DRM video without crashing.*

---

### F4: Fire TV HDMI-CEC Standby Wake-Up Latency (3–4 Seconds)

* **Component:** Fire OS TV Standby & HDMI-CEC Handshake.
* **Expected Behavior:** When an intruder trips a nighttime perimeter alarm, triggering the TV to power on and blast deterrent audio should occur in $<500\text{ms}$.
* **Actual Blocker:** When an Amazon Fire TV Stick or Smart TV is in deep low-power standby, waking the display panel via HDMI-CEC takes between 3,000ms and 4,200ms. An intruder walking up to a porch can cross the perimeter before the TV's speakers emit sound.
* **Severity:** **High.**
* **Vigil+ Workaround:** Architected the **Hallway Echo Boot-Bridge**:
  * An Amazon Echo Dot located in the entryway/hallway responds to local WebSocket commands in **$<150\text{ms}$**, immediately emitting low-latency footstep audio.
  * This covers the 3.5-second HDMI-CEC negotiation window until Fire TV's high-decibel living room speakers take over.
* **Upstream Recommendation for Amazon Fire TV & Alexa Teams:**
  > *Document HDMI-CEC standby latencies in the developer documentation for home automation developers, and provide a unified `Alexa.SmartHome.WakeAndPlay` API that coordinates near-field Echo speakers with far-field Fire TV displays.*

---

### F5: Model Context Protocol (MCP) Streamable HTTP Idempotency Deficit

* **Component:** MCP Specification (`2025-11-25+`) over Streamable HTTP.
* **Expected Behavior:** When an Alexa+ agent invokes a tool (such as `trigger_firetv_deterrence`), network latency or conversational stutter might trigger an agent retry.
* **Actual Blocker:** If the MCP tool lacks an explicit idempotency identifier, a retried tool call results in duplicate audio playback commands or conflicting state transitions.
* **Severity:** **Medium.**
* **Vigil+ Workaround:** All Vigil+ FastMCP tool definitions enforce an explicit `incident_id: str` and `idempotency_token: str` parameter. The server checks an internal cache; repeated invocations within a 15-second window return cached acknowledgments without re-triggering physical actuators.
* **Upstream Recommendation for MCP & Alexa+ Working Group:**
  > *Adopt standard HTTP `Idempotency-Key` headers or native idempotency tokens in the Model Context Protocol tool invocation schema.*

---

### F6: Bee Wearable Temporal Context Granularity

* **Component:** Bee CLI (`bee now --json` / `bee-skill`).
* **Expected Behavior:** Querying `bee now --json` to detect whether the user is currently asleep or active.
* **Actual Blocker:** The Bee CLI outputs conversational utterance arrays with broad timestamps, but lacks an explicit `wearer_sleep_state` boolean flag or high-resolution voice-activity silence metric.
* **Severity:** **Medium.**
* **Vigil+ Workaround:** Built a temporal recency evaluator in `BeeAdapter`: it parses the utterance array delta, checking if ambient speech activity has been silent for $>60\text{ minutes}$. Combined with accelerometer stillness, it infers $H_{\text{asleep}}$ with high reliability.
* **Upstream Recommendation for Bee Computer Team:**
  > *Expose a first-class `temporal_silence_seconds: int` and `wearer_motion_level: float` directly in the `bee now --json` payload to simplify ambient context reasoning for developers.*
