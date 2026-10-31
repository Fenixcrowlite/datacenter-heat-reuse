"""Idempotent evidence attachment to EXISTING DataCenter card; no task status change."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from v08_matlab_receipt_gate import ROOT, snapshot, digest

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-dchr-a25-v08-receipt-gate-20261025-2051"
FLAGS = ("STOP", "STOP.flag", "STOP.txt", ".STOP", "PAUSE", "PAUSE.flag",
         "PAUSE.txt", ".PAUSE", "STOP_MANAGED_WORKERS.txt")
ROOTS = (HERE, HERE.parent, CENTER, CENTER / "agent_knowledge", ROOT,
         ROOT / "matlab" / "pool_measurement_v08",
         ROOT / "results" / "pool_measurement_v08")
FILES = ("v08_matlab_receipt_gate.py", "test_v08_matlab_receipt_gate.py",
         "V08_MATLAB_RECEIPT_AUDIT.json", "MATLAB_V08_RECEIPT_RUNBOOK.md",
         "TEST_LOG.txt", "register_a25.py")

def register() -> dict:
    for root in ROOTS:
        for flag in FLAGS:
            if (root / flag).exists():
                raise RuntimeError("STOP_ACTIVE " + str(root / flag))
    for file in FILES:
        if not (HERE / file).is_file():
            raise RuntimeError("MISSING " + file)
    log = (HERE / "TEST_LOG.txt").read_text(encoding="utf-8")
    if "Ran 20 tests" not in log or not log.rstrip().endswith("OK"):
        raise RuntimeError("TEST_LOG_FAIL")
    report = json.loads((HERE / "V08_MATLAB_RECEIPT_AUDIT.json").read_text(encoding="utf-8"))
    if report["status"] != "BLOCKED_MATLAB_EXECUTION_RECEIPT_MISSING":
        raise RuntimeError("RECEIPT_STATUS_UNEXPECTED")
    if report["source_class"] != "D_SYNTHETIC" or len(report["current_sha256"]) != 13:
        raise RuntimeError("EVIDENCE_SCHEMA")
    if report["current_sha256"] != snapshot(ROOT)["sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    hashes = {name: digest(HERE / name) for name in FILES}
    manifest = HERE / "SHA256_MANIFEST.json"
    manifest.write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
    payload = {
        "scope": "isolated_matlab_v08_execution_receipt_validation_gate",
        "artifact_directory": str(HERE),
        "evidence_sha256": hashes["V08_MATLAB_RECEIPT_AUDIT.json"],
        "source_code_sha256": hashes["v08_matlab_receipt_gate.py"],
        "qa_log_sha256": hashes["TEST_LOG.txt"],
        "manifest_sha256": digest(manifest),
        "qa": "20/20 synthetic mutation tests PASS; py_compile PASS; 13 actual source/output SHA256 verified",
        "finding": "No matching MATLAB v08 execution receipt/log in four bounded searched directories; static release consistency is NOT execution attestation",
        "limits": "No MATLAB process was started; no proof of actual process execution, physical validation or real measurements",
        "next_step": "Owner-controlled isolated MATLAB v08 rerun with trusted process log+hash receipt, then run v08_matlab_receipt_gate.py --receipt"
    }
    with sqlite3.connect(CENTER / "tasks.sqlite3", timeout=5, isolation_level=None) as db:
        db.execute("PRAGMA busy_timeout=5000")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("REGISTRY_CORRUPT")
        db.execute("BEGIN IMMEDIATE")
        try:
            state = db.execute("SELECT status,stage FROM tasks WHERE id=?", (TASK,)).fetchone()
            if state != ("review", "planned"):
                raise RuntimeError("TASK_STATE_CHANGED " + repr(state))
            rows = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                              (TASK, ACTOR)).fetchall()
            if len(rows) > 1:
                raise RuntimeError("DUPLICATE")
            if rows:
                if json.loads(rows[0][1]) != payload:
                    raise RuntimeError("ACTOR_COLLISION")
                event, action = rows[0][0], "EXISTING_EVENT"
            else:
                event = db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                                   (TASK, time.time(), "evidence", ACTOR,
                                    json.dumps(payload, ensure_ascii=False))).lastrowid
                action = "CREATED_EVENT"
            db.commit()
        except Exception:
            db.rollback()
            raise
    result = {"task_id": TASK, "event_id": event, "action": action, **payload}
    (HERE / "REGISTRY_RESULT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    return result

if __name__ == "__main__":
    x = register()
    print(json.dumps({k: x[k] for k in ("task_id", "event_id", "action", "evidence_sha256")}))
