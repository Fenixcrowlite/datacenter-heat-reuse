"""Close the executed monitor gate with hash-bound acceptance evidence.

Implementation QA only. This does not run or fabricate any numerical result.
"""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--monitor-dir", type=Path, required=True)
    parser.add_argument("--acceptance-dir", type=Path, required=True)
    parser.add_argument("--monitor-qa", type=Path, required=True)
    parser.add_argument("--acceptance-qa", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    monitor_dir, acceptance_dir = args.monitor_dir.resolve(), args.acceptance_dir.resolve()
    for directory in (monitor_dir, acceptance_dir):
        assert directory.is_relative_to(ROOT/"results") and directory.is_dir()
    monitor = read(monitor_dir/"gate_fault_rejections_v26.json")
    acceptance = read(acceptance_dir/"acceptance_summary_v24.json")
    monitor_qa, acceptance_qa, receipt = map(read, (args.monitor_qa, args.acceptance_qa, args.receipt))
    model = ROOT/"matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx"
    spec = ROOT/"audit/stateflow_monitor_fault_cases_v26.json"
    prior = read(ROOT/"audit/Stateflow_evidence_manifest_v22_20261009T030247_850694Z.json")
    baseline14 = ROOT/"matlab/simulink/DCHR_Dispatch_Stateflow_v14.slx"
    baseline22 = ROOT/"matlab/simulink/DCHR_Dispatch_Stateflow_v22.slx"
    assert sha(baseline14) == prior["preserved_baseline_sha256"]
    assert sha(baseline22) == next(r["sha256"] for r in prior["files"] if r["path"] == relative(baseline22))
    assert receipt["matlab_batch_exit_code"] == 0
    log = ROOT/receipt["log_file"]
    assert receipt["log_sha256"] == sha(log)
    log_text = log.read_text(encoding="utf-8-sig", errors="replace")
    assert "MONITOR_OUTPUT=" in log_text and "ACCEPTANCE_OUTPUT=" in log_text
    assert acceptance["failed"] == 0 and acceptance["checks"] == acceptance["passed"]
    assert acceptance["simulink_executed"] and acceptance["stateflow_executed"]
    assert acceptance["modes_observed"] == list(range(6))
    assert acceptance["runtime_invalid_cases"] == acceptance["runtime_invalid_cases_rejected"] == 44
    with (acceptance_dir/"stateflow_assertions_v24.csv").open(newline="", encoding="utf-8-sig") as stream:
        assertions = list(csv.DictReader(stream))
    assert len(assertions) == acceptance["checks"] and all(r["passed"] in ("1", "true") for r in assertions)
    assert monitor["cases"] == monitor["rejected"] == monitor["expected_gate_observed"] == len(read(spec)["cases"])
    assert monitor["accepted_invalid_traces"] == 0 and monitor["restored_baseline_matches"]
    assert monitor["model_sha256_before"] == monitor["model_sha256_after"] == sha(model)
    assert monitor_qa["failed"] == 0 and monitor_qa["checks"] == monitor_qa["passed"]
    assert monitor_qa["evidence_summary_sha256"] == sha(monitor_dir/"gate_fault_rejections_v26.json")
    assert monitor_qa["verifier_sha256"] == sha(ROOT/"audit/verify_stateflow_gate_evidence_v26.py")
    assert monitor_qa["spec_sha256"] == sha(spec)
    assert acceptance_qa["failed"] == 0
    assert acceptance_qa["model_sha256"] == sha(model)
    assert acceptance_qa["trace_sha256"] == sha(acceptance_dir/"stateflow_trace_v24.csv")
    assert acceptance_qa["rejections_sha256"] == sha(acceptance_dir/"runtime_rejections_v24.json")
    assert acceptance_qa["verifier_sha256"] == sha(ROOT/"audit/verify_stateflow_runtime_v24.py")
    for key in ("structure", "runtime_rejections", "trace_qa", "self_test"):
        assert acceptance_qa[key]["failed"] == 0
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    next_task = ("Audit an accessible primary-text TES standing-loss model; derive an independent continuous/exponential "
                 "reference and timestep-convergence comparison before changing storage physics. Preserve the v24 "
                 "loss-first linear baseline. Record acquisition limits and primary-text locators; no paper replication claim.")
    limits = [
        "Normal-mode host MATLAB HP adapter; standalone generated-code deployment remains untested.",
        "Loss-first linear TES retention remains time-partition dependent; fresh charge loses standing heat next interval.",
        "Fault injection verifies numerical contract rejection; no equipment fault, hysteresis, dwell, cycling or sensor model.",
        "Reservoir temperature, fixed COP and TES efficiencies remain engineering assumptions without equipment calibration.",
        "No hydraulic/network/fuel/auxiliary model, primary-paper replication or measured-system validation.",
        "Nonfatal Stateflow allocator-output shadow warning remains preserved in logs.",
        "The prior v24 monitor run is incomplete; its interruption cause is unverified. Second-tick domain failure timing is unverified."]
    status = dict(version="0.26", inherits="STATUS_stateflow_v22.json", research_inherits="STATUS_v25.json",
        checkpoint="Completed actual Stateflow runtime-monitor fault acceptance on preserved v24 model",
        timestamp_utc=now.isoformat(), stateflow_acceptance="PASS", matlab_batch_exit_code=0,
        matlab_version=acceptance["matlab_version"], generated_model=relative(model),
        model_version="0.24", model_modified_this_run=False, model_sha256=sha(model),
        monitor_result_directory=relative(monitor_dir), acceptance_result_directory=relative(acceptance_dir),
        scenarios=acceptance["scenarios"], intervals=acceptance["intervals"],
        matlab_checks_passed=acceptance["passed"], matlab_checks_failed=acceptance["failed"],
        runtime_domain_cases_rejected=acceptance["runtime_invalid_cases_rejected"],
        actual_monitor_fault_cases_rejected=monitor["rejected"],
        independent_monitor_checks_passed=monitor_qa["passed"], independent_monitor_failures=monitor_qa["failed"],
        independent_trace_checks_passed=acceptance_qa["trace_qa"]["passed"],
        independent_runtime_checks_passed=acceptance_qa["runtime_rejections"]["passed"],
        independent_structure_checks_passed=acceptance_qa["structure"]["passed"],
        modes_observed=acceptance["modes_observed"],
        max_abs_balance_residual_MWh=acceptance["max_abs_balance_residual_MWh"],
        independent_csv_max_abs_balance_residual_MWh=acceptance_qa["trace_qa"]["max_abs_system_residual_MWh"],
        primary_source_signoffs=0, total_sources=31, primary_text_verified_this_run=False,
        primary_paper_replication=False, independent_physical_validation="NOT_TESTED", standalone_codegen=False,
        limitations=limits, next=next_task)
    write(ROOT/"STATUS_stateflow_v26.json", status)
    stage = (f"# v26: completed executable Stateflow monitor acceptance\n\n"
        f"PASS on preserved model `matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx` (model version 0.24): "
        f"{monitor['rejected']}/{monitor['cases']} actual in-memory chart corruptions rejected by their specified runtime-monitor "
        f"assertions; independent monitor evidence {monitor_qa['passed']}/{monitor_qa['checks']} PASS. "
        "Clean two-interval fixed-COP simulations before and after injection agree exactly; independent TES anchors are "
        "1 → 3.69 → 6.3531 MWh. The saved model and allocation source hashes are unchanged.\n\n"
        f"Fresh full MATLAB acceptance: {acceptance['passed']}/{acceptance['checks']} PASS; "
        f"{acceptance['scenarios']} scenarios, {acceptance['intervals']} intervals, all six modes and "
        f"{acceptance['runtime_invalid_cases_rejected']} actual invalid-domain/clock rejections. "
        f"Independent exported-trace QA {acceptance_qa['trace_qa']['passed']} checks PASS; "
        f"saved-model graph QA {acceptance_qa['structure']['passed']} checks PASS. "
        f"MATLAB maximum residual {acceptance['max_abs_balance_residual_MWh']:.12g} MWh.\n\n"
        "The pre-existing v24 fault run ended without baseline/rejection summary; its cause remains unknown. "
        "This additive harness supplies that missing executed gate and includes nonfinite output, fractional mode, "
        "power/capacity overflow, false losses/residuals, allocation and exclusivity defects. It closes v24 acceptance "
        "without rebuilding or overwriting the versioned model.\n\n"
        f"Evidence: `{relative(monitor_dir)}`, `{relative(acceptance_dir)}`, "
        f"`{relative(args.monitor_qa)}`, `{relative(args.acceptance_qa)}`, `{relative(log)}`.\n\n"
        "Scope: engineering-assumption implementation QA; full primary signoffs remain 0/31. "
        "No primary-paper replication or independent physical validation. " + " ".join(limits) + "\n\n"
        "Reproduce from project root: `matlab -batch \"addpath('matlab','matlab/simulink'); "
        "run_stateflow_monitor_faults_v26; run_stateflow_acceptance_v24;\"`. Run the independent "
        "`audit/verify_stateflow_gate_evidence_v26.py --result-dir <monitor_directory> --report <fresh_report>` and "
        "`audit/verify_stateflow_runtime_v24.py --model matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx "
        "--trace <acceptance_directory>/stateflow_trace_v24.csv --rejections <acceptance_directory>/runtime_rejections_v24.json "
        "--self-test --report <fresh_report>`.\n\nNext: " + next_task + "\n")
    with (ROOT/"MASTER_STAGEBOARD_stateflow_v26.md").open("x", encoding="utf-8") as stream:
        stream.write(stage)
    progress = (f"\n\n## {now.isoformat()} — v26 completed Stateflow runtime-monitor fault gate\n\n"
        "Read latest v25 STATUS/stageboard, authoritative v22 Stateflow status/stageboard, acceptance contract, "
        "research frontier and relevant v14/v16/v22/v24 production code before changes. Found v24 had passed "
        "valid/domain gates but unfinished monitor-fault evidence and no closing status. Added a versioned two-tick "
        "actual-model harness and independently specified 12 corruption cases. Retained every prior model/evidence.\n\n"
        f"Pass/fail: local MATLAB batch exit 0; monitor {monitor['rejected']}/{monitor['cases']} specified assertion "
        f"rejections; independent monitor {monitor_qa['passed']}/{monitor_qa['checks']} PASS. "
        f"Full fresh acceptance {acceptance['passed']}/{acceptance['checks']} PASS across {acceptance['scenarios']} "
        f"scenarios/{acceptance['intervals']} intervals/all six modes; 44/44 actual domain rejections. "
        f"Independent valid trace {acceptance_qa['trace_qa']['passed']} PASS, graph {acceptance_qa['structure']['passed']} PASS. "
        "Unmutated and restored two-tick baselines match exactly and independent energy anchors pass. "
        "Sandbox MATLAB startup FAIL (filesystem inconsistency); auto-reviewed authorized local retry PASS. "
        "Nonfatal output shadow warnings retained. Prior v24 interruption cause unverified.\n\n"
        "Files created: matlab/simulink/run_stateflow_monitor_faults_v26.m; independent audit spec/verifier/self-test/"
        "QA review; audit/finalize_stateflow_checkpoint_v26.py; STATUS_stateflow_v26.json; MASTER_STAGEBOARD_stateflow_v26.md; "
        f"timestamped logs/receipt, `{relative(monitor_dir)}` and `{relative(acceptance_dir)}` numeric CSVs, SimulationOutput "
        "MATs and rejection diagnostics; hash manifest. Existing edits: append this mutable ledger and acceptance completion record.\n\n"
        "Remaining limitations: " + " ".join(limits) + "\n\nNext actionable task: " + next_task + "\n\n"
        "Run stops at this coherent gate and handoff. No scheduler, agent runner, user settings, Jarvice, unrelated "
        "project or external publication was touched.\n")
    with (ROOT/"automation/engineering_progress.md").open("a", encoding="utf-8") as stream:
        stream.write(progress)
    with (ROOT/"automation/STATEFLOW_ACCEPTANCE.md").open("a", encoding="utf-8") as stream:
        stream.write(f"\n\n## Completed acceptance record — {now.isoformat()} / checkpoint v26\n\n"
            "The original v14 prototype remains preserved. Actual versioned v24 model now has complete executed "
            "dispatch, domain and monitor-corruption gates plus independent QA. Authoritative checkpoint: "
            "`STATUS_stateflow_v26.json` and `MASTER_STAGEBOARD_stateflow_v26.md`. "
            "The v26 harness tests the saved v24 model without modifying it; model and checkpoint versions are distinct. "
            "The required six cases/modes, v16 reference comparison, traces, SOC/flow limits and first-law assertions pass. "
            "This is implementation acceptance only, with limitations recorded in the checkpoint.\n")
    paths = {ROOT/"STATUS_stateflow_v26.json", ROOT/"MASTER_STAGEBOARD_stateflow_v26.md", model, baseline14, baseline22,
             args.monitor_qa.resolve(), args.acceptance_qa.resolve(),
             args.receipt.resolve(), log, ROOT/"matlab/simulink/run_stateflow_monitor_faults_v26.m"}
    paths.update(p for p in (ROOT/"audit").glob("*v26*") if p.is_file())
    paths.update(p for p in (ROOT/"matlab/simulink").glob("*v24.m") if p.is_file())
    paths.update(ROOT/p for p in ("matlab/simulink/dchr_stateflow_hp_v22.m", "matlab/+dchr/simulate_dispatch_v16.m",
        "matlab/+dchr/+components/heat_pump_step_v14.m", "matlab/+dchr/+components/storage_step_v16.m",
        "audit/verify_stateflow_runtime_v24.py", "audit/verify_stateflow_trace_v22.py", "audit/stateflow_domain_cases_v24.json",
        "audit/stateflow_qa_vectors_v22.csv", "audit/dispatch_reference_vectors_v18.csv"))
    paths.update(p for directory in (monitor_dir, acceptance_dir) for p in directory.iterdir() if p.is_file())
    paths.update(p for p in (ROOT/"automation/logs").glob("*v26*") if p.is_file() and "finalize" not in p.name and "integrity" not in p.name)
    manifest_path = ROOT/"audit"/f"Stateflow_evidence_manifest_v26_{stamp}.json"
    write(manifest_path, dict(version="0.26", timestamp_utc=now.isoformat(), stateflow_acceptance="PASS",
        scope="Executed saved-model implementation QA, not physical validation", model_modified_this_run=False,
        mutable_files=["automation/engineering_progress.md", "automation/STATEFLOW_ACCEPTANCE.md"],
        ledger_sha256_at_packaging=sha(ROOT/"automation/engineering_progress.md"),
        acceptance_contract_sha256_at_packaging=sha(ROOT/"automation/STATEFLOW_ACCEPTANCE.md"),
        excluded_active_receipts="Finalization/integrity receipt logs; cache/codegen directories are not acceptance artifacts",
        files=[dict(path=relative(p), bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(paths)]))
    print(json.dumps(dict(status="PASS", manifest=relative(manifest_path), matlab_checks=acceptance["passed"],
        actual_fault_rejections=monitor["rejected"], independent_monitor_checks=monitor_qa["passed"]), indent=2))


if __name__ == "__main__":
    main()
