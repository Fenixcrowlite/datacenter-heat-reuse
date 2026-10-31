"""Attach verified metrology evidence to EXISTING Synapse task, idempotently."""
import hashlib
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CENTER = HERE.parent.parent
DCHR = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-dchr-a26-correlated-metrology-20261025-2155"
FILES = ("correlated_pool_metrology.py", "test_correlated_pool_metrology.py",
         "monte_carlo_crosscheck.py", "CORRELATED_METROLOGY_EVIDENCE.json",
         "MONTE_CARLO_QA.json", "METROLOGIA_KORELOVANYCH_CHYB_SK.md",
         "TEST_LOG.txt", "register_a26.py")
FLAGS = ("STOP", "STOP.flag", "STOP.txt", ".STOP", "PAUSE", "PAUSE.flag",
         "PAUSE.txt", ".PAUSE", "STOP_MANAGED_WORKERS.txt")
ROOTS = (HERE, HERE.parent, CENTER, CENTER/"agent_knowledge",
         DCHR, DCHR/"matlab"/"pool_measurement_v08",
         DCHR/"results"/"pool_measurement_v08")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def register():
    for root in ROOTS:
        for name in FLAGS:
            if (root/name).exists():
                raise RuntimeError("STOP_ACTIVE "+str(root/name))
    for f in FILES:
        if not (HERE/f).is_file():
            raise RuntimeError("MISSING "+f)
    tests = (HERE/"TEST_LOG.txt").read_text(encoding="utf-8")
    if "Ran 20 tests" not in tests or not tests.rstrip().endswith("OK"):
        raise RuntimeError("QA_LOG_NOT_PASS")
    ev = json.loads((HERE/"CORRELATED_METROLOGY_EVIDENCE.json").read_text(encoding="utf-8"))
    mc = json.loads((HERE/"MONTE_CARLO_QA.json").read_text(encoding="utf-8"))
    if ev["source_class"] != "D_SYNTHETIC" or len(ev["heat_cases"]) != 3:
        raise RuntimeError("BAD_SOURCE_CLASS")
    if ev["original_uncertainty_source_sha256"] != sha(Path(ev["original_uncertainty_source_path"])):
        raise RuntimeError("ORIGINAL_SOURCE_CHANGED")
    if mc["status"] != "PASS" or len(mc["cases"]) != 3 or any(
        x["relative_std_error"] > .025 for x in mc["cases"].values()):
        raise RuntimeError("MONTE_CARLO_FAILED")
    hashes = {f: sha(HERE/f) for f in FILES}
    manifest = HERE/"SHA256_MANIFEST.json"
    manifest.write_text(json.dumps(hashes, indent=2)+"\n", encoding="utf-8")
    payload = {
        "scope": "isolated_correlated_metrology_uncertainty_envelope_D_synthetic",
        "artifact_directory": str(HERE),
        "evidence_sha256": hashes["CORRELATED_METROLOGY_EVIDENCE.json"],
        "source_code_sha256": hashes["correlated_pool_metrology.py"],
        "monte_carlo_sha256": hashes["MONTE_CARLO_QA.json"],
        "qa_log_sha256": hashes["TEST_LOG.txt"],
        "manifest_sha256": sha(manifest),
        "qa": "20/20 unit tests PASS; py_compile PASS; independent seeded 3x80000 Gaussian Monte Carlo PASS",
        "finding": "Temperature covariance shifts assumed flow-based u(P) from 11.124 kW (r=0) to 6.068 (r=+0.9) or 14.514 (r=-0.9); 15-min 500m3 storage finite-difference uncertainty remains very large",
        "limits": "Assumed Class D correlations, not measured; no equipment calibration, field validation, pool standards signoff or MATLAB execution",
        "next_step": "Collect traceable paired flow and supply/return temperature records, estimate covariance/autocorrelation and compare with independent calorimeter"
    }
    with sqlite3.connect(CENTER/"tasks.sqlite3", timeout=5, isolation_level=None) as db:
        db.execute("PRAGMA busy_timeout=5000")
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise RuntimeError("SQLITE_INTEGRITY")
        db.execute("BEGIN IMMEDIATE")
        try:
            row = db.execute("SELECT status,stage FROM tasks WHERE id=?", (TASK,)).fetchone()
            if row != ("review", "planned"):
                raise RuntimeError("TASK_STATE_CHANGED "+repr(row))
            found = db.execute(
                "SELECT id,data_json FROM task_events WHERE task_id=? AND kind='evidence' AND actor=?",
                (TASK, ACTOR)).fetchall()
            if len(found) > 1:
                raise RuntimeError("DUPLICATE_ACTOR")
            if found:
                if json.loads(found[0][1]) != payload:
                    raise RuntimeError("ACTOR_PAYLOAD_CONFLICT")
                event_id, action = found[0][0], "EXISTING_EVENT"
            else:
                event_id = db.execute(
                    "INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                    (TASK, time.time(), "evidence", ACTOR,
                     json.dumps(payload, ensure_ascii=False))).lastrowid
                action = "CREATED_EVENT"
            db.commit()
        except BaseException:
            db.rollback()
            raise
    result = {"task_id":TASK,"event_id":event_id,"action":action,**payload}
    (HERE/"REGISTRY_RESULT.json").write_text(
        json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return result


if __name__ == "__main__":
    r=register()
    print(json.dumps({k:r[k] for k in ("task_id","event_id","action","evidence_sha256")}))
