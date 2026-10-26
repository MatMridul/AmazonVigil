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
- ☐ 🔴 **SEC.1 — Authorization guard on MCP tools (§4.1, the critical gap).**
  Add bearer validation as MCP transport middleware in `src/server.py`, calling
  `AuthorizationServer.validate_bearer`. Deny-by-default: every state-changing
  tool (`trigger_tactical_wake`, `trigger_firetv_deterrence`,
  `format_emergency_cad_packet`, `disarm_perimeter_alert`, `set_mesh_guard_profile`)
  requires a valid token; read-only tools may be explicitly marked public.
  AC: a `tools/call` on any actuation tool WITHOUT a valid bearer returns 401;
  WITH a valid bearer succeeds. New test `tests/test_tool_authz.py` proves both.
- ☐ 🔴 **SEC.2 — Real disarm-PIN verification (§4.2).** In
  `disarm_perimeter_alert` (`src/server.py`) verify the PIN *value* against a
  stored **hashed** PIN (not just `isdigit()/len()==4`); remove reliance on any
  literal. Add attempt lockout (e.g. 5 tries → cooldown). AC: wrong PIN rejected,
  right PIN disarms, 6th wrong attempt is locked out; test covers all three.
- ☐ 🔴 **SEC.3 — Secrets & PIN hashing (§4.3).** Add `argon2-cffi`; store the
  disarm PIN as an Argon2 hash in config, never plaintext. Introduce a `.env`
  (gitignored — already is) + `python-dotenv` for dev creds; document the AWS
  Secrets Manager path for the field. Remove `_DEMO_DISARM_PIN = "1234"` literal
  from `src/web/server.py` (load from config/hash). AC: grep finds no plaintext
  PIN/secret in `src/`; gitleaks clean.
- ☐ **SEC.4 — Integrity: trust the check, not the payload (§4.8).** In
  `src/adapters/ring_adapter.py`, set `verified_signature` ONLY from
  `verify_webhook`, never from the inbound payload field. AC: a payload claiming
  `verified_signature: true` with a bad HMAC is treated as unverified; test added.

### Engineering baseline (DEVELOPMENT_PLAN §3)
- ☐ **SEC.5 — CI pipeline.** `.github/workflows/ci.yml`: uv install → `ruff
  check` → `ruff format --check` → `mypy src` → `pytest --cov=src --cov-fail-under=85`
  → `pip-audit` → `gitleaks`. AC: green on a PR; a deliberately-broken test fails it.
- ☐ **SEC.6 — Lint/format/type config.** Add `[tool.ruff]` (enable `S` bandit
  rules, bugbear, isort) + `[tool.mypy]` (strict on `src/`) to `pyproject.toml`.
  Fix what they flag. AC: `ruff check` and `mypy src` both clean.
- ☐ **SEC.7 — Pre-commit.** `.pre-commit-config.yaml`: ruff, ruff-format,
  gitleaks, trailing-whitespace, eof-fixer, check-added-large-files. AC:
  `pre-commit run --all-files` passes.
- ☐ 🔴 **SEC.8 — Dependency / slopsquatting audit (§4.6).** Run `pip-audit`;
  manually confirm each of the 9 runtime deps resolves to its real PyPI project
  (none hallucinated — spot-verified in planning, re-confirm in CI). Ensure
  `uv.lock` is committed WITH hashes. AC: `pip-audit` clean; lockfile hashes present.
- ☐ **SEC.9 — Structured audit logging (§4.9).** Add stdlib `logging` + JSON
  formatter module; log every security event (auth ok/fail, disarm attempt, CAD
  stage, profile change, actuation) — NEVER a secret/PIN. Replace `print` in
  `src/` entrypoints. AC: an auth failure and a disarm attempt produce a log line
  with no secret in it; test asserts the redaction.
- ☐ **SEC.10 — Invariant test suite.** `tests/test_invariants.py`: assert
  `permitted_actuators(SILENT_DURESS, L)==()` for all L; L3 without corroboration
  held to L2; CAD tool never auto-sends. AC: all pass; mutating the cap in source
  makes them fail (verify once).
- ☐ **SEC.11 — `docs/SECURITY_AUDIT.md`.** Record every §4 item as PASS/FIXED/N-A
  with the closing commit. AC: all 11 classes addressed; no open HIGH/CRITICAL.
- ☐ **SEC.12 — Review in-repo agent-instruction files (§4.11).** Read
  `references/bee-skill/CLAUDE.md` and any `.cursorrules`/`AGENTS.md` for injected
  directives. AC: documented clean (or the injection flagged & removed).

**→ Cut `v0.2.0`** when all A boxes are ☑ and CI is green on `main`.

---

## Phase B — Persistence & durability → `0.3.0`
- ☐ **B.1** Introduce a datastore abstraction (`src/store/`) — SQLite default
  (local/edge), interface-clean so DynamoDB can back it in the field. AC: the
  interface has an in-memory + SQLite impl, both tested.
- ☐ **B.2** Move the incident store (`_incidents` dict in `server.py`) behind it.
  AC: an incident staged, server restarts, incident still queryable.
- ☐ **B.3** Persist OAuth tokens + auth codes (`mcp_auth.py` in-memory dicts).
  AC: a restart does not invalidate a live token before its TTL.
- ☐ **B.4** Persist guard profiles + the hashed disarm PIN. AC: profile survives
  restart.
- ☐ 🔴 **B.5** Parameterized queries ONLY — no string-built SQL anywhere (§4.4).
  AC: grep shows zero f-string/`%`-format SQL; ruff-S flags none.

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
