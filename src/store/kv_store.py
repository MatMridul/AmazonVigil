"""Generic key-value store (Phase B.3/B.4).

Backs OAuth token/code persistence and guard-profile persistence. Same shape as
the incident store — a namespaced JSON key-value map — so the two concerns share
one SQLite file and one backend contract. Values are JSON-serializable.

Keys are namespaced (``namespace`` + ``key``) so tokens, codes and profiles
never collide. All SQLite access is parameterized (§4.4).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class KeyValueStore(Protocol):
    """Namespaced JSON key-value store."""

    def put(self, namespace: str, key: str, value: dict) -> None: ...
    def get(self, namespace: str, key: str) -> dict | None: ...
    def delete(self, namespace: str, key: str) -> None: ...
    def keys(self, namespace: str) -> list[str]: ...


class InMemoryKV:
    """Ephemeral dict-backed KV (tests / transient runs)."""

    def __init__(self) -> None:
        self._d: dict[tuple[str, str], dict] = {}

    def put(self, namespace: str, key: str, value: dict) -> None:
        self._d[(namespace, key)] = dict(value)

    def get(self, namespace: str, key: str) -> dict | None:
        v = self._d.get((namespace, key))
        return dict(v) if v is not None else None

    def delete(self, namespace: str, key: str) -> None:
        self._d.pop((namespace, key), None)

    def keys(self, namespace: str) -> list[str]:
        return [k for (ns, k) in self._d if ns == namespace]


_DDL = """
CREATE TABLE IF NOT EXISTS kv (
    namespace TEXT NOT NULL,
    key       TEXT NOT NULL,
    value     TEXT NOT NULL,
    PRIMARY KEY (namespace, key)
)
"""


class SqliteKV:
    """Durable KV backed by a single SQLite file (shares the state DB)."""

    def __init__(self, db_path: str | Path = "vigil_state.db") -> None:
        self._path = str(db_path)
        with self._connect() as conn:
            conn.execute(_DDL)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def put(self, namespace: str, key: str, value: dict) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO kv (namespace, key, value) VALUES (?, ?, ?) "
                "ON CONFLICT(namespace, key) DO UPDATE SET value = excluded.value",
                (namespace, key, json.dumps(value)),
            )

    def get(self, namespace: str, key: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM kv WHERE namespace = ? AND key = ?",
                (namespace, key),
            ).fetchone()
        return json.loads(row[0]) if row else None

    def delete(self, namespace: str, key: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM kv WHERE namespace = ? AND key = ?", (namespace, key))

    def keys(self, namespace: str) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute("SELECT key FROM kv WHERE namespace = ?", (namespace,)).fetchall()
        return [r[0] for r in rows]
