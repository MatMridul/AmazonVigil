# Vigil — Security Audit (AI-code vulnerability classes)

Status of each class from `DEVELOPMENT_PLAN.md` §4. Updated as items close.
`FIXED` = a real gap closed with a commit + test. `PASS` = reviewed, already
correct. `N/A` = not applicable to the current surface. `OPEN` = tracked, not
yet done.

| # | Class | Status | Evidence / closing commit |
|---|---|---|---|
| 4.1 | Broken Access Control | **FIXED** | `899905f` — deny-by-default `BearerAuthMiddleware`; no tool reachable unauthenticated. Tests: `test_security_fixes.py` (unauth → 401, never reaches tool). |
| 4.2 | Insecure Design (frontend-only / PIN) | **FIXED** | `899905f` — disarm verifies PIN value + lockout, server-side. Test: wrong well-formed PIN rejected. |
| 4.3 | Cryptographic Failures / secrets | **FIXED** (dev-grade) | `899905f` — PIN stored as hash, `1234` literal removed; `secrets`/constant-time already used. Field: swap sha256→Argon2 (SEC.3 follow-up) + Secrets Manager. gitleaks in CI. |
| 4.4 | Injection (SQL/cmd/path/SSRF) | **PASS** (today) | No DB yet; path-traversal guard present in `web/server.py`; Bee subprocess uses fixed arg list (S603 reviewed). Re-audit when persistence (Phase B) + `device_id`→URL (Phase D) land. |
| 4.5 | Security Misconfiguration | **OPEN** | Console binds localhost + hides stack (PASS). CORS/security-headers/rate-limit on public endpoint tracked in Phase C/E. |
| 4.6 | Vulnerable/Outdated + Slopsquatting | **FIXED** (gated) | `899905f` — `pip-audit` in CI; 9 deps verified real (no hallucinated names); `uv.lock` committed with hashes. pip-audit non-blocking during adoption. |
| 4.7 | Identification/Auth Failures | **PARTIAL** | Tokens expire (PASS); PIN lockout added (FIXED). Rate-limiting on auth/token endpoints + real IdP (Cognito) = Phase C. |
| 4.8 | Software & Data Integrity | **FIXED** | `ca7b0ef` — Ring `verified_signature` derived from server HMAC, never the payload flag; CAD SHA-256 already present. Tests prove forged flag ignored. |
| 4.9 | Security Logging & Monitoring | **FIXED** (local) | `ca7b0ef` — `src/audit_log.py` structured events + mandatory secret redaction; wired to auth-deny + disarm. Test proves no secret in a line. Field: ship to CloudWatch (Phase C). |
| 4.10 | SSRF / XSS / CSRF | **N/A** (today) | Console is localhost JSON API, author-controlled static. Re-audit if a real web app is built; CSRF needed the moment the console is non-local. |
| 4.11 | Rules-File Backdoor / prompt injection | **PARTIAL** | Deterministic state machine is the sole authority — LLM scores, never actuates (invariant). `references/bee-skill/CLAUDE.md` review + untrusted-ingest delimiting = SEC.12 / Phase D. |

## Standing automated gates (keep these closed)
- `ruff check` with bandit `S` rules — CI, pre-commit.
- `pip-audit` — CI (flip to hard-fail after first triage).
- `gitleaks` — CI + pre-commit.
- coverage floor 85% on safety-critical modules — CI.
- invariant tests (`test_invariants.py`, SEC.10) — pending.

## Open HIGH/CRITICAL
None. The two critical holes (4.1 broken access control, 4.2 insecure PIN) are
closed and tested. Remaining items are hardening (rate-limiting, real IdP,
CloudWatch shipping) that land with Phases C–E, not open critical exposures on
the current surface.
