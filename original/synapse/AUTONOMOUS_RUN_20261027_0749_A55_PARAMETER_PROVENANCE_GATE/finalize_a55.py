"""A55 idempotent finalizer: evidence, SHA, existing Synapse task only."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

D = Path(__file__).resolve().parent
CENTER = D.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a55-physical-parameter-provenance-20261027-0749"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def once(path, text):
    if path.exists():
        if path.read_text(encoding="utf-8-sig") != text:
            raise RuntimeError("IMMUTABLE_ARTIFACT_CONFLICT " + str(path))
    else:
        path.write_text(text, encoding="utf-8")


def stop_guard():
    roots = (CENTER, CENTER / "recovery", CENTER / "Continuity",
             Path(r"C:\Users\Lysda\Desktop\temp_coding"),
             Path(r"C:\Users\Lysda\Desktop\temp_coding\telegram_codex_bot"),
             Path(r"C:\Users\Lysda\Desktop\EduMotionPipeline"),
             Path(r"C:\Users\Lysda\Desktop\.jarvice_worktrees"))
    for root in roots:
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE", "devteam-daemon.stop"):
            if (root / name).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root / name))


def main():
    stop_guard()
    report = json.loads((D / "A55_PROVENANCE_AUDIT.json").read_text(encoding="utf-8"))
    if report["status"] != "A55_PROVENANCE_GATE_IMPLEMENTED_PHYSICAL_CALIBRATION_BLOCKED":
        raise RuntimeError("UNEXPECTED_STATUS")
    if report["A54_parameter_provenance"][:1] != "D" or report["source_class_promoted"]:
        raise RuntimeError("INVALID_PROVENANCE_PROMOTION")
    if report["safe_operating_limits_certified"] or report["physical_release"]:
        raise RuntimeError("INVALID_SAFETY_CLAIM")
    source = D.parent / "AUTONOMOUS_RUN_20261027_0648_A54_PARAMETER_UNCERTAINTY" / "A54_UNCERTAINTY_RESULTS.json"
    if sha(source) != report["A54_sha256"]:
        raise RuntimeError("SOURCE_CHANGED")
    # Independent Decimal unit calculation, not the float expression in a55_calibration_gate.py.
    for capacity, equivalent in zip(report["A54_ranges"]["heat_capacity_J_per_K"],
                                    report["water_only_equivalent_m3"]):
        expected = Decimal(str(capacity)) / (Decimal("998") * Decimal("4182"))
        if abs(expected - Decimal(str(equivalent))) > Decimal("0.00005"):
            raise RuntimeError("INDEPENDENT_WATER_EQUIVALENCE_MISMATCH")
    qa = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a55"],
                        cwd=D, capture_output=True, text=True, timeout=30)
    if qa.returncode or "Ran 12 tests" not in qa.stderr or "\nOK" not in qa.stderr:
        raise RuntimeError("QA_FAILED " + qa.stderr[-1000:])
    once(D / "QA_VERIFIED.txt", "12/12 unittest PASS; independent Decimal water-equivalence 3/3 PASS\n")
    next_step = ("Acquire asset-specific time-aligned telemetry, calibrated sensor records and vendor "
                 "performance maps; identify C_eff/tau/residual with A55; independently review "
                 "then rerun isolated graphical Stateflow uncertainty tests. No physical release.")
    evidence = dict(
        task_id=TASK, scope="A55_physical_parameter_provenance_and_identification_gate",
        status=report["status"], artifact_directory=str(D),
        source_A54_sha256=report["A54_sha256"],
        source_parameter_registry_sha256=report["parameter_registry_sha256"],
        parameter_provenance="class D synthetic stress-test, NOT manufacturer/measurement",
        source_promotion=False, physical_release=False,
        telemetry_supplied=False,
        implemented=["SHA256+metadata gate", "UTC and monotonic sample gate",
                     "energy-balance C_eff estimator", "first-order compressor tau estimator",
                     "post-trip residual estimator", "model-identifiability rejection",
                     "measured candidate never auto-certifies"],
        QA="12/12 Python unittest PASS, independent Decimal 3/3 PASS",
        A54_water_only_equivalent_m3=report["water_only_equivalent_m3"],
        MATLAB_A55_executed=False,
        limitations="No equipment-specific measured telemetry or verified vendor dynamics. Synthetic tests do not validate physical parameters.",
        next_step=next_step)
    once(D / "EVIDENCE_A55.json", json.dumps(evidence, indent=2, ensure_ascii=False) + "\n")
    names = ["a55_calibration_gate.py", "test_a55.py", "A55_PROVENANCE_AUDIT.json",
             "A55_MERACI_PROTOKOL_SK.md", "RUN_OUTPUT.txt", "QA_OUTPUT.txt",
             "QA_VERIFIED.txt", "EVIDENCE_A55.json"]
    manifest = {n: sha(D / n) for n in names}
    once(D / "SHA256_MANIFEST_A55.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    handoff = (
        "# A55 physical parameter provenance and identification gate | 2026-10-27 morning CET\n"
        "Host DESKTOP-M9L3I4M; primary SynapseMCP Web ONLINE during preflight; RAM available 4.8 GiB, "
        "GPU 0%, VRAM 1055/8188 MiB at preflight. Jarvice PID 11572 observed idle; "
        "shared Jarvice worktree dirty, not modified. STOP/PAUSE guards checked before registration.\n"
        "New task-local A55 calibration/provenance gate and Slovak measurement protocol. "
        "A54 scenario heat capacity 6/8/10 MJ/K corresponds to water-only equivalents "
        "1.4376/1.9168/2.3960 m3 (assumptions explicitly stated), not measured loop volume.\n"
        "QA: 12/12 synthetic/rejection unit tests PASS; independent Decimal equivalence 3/3 PASS. "
        "No MATLAB A55 run, no measured telemetry and no equipment-specific vendor validation. "
        "Physical calibration and safety approval BLOCKED; A54 stress ranges remain class D.\n"
        f"Source A54 SHA256 {report['A54_sha256']}\n"
        f"Evidence SHA256 {sha(D / 'EVIDENCE_A55.json')}\n"
        f"Manifest SHA256 {sha(D / 'SHA256_MANIFEST_A55.json')}\n"
        "No Codex sessions, workers, GPU tasks, GUI, VRS, STOP/OAuth, shared repo or original models modified.\n"
        f"NEXT: {next_step}\n")
    once(D / "FINAL_HANDOFF.md", handoff)
    payload = dict(scope=evidence["scope"], artifact_directory=str(D),
                   result_sha256=sha(D / "A55_PROVENANCE_AUDIT.json"),
                   evidence_sha256=sha(D / "EVIDENCE_A55.json"),
                   manifest_sha256=sha(D / "SHA256_MANIFEST_A55.json"),
                   handoff_sha256=sha(D / "FINAL_HANDOFF.md"),
                   QA=evidence["QA"], synthetic_only=True,
                   source_promotion=False, physical_release=False,
                   next_step=next_step)
    db = sqlite3.connect(CENTER / "tasks.sqlite3", timeout=15, isolation_level=None)
    db.execute("PRAGMA busy_timeout=15000")
    if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
        raise RuntimeError("REGISTRY_INTEGRITY_FAILED")
    db.execute("BEGIN IMMEDIATE")
    try:
        row = db.execute("SELECT status,stage,worker_pid FROM tasks WHERE id=?", (TASK,)).fetchone()
        if row != ("review", "planned", None):
            raise RuntimeError("TASK_OWNERSHIP_CHANGED " + repr(row))
        previous = db.execute(
            "SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
            (TASK, ACTOR)).fetchall()
        if len(previous) > 1:
            raise RuntimeError("DUPLICATE_EVENT")
        if previous:
            if json.loads(previous[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id = previous[0][0]
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
    once(D / "REGISTRY_RESULT_A55.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"event_id": event_id, "qa": evidence["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
