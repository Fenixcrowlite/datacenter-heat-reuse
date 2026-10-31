"""A61 final QA, immutable SHA evidence and idempotent event in EXISTING Synapse card."""
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
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a61-pool-discrete-closure-20261027-1400"
SCRIPTS = ("a61_pool_discrete_closure.py", "test_a61.py",
           "independent_qa_a61.py", "finalize_a61.py")
MANIFEST_FILES = SCRIPTS + ("A61_TECHNICKY_PROTOKOL_SK.md",
                           "REPORT_A61.json", "INDEPENDENT_QA_A61.json",
                           "QA_CLEAN.txt", "EVIDENCE_A61.json")
PHYSICS = (PROJECT / "matlab/pool_feedback_v04/alokuj_teplo_v04_sk.txt",
           PROJECT / "matlab/pool_feedback_v04/vypocitaj_dopyt_bazena_sk.txt",
           PROJECT / "matlab/pool_feedback_v04/spusti_scenare_v04_sk.m")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_once(path, data):
    if path.exists():
        if path.read_text(encoding="utf-8") != data:
            raise RuntimeError("EXISTING_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(data, encoding="utf-8")


def guard():
    for root in (CENTER, CENTER / "recovery", D, PROJECT,
                 Path(r"C:\Users\Lysda\Desktop\temp_coding")):
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag"):
            if (root / name).exists():
                raise RuntimeError("STOP_PAUSE_ACTIVE " + str(root / name))


def main():
    guard()
    for name in SCRIPTS:
        ast.parse((D / name).read_text(encoding="utf-8"), filename=name)
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a61"],
                          cwd=D, capture_output=True, text=True, timeout=25)
    if proc.returncode or "Ran 16 tests" not in proc.stderr or not proc.stderr.rstrip().endswith("OK"):
        raise RuntimeError("TESTS_FAILED " + proc.stderr[-2200:])
    write_once(D / "QA_CLEAN.txt",
               re.sub(r"Ran 16 tests in [0-9.]+s", "Ran 16 tests in <variable>s", proc.stderr))
    report = json.loads((D / "REPORT_A61.json").read_text(encoding="utf-8"))
    independent = json.loads((D / "INDEPENDENT_QA_A61.json").read_text(encoding="utf-8"))
    assert report["status"] == "VERIFIED_SYNTHETIC_DISCRETE_CLOSURE"
    assert report["physical_release"] is False
    assert independent["physical_release"] is False
    assert independent["source_kind"] == "derived_simulation"
    assert independent["qa_kind"] == "independent_decimal_source_recalculation"
    sys.path.insert(0, str(D))
    from independent_qa_a61 import inspect, SPEC
    for version in ("v08", "v09"):
        a = report[version]
        b = independent[version]
        assert a["samples"] == b["rows"] == 672
        assert a["negative_loss_samples"] == b["negative_loss_rows"] == 91
        assert a["max_abs_step_residual_W"] < 1e-6
        assert a["discrete_steps_h"] == 168
        assert a["time_span_h"] == 167.75
        assert -20.001 < a["A60_trapezoid_minus_discrete_kWh"] < -19.999
        assert abs(a["integrated_closure_J"]) < 1
        raw = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv") if version == "v08" else Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\scada_v09\matlab_live_v01\runtime\jobs\79b874c619674e1e966c72bf92eb67b3\result.csv")
        qkey, lkey, _ = SPEC[version]
        assert inspect(raw, a, qkey, lkey) == b
    assert all(p.is_file() for p in PHYSICS)
    evidence = {
        "task_id": TASK, "scope": "A61_discrete_pool_first_law_v08_v09",
        "artifact_directory": str(D), "status": "VERIFIED_DERIVED_SIMULATION_ONLY",
        "unittest": "16/16 PASS", "ast": "4/4 PASS",
        "decimal_state_updates": 1344, "negative_signed_loss_samples": [91, 91],
        "max_residual_W": {v: report[v]["max_abs_step_residual_W"] for v in ("v08", "v09")},
        "a60_integral_boundary_bias_kWh": {v: report[v]["A60_trapezoid_minus_discrete_kWh"] for v in ("v08", "v09")},
        "physics_source_sha256": {str(p): sha(p) for p in PHYSICS},
        "physical_release": False, "actual_instrument_data": False,
        "shared_source_modified": False, "new_codex_sessions": 0,
        "next_step": "Add explicit signed Q_pool_loss and discrete-step energy accounting to a future isolated A60 schema revision; keep A60 original immutable. Obtain authenticated real telemetry for A55-A59.",
    }
    write_once(D / "EVIDENCE_A61.json", json.dumps(evidence, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    manifest = {name: sha(D / name) for name in MANIFEST_FILES}
    write_once(D / "SHA256_MANIFEST_A61.json",
               json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    handoff = (
        "# A61 DataCenter discrete pool energy closure | " + now + "\n"
        "Primary SynapseMCP Web live ping OK; STOP/PAUSE scoped checks clear; task review/planned, no active task worker.\n"
        "Input: immutable D_SYNTHETIC v08 and MATLAB v09 original CSV plus A60 derived CSV/summary, 672 rows each.\n"
        "Actual implementation: source SHA validation, explicit Q_pool_loss channel, correct forward-Euler step indexing, signed heat-gain interpretation.\n"
        "QA: 16/16 unittest PASS, 4/4 AST PASS, 1344/1344 Decimal state updates independently checked.\n"
        "Max state closure: v08 2.18e-7 W, v09 2.16e-7 W; 91/672 negative signed loss rows in each source.\n"
        "Full discrete 168h Q_pool v08=10.393084303 MWh, loss=3.687212453 MWh, stored=6.705871850 MWh.\n"
        "A60 trapezoid covers timestamp span 167.75h and reports 20.000398 kWh less than 672-step discrete sum.\n"
        "This is a time-integration convention difference, not automatically a defect in A60.\n"
        "Physical validation BLOCKED: no calibrated real telemetry, hardware certificates or independent physical acceptance.\n"
        "No changes to A60, SCADA, MATLAB, shared GUI, STOP/OAuth, foreign branches; VRS skipped; no Codex/GPU jobs.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A61.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A61.json") + "\n"
        "NEXT: isolate future A60 schema v2 with signed-loss channel and both integration conventions; preserve existing A60 and compare full Stateflow/SCADA.\n"
    )
    write_once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A61.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A61.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "16/16 unittest; 4/4 AST; 1344/1344 Decimal state updates",
        "physical_release": False, "source_kind": "derived_simulation",
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
        found = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                           (TASK, ACTOR)).fetchall()
        if len(found) > 1:
            raise RuntimeError("DUPLICATE_EVIDENCE_EVENT")
        if found:
            if json.loads(found[0][1]) != payload:
                raise RuntimeError("EVIDENCE_EVENT_CONFLICT")
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
    write_once(D / "REGISTRY_RESULT_A61.json",
               json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                          indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"event_id": event_id, "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"], "QA": payload["QA"]}))


if __name__ == "__main__":
    main()
