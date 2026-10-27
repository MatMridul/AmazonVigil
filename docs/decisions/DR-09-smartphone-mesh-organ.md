# DR-09: Smartphone as a First-Class Mesh Organ

**Status:** Accepted
**Status History:** 2026-10-23 Proposed; 2026-10-23 Accepted
**Date:** 2026-10-23
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

Vigil's thesis is a *thin but smart* protective nervous system: one reasoning
layer (Alexa+) correlating four Amazon organs — Ring (perimeter sight/sound),
Bee (resident bio-state), Alexa+ (brain/voice), Fire TV (deterrence actuator).
Three real-world constraints cannot be satisfied by those four organs alone:

1. **The Bee Pioneer clip is screenless and has no vibration endpoint**
   (`bee-cli` is read-only; no haptic command). So "wake the sleeping resident"
   in `NIGHT_SENTRY` is a promise the wearable hardware cannot keep.
2. **Wi-Fi drops routinely** (DHCP renewal, router reboot, storm, severed cable).
   The entire mesh rides on the home network; a drop blinds it.
3. **Automated 911 dispatch is illegal** (FCC / 47 U.S.C. § 227) and false
   dispatches carry $100–$500 municipal fines. A fully-automated CAD path is not
   legally shippable.

Nearly every resident charges a smartphone on the nightstand within arm's reach,
carries an independent cellular radio, and expects to physically authorize an
emergency call. The phone is therefore not a fifth gadget bolted on — it is the
organ that makes the other four *survivable in the real world*.

The product-design treatment of these roles is frozen in
`docs/UI_UX_DESIGN_DECISIONS.md` under **UX-06** (smartphone node, network
resilience, RBAC) and **UX-04** (wearable dual-tier contract, which delegates
wake actuation and 30s CAD staging to the phone). This DR formalizes the
*architectural* mandate those UX decisions imply.

## Decision

The smartphone is a first-class node in the Vigil mesh with four mandated roles:

1. **Nightstand Mode — contained secondary wake actuator.** Patches the Bee
   screenless/no-haptic gap. Uses native Critical Alerts to bypass Do Not
   Disturb; emits a rising low-frequency 40–80Hz hum (never a high-frequency
   siren) and wakes the screen to ~50% warm brightness with the Active Protector
   guidance card. This is the actuator the `night_sentry` wake path actually
   drives when the wearable cannot.

2. **Cellular fail-safe witness.** A network drop is modeled as an
   **unobservability state (Φ_net = 0), never a home invasion** — it must never
   trigger an automated external dispatch. On Φ_net = 0 the local devices harden
   into Local Edge Sentry (local rule tables); the phone's independent cellular
   radio becomes the out-of-band witness, notifies the resident ("Home network
   offline. Local sentry active."), and preserves manual 1-tap CAD capability.

3. **Human-in-the-loop CAD authorization node (FCC-mandated).** The phone is the
   primary physical surface for the staged RapidSOS CAD manifest. On a verified
   L3 breach it displays the staged packet (GPS, camera stills, SHA-256 integrity
   hash), runs the 10-second cancellation countdown (`CadStaging`), and requires
   explicit authorization — `[TRANSMIT 911 NOW]` vs `[CANCEL WITH PIN 1-2-3-4]`
   (`verify_disarm_pin`) — so a groggy 3 AM resident never triggers a false
   dispatch. This makes `DISPATCH_EMERGENCY` legally shippable.

4. **Pocket Mission Control with 3-tier household RBAC (anti-surveillance).** The
   app shows the Sanctuary State Capsule ("Perimeter Secure — 3/3 Residents on
   Premises") and records **zero** room-by-room forensic timelines of family
   members. RBAC: (1) Primary Admin — full sensitivity/modes/logs; (2) Verified
   Resident — status, 1-tap SOS, intercom, self-disarm, no snooping; (3) Trusted
   Caretaker — time-bounded perimeter disarm during an active shift only.

## Enforcement Points (boundary = a cap/path, not a sentence)

- **Φ_net = 0 ⇒ no automated dispatch** is a state-machine path, not a comment:
  the network-loss branch routes to Local Edge Sentry and the manual-only CAD
  path, structurally unable to auto-dispatch.
- **CAD requires human authorization** — `DISPATCH_EMERGENCY` stages via
  `CadStaging` (10s buffer) and completes only through explicit
  transmit/PIN-disarm, never autonomously.
- **Anti-surveillance** — the data model exposes aggregate presence count only;
  there is no per-resident room-timeline field to leak.

## Strongest Argument Against

Adding a fifth surface widens scope with ~12 hours to the deadline, and the phone
is not an Amazon device, so it does not strengthen any single track's
"calls-the-tech" eligibility. Accepted because the phone resolves three
*correctness/legal* failures the four Amazon organs cannot, and because it is
rendered as a framed viewport sharing the single Phase 8 scenario state store
(one pipeline, two surfaces) rather than a separately-built app — so the added
build cost is a viewport, not a second product.

## Consequences

- Phase 7 `src/web/` ships **two interactive hero surfaces** under one Surface
  Switcher: Mission Control (the brain correlating the mesh) and the Nightstand
  Phone viewport (the human authorizing the dispatch), both driven by the shared
  scenario store.
- The phone is honestly badged: its actuation (40–80Hz hum, Critical Alerts) is
  MODELED where no device is present, consistent with the DR-04 honesty split.
- `night_sentry` wake, Φ_net=0 handling, and CAD human-authorization now have a
  named physical home rather than an aspirational one.
