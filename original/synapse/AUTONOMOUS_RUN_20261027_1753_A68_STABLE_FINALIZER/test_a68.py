"""Regression tests for A66's changing timestamp / immutable conflict defect."""
from contextlib import closing
import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from a68_checkpoint import canonical, freeze, immutable, record_once, sha


class CheckpointTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p = self.root / "checkpoint.json"
        self.hash = "a" * 64

    def test_frozen_time_replays_byte_identically(self):
        first = freeze(self.p, "a68", self.hash, datetime(2026, 10, 27, 16, 0, tzinfo=timezone.utc))
        before = self.p.read_bytes()
        second = freeze(self.p, "a68", self.hash, datetime(2030, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(first, second)
        self.assertEqual(before, self.p.read_bytes())
        self.assertEqual(first["created_at_utc"], "2026-10-27T16:00:00+00:00")

    def test_hash_mismatch_fails_closed(self):
        freeze(self.p, "a68", self.hash)
        with self.assertRaisesRegex(ValueError, "CHECKPOINT_CONFLICT"):
            freeze(self.p, "a68", "b" * 64)

    def test_scope_mismatch_fails_closed(self):
        freeze(self.p, "a68", self.hash)
        with self.assertRaisesRegex(ValueError, "CHECKPOINT_CONFLICT"):
            freeze(self.p, "foreign", self.hash)

    def test_bad_hash_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE_HASH"):
            freeze(self.p, "a68", "123")

    def test_naive_time_rejected(self):
        with self.assertRaisesRegex(ValueError, "NAIVE_TIME"):
            freeze(self.p, "a68", self.hash, datetime(2026, 10, 27))

    def test_corrupted_checkpoint_rejected(self):
        self.p.write_text("{", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INVALID_CHECKPOINT"):
            freeze(self.p, "a68", self.hash)

    def test_noncanonical_checkpoint_rejected(self):
        freeze(self.p, "a68", self.hash)
        self.p.write_text(json.dumps(json.loads(self.p.read_text())), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "NONCANONICAL_CHECKPOINT"):
            freeze(self.p, "a68", self.hash)

    def test_immutable_replay_and_conflict(self):
        self.assertTrue(immutable(self.p, b"fixed"))
        self.assertFalse(immutable(self.p, b"fixed"))
        with self.assertRaisesRegex(ValueError, "IMMUTABLE_CONFLICT"):
            immutable(self.p, b"changed")

    def test_sha_matches_independent_hash(self):
        import hashlib
        immutable(self.p, canonical({"x": 1}))
        self.assertEqual(sha(self.p), hashlib.sha256(self.p.read_bytes()).hexdigest())


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db = Path(self.tmp.name) / "tasks.db"
        with closing(sqlite3.connect(self.db, isolation_level=None)) as conn:
            conn.executescript("""
                CREATE TABLE tasks(id TEXT PRIMARY KEY,status TEXT,stage TEXT,worker_pid INTEGER);
                CREATE TABLE task_events(id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id TEXT,at REAL,kind TEXT,actor TEXT,data_json TEXT);
                INSERT INTO tasks VALUES ('scc-demo','review','planned',NULL);
            """)

    def test_exact_replay_one_event(self):
        payload = {"sha": "a" * 64}
        first = record_once(self.db, "scc-demo", "a68-test", payload)
        second = record_once(self.db, "scc-demo", "a68-test", payload)
        self.assertEqual(first, second)
        with closing(sqlite3.connect(self.db, isolation_level=None)) as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM task_events").fetchone()[0], 1)

    def test_changed_payload_rejected(self):
        record_once(self.db, "scc-demo", "a68-test", {"x": 1})
        with self.assertRaisesRegex(ValueError, "EVENT_CONFLICT"):
            record_once(self.db, "scc-demo", "a68-test", {"x": 2})

    def test_changed_task_state_rejected(self):
        with closing(sqlite3.connect(self.db, isolation_level=None)) as conn:
            conn.execute("UPDATE tasks SET worker_pid=999 WHERE id='scc-demo'")
        with self.assertRaisesRegex(ValueError, "TASK_STATE_CHANGED"):
            record_once(self.db, "scc-demo", "a68-test", {"x": 1})

    def test_duplicate_events_rejected(self):
        with closing(sqlite3.connect(self.db, isolation_level=None)) as conn:
            conn.execute("INSERT INTO task_events(task_id,kind,actor,data_json) VALUES (?,?,?,?)",
                         ("scc-demo", "evidence", "a68-test", "{}"))
            conn.execute("INSERT INTO task_events(task_id,kind,actor,data_json) VALUES (?,?,?,?)",
                         ("scc-demo", "evidence", "a68-test", "{}"))
        with self.assertRaisesRegex(ValueError, "DUPLICATE_EVENTS"):
            record_once(self.db, "scc-demo", "a68-test", {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
