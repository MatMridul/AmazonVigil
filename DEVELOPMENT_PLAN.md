# Vigil — Development Plan: from demo-grade to field-ready

> Scope: take Vigil from its current state (a tested deterministic core + a
> reference-grade in-memory OAuth layer + simulated device adapters, all on
> branch `feat/phase-1-core`) to a **field-ready, deployable security mesh** a
> real household could run.
>
> Audience: Mridul. Written plain where the topic is outside day-to-day code.
> Companion file: [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md) — the
> checkbox task list that executes this plan.

---

## 0. Honest baseline — what is real today

Verified by reading the live source on 2026-10-27, not the conversation summary:

| Area | State today | Field-ready? |
|---|---|---|
| Deterministic core (`state_machine`, `cad_dispatcher`, `integrity_auditor`) | Real, pure, 165 tests green | **Yes** (needs persistence + audit log) |
| Safety invariants (silence-under-duress, no-auto-911, L3 corroboration) | Enforced as caps/dispatch tables in code | **Yes** — keep as invariants, add invariant tests |
| OAuth 2.1 / PKCE / PRM discovery (`mcp_auth.py`) | Real protocol logic, but **in-memory, single-process, no real IdP, tokens never persisted** | **No** — reference-grade only |
| MCP server (`server.py`) | 8 tools live; incident store is an **in-process dict**; actuators `simulated: True` | **No** — stateless, non-durable, no auth guard on tools |
| Device adapters (Ring/Bee/Bedrock) | Coded to real vendor contracts, run **simulated** when no creds | **Partial** — live read path is stubbed |
| Web console (`web/server.py`) | stdlib HTTP, **localhost-only**, path-traversal guarded, no stack leak | **Demo-grade** — fine for operator, not internet-facing |
| Exposure | ngrok tunnel, **unauthenticated**, Host-rewrite hack | **No** — not a deployment |
| CI / release automation | **None** (`no .github`) | **No** |
| Persistence / state durability | **None** — all state dies with the process | **No** |
| Secrets management | Env vars + a literal demo PIN (`_DEMO_DISARM_PIN = "1234"`) | **No** |

The gap between "demo that proves the architecture" and "field-ready" is
**four things, in order of importance**: (1) real auth + real persistence,
(2) the live device read paths, (3) a real deployment target with CI, and
(4) the AI-code security hardening pass (§4). None of it throws away what
exists — the deterministic heart stays exactly as is.

---

## 1. Versioning

**Scheme: Semantic Versioning 2.0.0** (`MAJOR.MINOR.PATCH`), because this is a
system with an external contract (the 8 MCP tools + the Alexa+ account-linking
surface). The MCP tool signatures and the OAuth discovery documents ARE a public
API; breaking them is a MAJOR bump.

- **MAJOR** — a breaking change to any MCP tool signature, the threat-level
  enum, the CAD packet schema, or the OAuth discovery contract.
- **MINOR** — a new tool, a new device adapter, a new guard mode, backward-compatible.
- **PATCH** — bug fix, security fix, doc, dependency bump with no API change.

**Pre-release tags** while hardening: `1.0.0-rc.1`, `1.0.0-rc.2`, … The current
tree is effectively `0.1.0` (what `pyproject.toml` already declares). Field-ready
is `1.0.0`.

**Git flow (minimal, enforced):**
- `main` — protected, always releasable, always green. No direct pushes (and the
  agent is policy-blocked from pushing to it regardless — you push the final).
- `feat/*`, `fix/*`, `chore/*` — all work branches off `main`, merged via PR.
- The current work sits on `feat/phase-1-core`; after this plan's first merge it
  should be renamed/retargeted so `main` carries the released line.

**Tags & releases:** every `MINOR`/`MAJOR` cut as an annotated git tag `vX.Y.Z`
plus a GitHub Release with a changelog section. Keep a `CHANGELOG.md`
(Keep a Changelog format) updated in the same PR that lands the change — never
retroactively.

**Conventional Commits** (already in use — `feat(auth):`, `fix(auth):`,
`docs(design):`). Keep it; it lets the changelog be generated, not hand-written.

---

## 2. Definition of Done (DoD)

A unit of work is **Done** only when ALL of these hold. This is the gate; "it
runs on my machine" is not on the list.

**Per task / PR:**
1. Code implements the task's stated scope and nothing it wasn't asked to.
2. **Tests exist and pass** — unit tests for logic, an integration test for any
   new seam. The suite runs clean under the existing strict `filterwarnings =
   ["error"]` discipline (a warning fails the build — keep that).
