# Vigil — Implementation Plan (tasks)

> Executes [`DEVELOPMENT_PLAN.md`](DEVELOPMENT_PLAN.md). Each task has a concrete
> file target and an acceptance criterion (AC). Check a box only when its AC
> holds AND the Definition of Done (plan §2) is met. Phases are in dependency
> order — do not start a phase until the prior one's release tag is cut.
>
> Branch per phase off `main` (e.g. `feat/phaseA-hardening`), PR, merge green.
> Current branch is `feat/phase-1-core`; first action is to make `main` the
> released line (TASK ENV.0).

Legend:  ☐ todo · ◐ in progress · ☑ done · 🔴 security-critical · 👤 needs Mridul

---

## Phase ENV — baseline (do first)
- ☐ **ENV.0** Merge/retarget so `main` carries the current green line. Open a PR
  from `feat/phase-1-core` → `main`; you merge it (agent is blocked from pushing
  to `main`). AC: `main` == current HEAD, CI (added in SEC.5) green on it.
- ☐ **ENV.1** Add `CHANGELOG.md` (Keep a Changelog), seed with `0.1.0` = current
  state. AC: file exists, first entry matches reality.
- ☐ **ENV.2** Add `CONTRIBUTING.md` + `docs/THREAT_MODEL.md` skeleton. AC: both
  committed; threat model lists the 8 tools' trust boundaries.

---

## Phase A — Security hardening & engineering baseline → `0.2.0`

### Security fixes (map to DEVELOPMENT_PLAN §4)
- ☑ 🔴 **SEC.1 — Authorization guard on MCP tools (§4.1, the critical gap).**
  Done `899905f` — deny-by-default `BearerAuthMiddleware` in `src/mcp_auth.py`,
  wired in `build_asgi_app`. Unauthenticated actuation call → 401, proven in
  `tests/test_security_fixes.py`.
- ☑ 🔴 **SEC.2 — Real disarm-PIN verification (§4.2).** Done `899905f` —
  value-checked against a stored hash with lockout; MCP + web console both use
  `PinVerifier`. Wrong well-formed PIN rejected (test).
- ◐ 🔴 **SEC.3 — Secrets & PIN hashing (§4.3).** Partial `899905f` — PIN stored
  as hash, `1234` literal removed, `.env` gitignored. FOLLOW-UP: swap dev sha256
  → Argon2 (`argon2-cffi`) + AWS Secrets Manager for the field.
- ☑ **SEC.4 — Integrity: trust the check, not the payload (§4.8).** Done
  `ca7b0ef` — Ring `verified_signature` derived from the server HMAC only; forged
  flag ignored (test).

### Engineering baseline (DEVELOPMENT_PLAN §3)
- ☑ **SEC.5 — CI pipeline.** Done `899905f` — `.github/workflows/ci.yml` green on
  the branch (ruff/mypy/pytest-cov/pip-audit/gitleaks).
- ◐ **SEC.6 — Lint/format/type config.** ruff clean; mypy down 12→4 (remaining 4
  pre-existing Pillow/boto3 typing, non-blocking). Flip mypy to hard-fail after
  the last 4 are resolved.
- ☑ **SEC.7 — Pre-commit.** Config added; hooks installed (`pre-commit install`).
- ☑ 🔴 **SEC.8 — Dependency / slopsquatting audit (§4.6).** `pip-audit --skip-editable`
  BLOCKING in CI; clean (no known vulns); 9 deps verified real; `uv.lock` hashes.
- ☑ **SEC.9 — Structured audit logging (§4.9).** Done `ca7b0ef` — `src/audit_log.py`
  with mandatory secret redaction; wired to auth-deny + disarm; redaction tested.
- ☑ **SEC.10 — Invariant test suite.** Done — `tests/test_invariants.py`, 11 tests
  lock silence-under-duress / no-auto-911 / L3-corroboration.
- ☑ **SEC.11 — `docs/SECURITY_AUDIT.md`.** Created — each class PASS/FIXED/N-A
  with closing commit; zero open HIGH/CRITICAL.
- ☑ **SEC.12 — Review in-repo agent-instruction files (§4.11).** Done —
  `references/bee-skill/CLAUDE.md` reviewed clean (legit skill-packaging, no
  injected directives).

**→ Cut `v0.2.0`** when all A boxes are ☑ and CI is green on `main`.

---

## Phase B — Persistence & durability → `0.3.0`
- ☑ **B.1** Datastore abstraction (`src/store/`) — `IncidentStore` protocol with
  `InMemoryStore` + `SqliteStore`; both tested, parity proven (`tests/test_store.py`).
- ☑ **B.2** Incident store (`_incidents`) moved behind it; durable when
  `VIGIL_STATE_DB` is set. AC MET: `test_sqlite_state_survives_restart` proves a
  record written by one instance is read by a fresh instance on the same file.
- ☑ **B.3** OAuth tokens persisted (`mcp_auth.py`). `AuthorizationServer` takes an
  optional durable token store; tokens written with an ABSOLUTE wall-clock expiry
  (monotonic would be meaningless post-restart), `validate_bearer` falls back to
  the store on a miss. Auth CODES stay in-memory by design (single-use, 5-min).
  AC MET: `test_token_survives_restart` + wall-clock expiry test.
