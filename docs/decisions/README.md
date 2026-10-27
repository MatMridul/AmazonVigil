# Decision Records (DRs)

This folder is Amazon Vigil's durable decision memory. Every consequential design,
ideation, or build decision is logged here. Start with
[`DR-00-template.md`](DR-00-template.md) — it defines what a DR is, when to write
one, how to write it, and the immutability rule.

## Index

| DR | Title | Status |
| :-- | :-- | :-- |
| [DR-00](DR-00-template.md) | Decision Record Template & Process | Meta |
| [DR-01](DR-01-spec-authority-and-layout.md) | Spec Authority & Phase 1 Project Layout | Accepted |
| [DR-02](DR-02-frame-scaling-geometry.md) | Camera Frame Scaling Geometry | Accepted |
| [DR-03](DR-03-canonical-threatlevel-enum.md) | Canonical ThreatLevel Enum | Accepted |
| [DR-04](DR-04-phase-1-scope.md) | Phase 1 Scope Boundary & Adapter Stubbing | Accepted |
| [DR-05](DR-05-single-process-tests.md) | Single-Process Test Execution Under Host RAM Pressure | Accepted |
| [DR-06](DR-06-pin-mcp-v1-major.md) | Pin `mcp` to the v1 Major (`<2.0.0`) | Accepted |
| [DR-07](DR-07-phase-3-state-machine.md) | Phase 3 Deterministic State Machine & CAD Staging Design | Accepted |
| [DR-08](DR-08-phase-8-scenario-simulator.md) | Phase 8 Scenario Simulator — Deterministic Edge Path | Accepted |
| [DR-09](DR-09-smartphone-mesh-organ.md) | Smartphone as a First-Class Mesh Organ | Accepted |
| [DR-10](DR-10-alexa-mcp-eligibility.md) | Alexa+ MCP Server as the Primary-Track Eligibility Code Path | Accepted |

## Namespace boundary: `DR-*` vs `UX-*`

Two decision namespaces exist in this repo and they are **not** the same series:

- **`DR-*`** (this folder, `docs/decisions/`) — **System Architecture** decisions:
  spec authority, data model, engine logic, scope, tooling, deployment. These are
  the canonical, numbered, immutable architectural records.
- **`UX-*`** (`docs/UI_UX_DESIGN_DECISIONS.md`) — **Product & UI/UX Design**
  decisions: visual tone, hero object, per-surface behavior, wearable/phone UX.

The two series are independent and numbers may coincide across them (a `DR-04`
and a `UX-04` are unrelated). When an architectural DR formalizes something a UX
decision implies, it cites the `UX-*` id as its design source (e.g. DR-09 cites
UX-06/UX-04). This boundary was introduced to resolve an earlier collision where
the UI doc and this folder both used `DR-*` numbering for different decisions.

## Quick rules

- One decision per DR. Next free two-digit number; numbers are never reused.
- Accepted DRs are append-only in their reasoning sections. Overturns get a new
  superseding DR or an appended Status History line — never a silent rewrite.
- Add a row to the index table above whenever you add a DR.
