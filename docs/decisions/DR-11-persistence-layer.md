# DR-11 — Persistence layer: pluggable IncidentStore (SQLite default)

- **Status:** Accepted
- **Status history:** Proposed 2026-10-27 → Accepted 2026-10-27 (Phase B.1/B.2)
- **Phase:** B (persistence & durability)

## Question
How should Vigil persist operational state (incidents now; tokens, guard
profiles next) so it survives a process restart, without coupling the server to
one database and without reopening the frozen architecture?

## Decision
Introduce a minimal `IncidentStore` protocol (`merge` / `get` / `ids` /
`delete` over JSON records keyed by incident id) with two implementations:
`InMemoryStore` (ephemeral — tests, transient runs) and `SqliteStore` (durable,
one file). The server depends only on the protocol; `_build_incident_store()`
selects the backend from `VIGIL_STATE_DB` (set → SQLite, unset → in-memory).

## Why
- **Smallest surface that covers real use.** The MCP tools only stage CAD, mark
  disarmed, and list/read incidents — three operations. A key-record store is
  enough; no ORM, no schema churn.
- **Field-swappable.** A DynamoDB backend (Phase C, AWS account exists) drops in
  behind the same protocol with zero server change.
- **Safe by construction.** All SQLite access is parameterized (§4.4 — no
  string-built SQL); WAL mode + per-call connections make it safe from the
  ThreadingHTTP/MCP worker threads.
- **Honest default.** In-memory stays the default so tests and offline demos are
  unchanged; durability is opt-in via one env var, and the restart-survival
  guarantee is proven by a test, not asserted in prose.

## Strongest argument against
A bare key-record store will not express relational queries (e.g. "all incidents
disarmed in the last hour") that a richer schema would. Accepted for now: the
current tools need none of that, and the protocol can grow a query method (or be
replaced by a DynamoDB/SQL backend) without breaking callers. Revisit if a
reporting/analytics surface lands.

## Enforcement / test
`tests/test_store.py::test_sqlite_state_survives_restart` — a record written by
one `SqliteStore` instance is read by a fresh instance on the same file.
Parity tests run both backends through the identical interface.
