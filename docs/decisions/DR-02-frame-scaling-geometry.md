# DR-02: Camera Frame Scaling Geometry

**Status:** Accepted
**Status History:** 2026-10-14 Proposed; 2026-10-14 Accepted
**Date:** 2026-10-14
**Deciders:** Mridul (owner) + Kiro (architect)
**Supersedes:** N/A
**Superseded By:** N/A

## Context

Frame downscaling before Bedrock payload generation was specified three
inconsistent ways:

- Phase 1 prompt rule #4: "proportionally downscaled preserving native 16:9 to
  1024x576 WebP (75% pixel reduction)".
- Phase 1 prompt Task 1.3: "proportional bicubic resizing to 1024x576 WebP at
  quality 80".
- `SPEC.md` §5.2: WebP, no quality number, "e.g. 1024x576 for 16:9".
- `SPEC.md` §7 / Devil's Advocate #8: "WebP compression (65% token cut)".

The "75% pixel reduction" only holds if the source is exactly 2048x1152. The
"65% token cut" is a different number again. A hardcoded reduction percentage is
not a safe invariant because it depends on unknown source dimensions.

## Options Considered

- **Option A — Max-fit box, downscale only.** Fit within 1024x576 preserving
  aspect ratio; never upscale a smaller source. WebP quality 80. Assert on
  bounds and aspect ratio, not on a fixed reduction percentage.
- **Option B — Hard resize to exactly 1024x576.** Simpler assertion but distorts
  or forces upscaling for non-16:9 or small sources, and bakes in a reduction
  percentage that is only true for one input size.

## Decision

**Option A.** Max-fit box: max 1024x576, aspect ratio preserved, downscale only
(never upscale), output WebP quality 80. Tests assert:

- output dimensions ≤ (1024, 576),
- aspect ratio preserved within ±1%,
- output format is WebP.

The hardcoded "75%" / "65%" reduction claim is **dropped** from code and tests.

## Rationale

Pixel-reduction percentage is a function of source size, so it is not a property
of the resizer and cannot be a stable test invariant. Bounds + aspect-ratio +
format are the real, testable guarantees. Downscale-only avoids wasting tokens
re-inflating an already-small frame.

## Strongest Argument Against

Dropping the explicit percentage loses a crisp marketing/token-budget number that
appears in the spec narrative. Mitigated by keeping the WebP-quality knob, which
is the actual token-cost lever, and documenting typical reduction in prose rather
than asserting it in code.

## Consequences

- `preprocess_frame` is a downscale-only max-fit resize to WebP q80.
- Spec prose mentioning "75%"/"65%" is descriptive, not a code contract.
- Non-16:9 sources are handled gracefully (letterbox-free, just bounded).
