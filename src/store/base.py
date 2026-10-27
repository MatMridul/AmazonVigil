"""Store protocol + in-memory implementation (Phase B.1).

``IncidentStore`` is the one interface the server depends on. It stores a JSON
record (a dict) per incident id and supports the three operations the MCP tools
actually need: merge a partial update into a record, read a record, and list
known ids. Keeping it this small means the SQLite and (future) DynamoDB backends
are drop-in, and the server never knows which one it holds.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class IncidentStore(Protocol):
    """Durable key-record store for incident state."""

    def merge(self, incident_id: str, fields: dict) -> None:
        """Merge ``fields`` into the record for ``incident_id`` (upsert)."""
        ...

    def get(self, incident_id: str) -> dict | None:
        """Return the record for ``incident_id``, or None if unknown."""
        ...

    def ids(self) -> list[str]:
        """Return all known incident ids."""
        ...

    def delete(self, incident_id: str) -> None:
        """Remove an incident record (no-op if absent)."""
        ...


class InMemoryStore:
    """Ephemeral dict-backed store (previous behavior; tests, transient runs)."""

    def __init__(self) -> None:
        self._data: dict[str, dict] = {}

    def merge(self, incident_id: str, fields: dict) -> None:
        self._data.setdefault(incident_id, {}).update(fields)

    def get(self, incident_id: str) -> dict | None:
        rec = self._data.get(incident_id)
        return dict(rec) if rec is not None else None

    def ids(self) -> list[str]:
        return list(self._data.keys())

    def delete(self, incident_id: str) -> None:
        self._data.pop(incident_id, None)
