"""Immutable checkpoint timestamps and idempotent Synapse evidence registration.

This module does not start workers or alter existing evidence.
"""
from __future__ import annotations
import hashlib
import json
import os
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

_HEX = re.compile(r"^[0-9a-f]{64}$")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(data):
    return (json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def immutable(path, data):
    """Write once with exclusive creation; on replay compare exact bytes."""
    path = Path(path)
    payload = data if isinstance(data, bytes) else data.encode("utf-8")
    try:
        fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        if path.read_bytes() != payload:
            raise ValueError("IMMUTABLE_CONFLICT:" + str(path))
        return False
    with os.fdopen(fd, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return True


def freeze(path, scope, source_sha256, now=None):
    """Create timestamp once, then reuse. Reject changed inputs or malformed state."""
    path = Path(path)
    if not isinstance(source_sha256, str) or not _HEX.fullmatch(source_sha256):
        raise ValueError("INVALID_SOURCE_HASH")
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("INVALID_SCOPE")
    if not path.exists():
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ValueError("NAIVE_TIME")
        stamp = instant.astimezone(timezone.utc).isoformat(timespec="seconds")
        immutable(path, canonical({"schema": 1, "scope": scope,
                                   "source_sha256": source_sha256,
                                   "created_at_utc": stamp}))
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        if set(record) != {"schema", "scope", "source_sha256", "created_at_utc"}:
            raise ValueError("INVALID_CHECKPOINT_FIELDS")
        stamp = datetime.fromisoformat(record["created_at_utc"])
        if stamp.tzinfo is None or stamp.utcoffset() is None or stamp.utcoffset().total_seconds() != 0:
            raise ValueError("INVALID_CHECKPOINT_TIME")
        if record["schema"] != 1 or record["scope"] != scope or record["source_sha256"] != source_sha256:
            raise ValueError("CHECKPOINT_CONFLICT")
        if canonical(record) != path.read_bytes():
            raise ValueError("NONCANONICAL_CHECKPOINT")
        return record
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("INVALID_CHECKPOINT") from exc


def record_once(registry, task_id, actor, payload):
    """Insert exactly one evidence event; require unchanged task ownership/state."""
    if not task_id.startswith("scc-") or not actor:
        raise ValueError("INVALID_IDENTITY")
    db = sqlite3.connect(registry, timeout=15, isolation_level=None)
    try:
        db.execute("PRAGMA busy_timeout=15000")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("REGISTRY_INTEGRITY")
        db.execute("BEGIN IMMEDIATE")
        try:
            state = db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?", (task_id,)).fetchone()
            if state != ("review", "planned", None):
                raise ValueError("TASK_STATE_CHANGED:" + repr(state))
            rows = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                              (task_id, actor)).fetchall()
            if len(rows) > 1:
                raise ValueError("DUPLICATE_EVENTS")
            if rows:
                if json.loads(rows[0][1]) != payload:
                    raise ValueError("EVENT_CONFLICT")
                event_id = rows[0][0]
            else:
                event_id = db.execute(
                    "INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                    (task_id, time.time(), "evidence", actor, json.dumps(payload, ensure_ascii=False, sort_keys=True))
                ).lastrowid
            db.commit()
            return event_id
        except BaseException:
            db.rollback()
            raise
    finally:
        db.close()
