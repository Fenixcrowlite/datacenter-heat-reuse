"""Finalize A68 with a frozen timestamp and immutable event payload."""
from pathlib import Path
import hashlib
import json
import re
from a68_checkpoint import canonical, freeze, immutable, record_once, sha

D = Path(__file__).resolve().parent
CENTER = D.parent.parent
TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a68-stable-finalizer-20261027-1753"
SOURCES = ("a68_checkpoint.py", "test_a68.py", "finalize_a68.py",
           "A68_STABILNY_CHECKPOINT_SK.md", "QA_A68_CLEAN.txt")
MANIFEST_FILES = SOURCES + ("CHECKPOINT_A68.json", "EVIDENCE_A68.json")


def guard():
    for root in (CENTER, CENTER / "recovery", D, CENTER.parent / "temp_coding",
                 CENTER.parent / "EduMotionPipeline"):
        for name in ("STOP", "PAUSE", "STOP.flag", "PAUSE.flag"):
            if (root / name).exists():
                raise RuntimeError("STOP_PAUSE:" + str(root / name))


def main():
    guard()
    raw = (D / "QA_A68.txt").read_text(encoding="utf-16")
    if not re.search(r"Ran 13 tests in [0-9.]+s", raw) or not re.search(r"\nOK\s*$", raw):
        raise RuntimeError("QA_FAILED")
    clean = re.sub(r"Ran 13 tests in [0-9.]+s", "Ran 13 tests in <variable>s", raw)
    immutable(D / "QA_A68_CLEAN.txt", clean)
    source_map = {name: sha(D / name) for name in SOURCES}
    source_digest = hashlib.sha256(canonical(source_map)).hexdigest()
    checkpoint = freeze(D / "CHECKPOINT_A68.json", "A68_stable_finalizer", source_digest)
    evidence = {
        "scope": "A68_stable_finalizer_replay", "task_id": TASK,
        "artifact_directory": str(D),
        "checkpoint_created_at_utc": checkpoint["created_at_utc"],
        "source_sha256": source_digest, "unit_tests": "13/13 PASS",
        "python_compile": "PASS", "regression": "timestamp and event replay",
        "source_kind": "derived_simulation", "physical_release": False,
        "status": "VERIFIED_STABLE_CHECKPOINT",
        "next_step": "Use this module in the next isolated finalizer; never rewrite A66/A67 evidence."
    }
    immutable(D / "EVIDENCE_A68.json", canonical(evidence))
    manifest = {name: sha(D / name) for name in MANIFEST_FILES}
    immutable(D / "SHA256_MANIFEST_A68.json", canonical(manifest))
    handoff = (
        "# A68 stable finalizer | " + checkpoint["created_at_utc"] + "\n"
        "A66 timestamp replay defect fixed for future scoped finalizers, not patched in A66.\n"
        "QA: 13/13 tests, Python compile PASS; Windows SQLite handle cleanup regression resolved.\n"
        "Initial QA failed 4 tests because temporary SQLite handles stayed open on Windows; corrected and rerun PASS.\n"
        "Primary SynapseMCP Web unavailable at intake (internal 10001); alternate protected SynapseMCP live.\n"
        "No Codex, GPU jobs, VRS, GUI, OAuth, foreign worktree or original A66/A67 changes.\n"
        "Source kind: derived simulation; physical validation BLOCKED.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A68.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A68.json") + "\n"
        "NEXT: " + evidence["next_step"] + "\n"
    )
    immutable(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A68.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A68.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "13/13 unittest; stable checkpoint; no duplicate events",
        "source_kind": "derived_simulation", "physical_release": False,
        "next_step": evidence["next_step"]
    }
    guard()
    event_id = record_once(CENTER / "tasks.sqlite3", TASK, ACTOR, payload)
    immutable(D / "REGISTRY_RESULT_A68.json", canonical({"event_id": event_id, "task_id": TASK, **payload}))
    print(json.dumps({"event_id": event_id, "checkpoint": checkpoint["created_at_utc"],
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"],
                      "manifest_entries": len(manifest)}, sort_keys=True))


if __name__ == "__main__":
    main()