- ☑ **B.4** Guard profile persisted (`set_mesh_guard_profile` → KV store,
  `active_guard_profile()` read-back). AC MET: `test_guard_profile_survives_restart`.
  (Disarm PIN hash already loaded from config/env, not in-process state.)
- ☑ 🔴 **B.5** Parameterized queries ONLY — `SqliteStore` + `SqliteKV` both use
  bound params; ruff-S flags none. Verified.

**→ Cut `v0.3.0`.**

---

## Phase C — Real identity → `0.4.0`  👤 (AWS resources)
- ☐ 👤 **C.1** Stand up a Cognito user pool (free tier) as the field IdP; keep
  the in-memory AS as documented local-dev fallback. AC: discovery docs can point
  at Cognito; local dev still works offline.
- ☐ 🔴 **C.2** Rate limiting on `/authorize`, `/token`, disarm, and `/mcp` (§4.7).
  AC: Nth rapid request in a window is throttled; test proves it.
- ☐ **C.3** Wire audit logging (SEC.9) to CloudWatch for the field profile. AC:
  events land in CloudWatch when the AWS profile is active.

**→ Cut `v0.4.0`.** Flag every AWS resource cost before creating it.

---

## Phase D — Live device read paths → `0.5.0`
- ☐ **D.1** Ring webhook receiver endpoint: verify HMAC (SEC.4), parse real
  events into `Telemetry`. AC: a signed sample event flows ingest→engine→result;
  an unsigned one is rejected. Device-optional fallback preserved.
- ☐ **D.2** Ring WHEP live-video session wiring (behind creds). AC: `whep_session_url`
  reaches a real session with a token; `device_id` allow-listed (§4.4 SSRF).
- ☐ **D.3** Bee adapter real `bee now --json` polling for sleep/awake. AC: live
  bio-state flows when the CLI is present; MODELED fallback when absent.
- ☐ 🔴 **D.4** Bedrock reasoner behind the thin port + **Task 3.2 edge-rule
  fallback** (currently unbuilt) for >1500ms/unreachable. Ingested text treated as
  untrusted data, never instructions; LLM scores only, never actuates (§4.11).
  AC: a scenario scores via Bedrock when reachable, via the edge table when not,
  and no Bedrock output can bypass the corroboration gate (invariant test).

**→ Cut `v0.5.0`.** Bedrock calls are metered — cache + rate-limit, flag cost.

---

## Phase E — Deployment target & exposure → `0.6.0`
- ☐ **E.1** Dockerfile + compose for a home-server/Pi deploy. AC: `docker compose
  up` boots the server + console reproducibly from a clean checkout.
- ☐ 🔴 **E.2** Real edge: reverse proxy (Caddy/Nginx or API Gateway) with TLS,
  CORS allow-list (Alexa+ origin + console only), security headers (HSTS,
  X-Content-Type-Options), no `Server` banner (§4.5). Retire the ngrok
  Host-rewrite hack. AC: public endpoint serves TLS with the headers; CORS rejects
  an off-list origin.
- ☐ **E.3** `scripts/coldstart_check.sh|.ps1` — clean clone → setup → boot → real
  MCP handshake → three surfaces render, scripted. AC: passes on a fresh clone.

**→ Cut `v0.6.0`.**

---

## Phase F — Alexa+ certification → `0.9.0`  👤 (you + browser + AWS)
> From `RETURN_STATUS.md`. Agent preps everything; you do the consented steps.
- ☐ 👤 **F.1** Create the IAM user + `sts:AssumeRole` to Amazon's role, generate
  keys (you do this consciously — standing secret).
- ☐ 👤 **F.2** `aws codeartifact login` + `npm install -g @alexa-ai/cli` in WSL
  (Node 24 present). AC: CLI installs.
- ☐ 👤 **F.3** `alexa-ai configure` → LWA browser consent. AC: CLI authed.
- ☐ **F.4** `alexa-ai new mcp` against the authenticated public URL; validate via
  Local Inspector; dev-stage deploy (free tier). AC: Local Inspector lists all 8
  tools against the live server. STOP before public certification.
- ☐ 👤 **F.5** Certification submission — your decision only.

**→ Cut `v0.9.0`** after dev-stage deploy validates.

---

## Phase G — Field pilot & `1.0.0`  👤
- ☐ **G.1** Full §4 security audit re-run; `docs/SECURITY_AUDIT.md` all green,
  zero open HIGH/CRITICAL. AC: CI + manual audit both clean.
- ☐ **G.2** Threat model reviewed & current; README deploy section accurate.
- ☐ 👤 **G.3** One real household pilot (yours is enough): one real device, runs
  unattended ≥1 week, state survives restarts, audit log reviewed. AC: a week of
  clean operation logged.
- ☐ 👤 **G.4** Tag `v1.0.0`, GitHub Release with changelog. AC: released.

---

## Quick-start order (if you want the highest-value first)
1. **SEC.1** (auth guard) — closes the one genuinely serious open hole today.
2. **SEC.5–SEC.8** (CI + audits) — the net that keeps everything else from regressing.
3. **SEC.2/SEC.3** (PIN) — the second real hole.
4. Then B → C → D → E → F → G in order.

The two security fixes SEC.1 and SEC.2 are small, high-impact, and entirely
local (no account, no cost). They're the right first session's work.
