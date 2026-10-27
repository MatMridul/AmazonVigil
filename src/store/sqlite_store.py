"""Durable SQLite-backed incident store (Phase B.1).

One row per incident: ``(incident_id TEXT PRIMARY KEY, record TEXT)`` where
``record`` is the JSON-serialized dict. ``merge`` reads-modifies-writes the JSON
so a partial update behaves exactly like the in-memory ``dict.update``, which is
what the MCP tools rely on (stage CAD, mark disarmed, etc.).

All access is PARAMETERIZED (no string-built SQL — §4.4). The connection uses
``check_same_thread=False`` with a short-lived connection per call so the
ThreadingHTTP/MCP server can touch it from worker threads safely; WAL mode keeps
concurrent reads non-blocking. State written here survives a process restart —
the whole point of Phase B.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_DDL = """
CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    record      TEXT NOT NULL
)
"""


class SqliteStore:
    """Durable incident store backed by a single SQLite file."""

    def __init__(self, db_path: str | Path = "vigil_state.db") -> None:
        self._path = str(db_path)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(_DDL)

    def merge(self, incident_id: str, fields: dict) -> None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record FROM incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
            record = json.loads(row[0]) if row else {}
            record.update(fields)
            conn.execute(
                "INSERT INTO incidents (incident_id, record) VALUES (?, ?) "
                "ON CONFLICT(incident_id) DO UPDATE SET record = excluded.record",
                (incident_id, json.dumps(record)),
            )

    def get(self, incident_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT record FROM incidents WHERE incident_id = ?",
                (incident_id,),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def ids(self) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT incident_id FROM incidents").fetchall()
        return [r[0] for r in rows]

    def delete(self, incident_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM incidents WHERE incident_id = ?", (incident_id,))
