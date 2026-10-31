"""Finalize scoped A59 evidence and idempotently attach to existing Synapse task."""
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
ACTOR = "chatgpt-a59-scada-ingest-20261027-1150"
A55 = D.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE" / "a55_calibration_gate.py"
EXPECTED_A55 = "e65e2ec1e2e7927023637c0bd8f430dcfb1045346666220ede8ecb7ed0e5be91"


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def once(path, content):
    if path.exists():
        if path.read_text(encoding="utf-8") != content:
            raise RuntimeError("IMMUTABLE_CONFLICT " + str(path))
    else:
        path.write_text(content, encoding="utf-8")


def guard():
    roots = [CENTER, CENTER / "recovery", CENTER / "Continuity",
             Path("C:/Users/Lysda/Desktop/temp_coding"),
             Path("C:/Users/Lysda/Desktop/temp_coding/telegram_codex_bot"),
             Path("C:/Users/Lysda/Desktop/EduMotionPipeline"),
             Path("C:/Users/Lysda/Desktop/.jarvice_worktrees")]
    for root in roots:
        for name in ("STOP", "STOP.flag", "PAUSE", "PAUSE.flag", ".STOP", ".PAUSE", "devteam-daemon.stop"):
            if (root / name).exists():
                raise RuntimeError("STOP_ACTIVE " + str(root / name))


def main():
    guard()
    if sha(A55) != EXPECTED_A55:
        raise RuntimeError("UPSTREAM_A55_CHANGED")
    scripts = ("a59_scada_ingest.py", "test_a59.py", "build_demo_a59.py",
               "registry_probe.py", "finalize_a59.py")
    for file in scripts:
        ast.parse((D / file).read_text(encoding="utf-8"), filename=file)
    p = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a59"],
                       cwd=D, capture_output=True, text=True, timeout=30)
    if p.returncode != 0 or "Ran 17 tests" not in p.stderr or not p.stderr.rstrip().endswith("OK"):
        raise RuntimeError("A59_QA_FAILED " + p.stderr[-2000:])
    clean = re.sub(r"Ran 17 tests in [0-9.]+s", "Ran 17 tests in <variable>s", p.stderr)
    once(D / "QA_CLEAN.txt", clean)
    sys.path.insert(0, str(D))
    sys.path.insert(0, str(A55.parent))
    import a59_scada_ingest as a59
    import a55_calibration_gate as a55
    raw = D / "DEMO_SYNTHETIC_INPUT" / "scada_export.csv"
    mapping = D / "DEMO_SYNTHETIC_INPUT" / "mapping.json"
    normalized = D / "DEMO_SYNTHETIC_NORMALIZED"
    proof = json.loads((normalized / "provenance.json").read_text(encoding="utf-8"))
    if (proof["raw_csv_sha256"] != sha(raw) or proof["mapping_sha256"] != sha(mapping)
            or proof["normalized_csv_sha256"] != sha(normalized / "telemetry.csv")
            or proof["metadata_sha256"] != sha(normalized / "metadata.json")
            or proof["physical_release"] or proof["rows"] != 30
            or proof["source_kind"] != "synthetic_test"):
        raise RuntimeError("DEMO_PROVENANCE_FAILED")
    result = a55.calibrate(normalized / "telemetry.csv", normalized / "metadata.json")
    if (abs(result["capacity"]["value_J_per_K"] - 8_000_000) > 1
            or abs(result["compressor_tau"]["median_s"] - 300) > .01
            or abs(result["residual_fraction"]["median_fraction"] - .12) > 1e-9
            or result["physical_release"]):
        raise RuntimeError("INDEPENDENT_A55_ACCEPTANCE_FAILED")
    summary = {
        "unit_tests": "17/17 PASS", "ast": "5/5 PASS",
        "independent_A55_capacity_J_per_K": result["capacity"]["value_J_per_K"],
        "independent_A55_tau_s": result["compressor_tau"]["median_s"],
        "independent_A55_residual_fraction": result["residual_fraction"]["median_fraction"],
        "demo_rows": 30, "synthetic_only": True, "physical_release": False,
        "upstream_A55_sha256": EXPECTED_A55,
    }
    once(D / "QA_SUMMARY_A59.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    next_step = ("Obtain actual SCADA CSV export with all ten channels and documented units, "
                 "map it via A59, independently authenticate calibration/UTC/vendor documents, "
                 "then run A55-A58 and compare with Stateflow; physical validation remains blocked.")
    evidence = {
        "task_id": TASK, "scope": "A59_SCADA_CSV_ingestion_into_A55",
        "artifact_directory": str(D), "status": "VERIFIED_SYNTHETIC_INTEGRATION",
        "QA": summary, "real_telemetry_processed": False, "physical_release": False,
        "shared_sources_modified": False, "next_step": next_step,
    }
    once(D / "EVIDENCE_A59.json", json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    files = list(scripts) + ["A59_IMPORT_PROTOCOL_SK.md", "QA_CLEAN.txt", "QA_SUMMARY_A59.json", "EVIDENCE_A59.json"]
    files += ["DEMO_SYNTHETIC_INPUT/" + f.name for f in sorted((D / "DEMO_SYNTHETIC_INPUT").iterdir()) if f.is_file()]
    files += ["DEMO_SYNTHETIC_NORMALIZED/" + f.name for f in sorted(normalized.iterdir()) if f.is_file()]
    manifest = {f: sha(D / f) for f in files}
    once(D / "SHA256_MANIFEST_A59.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    handoff = (
        "# A59 SCADA CSV importer | " + datetime.now().astimezone().isoformat(timespec="seconds") + "\n"
        "Primary SynapseMCP Web ping verified 11:50 CET. STOP/PAUSE checked; "
        "Jarvice main worktree dirty and untouched. Existing Jarvice parent/child PIDs 7344/11572 observed.\n"
        "Real source implementation: CSV channel/unit mapping with fail-closed checks, "
        "immutable new-output directory, SHA256 provenance and A55-compatible normalized CSV.\n"
        "QA: 17/17 unittest PASS, 5/5 AST PASS, independent A55 numerical calibration PASS.\n"
        "Demo is synthetic, 30 samples. No actual SCADA data or issuer authentication.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A59.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A59.json") + "\n"
        "A55 original SHA256 unchanged: " + EXPECTED_A55 + "\n"
        "No new Codex, GPU job, worker, GUI changes, OAuth/STOP modifications or VRS work.\n"
        "BLOCKED: real SCADA export, instrument certificates, independent physical validation.\n"
        "NEXT: " + next_step + "\n"
    )
    once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A59.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A59.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "17/17 unittest, 5/5 AST, independent A55 numerical acceptance PASS",
        "synthetic_only": True, "physical_release": False, "next_step": next_step,
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
            raise RuntimeError("TASK_OWNERSHIP_CHANGED " + repr(state))
        prior = db.execute("SELECT id,data_json FROM task_events WHERE task_id=? AND actor=? AND kind='evidence'",
                           (TASK, ACTOR)).fetchall()
        if len(prior) > 1:
            raise RuntimeError("DUPLICATE_EVENT")
        if prior:
            if json.loads(prior[0][1]) != payload:
                raise RuntimeError("EVENT_CONFLICT")
            event_id = prior[0][0]
        else:
            event_id = db.execute(
                "INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                (TASK, time.time(), "evidence", ACTOR, json.dumps(payload, ensure_ascii=False))
            ).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    once(D / "REGISTRY_RESULT_A59.json",
         json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                    ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"event_id": event_id, "QA": payload["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
