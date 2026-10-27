"""Phase B persistence tests — state survives a restart.

Proves the store interface (in-memory + SQLite parity) and the load-bearing
Phase B guarantee: a SQLite-backed incident written by one process instance is
still there for a FRESH instance pointed at the same file — i.e. it survives a
restart. The in-memory store deliberately does NOT survive (and the test asserts
that contrast, so the two behaviors can't be silently confused).
"""

from __future__ import annotations

import pytest

from src.store import InMemoryStore, SqliteStore
from src.store.base import IncidentStore


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path) -> IncidentStore:
    if request.param == "memory":
        return InMemoryStore()
    return SqliteStore(tmp_path / "state.db")


# --- interface parity (both backends behave identically) ------------------ #


def test_merge_and_get(store):
    store.merge("INC-1", {"cad": {"sha256": "abc"}})
    rec = store.get("INC-1")
    assert rec["cad"]["sha256"] == "abc"


def test_merge_is_partial_update(store):
    store.merge("INC-2", {"cad": {"x": 1}})
    store.merge("INC-2", {"disarmed": True})
    rec = store.get("INC-2")
    assert rec["cad"] == {"x": 1}
    assert rec["disarmed"] is True  # earlier field preserved


def test_get_unknown_is_none(store):
    assert store.get("nope") is None


def test_ids_lists_known(store):
    store.merge("A", {"k": 1})
    store.merge("B", {"k": 2})
    assert set(store.ids()) == {"A", "B"}


def test_delete(store):
    store.merge("X", {"k": 1})
    store.delete("X")
    assert store.get("X") is None
    store.delete("X")  # idempotent


def test_implements_protocol(store):
    assert isinstance(store, IncidentStore)


# --- the Phase B guarantee: SQLite survives a restart --------------------- #


def test_sqlite_state_survives_restart(tmp_path):
    db = tmp_path / "survive.db"

    # Instance 1 writes an incident, then goes away (simulating a crash/restart).
    s1 = SqliteStore(db)
    s1.merge("INC-RESTART", {"cad": {"sha256": "deadbeef"}, "disarmed": False})
    del s1

    # Instance 2 is a cold start against the same file — the record is still there.
    s2 = SqliteStore(db)
    rec = s2.get("INC-RESTART")
    assert rec is not None, "SQLite state did NOT survive restart"
    assert rec["cad"]["sha256"] == "deadbeef"
    assert rec["disarmed"] is False
    assert "INC-RESTART" in s2.ids()


def test_inmemory_does_not_survive_restart():
    s1 = InMemoryStore()
    s1.merge("INC-EPH", {"k": 1})
    # A fresh in-memory instance is empty — ephemeral by design.
    s2 = InMemoryStore()
    assert s2.get("INC-EPH") is None
