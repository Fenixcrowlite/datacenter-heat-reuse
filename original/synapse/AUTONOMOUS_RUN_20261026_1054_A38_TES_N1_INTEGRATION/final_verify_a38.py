"""Independent final evidence/registry integrity gate for A38 (read-only except own FINAL_QA.json)."""
import hashlib
import json
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a38-dchr-tes-n1-integrated-20261026-1054"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((HERE / "SHA256_MANIFEST.json").read_text(encoding="utf8"))
    assert len(manifest) >= 20
    for name, digest in manifest.items():
        if sha(HERE / name) != digest:
            raise RuntimeError("MANIFEST_MISMATCH " + name)
    evidence = json.loads((HERE / "EVIDENCE.json").read_text(encoding="utf8"))
    results = json.loads((HERE / "RESULTS_A38.json").read_text(encoding="utf8"))
    qa = json.loads((HERE / "INDEPENDENT_QA.json").read_text(encoding="utf8"))
    receipt = json.loads((HERE / "REGISTRY_RESULT.json").read_text(encoding="utf8"))
    assert evidence["physical_release_allowed"] is False
    assert evidence["matlab_stateflow_executed"] is False
    assert results["physical_release_allowed"] is False
    assert qa["status"] == "PASS" and qa["decimal_invariant_checks"] == 225792
    assert sha(HERE / "EVIDENCE.json") == receipt["evidence_sha256"]
    assert sha(HERE / "SHA256_MANIFEST.json") == receipt["manifest_sha256"]
    assert sha(HERE / "RESULTS_A38.json") == receipt["results_sha256"]
    with sqlite3.connect(CENTER / "tasks.sqlite3", timeout=6) as db:
        integrity = db.execute("pragma quick_check").fetchone()[0]
        assert integrity == "ok"
        task = db.execute("select status,stage,worker_pid,owner from tasks where id=?", (TASK,)).fetchone()
        assert task == ("review", "planned", None, "MATLAB/Stateflow QA")
        events = db.execute("select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                            (TASK, ACTOR)).fetchall()
        assert len(events) == 1
        event_id, event_json = events[0]
        assert event_id == receipt["event_id"]
        assert json.loads(event_json) == {k: v for k, v in receipt.items() if k not in ("task_id", "event_id")}
    final = {
        "status": "PASS", "manifest_files": len(manifest),
        "sha256_verified": len(manifest), "event_id": event_id,
        "exact_event_count": len(events), "sqlite_quick_check": integrity,
        "task_status": task[0], "task_stage": task[1],
        "active_worker_pid": task[2], "matlab_executed": False,
        "unit_tests": 16, "decimal_checks": qa["decimal_invariant_checks"],
        "cases": 12, "intervals_per_case": 672,
        "physical_release_allowed": False,
    }
    (HERE / "FINAL_QA.json").write_text(json.dumps(final, indent=2) + "\n", encoding="utf8")
    print(json.dumps(final, indent=2))
if __name__ == "__main__":
    main()
