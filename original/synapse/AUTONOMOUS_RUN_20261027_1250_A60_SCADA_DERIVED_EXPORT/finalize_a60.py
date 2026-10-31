"""A60 deterministic QA, SHA manifest, handoff and idempotent EXISTING Synapse event."""
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
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a60-scada-derived-export-20261027-1250"
SRC = ["a60_scada_derived_export.py", "test_a60.py", "independent_qa_a60.py", "finalize_a60.py"]
FILES = SRC + ["A60_ANALYTICKY_PROTOKOL_SK.md", "QA_CLEAN.txt",
               "INDEPENDENT_QA_A60.json", "EVIDENCE_A60.json",
               "OUTPUT_V08_DERIVED/analysis_timeseries.csv",
               "OUTPUT_V08_DERIVED/summary.json",
               "OUTPUT_V09_DERIVED/analysis_timeseries.csv",
               "OUTPUT_V09_DERIVED/summary.json"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(path: Path, text: str):
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise RuntimeError("EXISTING_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(text, encoding="utf-8")


def guard():
    for root in (CENTER, CENTER / "recovery", D,
                 Path(r"C:\Users\Lysda\Desktop\temp_coding"),
                 Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag"):
            if (root / name).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root / name))


def main():
    guard()
    for name in SRC:
        ast.parse((D / name).read_text(encoding="utf-8"), filename=name)
    proc = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a60"],
                          cwd=D, capture_output=True, text=True, timeout=25)
    if proc.returncode or "Ran 15 tests" not in proc.stderr or not proc.stderr.rstrip().endswith("OK"):
        raise RuntimeError("A60_TESTS_FAILED " + proc.stderr[-1600:])
    once(D / "QA_CLEAN.txt", re.sub(r"Ran 15 tests in [0-9.]+s",
                                    "Ran 15 tests in <variable>s", proc.stderr))
    sys.path.insert(0, str(D))
    from independent_qa_a60 import compare
    report = compare(D / "OUTPUT_V08_DERIVED", D / "OUTPUT_V09_DERIVED")
    saved = json.loads((D / "INDEPENDENT_QA_A60.json").read_text(encoding="utf-8"))
    if report != saved or report["comparisons"] != 5376 or report["independent_integral_checks"] != 10:
        raise RuntimeError("INDEPENDENT_QA_CHANGED")
    if report["physical_release"] or report["calibration_ready"]:
        raise RuntimeError("UNAUTHORIZED_PHYSICAL_RELEASE")
    evidence = {
        "task_id": TASK, "scope": "A60_existing_SCADA_v08_v09_derived_export",
        "artifact_directory": str(D), "status": "VERIFIED_SIMULATION_DATA_EXPORT",
        "unit_tests": 15, "ast_checks": len(SRC),
        "independent_comparisons": report["comparisons"],
        "independent_integrals": report["independent_integral_checks"],
        "source_sha256": report["source_sha256"],
        "synthetic_or_derived_only": True, "physical_release": False,
        "shared_sources_modified": False,
        "next_step": "Acquire actual instrumented SCADA CSV with A59 channels and authenticated documents, then A55-A58; physical validation BLOCKED.",
    }
    once(D / "EVIDENCE_A60.json", json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    manifest = {name: sha(D / name) for name in FILES}
    once(D / "SHA256_MANIFEST_A60.json",
         json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    handoff = (
        "# A60 DataCenter SCADA derived simulation export | " + now + "\n"
        "Primary SynapseMCP Web ping verified, STOP/PAUSE checked, task remains review/planned/no worker.\n"
        "Input: actual existing v08 healthy simulation and v09 MATLAB live job result CSV, 672 rows each, 167.75 hours.\n"
        "Implementation: two source-schema adapters to immutable analysis CSV, SHA provenance, trapezoidal energy metrics.\n"
        "QA: 15/15 unittest PASS; 4/4 AST PASS; independent Decimal integrals 10/10 PASS; 5376/5376 cross-version comparisons PASS.\n"
        "Comparison max |delta|: T_pool_C 1.95e-8 C, Q_reject_W 0.0417 W, E_TES_J 48.985 J.\n"
        "Simulation energy v08: Q_DC 28.51016 MWh, Q_pool 10.37308 MWh, Q_DH 16.07613 MWh, HP electricity 4.75632 MWh.\n"
        "Tolerances are exploratory software checks, not physical accuracy or safety certification.\n"
        "No actual instrument data; physical calibration remains BLOCKED. A59-A55 real input cannot be manufactured.\n"
        "No Codex/GPU jobs/workers, no shared GUI/STOP/OAuth/source changes, VRS skipped.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A60.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A60.json") + "\n"
        "NEXT: Obtain real timestamped calibrated SCADA export; run A59 then A55-A58, and Stateflow comparison.\n"
    )
    if not (D / "FINAL_HANDOFF.md").exists():
        once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A60.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A60.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "15/15 unittest; 4/4 AST; 5376/5376 cross-version; 10/10 Decimal integrals",
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
        existing = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                              (TASK, ACTOR)).fetchall()
        if len(existing) > 1:
            raise RuntimeError("DUPLICATE_EVENT")
        if existing:
            if json.loads(existing[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id = existing[0][0]
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
    once(D / "REGISTRY_RESULT_A60.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"event_id": event_id, "QA": payload["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
