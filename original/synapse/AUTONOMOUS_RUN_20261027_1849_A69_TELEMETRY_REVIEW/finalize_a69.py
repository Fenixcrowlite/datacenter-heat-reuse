"""A69 idempotent finalization via verified A68 checkpoint helper."""
import hashlib
import json
import re
import sys
from pathlib import Path

D = Path(__file__).resolve().parent
CENTER = D.parent.parent
A68 = D.parent / "AUTONOMOUS_RUN_20261027_1753_A68_STABLE_FINALIZER"
sys.path.insert(0, str(A68))
from a68_checkpoint import canonical, freeze, immutable, record_once, sha  # noqa: E402

TASK = "scc-3d9d172beb6e1b"
ACTOR = "chatgpt-a69-offline-telemetry-review-20261027-1849"
SOURCES = (
    "a69_telemetry_review.py", "test_a69.py", "qa_independent_a69.py",
    "qa_browser_a69.py", "finalize_a69.py", "A69_TECHNICAL_SK.md",
    "QA_A69_CANONICAL.txt", "INDEPENDENT_QA_A69.json", "BROWSER_QA_A69.json",
    "FIXTURE/telemetry.csv", "FIXTURE/metadata.json", "FIXTURE/provenance.json",
    "OUTPUT_SYNTHETIC/summary.json", "OUTPUT_SYNTHETIC/review.html",
    "OUTPUT_SYNTHETIC/source_receipt.json",
)
MANIFEST_FILES = SOURCES + ("CHECKPOINT_A69.json", "EVIDENCE_A69.json")
NEXT = ("Use A59 channel mapping on a verified SCADA export, produce A69 review; "
        "obtain calibration/timebase evidence for A57/A58 before physical acceptance.")


def guard():
    roots = (CENTER, CENTER / "recovery", D,
             CENTER.parent / "temp_coding", CENTER.parent / "EduMotionPipeline")
    for root in roots:
        for name in ("STOP", "PAUSE", "STOP.flag", "PAUSE.flag"):
            if (root / name).exists():
                raise RuntimeError("STOP_PAUSE:" + str(root / name))


