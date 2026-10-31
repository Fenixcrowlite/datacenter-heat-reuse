"""Record this bounded v14 run; preserve all earlier checkpoints/evidence.

This is evidence packaging, not another physics test or a paper signoff.
Must be run only after the listed Python and MATLAB gates have completed.
"""
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = "audit/heat_pump_reference_tests_v14_20261008T215215_727651Z.json"
VECTORS = "audit/heat_pump_vectors_v14_20261008T215215_727651Z.csv"
MATLAB_DIR = "results/hp_contract_v14_20261008_235235"
MATLAB = MATLAB_DIR + "/matlab_heat_pump_contract_v14.json"
ACQUISITION = "audit/Marcinichen_acquisition_v14_20261008T214932788906Z.json"
ACQ_TESTS = "audit/Marcinichen_acquisition_v14_tests_20261008T214932831440Z.json"


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write_new(relative, content):
    with (ROOT / relative).open("x", encoding="utf-8") as stream:
        stream.write(content)


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    iso = now.isoformat()
    manifest_path = f"audit/heat_pump_evidence_manifest_v14_{stamp}.json"
    py, mat, acq, acqt = map(read_json, (PYTHON, MATLAB, ACQUISITION, ACQ_TESTS))
    assert py["failed"] == py["errors"] == mat["failed"] == acqt["failed"] == acqt["errors"] == 0
    assert py["passed"] == 16 and mat["passed"] == 31 and acqt["passed"] == 7
    with (ROOT / VECTORS).open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == py["comparison_vectors"] == mat["vectors"] == 518
    for relative, expected in py["source_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
    assert acq["primary_text_verified"] is False
    assert acq["status"] == "TRANSPORT_BLOCKED"
    assert not mat["annual_dispatch_integrated"] and not mat["simulink_executed"] and not mat["stateflow_executed"]
    assert not (ROOT / "STATUS_v14.json").exists()
    assert not (ROOT / "MASTER_STAGEBOARD_v14.md").exists()
    next_task = (
        "Audit local Sintong original Eq.15-16 IASE/free-cooling flow-ratio domain and Park [38] "
        "provenance; derive passive temperature bounds and record page-level evidence. "
        "Do not repeat the already corrected v07 Eq.17/24 transcription."
    )
    integration_task = (
        "Integrate heat_pump_step_v14 into a separate finite-boiler/TES/unmet dispatch; "
        "compare a deterministic multi-step trace to independent Python before a new Simulink model."
    )
    status = {
        "project": "DataCenter_Heat_Reuse", "version": "0.14", "updated_utc": iso,
        "kind": "additive_component_checkpoint_status", "inherits_status": "STATUS_v12.json",
        "inherits_stageboard": "MASTER_STAGEBOARD_v12.md",
        "milestone": "M3_PARTIAL_ACTUAL_MATLAB_COMPONENT_REFERENCE_GATE",
        "delivered": "Strict heat-pump domain and source-constrained actual part-load output",
        "evidence": ["audit/Heat_pump_domain_and_part_load_v14.md", PYTHON, VECTORS, MATLAB,
                     "audit/Marcinichen_acquisition_v14.md", ACQUISITION, ACQ_TESTS, manifest_path],
        "tests": {
            "independent_python": {"passed": py["passed"], "failed": 0, "errors": 0},
            "matlab_runtime": {"passed": mat["passed"], "failed": 0, "vectors": mat["vectors"],
                               "version": mat["matlab_version"], "max_absolute_residual": mat["max_absolute_residual"]},
            "acquisition_gate_synthetic_only": {"passed": acqt["passed"], "failed": 0},
            "primary_paper_replication": "NOT_PERFORMED",
            "annual_dispatch_v14": "NOT_INTEGRATED",
            "simulink_v14": "NOT_BUILT_OR_EXECUTED",
            "stateflow_v14": "NOT_BUILT_OR_EXECUTED_AVAILABILITY_NOT_CHECKED",
        },
        "attempts_retained": [
            {"log": "automation/logs/matlab_hp_v14_smoke_20261008_235035.log",
             "result": "FAIL_STARTUP_SANDBOX_FILESYSTEM_INCONSISTENCY"},
            {"log": "automation/logs/matlab_hp_v14_contract_20261008_235131.log",
             "result": "FAIL_TEST_HARNESS_STRUCT_INITIALIZATION_FIXED"},
            {"log": "automation/logs/matlab_hp_v14_contract_20261008_235235.log",
             "result": "PASS_31_OF_31"},
        ],
        "findings": [
            {"id": "F14-HP-01", "state": "FIXED_IN_NEW_COMPONENT_ONLY", "topic": "Invalid or sub-kelvin lift clamping"},
            {"id": "F14-HP-02", "state": "FIXED_IN_NEW_COMPONENT_ONLY", "topic": "Upward COP floor can violate Carnot"},
            {"id": "F14-HP-03", "state": "RESOLVED_IN_NEW_COMPONENT_ONLY", "topic": "Nominal versus actual source-limited output"},
            {"id": "F14-ROUNDING", "state": "FIXED_AND_REGRESSION_CHECKED", "topic": "Exact COP cutoff rounded by one unit"},
        ],
        "prior_v13_evidence": {
            "newly_executed_this_run": False,
            "log": "automation/logs/matlab_20261008_234306.log",
            "observed_passed": 4,
            "note": "v13 finite-boiler wrapper exists; still calls unchanged legacy HP and storage components.",
        },
        "research_status": {
            "full_primary_signoffs": 0, "count_source": "inherited STATUS_v12.json",
            "marcinichen": "FULL_ORIGINAL_NOT_ACQUIRED",
            "local_acquisition": "TRANSPORT_BLOCKED_WINERROR_10013",
            "web_epfl_pdf": "HTTP_429", "web_publisher": "HTTP_403",
            "metadata_abstract_is_primary_equation_evidence": False,
        },
        "limitations": [
            "Scenario Carnot fraction, COP thresholds, reservoir proxies and linear part-load penalty lack calibration",
            "No cycling, direct-recovery selection, minimum compressor loading, equipment dynamics or auxiliary electricity",
            "Legacy annual models retain old HP behavior until separately versioned integration",
            "No Simulink/Stateflow execution or availability claim in this run",
        ],
        "next": [next_task, integration_task],
    }
    write_new("STATUS_v14.json", json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    stageboard = f"""# DataCenter Heat Reuse — stageboard v0.14

UTC checkpoint: {iso}. Additive to MASTER_STAGEBOARD_v12.md and STATUS_v12.json. New files preserve previous checkpoints, components, datasets and .slx models.

M2/M3 partial component gate: new strict-domain heat-pump step derives first-law and reservoir-entropy constraints, treats minimum COP as operating eligibility, and sizes output against actual part-load COP. Python solves an analytical quadratic; MATLAB bisects the monotone physical interval. This is engineering-model verification, not source replication or equipment validation.

- Independent Python: {py['passed']}/16 PASS; deterministic seed 14026.
- MATLAB R2026a: {mat['passed']}/31 PASS across 518 vectors (181 available, 337 unavailable). Maximum absolute comparison residual {mat['max_absolute_residual']:.12g}. Evidence: {MATLAB}.
- Primary acquisition safety gates: 7/7 PASS on synthetic fixtures. Marcinichen full text remains unavailable (EPFL web429, publisher web403, local transport restriction). No equation/table verification or source signoff upgraded.
- Earlier v13 MATLAB log shows four passed finite-boiler checks; v13 still calls the legacy heat-pump component. Those checks were not rerun here.

The first MATLAB sandbox startup failed; the first local gate exposed a test-harness struct initialization error, corrected before the passing gate. All failed and passing timestamped logs are retained. An independently found one-unit rounding issue at the exact COP cutoff is covered by the revised vector set. Code Analyzer produced one advisory about a now-unneeded suppression comment in the harness; no numerical check failed in the final run.

M1 remains IN_PROGRESS, with zero full source signoffs inherited from v12. M3 remains partial. M4/M5 have no new executable Simulink/Stateflow deliverable; Stateflow availability was not tested. v14 annual dispatch integration is still open.

Next scheduled task: {next_task}

Following engineering task: {integration_task}

Details: audit/Heat_pump_domain_and_part_load_v14.md, STATUS_v14.json, automation/engineering_progress.md. Immutable file hashes: {manifest_path}.
"""
    write_new("MASTER_STAGEBOARD_v14.md", stageboard)
    progress = f"""
## {iso} — v14 heat-pump domain / actual part-load component gate

Completed one bounded run. Read v12 status/stageboard, research frontier and existing physics/components before edits. Created a strict scalar HP component, independently derived first-law/entropy/Carnot and source-bound quadratic equations, and verified MATLAB bisection against independent Python analytical roots. Legacy code remains unchanged. A lower COP is never raised to satisfy a threshold; unavailable points have zero flows and undefined operating COP. Corrected a MATLAB test-harness initialization error and a one-unit cutoff-rounding defect, retaining failure and earlier reference evidence.

Pass/fail: Python16/16 PASS; MATLAB31/31 PASS over518 vectors, maximum absolute residual {mat['max_absolute_residual']:.12g}; acquisition safety7/7 PASS on synthetic fixtures. Sandbox MATLAB startup FAIL (filesystem inconsistency); first local harness FAIL (dissimilar struct assignment), corrected; final gate PASS. Original Marcinichen acquisition FAIL/blocked: EPFL web429, publisher web403, local WinError10013. Metadata/abstract is not primary equation/table verification. No paper replication, calibrated experiment, annual-v14 dispatch, Simulink or Stateflow result claimed. Stateflow availability not checked.

Files created: matlab/+dchr/+components/heat_pump_step_v14.m; matlab/run_heat_pump_contract_v14.m; audit/heat_pump_reference_v14.py; audit/test_heat_pump_reference_v14.py; audit/Heat_pump_domain_and_part_load_v14.md; audit/Marcinichen_acquisition_v14.py, _test.py, .md and timestamped JSON; timestamped Python vector/test evidence and console logs; {MATLAB_DIR}/ three MATLAB result files; audit/finalize_checkpoint_v14.py; STATUS_v14.json; MASTER_STAGEBOARD_v14.md; this progress ledger; {manifest_path}. No pre-existing baseline artifact was edited. The progress ledger was absent when this run began and is now maintained.

Logs: automation/logs/hp_reference_v14_20261008T215215_727651Z.log; automation/logs/matlab_hp_v14_contract_20261008_235235.log; earlier failed MATLAB and initial Python logs preserved; acquisition logs under automation/logs/Marcinichen_acquisition_v14_*.log. Exact paths/hashes are in the manifest. Packaging consistency verification checks evidence counts, Python source hashes and non-validation flags; it does not rerun physics.

Remaining limits: temperature/reservoir and efficiency/part-load parameters are scenario assumptions; no refrigerant map, cycling, minimum compressor loading, ramp/fault/auxiliary-power model. New component is not integrated into v13 or old .slx model. Marcinichen original still blocks the pump/compressor temperature attribution. No full primary signoff exists.

Next actionable task: {next_task}

Following engineering handoff: {integration_task}

Run stops at this coherent component gate and handoff. Scheduler, runner, settings and unrelated projects were not modified.
"""
    progress_path = ROOT / "automation/engineering_progress.md"
    if not progress_path.exists():
        write_new("automation/engineering_progress.md", "# Engineering progress\n")
    with progress_path.open("a", encoding="utf-8") as stream:
        stream.write(progress)
    files = [
        "STATUS_v14.json", "MASTER_STAGEBOARD_v14.md", "automation/engineering_progress.md",
        "audit/finalize_checkpoint_v14.py", "audit/Heat_pump_domain_and_part_load_v14.md",
        "matlab/+dchr/+components/heat_pump_step_v14.m", "matlab/run_heat_pump_contract_v14.m",
        "audit/heat_pump_reference_v14.py", "audit/test_heat_pump_reference_v14.py",
        PYTHON, VECTORS, MATLAB, MATLAB_DIR + "/matlab_heat_pump_vectors_v14.csv",
        MATLAB_DIR + "/matlab_heat_pump_contract_v14.csv", ACQUISITION, ACQ_TESTS,
        "audit/Marcinichen_acquisition_v14.md", "audit/Marcinichen_acquisition_v14.py",
        "audit/Marcinichen_acquisition_v14_test.py",
    ]
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT / "automation/logs").iterdir()
              if p.is_file() and ("hp_v14" in p.name or "hp_reference_v14" in p.name or "Marcinichen_acquisition_v14" in p.name)]
    files += [p.relative_to(ROOT).as_posix() for p in (ROOT / "audit").iterdir()
              if p.name.startswith(("heat_pump_reference_tests_v14_", "heat_pump_vectors_v14_"))]
    manifest = {
        "timestamp_utc": iso, "category": "immutable_post_gate_file_manifest",
        "packaging_checks": "PASS", "primary_replication": False,
        "files": {p: {"bytes": (ROOT / p).stat().st_size,
                      "sha256": hashlib.sha256((ROOT / p).read_bytes()).hexdigest()}
                  for p in sorted(set(files))},
    }
    write_new(manifest_path, json.dumps(manifest, indent=2) + "\n")
    log_path = f"automation/logs/checkpoint_v14_{stamp}.log"
    write_new(log_path, f"UTC {iso}\nEvidence count/source hash/verification-category consistency: PASS\n"
              f"Manifest: {manifest_path}\nPython16/16; MATLAB31/31 over518 vectors; synthetic acquisition7/7\n"
              "Primary original acquisition: BLOCKED; no source signoff\n")
    print(json.dumps({"checkpoint": "STATUS_v14.json", "manifest": manifest_path,
                      "packaging_log": log_path, "python_passed": py["passed"],
                      "matlab_passed": mat["passed"], "vectors": mat["vectors"]}))


if __name__ == "__main__":
    main()