3. **The full suite is green**, not just the targeted file (lesson learned:
   a signature change can be green locally and break a caller elsewhere).
4. **Security checklist (§4) reviewed** for the touched surface — every box that
   applies to the change is checked, in the PR description.
5. **No secret in the diff** — scanned (gitleaks), not eyeballed.
6. **Lint + format + type-check pass** (ruff + mypy — added in §3).
7. **A decision record** (`docs/decisions/DR-NN`) exists for any architectural
   choice, following the existing immutable-Pass-1 DR convention.
8. **Docs updated in the same PR** — README/CHANGELOG/relevant design doc. No
   "docs later."
9. **Provenance honesty preserved** — anything MODELED is still badged MODELED;
   no simulated reading is relabeled live.

**Per release (`vX.Y.Z` → field-ready `1.0.0`):**
10. CI green on `main` (§3).
11. The whole §4 security audit passes with zero open HIGH/CRITICAL.
12. A clean-clone cold-start works: fresh checkout → documented setup → server
    boots → a real MCP client handshakes → the three surfaces render. Scripted,
    not manual.
13. `README.md` deployment section is accurate against the actual deploy target.
14. Threat-model doc (`docs/THREAT_MODEL.md`) reviewed and current.

---

## 3. Software standards (the engineering contract)

These make the codebase defensible as a *product*, not a hackathon artifact.

**Language / runtime**
- Python ≥ 3.11 (already pinned). Pin the exact patch in CI; pin all deps in
  `uv.lock` (already present — keep it committed and authoritative).

**Tooling (add — none of this exists yet):**
- **Formatter:** `ruff format` (replaces black, one tool).
- **Linter:** `ruff check` with a sane rule set (pyflakes, bugbear, security
  `S` rules from bandit, isort). The `S` rules specifically catch many of the
  AI-code issues in §4 automatically.
- **Type checker:** `mypy --strict` on `src/`. The core is already heavily typed;
  this just enforces it.
- **Tests:** `pytest` (already), with `pytest-cov`. **Coverage floor 85%** on
  `src/core/` and `src/` auth/pipeline modules (the safety-critical code),
  measured in CI, build fails below floor.
- **Secret scan:** `gitleaks` in CI and as a pre-commit hook.
- **Dependency audit:** `pip-audit` (the Python equivalent of `npm audit`) in CI,
  weekly and on every PR. **This is the single most important automated defense
  against the AI-code supply-chain risks in §4.**
- **Pre-commit** (`.pre-commit-config.yaml`): ruff, ruff-format, gitleaks,
  trailing-whitespace, end-of-file-fixer, check-added-large-files.

**CI (GitHub Actions — `no .github` today, this is net-new):**
- `ci.yml` on every push/PR: install (uv) → ruff → mypy → pytest+coverage →
  pip-audit → gitleaks. All must pass. This is the enforcement arm of the DoD.
- `release.yml` on tag `v*`: build wheel, attach to a GitHub Release, generate
  changelog from Conventional Commits.
- Branch protection on `main`: require `ci.yml` green + 1 review (you) before merge.

**Code conventions**
- Keep the existing module-docstring discipline (every file explains itself).
- Keep decision records immutable Pass-1 (existing DR-00 template).
- Public functions typed and docstringed; no bare `except:` (the web server's
  `except Exception` that returns `{"error": type(exc).__name__}` is correct —
  it deliberately does not leak the stack; keep that pattern).
- **Structured logging** (stdlib `logging` with a JSON formatter) — no `print`
  in `src/` except CLI entrypoints. Field-ready systems need an audit trail.

**Testing standards**
- Deterministic tests only — the core already takes `now` as an argument; keep
  all time/randomness injectable so tests are replayable.
- **Invariant tests** (new category): assert the safety caps *cannot* be
  violated — e.g. `permitted_actuators(SILENT_DURESS, L3) == ()` for every level;
  `format_emergency_cad_packet` never auto-sends; L3 without corroboration is
  held to L2. These guard the moat against future edits.
- Adversarial tests for auth: expired token, replayed code, wrong PKCE verifier,
  resource mismatch, bearer in query string (must be rejected).

---

## 4. AI-coding-agent vulnerability audit (the requested focus)

**Why this matters, in one line:** independent 2025–2026 studies found
**~45% of AI-generated code introduces an OWASP Top-10 vulnerability**, AI code
is **2.74× more likely to contain XSS**, one study found **100% of AI-built apps
lacked CSRF protection**, and **~20% of AI code references hallucinated packages**
that attackers pre-register ("slopsquatting"). These are *default* failure modes
of how coding agents are trained — they inherit insecure patterns from public
code and optimize for "it works," not "it's safe." Vigil was substantially
AI-built, so every one of these is a live risk until proven absent.

