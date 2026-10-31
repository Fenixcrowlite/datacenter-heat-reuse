"""A38 idempotent evidence registration into EXISTING DataCenter card only.
No task/worker creation, no status mutation, no remote publishing.
"""
import hashlib
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a38-dchr-tes-n1-integrated-20261026-1054"
V08 = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
V04 = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_feedback_v04\alokuj_teplo_v04_sk.txt")
V07 = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_redundancy_v07\fyzikalne_ochrany_v07.txt")
A36 = HERE.parent / "AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE" / "scenario_both_off.csv"
A37 = HERE.parent / "AUTONOMOUS_RUN_20261026_1025_A37_DCHR_IT_THERMAL_PROTECTION" / "thermal_n1.py"
A37B = HERE.parent / "AUTONOMOUS_RUN_20261026_1037_A37B_DCHR_TES_SOC_REDIRECT" / "tes_soc.py"
STOP_NAMES = ("STOP", "STOP.flag", "STOP.txt", ".stop", ".STOP", "PAUSE",
              "PAUSE.flag", "PAUSE.txt", ".pause", ".PAUSE", "STOP_MANAGED_WORKERS.txt")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_once(path, data):
    if path.exists():
        if json.loads(path.read_text(encoding="utf8")) != data:
            raise RuntimeError("EXISTING_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")

def main():
    for root in (CENTER, CENTER / "recovery", HERE, V08.parent.parent.parent):
        for name in STOP_NAMES:
            if (root / name).exists():
                raise RuntimeError("STOP_ACTIVE " + str(root / name))
    results = json.loads((HERE / "RESULTS_A38.json").read_text(encoding="utf8"))
    qa = json.loads((HERE / "INDEPENDENT_QA.json").read_text(encoding="utf8"))
    tests = (HERE / "TEST_LOG.txt").read_text(encoding="utf8")
    if (results["status"] != "SYNTHETIC_INTEGRATED_REFERENCE_ONLY" or
        results["physical_release_allowed"] or results["matlab_stateflow_executed"] or
        len(results["cases"]) != 12 or results["samples"] != 672 or
        results["TES_clipped_intervals"] != 6):
        raise RuntimeError("MODEL_RESULT_INVALID")
    if qa["status"] != "PASS" or qa["rows"] != 8064 or qa["decimal_invariant_checks"] != 225792:
        raise RuntimeError("INDEPENDENT_QA_INVALID")
    if "Ran 16 tests" not in tests or "\nOK" not in tests:
        raise RuntimeError("UNIT_TESTS_NOT_PASS")
    for path, key in ((V08,"v08_sha256"), (V04,"v04_sha256"), (V07,"v07_sha256"),
                      (A36,"a36_csv_sha256"), (A37,"a37_thermal_py_sha256"),
                      (A37B,"a37b_tes_py_sha256")):
        if sha(path) != results["upstream"][key]:
            raise RuntimeError("UPSTREAM_SOURCE_CHANGED " + key)
    for case in results["cases"].values():
        if sha(HERE / case["trace"]) != case["sha256"]:
            raise RuntimeError("TRACE_CHANGED " + case["trace"])
    evidence = {
        "scope": "isolated_A38_synthetic_TES_SOC_REJECT_N1_IT_thermal_coupled_672_replay",
        "qa": "16/16 Python tests PASS; 12 cases x 672 rows; 225792 independent Decimal checks PASS",
        "finding": "A37B TES saturation adds 61.346161 kWh unhandled heat in no-REJECT scenario; corrected model still predicts unsafe extrapolated temperatures; A37 preclip equivalence verified",
        "model_status": "PYTHON_SYNTHETIC_VERIFIED_MATLAB_CANDIDATE_UNEXECUTED",
        "release_status": "PHYSICAL_RELEASE_BLOCKED",
        "next_step": "Run dchr_a38_replay_acceptance.m in owned MATLAB session, then implement Stateflow transitions; obtain certified REJECT/IT/TES and field data",
        "physical_release_allowed": False,
        "matlab_stateflow_executed": False,
        "source_v08_sha256": results["upstream"]["v08_sha256"],
        "results_sha256": sha(HERE / "RESULTS_A38.json"),
        "independent_qa_sha256": sha(HERE / "INDEPENDENT_QA.json"),
    }
    save_once(HERE / "EVIDENCE.json", evidence)
    filenames = [
        "integrated_a38.py", "test_a38.py", "independent_qa.py",
        "dchr_a38_step.m", "dchr_a38_replay_acceptance.m",
        "DCHR_A38_INTEGRATION_RU.md", "RESULTS_A38.json", "INDEPENDENT_QA.json",
        "TEST_LOG.txt", "RUN_LOG.json", "INDEPENDENT_QA_LOG.txt",
        "EVIDENCE.json", "register_a38.py",
    ] + [x["trace"] for x in results["cases"].values()]
    save_once(HERE / "SHA256_MANIFEST.json", {f: sha(HERE / f) for f in filenames})
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(HERE),
        "evidence_sha256": sha(HERE / "EVIDENCE.json"),
        "manifest_sha256": sha(HERE / "SHA256_MANIFEST.json"),
        "results_sha256": evidence["results_sha256"],
        "qa": evidence["qa"], "finding": evidence["finding"],
        "model_status": evidence["model_status"],
        "release_status": evidence["release_status"],
        "next_step": evidence["next_step"],
    }
    with sqlite3.connect(CENTER / "tasks.sqlite3", timeout=6, isolation_level=None) as db:
        db.execute("pragma busy_timeout=6000")
        if db.execute("pragma quick_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLITE_CORRUPT")
        db.execute("begin immediate")
        try:
            state = db.execute(
                "select status,stage,worker_pid,owner from tasks where id=?", (TASK,)
            ).fetchone()
            if state != ("review", "planned", None, "MATLAB/Stateflow QA"):
                raise RuntimeError("TASK_OWNERSHIP_CHANGED " + repr(state))
            found = db.execute(
                "select id,data_json from task_events where task_id=? and actor=? and kind='evidence'",
                (TASK, ACTOR)
            ).fetchall()
            if len(found) > 1:
                raise RuntimeError("DUPLICATE_EVENT")
            if found:
                if json.loads(found[0][1]) != payload:
                    raise RuntimeError("EVENT_PAYLOAD_CONFLICT")
                event_id, action = found[0][0], "EXISTING_EVENT"
            else:
                event_id = db.execute(
                    "insert into task_events(task_id,at,kind,actor,data_json) values(?,?,?,?,?)",
                    (TASK, time.time(), "evidence", ACTOR, json.dumps(payload, ensure_ascii=False))
                ).lastrowid
                action = "CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback()
            raise
    save_once(HERE / "REGISTRY_RESULT.json", {"task_id": TASK, "event_id": event_id, **payload})
    print(json.dumps({"action": action, "task_id": TASK, "event_id": event_id,
                      "evidence_sha256": payload["evidence_sha256"],
                      "manifest_sha256": payload["manifest_sha256"]}, indent=2))
if __name__ == "__main__":
    main()
