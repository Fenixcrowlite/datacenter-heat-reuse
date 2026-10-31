"""A58 deterministic QA/evidence and one idempotent event in existing Synapse card."""
from __future__ import annotations
import ast
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

D = Path(__file__).resolve().parent
CENTER = D.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a58-primary-document-chain-20261027-1047"
UPSTREAM = D.parent / "AUTONOMOUS_RUN_20261027_0952_A57_UNCERTAINTY_TIMEBASE_QA" / "a57_uncertainty_gate.py"
EXPECTED = "309fdf0ab614a0c2f858cde0066cafae5d3f9039fab2eeab85b080d30e19ec1f"


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_once(path: Path, content: str):
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
    if sha(UPSTREAM) != EXPECTED:
        raise RuntimeError("A57_SOURCE_CHANGED")
    scripts = ("a58_document_gate.py", "build_demo_a58.py", "test_a58.py", "finalize_a58.py")
    for f in scripts:
        ast.parse((D / f).read_text(encoding="utf-8"), filename=f)
    p = subprocess.run([sys.executable, "-B", "-m", "unittest", "-v", "test_a58"],
                       cwd=D, capture_output=True, text=True, timeout=35)
    if p.returncode != 0 or "Ran 25 tests" not in p.stderr or not p.stderr.rstrip().endswith("OK"):
        raise RuntimeError("A58_QA_FAILED " + p.stderr[-1600:])
    stable = re.sub(r"Ran 25 tests in [0-9.]+s", "Ran 25 tests in <variable>s", p.stderr)
    write_once(D / "QA_OUTPUT_CLEAN.txt", stable)
    from a58_document_gate import audit
    bundle = D / "DEMO_SYNTHETIC"
    result = audit(bundle)
    if result["physical_release"] or result["independent_issuer_authentication"] or result["document_count"] != 6:
        raise RuntimeError("UNEXPECTED_DOCUMENT_GATE_RESULT")
    # Independent raw file hash checks, not only the audit's result object.
    manifest = json.loads((bundle / "document_manifest.json").read_text(encoding="utf-8"))
    for d in manifest["documents"]:
        if hashlib.file_digest((bundle / d["file"]).open("rb"), "sha256").hexdigest() != d["sha256"]:
            raise RuntimeError("INDEPENDENT_SHA_MISMATCH")
    write_once(D / "DEMO_A58_RESULT.json", json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    summary = {
        "tests": "25/25 PASS", "ast_parse": "4/4 PASS", "document_sha256": "6/6 PASS",
        "upstream_a57_sha256": EXPECTED, "source_kind": "synthetic_test",
        "real_primary_documents": False, "independent_issuer_authentication": False,
        "physical_release": False, "known_gap": "A57 did not require referenced certificate bytes; A58 now does",
    }
    write_once(D / "QA_SUMMARY_A58.json", json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    next_step = ("Obtain asset-specific original calibration certificates, UTC sync records, vendor map "
                 "and telemetry; independently authenticate issuers and instrument IDs, then run "
                 "A55+A56+A57+A58 on immutable real inputs before isolated Stateflow testing.")
    evidence = {
        "task_id": TASK, "scope": "A58_primary_document_chain_integrity_gate",
        "artifact_directory": str(D), "status": "VERIFIED_SYNTHETIC_QA_PHYSICAL_DOCUMENTS_BLOCKED",
        "QA": summary, "source_files_untouched": True, "synthetic_only": True,
        "issuer_authenticity_verified": False, "physical_release": False,
        "next_step": next_step,
    }
    write_once(D / "EVIDENCE_A58.json", json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    names = list(scripts) + ["A58_DOKUMENTACNY_PROTOKOL_SK.md", "QA_OUTPUT_CLEAN.txt",
                             "QA_SUMMARY_A58.json", "DEMO_A58_RESULT.json", "EVIDENCE_A58.json"]
    names += ["DEMO_SYNTHETIC/" + p.name for p in sorted(bundle.iterdir()) if p.is_file()]
    names += ["DEMO_SYNTHETIC/docs/" + p.name for p in sorted((bundle / "docs").iterdir())]
    hashes = {name: sha(D / name) for name in names}
    write_once(D / "SHA256_MANIFEST_A58.json", json.dumps(hashes, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    handoff = (
        "# A58 primary document chain gate | 2026-10-27 10:47 CET\n"
        "Live preflight: SynapseMCP Web ping OK 10:45:48 CET; host DESKTOP-M9L3I4M; "
        "RAM free 4.83 GiB, GPU 0%, VRAM 1057/8188 MiB at 10:46 CET.\n"
        "No STOP/PAUSE found in checked roots; Jarvice main worktree dirty, untouched. "
        "Jarvice worker PIDs 7344 (parent) and 11572 (child) observed, no restart.\n"
        "A58 validates real local bytes behind A57 certificate hashes, dates, asset binding, "
        "units, time sync, vendor-declared operating range and input SHA chain.\n"
        "QA: 25/25 unittest, 4/4 AST, 6/6 independent document SHA checks. "
        "All six demo documents explicitly synthetic; not real calibration/vendor evidence.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A58.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A58.json") + "\n"
        "A57 unchanged SHA256: " + EXPECTED + "\n"
        "No new Codex, worker, GPU job, shared GUI, VRS, OAuth, STOP or peer-owned branch changes.\n"
        "BLOCKED: physical calibration, issuer authenticity and vendor operating limits. "
        "No physical release.\n"
        "NEXT: " + next_step + "\n"
    )
    write_once(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A58.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A58.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "25/25 unittest, 4/4 AST, 6/6 independent document SHA PASS",
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
            event_id = db.execute("INSERT INTO task_events(task_id,at,kind,actor,data_json) VALUES(?,?,?,?,?)",
                                  (TASK, time.time(), "evidence", ACTOR,
                                   json.dumps(payload, ensure_ascii=False))).lastrowid
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
    write_once(D / "REGISTRY_RESULT_A58.json",
               json.dumps({"event_id": event_id, "task_id": TASK, **payload},
                          ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"event_id": event_id, "qa": payload["QA"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"]}))


if __name__ == "__main__":
    main()