Below: each class, **how it typically sneaks into AI code**, the **specific risk
in Vigil**, and the **concrete check**. The ☐ boxes are executable tasks in
`IMPLEMENTATION_PLAN.md` §SEC.

### 4.1 Broken Access Control (OWASP #1 — the top AI-code failure)
- **How AI introduces it:** builds the feature, forgets *who* may call it. UI
  hides a button; the API behind it checks nothing.
- **Vigil risk — REAL and present:** the 8 MCP tools have **no authorization
  guard today**. `mcp_auth.py` *can* validate a bearer, but `server.py`'s tools
  never call `validate_bearer`. Anyone who reaches `/mcp` can
  `trigger_firetv_deterrence`, `format_emergency_cad_packet`, or
  `disarm_perimeter_alert` — the actuation and emergency tools — with no token.
  The ngrok URL is public. This is the single most serious gap.
- **Check / fix:** ☐ enforce bearer validation on every state-changing tool at
  the transport layer (MCP middleware), not per-tool-by-hand. ☐ Deny-by-default:
  a tool with no explicit "public" marker requires a valid token. ☐ Test that an
  unauthenticated actuation call is rejected with 401.

### 4.2 Insecure Design — frontend-only / trust-boundary checks
- **How AI introduces it:** puts the security check where it's easy (the client),
  not where it's enforced (the server).
- **Vigil risk:** the disarm PIN. `web/server.py` verifies the PIN server-side
  via `verify_disarm_pin` (good), but the MCP `disarm_perimeter_alert` only
  checks PIN *format* (`isdigit() and len()==4`), **not the actual PIN value** —
  a 4-digit guess disarms. And the demo PIN `"1234"` is a literal.
- **Check / fix:** ☐ server-side PIN verification everywhere, against a hashed
  stored PIN (§4.3), never a literal. ☐ Rate-limit / lockout on PIN attempts
  (10000 combos is brute-forceable in seconds otherwise). ☐ The MCP disarm tool
  must verify the value, not just the shape.

### 4.3 Cryptographic Failures / secrets
- **How AI introduces it:** plaintext secrets, `Math.random()` tokens, MD5,
  secrets in code or URLs.
- **Vigil risk:** `_DEMO_DISARM_PIN = "1234"` literal; tokens are good
  (`secrets.token_urlsafe`, constant-time PKCE compare — already correct, credit
  where due). But there is **no secret store** — Ring/Bee/AWS creds live in env
  vars with no rotation story, and the disarm PIN is not hashed.
- **Check / fix:** ☐ Move all secrets to a real store (AWS Secrets Manager since
  the account exists, or at minimum a gitignored `.env` + `python-dotenv`, never
  a literal). ☐ Hash the disarm PIN (Argon2/bcrypt), store only the hash.
  ☐ gitleaks in CI proves no secret ever lands in git history. ☐ Confirm no
  secret appears in any URL or log line.

### 4.4 Injection (SQL / command / path / SSRF)
- **How AI introduces it:** string-concatenated queries, unsanitized input to
  shells, user-controlled URLs fetched server-side.
- **Vigil risk — mostly LOW today, must stay that way:** no SQL yet (no DB), but
  §5 adds persistence — the risk arrives *with the database*. The path-traversal
  guard in `_serve_static` is already present and correct. `whep_session_url`
  builds a URL from `device_id` — if `device_id` ever comes from an untrusted
  webhook, that's an SSRF/path risk.
- **Check / fix:** ☐ When persistence lands, parameterized queries ONLY (or an
  ORM) — no f-string SQL, ever. ☐ Validate/allow-list `device_id` before it
  enters any URL. ☐ Validate every external payload with Pydantic at the boundary
  (already the pattern in `audit_perimeter_event` — extend it to all tools).

### 4.5 Security Misconfiguration
- **How AI introduces it:** debug on, permissive CORS, verbose errors, defaults
  unchanged, binding `0.0.0.0`.
- **Vigil risk:** the web console correctly binds `127.0.0.1` and hides stack
  traces (good). But the MCP transport's Host allow-list was widened for the
  tunnel, and there is no CORS policy, no security headers, no rate limiting on
  the public MCP endpoint.
