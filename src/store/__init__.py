"""Vigil persistence layer (Phase B).

A small, interface-clean key-record store so operational state (incidents,
and — in later Phase B tasks — tokens and guard profiles) survives a process
restart. Two implementations ship:

* :class:`InMemoryStore` — the previous behavior, for tests and ephemeral runs.
* :class:`SqliteStore`   — durable local/edge storage (one file on disk).

The interface is deliberately minimal (get / put / list / delete over JSON
records keyed by a namespace + id), so a field deployment can add a DynamoDB
implementation behind the same :class:`IncidentStore` protocol without touching
the server tools. Values are JSON-serializable dicts; access is parameterized
(SEC.4/§4.4 — no string-built SQL).
"""

from src.store.base import IncidentStore, InMemoryStore
from src.store.kv_store import InMemoryKV, KeyValueStore, SqliteKV
from src.store.sqlite_store import SqliteStore

__all__ = [
    "IncidentStore",
    "InMemoryStore",
    "SqliteStore",
    "KeyValueStore",
    "InMemoryKV",
    "SqliteKV",
]
