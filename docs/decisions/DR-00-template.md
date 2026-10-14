# DR-00: Decision Record Template & Process

**Status:** Meta (this record defines the process; it is never "Accepted" like a design DR)
**Date:** 2026-10-14

---

## What a Decision Record (DR) is

A Decision Record captures a single, consequential decision made while designing,
ideating, or building Amazon Vigil — **what** was decided, **why**, what was
rejected, and the **strongest argument against** the chosen path. DRs are the
project's durable memory: anyone (human or agent) joining later should be able to
read the DR folder and understand not just the current architecture but the
reasoning and the roads not taken.

A DR is **not** a changelog entry, a task, or a status update. It records a
*decision*, not an *action*.

## When to write a DR

Write a DR when a choice meets **any** of these:

- It resolves an ambiguity or contradiction in the specs (e.g. two documents
  disagree, and we picked one).
- It is a **one-way door** — expensive or disruptive to reverse later (package
  choice, data model shape, naming convention, public API contract).
- It constrains future work (an invariant, a boundary, a prohibited pattern).
- It picks one option from several reasonable alternatives.
- A reviewer would later ask *"why was it done this way?"* and the answer is not
  obvious from the code.

Do **not** write a DR for: routine implementation details, reversible local
choices, formatting, or anything fully dictated by the frozen specs with no
judgment involved.

## How to write a DR

1. Copy this file to `DR-NN-short-kebab-title.md` where `NN` is the next free
   two-digit number (DR-01, DR-02, ...). Numbers are never reused.
2. Fill every section. If a section genuinely does not apply, write
   `N/A — <reason>`, never leave it blank.
3. Keep it tight: one decision per DR. If you are tempted to decide two things,
   write two DRs.
4. Commit the DR in the **same change** as (or immediately before) the work it
   governs, so the record and the code land together.

## Immutability rule (borrowed from the ATLAS discipline)

Once a DR is committed with status **Accepted**, the *Context*, *Options
Considered*, *Decision*, and *Strongest Argument Against* sections are **frozen**
(append-only; typo fixes are fine). If the decision is later overturned:

- A small reversal is recorded by **appending** to the *Status History* line and
  writing a *Superseded By* pointer — the original reasoning stays visible.
- A large reversal gets a **new superseding DR** that references the old one. We
  never silently rewrite history.

Status transitions are appended to the **Status History** line, never flipped in
place.

---

## Template (copy everything below this line)

```markdown
# DR-NN: <Short Title>

**Status:** Proposed  <!-- Proposed -> Accepted -> (optionally) Superseded -->
**Status History:** 2026-MM-DD Proposed
**Date:** 2026-MM-DD
**Deciders:** <who made the call — e.g. Mridul (owner) + Kiro (architect)>
**Supersedes:** N/A
**Superseded By:** N/A

## Context

What situation forced a decision? What ambiguity, contradiction, constraint, or
requirement is in play? Link the relevant spec sections.

## Options Considered

- **Option A — <name>:** description. Pros / cons.
- **Option B — <name>:** description. Pros / cons.
- (as many as were real candidates)

## Decision

The option chosen, stated plainly. What we will actually do.

## Rationale

Why this option beat the others. Tie back to spec, judging criteria, or
engineering reality.

## Strongest Argument Against

The best case a devil's advocate could make against this decision. If we are
wrong, this is how. (A DR with no honest counter-argument is incomplete.)

## Consequences

What this constrains or enables downstream. Follow-up work it creates. Invariants
it introduces.
```