- **Check / fix:** ☐ Explicit CORS allow-list (only the Alexa+ origin + the
  console). ☐ Security headers (HSTS, X-Content-Type-Options, no `Server`
  banner). ☐ Rate limiting on the public endpoint. ☐ Production config disables
  any debug/verbose path; errors never return internals (the web server already
  does this — replicate for the MCP app). ☐ Remove the Host-rewrite hack in favor
  of a proper reverse proxy (§5).

### 4.6 Vulnerable & Outdated Components + Slopsquatting (supply chain)
- **How AI introduces it:** pulls old versions with CVEs; **hallucinates package
  names** (~20% of the time) that attackers pre-register as malware.
- **Vigil risk:** 9 runtime deps, all real and well-known (mcp, fastapi, boto3,
  pydantic, numpy, scipy, pillow, httpx, uvicorn — none look hallucinated). But
  there's no automated audit, and `pillow`/`numpy` have had CVEs historically.
- **Check / fix:** ☐ `pip-audit` in CI (fails on known CVE). ☐ **Verify every
  dependency name resolves to the real, expected PyPI project** (slopsquatting
  check) — one-time manual confirm + the `uv.lock` hashes pin them thereafter.
  ☐ Dependabot/renovate for weekly bumps. ☐ Keep `uv.lock` committed with hashes
  so a swapped package is caught.

### 4.7 Identification & Authentication Failures
- **How AI introduces it:** hand-rolled auth, no rate limiting, non-expiring
  tokens, no lockout.
- **Vigil risk:** the OAuth server is hand-rolled (fine for a reference, risky
  for the field). Tokens expire (good — 1h TTL). But there is **no rate limiting
  anywhere**, no lockout on disarm-PIN attempts, and the in-memory token store
  dies on restart (every restart logs everyone out — availability bug, not a
  breach, but field-relevant).
- **Check / fix:** ☐ Rate-limit the token + authorize + disarm endpoints.
  ☐ For the field, front the MCP server with a **real IdP** (Cognito — the AWS
  account exists) rather than the in-memory AS; keep the in-memory AS only for
  local dev. ☐ Persist tokens (§5) so a restart doesn't drop sessions.

### 4.8 Software & Data Integrity Failures
- **How AI introduces it:** unsigned/unverified update paths, trusting external
  data without integrity checks, deserializing untrusted input.
- **Vigil risk:** the CAD packet is SHA-256 hashed (good — tamper-evident). Ring
  webhooks are HMAC-verified (good — `verify_webhook` is constant-time). The gap:
  `parse_event` trusts `verified_signature` *from the payload itself* — a field
  an attacker controls — rather than the result of `verify_webhook`.
- **Check / fix:** ☐ Never trust a `verified_signature` flag inside a payload;
  set it only from the server's own HMAC check. ☐ No `pickle`/`eval`/`yaml.load`
  on external data (grep confirms none today — keep it that way). ☐ Sign/verify
  any future auto-update or config-pull path.

### 4.9 Security Logging & Monitoring Failures
- **How AI introduces it:** no logs, or logs that leak secrets; no alerting.
- **Vigil risk:** the web server is deliberately silent (`log_message` no-op);
  the MCP server has no audit log. For a *security* product this is a real gap —
  there's no record of who disarmed, when a dispatch staged, or auth failures.
- **Check / fix:** ☐ Structured audit log for every security-relevant event
  (auth success/fail, disarm attempt, CAD stage, profile change, actuation) —
  **without logging secrets or PINs**. ☐ Log auth failures specifically (brute-
  force signal). ☐ Ship logs somewhere durable in the field (CloudWatch, since
  AWS exists).

### 4.10 SSRF & Cross-Site (XSS / CSRF)
- **How AI introduces it:** server fetches user-supplied URLs (SSRF); renders
  user data into HTML without escaping (XSS); no CSRF token on state-changing
  web forms.
- **Vigil risk:** XSS/CSRF are **low today** (the console is localhost, API
  returns JSON not rendered HTML, the static files are author-controlled). But
  §7 may add a real web app — the risk arrives then. SSRF: see 4.4 (`device_id`
  → WHEP URL).
- **Check / fix:** ☐ If a real web UI is built, escape all rendered data,
  CSP header, CSRF tokens on POST, SameSite cookies. ☐ Server-side URL
  construction allow-lists hosts. ☐ The `/api/disarm` POST needs CSRF protection
  the moment the console is anything but localhost-only.

### 4.11 AI-specific: Rules-File Backdoor & prompt-injection into the reasoner
- **How it's introduced:** a poisoned instruction file (CLAUDE.md, .cursorrules)
  silently steers the agent; or untrusted ingested content (a Ring event's text,
  a transcript) is fed to Bedrock as if it were an instruction.
