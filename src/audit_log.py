"""Security audit logging (SEC.9) — a structured, redacted event trail.

A security product must record WHO did WHAT and WHEN: auth success/failure,
disarm attempts, CAD staging, profile changes, actuation. This module emits one
structured (JSON) log line per security-relevant event to the stdlib ``logging``
framework, so a field deployment can ship them to CloudWatch/syslog by config.

**Redaction is mandatory and automatic.** Secret-bearing fields (PIN, token,
authorization header, bearer, verifier, secret, password) are never written —
they are replaced with ``"***"``. The whole point is an audit trail that is
itself safe to keep, so logging the event must never leak the credential that
authorized it. Call ``audit(...)`` with structured kwargs, never a pre-formatted
string holding a secret.
"""

from __future__ import annotations

import json
import logging
from typing import Any

_LOGGER_NAME = "vigil.audit"
_logger = logging.getLogger(_LOGGER_NAME)

# Field-name fragments whose VALUES must never be logged (case-insensitive).
_REDACT_KEYS = (
    "pin",
    "token",
    "authorization",
    "bearer",
    "verifier",
    "secret",
    "password",
    "code_verifier",
)

_REDACTED = "***"


def _redact(key: str, value: Any) -> Any:
    k = key.lower()
    if any(frag in k for frag in _REDACT_KEYS):
        return _REDACTED
    return value


def audit(event: str, *, outcome: str = "", **fields: Any) -> None:
    """Emit one structured security-audit event.

    ``event`` is a stable name (e.g. ``auth.denied``, ``disarm.attempt``,
    ``cad.staged``, ``actuation``, ``profile.set``). ``outcome`` is a short
    result (e.g. ``ok`` / ``denied`` / ``locked_out``). Extra ``fields`` are
    structured context — any secret-bearing field is redacted automatically.
    """
    record = {"event": event}
    if outcome:
        record["outcome"] = outcome
    for key, value in fields.items():
        record[key] = _redact(key, value)
    _logger.info(json.dumps(record, sort_keys=True))


def configure(level: int = logging.INFO) -> None:
    """Attach a basic JSON-line handler if none is configured (idempotent).

    A field deployment replaces this with a CloudWatch/syslog handler; here it
    just ensures audit lines are emitted to stderr during dev.
    """
    if _logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    _logger.addHandler(handler)
    _logger.setLevel(level)
    _logger.propagate = False
