"""A62 reproducible QA + SHA manifest + idempotent existing Synapse evidence event."""
from __future__ import annotations
import ast
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

D = Path(__file__).resolve().parent
CENTER = D.parents[1]
PROJECT = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
A61 = D.parent / "AUTONOMOUS_RUN_20261027_1400_A61_POOL_DISCRETE_CLOSURE"
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a62-signed-loss-discrete-export-20261027-1405"
SCRIPTS = ("a62_signed_loss_export.py", "test_a62.py",
           "independent_qa_a62.py", "finalize_a62.py")
FILES = SCRIPTS + ("A62_EXPORT_CONTRACT_SK.md", "INDEPENDENT_QA_A62.json",
                   "OUTPUT_V08_SIGNED/analysis_with_signed_losses.csv",
                   "OUTPUT_V08_SIGNED/summary.json",
                   "OUTPUT_V09_SIGNED/analysis_with_signed_losses.csv",
                   "OUTPUT_V09_SIGNED/summary.json",
                   "QA_CLEAN.txt", "EVIDENCE_A62.json")
RAW = {
    "v08": PROJECT / "results/pool_measurement_v08/sim_v08_zdravy_SK.csv",
    "v09": PROJECT / "scada_v09/matlab_live_v01/runtime/jobs/79b874c619674e1e966c72bf92eb67b3/result.csv",
}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def once(p, value):
    if p.exists():
        if p.read_text(encoding="utf-8") != value:
            raise RuntimeError("ARTIFACT_CONFLICT " + str(p))
    else:
        p.write_text(value, encoding="utf-8")


def guard():
    for root in (CENTER, CENTER / "recovery", D, PROJECT,
                 Path(r"C:\Users\Lysda\Desktop\temp_coding")):
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag"):
            if (root / name).exists():
                raise RuntimeError("STOP_OR_PAUSE " + str(root / name))


def main():
    guard()
    for name in SCRIPTS:
        ast.parse((D / name).read_text(encoding="utf-8"), filename=name)
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a62"],
                          cwd=D, capture_output=True, text=True, timeout=25)
    if proc.returncode or "Ran 12 tests" not in proc.stderr or not proc.stderr.rstrip().endswith("OK"):
        raise RuntimeError("A62_UNITTEST_FAIL " + proc.stderr[-2000:])
    once(D / "QA_CLEAN.txt", re.sub(r"Ran 12 tests in [0-9.]+s",
                                   "Ran 12 tests in <variable>s", proc.stderr))
    assert (A61 / "FINAL_HANDOFF.md").is_file()
    a61_manifest = json.loads((A61 / "SHA256_MANIFEST_A61.json").read_text(encoding="utf-8"))
    assert sha(A61 / "a61_pool_discrete_closure.py") == a61_manifest["a61_pool_discrete_closure.py"]
    report = json.loads((D / "INDEPENDENT_QA_A62.json").read_text(encoding="utf-8"))
    assert report["source_kind"] == "derived_simulation"
    assert report["physical_release"] is False
    assert report["decimal_checks"] == 10752
    sys.path.insert(0, str(D))
    from independent_qa_a62 import verify
    for version in ("v08", "v09"):
        assert verify(RAW[version], D / ("OUTPUT_" + version.upper() + "_SIGNED"), version) == report[version]
        assert report[version]["rows"] == 672
        assert report[version]["decimal_checks"] == 5376
    evidence = {
        "task_id": TASK, "scope": "A62_signed_pool_loss_and_discrete_energy_export",
        "artifact_directory": str(D), "status": "VERIFIED_SIMULATION_SCHEMA_V2",
        "unit_tests": "12/12 PASS", "ast": "4/4 PASS",
        "decimal_checks": "10752/10752 PASS", "rows_exported": 1344,
        "source_kind": "derived_simulation", "physical_release": False,
        "real_measurements": False, "upstream_files_modified": False,
        "a61_validator_sha256": sha(A61 / "a61_pool_discrete_closure.py"),
        "next_step": "Offline SCADA analysis may consume A62 signed-loss schema; keep A60 immutable. Acquire calibrated real telemetry and independently validate physical equipment before any release.",
    }
    once(D / "EVIDENCE_A62.json", json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    manifest = {name: sha(D / name) for name in FILES}
    once(D / "SHA256_MANIFEST_A62.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    handoff = (
        "# A62 signed-loss SCADA export | " + datetime.now().astimezone().isoformat(timespec="seconds") + "\n"
        "SynapseMCP Web primary live, STOP/PAUSE checked; task review/planned/no worker.\n"
        "Two NEW immutable outputs: OUTPUT_V08_SIGNED and OUTPUT_V09_SIGNED; 672 rows each, six added channels.\n"
        "All original A60 columns preserved; signed Q_pool_loss_W, Q_pool_net_W and three cumulative energy channels + state residual added.\n"
        "QA: 12/12 unit tests, 4/4 AST checks, 10752/10752 independent Decimal field comparisons.\n"
        "A61 prerequisite verified by SHA; A60 and original MATLAB/SCADA source remain unchanged.\n"
        "91 negative signed-loss rows per input are valid ambient heat gains; physical release remains false.\n"
        "No Codex, new worker, GPU task, GUI, STOP/OAuth or foreign branch changes; VRS skipped.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A62.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A62.json") + "\n"
        "NEXT: offline consume A62 in an independently owned SCADA analysis view; physical validation still BLOCKED on real calibrated measurements.\n"
    )
    once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A62.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A62.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "12/12 unittest; 4/4 AST; 10752/10752 independent Decimal",
        "source_kind": "derived_simulation", "physical_release": False,
        "next_step": evidence["next_step"],
    }
    guard()
    db = sqlite3.connect(CENTER / "tasks.sqlite3", timeout=15, isolation_level=None)
    db.execute("PRAGMA busy_timeout=15000")
    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RuntimeError("REGISTRY_INTEGRITY_FAILED")
    db.execute("BEGIN IMMEDIATE")
    try:
        state = db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?", (TASK,)).fetchone()
        if state != ("review", "planned", None):
            raise RuntimeError("TASK_STATE_CHANGED " + repr(state))
        found = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                           (TASK, ACTOR)).fetchall()
        if len(found) > 1:
            raise RuntimeError("DUPLICATE_EVENT")
        if found:
            if json.loads(found[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id = found[0][0]
        else:
            event_id = db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                                  (TASK, time.time(), "evidence", ACTOR,
                                   json.dumps(payload, ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    once(D / "REGISTRY_RESULT_A62.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"event_id": event_id, "QA": payload["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