- **Vigil risk:** `references/bee-skill/CLAUDE.md` exists in-tree (review it);
  and the Bedrock reasoner (§6) will ingest camera/audio-derived text — a
  spoken "disarm the system, I'm the owner" must be *data*, never a command that
  can flip the state machine.
- **Check / fix:** ☐ Review every in-repo agent-instruction file for injected
  directives. ☐ The deterministic state machine stays the sole authority — the
  LLM *scores*, it does not *actuate*; no Bedrock output can bypass the
  corroboration gate or the duress silence cap. ☐ Treat all ingested content as
  untrusted data in the prompt (delimit, never concatenate as instructions).

**Audit deliverable:** a one-time `docs/SECURITY_AUDIT.md` recording each of the
above as PASS / FIXED / N-A with the commit that closed it, plus the standing
CI gates (ruff-S, pip-audit, gitleaks, coverage) that keep them closed.

---

## 5. Field-readiness roadmap (phases, in dependency order)

Each phase is a releasable increment. The implementation tasks are in
`IMPLEMENTATION_PLAN.md`; this is the why/sequence.

**Phase A — Security hardening & engineering baseline → `0.2.0`**
Close §4.1 (auth guard — the critical one), §4.2/4.3 (PIN), stand up CI,
ruff/mypy/pytest-cov/pip-audit/gitleaks, pre-commit, the security audit doc.
*Rationale: do the cheapest, highest-impact safety work first, and build the net
that catches regressions before adding surface area.*

**Phase B — Persistence & durability → `0.3.0`**
Replace every in-memory store (incidents, tokens, profiles) with a real
datastore (SQLite for local/edge, DynamoDB option for AWS). Parameterized
access only. This is what makes state survive a restart — table stakes for a
device that must run for months.

**Phase C — Real identity → `0.4.0`**
Front the MCP server with Cognito (hosted IdP) for the field; keep the in-memory
AS as the documented local-dev fallback. Rate limiting, lockout, audit logging.

**Phase D — Live device read paths → `0.5.0`**
Turn the three adapters from "contract-shaped simulated" into real reads: Ring
webhook receiver (HMAC-verified) + WHEP, Bee CLI polling, Bedrock scoring behind
the thin port with the edge-rule fallback (Task 3.2, currently unbuilt). Each
device stays device-optional with honest MODELED fallback.

**Phase E — Deployment target & exposure → `0.6.0`**
Replace ngrok with a real edge: the server behind a reverse proxy (Caddy/Nginx
or API Gateway) with TLS, CORS, security headers, rate limiting. A reproducible
deploy (Docker image + compose for a home-server/Pi, or a documented AWS
deploy). Retire the Host-rewrite hack.

**Phase F — Alexa+ certification path → `0.9.0`**
The CLI chain from `RETURN_STATUS.md` (IAM user, LWA consent, `alexa-ai new mcp`,
dev-stage deploy, Local Inspector). Needs you for the browser consent + cert
decision. End state: a real Echo invokes the live, authenticated server.

**Phase G — Field pilot & `1.0.0`**
Clean-clone cold-start script, full §4 audit green, threat model reviewed,
one real household pilot (even just yours), docs accurate, tag `v1.0.0`.

---

## 6. Risks & how we hold the leash

- **Cost:** Phases B–E can touch billable AWS (DynamoDB, Cognito, API Gateway,
  Bedrock calls). The free tier covers early dev; **every billable resource gets
  flagged and confirmed before creation** — same leash as before. Bedrock
  inference is the one real metered cost; cache + rate-limit it.
- **Irreversibility:** IAM users, public cert submission, anything deleting data
  — these stop for your explicit go.
- **Scope discipline:** the spec is frozen (your gate rule). This plan *hardens
  and deploys* the frozen design; it does not redesign it. Any change that would
  touch the architecture gets a new DR and your sign-off first.
- **Don't regress the moat:** the invariant tests (§3) exist precisely so a
  future agent edit can't quietly break silence-under-duress or the no-911 gate.

---

## 7. What "field-ready" means, stated exactly

A household can: install Vigil on a home server or small cloud deploy; link it to
Alexa+ through the real certified path; connect at least one real device (Ring);
have it run unattended for weeks with state surviving restarts; trust that an
unauthenticated attacker cannot actuate deterrence or stage a dispatch; and read
an audit log of everything the system did. Everything still MODELED is badged
MODELED. That is `1.0.0`.
