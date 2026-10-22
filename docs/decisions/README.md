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

## Quick rules

- One decision per DR. Next free two-digit number; numbers are never reused.
- Accepted DRs are append-only in their reasoning sections. Overturns get a new
  superseding DR or an appended Status History line — never a silent rewrite.
- Add a row to the index table above whenever you add a DR.
