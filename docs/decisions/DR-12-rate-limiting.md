# DR-12 — Rate limiting on sensitive endpoints

- **Status:** Accepted
- **Status history:** Proposed 2026-10-27 → Accepted 2026-10-27 (Phase C hardening)
- **Phase:** C (identity / hardening)

## Question
How to defend the public auth + tool surface (`/authorize`, `/token`, `/mcp`)
against a brute-force or DoS flood, beyond SEC.2's per-PIN disarm lockout?

## Decision
A fixed-window per-client request counter (`RateLimiter`) applied by a
`RateLimitMiddleware` layered OUTERMOST on the ASGI app (added last → runs
first, so a flood is throttled before any auth work). Default 60 req / 60 s per
client key (X-Forwarded-For first hop, else peer IP). Over-cap requests get
`429` + `Retry-After: 60`. Discovery/health paths are never throttled.

## Why
- **Complements, not duplicates, SEC.2.** SEC.2 locks out per-PIN guessing;
  this caps per-CLIENT request volume on the auth endpoints a brute-forcer hits.
- **Outermost placement** means invalid-token floods cost no bearer-validation
  work — the throttle fires before the auth middleware.
- **Dependency-free, single-process.** Right-sized for an edge node; documented
  as needing a shared store (Redis/DynamoDB) behind multiple workers.

## Strongest argument against
A single-process in-memory counter does not coordinate across workers or nodes,
so behind a multi-worker deployment the effective cap is N× the configured one.
Accepted for the single-process edge target; Phase E (real deployment) moves the
counter to a shared store if the deploy fans out. X-Forwarded-For is also
spoofable unless the reverse proxy sets it authoritatively — Phase E's proxy
config (E.2) owns that.

## Enforcement / test
`tests/test_rate_limit.py` — cap, window reset, key independence, middleware 429
on a sensitive path, and no-throttle on discovery.
