"""A57: repeatable QA, immutable SHA evidence and idempotent existing Synapse card event."""
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
ACTOR = "chatgpt-a57-uncertainty-timebase-20261027-0952"
A55 = D.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE" / "a55_calibration_gate.py"
A56 = D.parent / "AUTONOMOUS_RUN_20261027_0855_A56_ADVERSARIAL_CALIBRATION_QA" / "a56_quality_gate.py"
A55_SHA = "e65e2ec1e2e7927023637c0bd8f430dcfb1045346666220ede8ecb7ed0e5be91"
A56_SHA = "0834471ae3505906167192769da7ba5baf9cabd2baac55352fb480f607e4358c"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def once(path: Path, content: str):
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(content, encoding="utf-8")


def guard():
    roots = [CENTER, CENTER / "recovery", CENTER / "Continuity",
             Path(r"C:\Users\Lysda\Desktop\temp_coding"),
             Path(r"C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot"),
             Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
             Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees")]
    for root in roots:
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE", "devteam-daemon.stop"):
            if (root / name).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root / name))


def main():
    guard()
    if sha(A55) != A55_SHA or sha(A56) != A56_SHA:
        raise RuntimeError("UPSTREAM_SOURCE_CHANGED")
    names_py = ("a57_uncertainty_gate.py", "test_a57.py", "run_a57.py",
                "build_demo_a57.py", "finalize_a57.py")
    for f in names_py:
        ast.parse((D / f).read_text(encoding="utf-8"), filename=f)
    qa = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a57"],
                        cwd=D, capture_output=True, text=True, timeout=30)
    if qa.returncode or "Ran 20 tests" not in qa.stderr or "\nOK" not in qa.stderr:
        raise RuntimeError("QA_FAILED " + qa.stderr[-1800:])
    import re
    stable_qa = re.sub(r"Ran 20 tests in [0-9.]+s", "Ran 20 tests in <variable>s", qa.stderr)
    once(D / "QA_OUTPUT_CLEAN.txt", stable_qa)
    from a57_uncertainty_gate import audit
    demo = D / "DEMO_SYNTHETIC"
    r = audit(demo / "telemetry.csv", demo / "metadata.json", demo / "uncertainty.json")
    prior = json.loads((demo / "A57_RESULT_SYNTHETIC.json").read_text(encoding="utf-8"))
    if r != prior or r["physical_release"] or r["source_kind"] != "synthetic_test":
        raise RuntimeError("DEMO_REGRESSION_OR_RELEASE_FLAG")
    oracle = json.loads((demo / "A57_DECIMAL_ORACLE.json").read_text(encoding="utf-8"))
    from decimal import Decimal
    if not oracle["oracle_pass"] or oracle["intervals"] != 64 or Decimal(oracle["energy_residual_max_abs_J"]) != 0:
        raise RuntimeError("INDEPENDENT_DECIMAL_ORACLE_FAILED")
    summary = {
        "unittest": "20/20 PASS", "ast_parse": "5/5 PASS",
        "independent_decimal_energy_intervals": "64/64 PASS",
        "synthetic_samples": 65,
        "capacity_demo_J_per_K": [r["capacity"]["lower_J_per_K"], r["capacity"]["upper_J_per_K"]],
        "tau_demo_s": [r["compressor_tau"]["lower_s"], r["compressor_tau"]["upper_s"]],
        "A55_source_sha256": A55_SHA, "A56_source_sha256": A56_SHA,
        "real_measurements": False, "physical_release": False,
    }
    once(D / "QA_SUMMARY_A57.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    next_step = ("Acquire original asset-specific telemetry, sensor accuracy and clock-sync records; "
                 "independently verify calibration documents and vendor compressor map; "
                 "rerun A55+A56+A57 before isolated Stateflow uncertainty testing. No physical release.")
    evidence = {
        "task_id": TASK, "scope": "A57_sensor_uncertainty_and_timebase_quality_gate",
        "artifact_directory": str(D), "status": "VERIFIED_SYNTHETIC_QA_PHYSICAL_CALIBRATION_BLOCKED",
        "QA": summary, "upstream_files_unchanged": True,
        "error_model": "deterministic supplied bounds, not statistical confidence intervals",
        "new_files": list(names_py) + ["A57_PROTOCOL_SK.md", "DEMO_SYNTHETIC"],
        "physical_release": False, "next_step": next_step,
    }
    once(D / "EVIDENCE_A57.json", json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    manifest_names = list(names_py) + ["A57_PROTOCOL_SK.md", "QA_OUTPUT_CLEAN.txt",
                      "QA_SUMMARY_A57.json", "EVIDENCE_A57.json"]
    manifest_names += ["DEMO_SYNTHETIC/" + f for f in
                       ("telemetry.csv", "metadata.json", "uncertainty.json",
                        "A57_RESULT_SYNTHETIC.json", "A57_DECIMAL_ORACLE.json")]
    manifest = {name: sha(D / name) for name in manifest_names}
    once(D / "SHA256_MANIFEST_A57.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    handoff = (
        "# A57 sensor uncertainty and UTC timebase QA | 2026-10-27 CET\n"
        "Host DESKTOP-M9L3I4M; primary SynapseMCP Web ping 09:52 CET OK. "
        "RAM available 4.82 GiB, GPU 0%, VRAM 1056/8188 MiB at preflight.\n"
        "STOP/PAUSE absent in checked roots; shared Jarvice Git branch dirty, not modified. "
        "Daemon status file PID 11572 was NOT confirmed as a live process; do not claim it live.\n"
        "Task-local A57 module and CLI created, plus Slovak protocol and 65-sample synthetic demo. "
        "A55/A56 unchanged SHA256 " + A55_SHA + " / " + A56_SHA + ".\n"
        "QA: 20/20 Python tests, 5/5 AST parses, 64/64 independent Decimal energy intervals. "
        "Synthetic capacity envelope 7.456-8.622 MJ/K; tau envelope 207-538 s, "
        "conditional on supplied synthetic bounds, NOT real safety limits.\n"
        "Evidence SHA256 " + sha(D / "EVIDENCE_A57.json") + "\n"
        "Manifest SHA256 " + sha(D / "SHA256_MANIFEST_A57.json") + "\n"
        "No new Codex, GPU tasks, GUI actions, VRS, STOP/OAuth or shared model modifications.\n"
        "BLOCKED: real telemetry, independent sensor calibration, equipment operating limits.\n"
        "NEXT: " + next_step + "\n"
    )
    once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A57.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A57.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "20/20 unittest, 5/5 AST, 64/64 Decimal oracle PASS",
        "synthetic_only": True, "physical_release": False, "next_step": next_step,
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
                (TASK, time.time(), "evidence", ACTOR, json.dumps(payload, ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    once(D / "REGISTRY_RESULT_A57.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event_id": event_id, "qa": payload["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