def main():
    guard()
    raw = (D / "QA_A69_CLEAN.txt").read_text(encoding="utf-16")
    if not re.search(r"Ran 19 tests in [0-9.]+s", raw) or not re.search(
            r"OK \(skipped=1\)\s*$", raw):
        raise RuntimeError("UNIT_QA_FAILED")
    normalized = re.sub(r"Ran 19 tests in [0-9.]+s",
                        "Ran 19 tests in <variable>s", raw)
    immutable(D / "QA_A69_CANONICAL.txt", normalized)
    independent = json.loads((D / "INDEPENDENT_QA_A69.json").read_text(encoding="utf-8"))
    browser = json.loads((D / "BROWSER_QA_A69.json").read_text(encoding="utf-8"))
    report = json.loads((D / "OUTPUT_SYNTHETIC" / "summary.json").read_text(encoding="utf-8"))
    receipt = json.loads((D / "OUTPUT_SYNTHETIC" / "source_receipt.json").read_text(encoding="utf-8"))
    if independent.get("status") != "PASS" or browser.get("status") != "PASS":
        raise RuntimeError("INDEPENDENT_QA_FAILED")
    if sorted(browser.get("viewport_results", {})) != ["1440", "320", "390"]:
        raise RuntimeError("VIEWPORT_COVERAGE_FAILED")
    for width, data in browser["viewport_results"].items():
        if data["innerWidth"] != int(width) or data["scrollWidth"] > int(width):
            raise RuntimeError("BROWSER_OVERFLOW:" + width)
    if report.get("physical_release") is not False or report.get("source_kind") != "synthetic_test":
        raise RuntimeError("PROVENANCE_NOT_SYNTHETIC")
    if report.get("rows") != 30 or independent.get("observed_intervals") != 29:
        raise RuntimeError("FIXTURE_MISMATCH")
    for name, expected in receipt["source_hashes"].items():
        if sha(D / "FIXTURE" / name) != expected:
            raise RuntimeError("SOURCE_RECEIPT_MISMATCH")
    for name, expected in receipt["output_sha256"].items():
        if sha(D / "OUTPUT_SYNTHETIC" / name) != expected:
            raise RuntimeError("OUTPUT_RECEIPT_MISMATCH")
    source_map = {name: sha(D / name) for name in SOURCES}
    source_digest = hashlib.sha256(canonical(source_map)).hexdigest()
    checkpoint = freeze(D / "CHECKPOINT_A69.json", "A69_offline_telemetry_review", source_digest)
    evidence = {
        "scope": "A69_offline_A59_telemetry_review", "task_id": TASK,
        "artifact_directory": str(D),
        "checkpoint_created_at_utc": checkpoint["created_at_utc"],
        "source_sha256": source_digest,
        "source_kind": "synthetic_test", "physical_release": False,
        "unit_tests": "18 PASS, 1 SKIP (Windows symlink privilege)",
        "independent_numeric_QA": "PASS; 4 exact Decimal energy channels",
        "browser_QA": "PASS; actual CSS viewports 320/390/1440",
        "provenance_sha256": "PASS; 3 input and 2 output",
        "product": "offline standalone HTML review + JSON summary + receipt",
        "status": "VERIFIED_SOFTWARE_NOT_PHYSICAL",
        "next_step": NEXT
    }
    immutable(D / "EVIDENCE_A69.json", canonical(evidence))
    manifest = {name: sha(D / name) for name in MANIFEST_FILES}
    immutable(D / "SHA256_MANIFEST_A69.json", canonical(manifest))
    handoff = (
        "# A69 offline A59 telemetry review | " + checkpoint["created_at_utc"] + "\n"
        "Product: OUTPUT_SYNTHETIC/review.html, summary.json, source_receipt.json.\n"
        "QA: 18 PASS / 1 SKIP; independent Decimal 4 channels PASS; "
        "Chrome CDP true 320/390/1440 CSS viewports PASS.\n"
        "Regression: existing TRIPPED states require baseline-aware test; "
        "Chrome CLI window-size cannot prove a 320px viewport.\n"
        "Input is SYNTHETIC A59 fixture, NOT calibrated equipment telemetry.\n"
        "Physical validation BLOCKED; no SCADA, MATLAB, shared GUI, VRS, "
        "OAuth, other branches, Codex, or GPU workers modified.\n"
        "Evidence SHA256: " + sha(D / "EVIDENCE_A69.json") + "\n"
        "Manifest SHA256: " + sha(D / "SHA256_MANIFEST_A69.json") + "\n"
        "NEXT: " + NEXT + "\n"
    )
    immutable(D / "FINAL_HANDOFF.md", handoff)
    payload = {
        "scope": evidence["scope"], "artifact_directory": str(D),
        "evidence_sha256": sha(D / "EVIDENCE_A69.json"),
        "manifest_sha256": sha(D / "SHA256_MANIFEST_A69.json"),
        "handoff_sha256": sha(D / "FINAL_HANDOFF.md"),
        "QA": "18 PASS/1 SKIP, independent Decimal PASS, true mobile Chrome 3/3 PASS",
        "source_kind": "synthetic_test", "physical_release": False,
        "next_step": NEXT
    }
    guard()
    event_id = record_once(CENTER / "tasks.sqlite3", TASK, ACTOR, payload)
    immutable(D / "REGISTRY_RESULT_A69.json", canonical({"event_id": event_id, "task_id": TASK, **payload}))
    print(json.dumps({"event_id": event_id, "task_id": TASK,
                      "evidence_sha256": payload["evidence_sha256"],
                      "handoff_sha256": payload["handoff_sha256"],
                      "manifest_entries": len(manifest)}, sort_keys=True))


if __name__ == "__main__":
    main()
