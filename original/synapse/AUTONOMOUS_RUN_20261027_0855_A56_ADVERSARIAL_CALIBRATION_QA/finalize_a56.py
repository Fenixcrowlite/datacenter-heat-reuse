"""A56 deterministic QA, immutable evidence and idempotent existing-card event."""
from __future__ import annotations
import ast
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent
CENTER = D.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a56-adversarial-calibration-qa-20261027-0855"
A55 = D.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE" / "a55_calibration_gate.py"
A55_SHA = "e65e2ec1e2e7927023637c0bd8f430dcfb1045346666220ede8ecb7ed0e5be91"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(path: Path, content: str) -> None:
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(content, encoding="utf-8")


def guard() -> None:
    roots = [CENTER, CENTER / "recovery", CENTER / "Continuity",
             Path(r"C:\Users\Lysda\Desktop\temp_coding"),
             Path(r"C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot"),
             Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
             Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")]
    for root in roots:
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE", "devteam-daemon.stop"):
            if (root / name).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root / name))


def main() -> None:
    guard()
    if sha(A55) != A55_SHA:
        raise RuntimeError("A55_SOURCE_CHANGED")
    for f in ("a56_quality_gate.py", "test_a56.py"):
        ast.parse((D / f).read_text(encoding="utf-8"), filename=f)
    qa = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a56"],
                        cwd=D, capture_output=True, text=True, timeout=30)
    if qa.returncode or "Ran 11 tests" not in qa.stderr or "\nOK" not in qa.stderr:
        raise RuntimeError("QA_FAILED " + qa.stderr[-1500:])
    expected = ("test_compressor_spike_a55_accepts_a56_rejects",
                "test_subresolution_sign_reversal_a55_accepts_a56_rejects",
                "test_capacity_drift_a55_accepts_a56_rejects")
    if any(test not in qa.stderr for test in expected):
        raise RuntimeError("MISSING_ADVERSARIAL_TEST")
    qa_summary = {
        "unittest": "11/11 PASS", "ast_parse": "2/2 PASS",
        "adversarial_regressions": "3/3 A55 accepted, A56 rejected",
        "A55_sha256": A55_SHA, "real_telemetry": False,
        "physical_release": False, "source_A55_modified": False,
    }
    once(D / "QA_SUMMARY_A56.json", json.dumps(qa_summary, indent=2) + "\n")
    next_step = ("Obtain asset-specific calibrated time-aligned telemetry and sensor uncertainty "
                 "records, verify source provenance independently, then rerun A55+A56 and "
                 "Stateflow uncertainty scenarios. No physical release.")
    evidence = {
        "task_id": TASK,
        "scope": "A56_independent_adversarial_calibration_quality_gate",
        "status": "VERIFIED_SYNTHETIC_QA_PHYSICAL_CALIBRATION_BLOCKED",
        "artifact_directory": str(D),
        "A55_source_sha256": A55_SHA,
        "new_module": "a56_quality_gate.py",
        "QA": "11/11 unittest PASS, 2/2 AST PASS, 3/3 adversarial A55 acceptance gaps closed",
        "verified_gaps": ["noncontractive compressor interval silently skipped",
                          "subresolution energy-sign reversal silently skipped",
                          "capacity drift hidden by global fit"],
        "original_A55_modified": False, "measured_data": False,
        "physical_release": False, "safety_certified": False,
        "model_scope": "first-order compressor assumption; conservative synthetic QA thresholds",
        "next_step": next_step,
    }
    once(D / "EVIDENCE_A56.json", json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    names = ["a56_quality_gate.py", "test_a56.py", "A56_METHOD_SK.md",
             "QA_SUMMARY_A56.json", "EVIDENCE_A56.json"]
    manifest = {name: sha(D / name) for name in names}
    once(D / "SHA256_MANIFEST_A56.json", json.dumps(manifest, indent=2) + "\n")
    handoff = (
        "# A56 adversarial calibration QA | 2026-10-27 CET\n"
        "Host DESKTOP-M9L3I4M; primary SynapseMCP Web live ping OK at 08:54 CET; "
        "preflight RAM available 4.9 GiB, GPU 0%, VRAM 1054/8188 MiB.\n"
        "STOP/PAUSE absent in known project roots; Jarvice singleton PID 11572 idle; "
        "shared Jarvice repo dirty and untouched.\n"
        "Created isolated a56_quality_gate.py, test_a56.py, Slovak method note. "
        "A55 source unchanged SHA256 " + A55_SHA + ".\n"
        "QA: 11/11 unittest PASS, 2/2 AST PASS, 3/3 adversarial synthetic A55 "
        "acceptance gaps reproduced and rejected by A56. No real telemetry.\n"
        "Assumptions: first-order compressor response, 80% usable energy intervals, "
        "10% split-half capacity drift; not equipment-certified thresholds.\n"
        "Evidence SHA256 " + sha(D / "EVIDENCE_A56.json") + "\n"
        "Manifest SHA256 " + sha(D / "SHA256_MANIFEST_A56.json") + "\n"
        "No new Codex, GPU workers, GUI actions, VRS, STOP/OAuth or shared files modified.\n"
        "BLOCKED: physical parameter validation, equipment-specific safe operating limits, "
        "vendor calibration records.\n"
        "NEXT: " + next_step + "\n"
    )
    once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A56.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A56.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": evidence["QA"], "synthetic_only": True,
        "physical_release": False, "next_step": next_step,
    }
    db = sqlite3.connect(CENTER / "tasks.sqlite3", timeout=15, isolation_level=None)
    db.execute("PRAGMA busy_timeout=15000")
    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RuntimeError("REGISTRY_INTEGRITY_FAILED")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?", (TASK,)).fetchone()
        if row != ("review", "planned", None):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED " + repr(row))
        old = db.execute(
            "SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
            (TASK, ACTOR)).fetchall()
        if len(old) > 1:
            raise RuntimeError("DUPLICATE_EVENT")
        if old:
            if json.loads(old[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id = old[0][0]
        else:
            event_id = db.execute(
                "INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK, time.time(), "evidence", ACTOR,
                 json.dumps(payload, ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    once(D / "REGISTRY_RESULT_A56.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event_id": event_id, "qa": evidence["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
