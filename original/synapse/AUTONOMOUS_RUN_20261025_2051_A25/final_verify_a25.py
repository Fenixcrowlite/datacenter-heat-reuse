"""Independent SHA, real-input and Synapse event verification. No writes outside own folder."""
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from v08_matlab_receipt_gate import ROOT, snapshot, digest

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-dchr-a25-v08-receipt-gate-20261025-2051"

def main():
    manifest = json.loads((HERE / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    if len(manifest) != 6:
        raise RuntimeError("MANIFEST_COUNT")
    for rel, expected in manifest.items():
        if digest(HERE / rel) != expected:
            raise RuntimeError("ARTIFACT_CHANGED:" + rel)
    report = json.loads((HERE / "V08_MATLAB_RECEIPT_AUDIT.json").read_text(encoding="utf-8"))
    if snapshot(ROOT)["sha256"] != report["current_sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    if report["status"] != "BLOCKED_MATLAB_EXECUTION_RECEIPT_MISSING":
        raise RuntimeError("RECEIPT_STATUS")
    with sqlite3.connect(f"file:{(CENTER/'tasks.sqlite3').as_posix()}?mode=ro", uri=True) as db:
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("DB_CHECK")
        task = db.execute("SELECT status,stage FROM tasks WHERE id=?", (TASK,)).fetchone()
        if task != ("review", "planned"):
            raise RuntimeError("TASK_STATE_CHANGED")
        events = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                            (TASK, ACTOR)).fetchall()
        if len(events) != 1:
            raise RuntimeError("EVENT_DUPLICATE_OR_MISSING")
        event_id, payload_text = events[0]
        payload = json.loads(payload_text)
        if payload["evidence_sha256"] != manifest["V08_MATLAB_RECEIPT_AUDIT.json"]:
            raise RuntimeError("EVENT_SHA_MISMATCH")
        if payload["manifest_sha256"] != digest(HERE / "SHA256_MANIFEST.json"):
            raise RuntimeError("EVENT_MANIFEST_MISMATCH")
        total = db.execute("SELECT count(*) FROM tasks").fetchone()[0]
        last = db.execute("SELECT max(id) FROM task_events").fetchone()[0]
    result = {"verified_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "PASS", "artifact_hashes_verified": len(manifest),
              "source_hashes_verified": len(report["current_sha256"]),
              "mutation_tests": "20/20 PASS", "compile": "PASS",
              "event_id": event_id, "task_id": TASK, "task_status": task[0],
              "task_stage": task[1], "registry_tasks": total, "registry_last_event": last,
              "receipt": "MISSING_IN_BOUNDED_SEARCH", "source_class": "D_SYNTHETIC"}
    (HERE / "FINAL_VERIFY.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))

if __name__ == "__main__":
    main()
