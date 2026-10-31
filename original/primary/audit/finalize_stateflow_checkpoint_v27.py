"""Package executed temporal Stateflow evidence without rerunning simulations."""
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


def write(path, data):
    with path.open("x", encoding="utf-8") as out:
        json.dump(data, out, indent=2, allow_nan=False)
        out.write("\n")


def relative(path):
    return path.resolve().relative_to(ROOT).as_posix()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--result-dir", type=Path, required=True)
    p.add_argument("--qa", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    directory = args.result_dir.resolve()
    assert directory.is_relative_to(ROOT/"results")
    summary_path = directory/"temporal_summary_v27.json"
    summary, qa, receipt = map(read, (summary_path, args.qa, args.receipt))
    prior = read(ROOT/"STATUS_stateflow_v26.json")
    model = ROOT/prior["generated_model"]
    spec = ROOT/"audit/stateflow_temporal_cases_v27.json"
    runner = ROOT/"matlab/simulink/run_stateflow_temporal_acceptance_v27.m"
    assert prior["stateflow_acceptance"] == "PASS"
    assert summary["model_sha256_before"] == summary["model_sha256_after"] == prior["model_sha256"] == sha(model)
    assert summary["spec_sha256"] == sha(spec) and summary["runner_sha256"] == sha(runner)
    assert summary["failed"] == 0 and summary["checks"] == summary["passed"]
    assert summary["cases"] == len(summary["records"]) == len(read(spec)["cases"])
    assert qa["failed"] == 0 and qa["checks"] == qa["passed"]
    assert qa["evidence_summary_sha256"] == sha(summary_path)
    assert qa["verifier_sha256"] == sha(ROOT/"audit/verify_stateflow_temporal_v27.py")
    assert receipt["matlab_batch_exit_code"] == 0
    log = ROOT/receipt["log_file"]
    assert sha(log) == receipt["log_sha256"] and "TEMPORAL_OUTPUT=" in log.read_text(encoding="utf-8-sig", errors="replace")
    with (directory/"temporal_assertions_v27.csv").open(encoding="utf-8-sig", newline="") as out:
        rows = list(csv.DictReader(out))
    assert len(rows) == summary["checks"] and all(r["passed"] in ("1", "true") for r in rows)
    assert all(r["valid_prefix_matches"] and r["timing_matches"] and r["cause_matches"] for r in summary["records"])
    rejected = [r for r in summary["records"] if r["expected_outcome"] == "runtime_rejection"]
    completed = [r for r in summary["records"] if r["expected_outcome"] == "complete"]
    assert len(rejected) == 10 and len(completed) == 2
    prior_manifest = read(ROOT/"audit/Stateflow_evidence_manifest_v26_20261009T080121_129319Z.json")
    preserved = {f["path"]: f["sha256"] for f in prior_manifest["files"]}
    preservation_paths = [p for p in preserved if p.startswith("matlab/") and p.endswith((".m", ".slx"))]
    assert all(sha(ROOT/p) == preserved[p] for p in preservation_paths), "Prior model/production source changed"
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    next_task = ("Audit an accessible primary-text TES standing-loss model; derive an independent continuous/exponential "
                 "reference and timestep-convergence comparison before changing storage physics. Preserve the v24 "
                 "loss-first linear baseline. Record full-text locators and acquisition limits; no paper replication claim.")
    limits = [
        "Temporal acceptance covers finite delayed source/demand/temperature-domain faults; delayed NaN/Inf ingestion timing remains untested.",
        "Actual Simulink captured and thrown diagnostics flatten inner causes; nested causes are verified only in separate host-adapter component calls.",
        "Normal-mode host MATLAB HP adapter; standalone generated-code deployment remains untested.",
        "Loss-first linear TES retention remains time-partition dependent; fresh charge loses standing heat next interval.",
        "No equipment fault, hysteresis, dwell, compressor cycling/ramping, sensor, hydraulic/network/fuel/auxiliary model.",
        "Reservoir temperature, COP and TES efficiencies remain engineering assumptions without equipment calibration.",
        "No primary-paper replication or measured-system physical validation; full primary signoffs remain 0/31.",
        "Nonfatal Stateflow allocator-output shadow warning remains in execution logs; earlier v24 interruption cause remains unknown."]
    status = dict(version="0.27", inherits="STATUS_stateflow_v26.json", research_inherits="STATUS_v25.json",
                  checkpoint="Executed delayed-input failure timing and sampled-boundary acceptance on preserved v24 Stateflow",
                  timestamp_utc=now.isoformat(), stateflow_acceptance="PASS", temporal_acceptance="PASS",
                  matlab_version=summary["matlab_version"], matlab_batch_exit_code=receipt["matlab_batch_exit_code"],
                  generated_model=relative(model), model_version="0.24", model_modified_this_run=False, model_sha256=sha(model),
                  result_directory=relative(directory), independent_qa=relative(args.qa),
                  matlab_checks_passed=summary["passed"], matlab_checks_failed=summary["failed"],
                  temporal_rejections=len(rejected), completed_future_input_controls=len(completed),
                  independently_checked_valid_prefixes=len(summary["records"]),
                  independent_checks_passed=qa["passed"], independent_checks_failed=qa["failed"],
                  independent_actual_temporal_checks=qa["temporal_evidence"]["passed"],
                  independent_integrity_checks=qa["integrity"]["passed"],
                  independent_post_fault_restart_checks=qa["post_fault_clean_restart"]["passed"],
                  independent_specification_checks=qa["specification"]["passed"],
                  synthetic_reviewer_self_checks=qa["synthetic_reviewer_self_test"]["passed"],
                  model_sample_intervals_h=sorted({r["dt_h"] for r in summary["records"]}),
                  prior_six_mode_acceptance=prior["stateflow_acceptance"], prior_acceptance_result_directory=prior["acceptance_result_directory"],
                  primary_text_verified_this_run=False, primary_source_signoffs=0, total_sources=31,
                  primary_paper_replication=False, independent_physical_validation="NOT_TESTED", standalone_codegen=False,
                  limitations=limits, next=next_task)
    write(ROOT/"STATUS_stateflow_v27.json", status)
    stage = (f"# v27: executed Stateflow failure timing and sample boundaries\n\n"
             f"PASS: {summary['passed']}/{summary['checks']} MATLAB assertions and {qa['passed']}/{qa['checks']} "
             "independent QA checks on the preserved v24 model (model version 0.24). Ten finite domain faults reject "
             "at the independently predicted first sampled invalid input, with Execution-phase metadata and exactly "
             "the accepted valid prefix. Sample intervals are 0.25, 0.5, 1 and 2 h; invalid changes occur at ticks "
             "1 and 3 and between ticks. Two invalid-future-input controls complete normally, including StopTime=0. "
             "Clean and partial numerical ports agree with the verified v16 reference and the independent closed-form "
             "fixed-COP/TES oracle. A final clean simulation confirms restart at the initial TES state.\n\n"
             f"Independent QA breakdown: {qa['temporal_evidence']['passed']} actual temporal checks, "
             f"{qa['integrity']['passed']} integrity checks, {qa['post_fault_clean_restart']['passed']} "
             f"post-fault restart checks, {qa['specification']['passed']} specification checks and "
             f"{qa['synthetic_reviewer_self_test']['passed']} synthetic reviewer self-tests.\n\n"
             "Actual Simulink diagnostics retain the physical-domain wrapper and fault-specific message but flatten "
             "inner causes in both captured and thrown modes. Separate host-adapter calls verify original causes; "
             "these component calls are not model-timing evidence. The initial record-assembly failure and completed "
             "60/70 run with incorrect inner-cause expectations are preserved, as is a subsequent JSON cell-schema "
             "setup failure before simulation. Sandbox startup failed before tests; "
             "authorized local MATLAB execution passed after repairs.\n\n"
             f"Evidence: `{relative(directory)}`, `{relative(args.qa)}`, `{relative(log)}`, "
             "`audit/Stateflow_temporal_independent_QA_v27.md`. The saved model and previous acceptance remain preserved. "
             "The existing v26 six-mode/39-interval/44-domain/12-monitor-fault acceptance is inherited rather than rerun.\n\n"
             "Implementation QA only. " + " ".join(limits) + "\n\n"
             "Reproduce from the project root: `matlab -batch \"addpath('matlab','matlab/simulink'); "
             "run_stateflow_temporal_acceptance_v27;\"`, then "
             "`python audit/verify_stateflow_temporal_v27.py --summary <fresh_result_directory>/temporal_summary_v27.json "
             "--self-test --report <fresh_QA_report>`.\n\nNext: " + next_task + "\n")
    stage_path = ROOT/"MASTER_STAGEBOARD_stateflow_v27.md"
    with stage_path.open("x", encoding="utf-8") as out:
        out.write(stage)
    progress = (f"\n\n## {now.isoformat()} — v27 actual Stateflow delayed-domain timing\n\n"
                "Read STATUS/stageboards v25/v26, research frontier, acceptance contract and relevant v14/v16/v22/v24/v26 "
                "source before changes. Closed the explicitly unverified second-tick timing gap with a versioned "
                "CaptureErrors harness, independent test specification, closed-form numerical oracle, corrupted-evidence "
                "self-tests and a separate QA reviewer. No physical model or saved .slx was changed.\n\n"
                f"Pass/fail: final local MATLAB exit 0; {summary['passed']}/{summary['checks']} PASS; ten delayed "
                f"finite faults reject at the predicted sample, two future-input controls complete; independent "
                f"QA {qa['passed']}/{qa['checks']} PASS. Clean/v16/analytic and valid-prefix/TES-memory checks pass. "
                "Sandbox startup FAIL before simulation; first local attempt FAIL record assembly; second local "
                "attempt 60/70 PASS with ten incorrect inner-cause assertions. Discovered that Simulink flattens "
                "nested causes in both error modes; clarified evidence scope. Third local attempt FAIL before "
                "simulation because heterogeneous JSON cases decode as cells; added explicit cell/struct handling "
                "and reran. Every earlier output/log "
                "is retained, including matched source/spec snapshots for the complete failed run.\n\n"
                "Files created: matlab/simulink/run_stateflow_temporal_acceptance_v27.m; audit/stateflow_temporal_cases_v27.json, "
                "audit/verify_stateflow_temporal_v27.py, audit/Stateflow_temporal_independent_QA_v27.md, "
                "audit/finalize_stateflow_checkpoint_v27.py; STATUS_stateflow_v27.json; MASTER_STAGEBOARD_stateflow_v27.md; "
                f"`{relative(directory)}` with actual SimulationOutput MATs, configured inputs, numerical traces, "
                "diagnostics, exception/component reports and assertions; timestamped QA/self-test/logs, receipt and manifest. "
                "Existing edit: append this mutable ledger and acceptance ledger.\n\n"
                f"Authoritative execution log: `{relative(log)}`; QA: `{relative(args.qa)}`.\n\n"
                "Remaining limitations: " + " ".join(limits) + "\n\nNext actionable task: " + next_task + "\n\n"
                "Run stops at this coherent temporal acceptance and handoff. No scheduler, runner, user settings, "
                "Jarvice, unrelated project or external publication was changed.\n")
    with (ROOT/"automation/engineering_progress.md").open("a", encoding="utf-8") as out:
        out.write(progress)
    with (ROOT/"automation/STATEFLOW_ACCEPTANCE.md").open("a", encoding="utf-8") as out:
        out.write(f"\n\n## Additional temporal acceptance — {now.isoformat()} / checkpoint v27\n\n"
                  "The preserved v24 model now also has executed delayed-domain timing, sampled-boundary and "
                  "valid-prefix acceptance with independent QA. Ten finite delayed faults and two future-input "
                  "controls pass. Authoritative checkpoint: STATUS_stateflow_v27.json and MASTER_STAGEBOARD_stateflow_v27.md. "
                  "The production model version remains 0.24. Primary/physical-validation limits remain explicit.\n")
    files = set(directory.glob("*.*"))
    files.update(p for p in (ROOT/"audit").glob("*v27*") if p.is_file())
    files.update(p for p in (ROOT/"automation/logs").glob("*temporal*v27*") if p.is_file())
    files.update({runner, args.qa.resolve(), args.receipt.resolve(), ROOT/"STATUS_stateflow_v27.json", stage_path})
    files.update(ROOT/p for p in preservation_paths)
    # Include retained failed attempts without including generated caches.
    for attempt in (ROOT/"results").glob("stateflow_temporal_v27_*"):
        files.update(p for p in attempt.glob("*.*") if p.is_file())
    manifest = dict(version="0.27", timestamp_utc=now.isoformat(), stateflow_temporal_acceptance="PASS",
                    inherited_acceptance_checkpoint="STATUS_stateflow_v26.json", preserved_prior_source_files=len(preservation_paths),
                    mutable_files_excluded=["automation/engineering_progress.md", "automation/STATEFLOW_ACCEPTANCE.md"],
                    files=[dict(path=relative(p), sha256=sha(p), bytes=p.stat().st_size) for p in sorted(files)])
    path = ROOT/"audit"/f"Stateflow_temporal_manifest_v27_{stamp}.json"
    write(path, manifest)
    print(json.dumps(dict(status="PASS", checkpoint="STATUS_stateflow_v27.json", manifest=relative(path),
                          immutable_files=len(manifest["files"]), preserved_source_files=len(preservation_paths))))


if __name__ == "__main__":
    main()
