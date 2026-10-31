"""Close the executed v28 fault gates as checkpoint v29, preserving prior evidence."""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rel(path):
    return Path(path).resolve().relative_to(ROOT).as_posix()


def write(path, value):
    with Path(path).open("x", encoding="utf-8") as out:
        json.dump(value, out, indent=2, allow_nan=False)
        out.write("\n")


def sections(report):
    return {k: v for k, v in report.items() if isinstance(v, dict) and "passed" in v and "failed" in v}


def qa_breakdown(reports):
    classes = {"actual_evidence", "synthetic_reviewer_self_test", "static_specification"}
    required = {
        "temporal": {"specification", "integrity", "temporal_evidence", "saved_model_structure", "post_fault_clean_restart"},
        "monitor": {"specification", "fault_rejections", "runtime_artifact_bindings", "saved_model_structure",
                    "baseline_trace", "restored_trace", "integrity"},
    }
    optional = {"temporal": {"synthetic_reviewer_self_test"}, "monitor": {"synthetic_verifier_self_test"}}
    breakdown = {}
    for label, report in reports:
        names = set(sections(report))
        assert required[label] <= names <= required[label] | optional[label], (label, names)
        for key, value in sections(report).items():
            category = value["evidence_class"]
            assert category in classes, (label, key, category)
            expected = ("static_specification" if key == "specification" else
                        "synthetic_reviewer_self_test" if key.startswith("synthetic_") else "actual_evidence")
            assert category == expected, (label, key, category, expected)
            assert all(type(value[m]) is int and value[m] >= 0 for m in ("checks", "passed", "failed"))
            assert value["checks"] > 0, (label, key, "Empty QA section")
            assert value["checks"] == value["passed"] + value["failed"]
            assert value["synthetic_only"] == (category == "synthetic_reviewer_self_test")
            breakdown[label + ":" + key] = {
                "passed": value["passed"], "failed": value["failed"],
                "synthetic_only": value["synthetic_only"], "evidence_class": category,
            }
        for category in classes:
            for metric in ("checks", "passed", "failed"):
                assert report[category + "_" + metric] == sum(
                    v[metric] for v in sections(report).values() if v["evidence_class"] == category
                ), (label, category, metric)
        for metric in ("checks", "passed", "failed"):
            assert report[metric] == sum(v[metric] for v in sections(report).values()), (label, metric)
    return breakdown


def verify_receipt(receipt, td, md):
    expected = {rel(td): "TEMPORAL_OUTPUT=", rel(md): "MONITOR_OUTPUT="}
    assert len(receipt["executions"]) == 2
    assert {e["result_directory"] for e in receipt["executions"]} == set(expected)
    assert len({e["log_file"] for e in receipt["executions"]}) == 2
    assert len({e["console_file"] for e in receipt["executions"]}) == 2
    for execution in receipt["executions"]:
        assert execution["matlab_batch_exit_code"] == 0 and execution["exit_observed"] is True
        assert sha(ROOT / execution["log_file"]) == execution["log_sha256"]
        assert sha(ROOT / execution["console_file"]) == execution["console_sha256"]
        directory = ROOT / execution["result_directory"]
        marker = expected[execution["result_directory"]] + str(directory)
        assert execution["output_marker"] == marker
        for key in ("log_file", "console_file"):
            assert marker in (ROOT / execution[key]).read_text(encoding="utf-8-sig", errors="replace")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--temporal-dir", type=Path, required=True)
    parser.add_argument("--monitor-dir", type=Path, required=True)
    parser.add_argument("--temporal-qa", type=Path, required=True)
    parser.add_argument("--monitor-qa", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--peer-review", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true", help="Validate all inputs without writing a checkpoint or ledgers")
    args = parser.parse_args()
    td, md = args.temporal_dir.resolve(), args.monitor_dir.resolve()
    assert td.is_relative_to(ROOT / "results") and md.is_relative_to(ROOT / "results")
    ts, ms = td / "temporal_summary_v29.json", md / "gate_fault_rejections_v29.json"
    temporal, monitor, tq, mq, receipt = map(read, (ts, ms, args.temporal_qa, args.monitor_qa, args.receipt))
    prior = read(ROOT / "STATUS_stateflow_v28.json")
    model = ROOT / prior["generated_model"]
    assert prior["stateflow_acceptance"] == "PASS" and sha(model) == prior["model_sha256"]
    assert sha(ROOT / "matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx") == prior["preserved_v24_sha256"]
    assert temporal["model_version"] == monitor["model_release"] == "0.28"
    for summary in (temporal, monitor):
        assert summary["version"] == "0.29"
        assert summary["model_sha256_before"] == summary["model_sha256_after"] == sha(model)
        assert summary["saved_model_modified"] is False
        assert summary["simulink_executed"] and summary["stateflow_executed"] and summary["stateflow_license"]
        assert summary["source_sha256_before"] == summary["source_sha256_after"]
        assert summary["saved_embedded_sources_match"]
        for row in summary["source_sha256_before"]:
            assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
        for row in summary["source_snapshot_hashes"]:
            assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
    for report, summary, summary_path, verifier in (
        (tq, temporal, ts, "verify_stateflow_temporal_v29.py"),
        (mq, monitor, ms, "verify_stateflow_gate_evidence_v29.py")
    ):
        assert report["failed"] == 0 and report["checks"] == report["passed"]
        assert report["evidence_summary_sha256"] == sha(summary_path)
        assert report["verifier_sha256"] == sha(ROOT / "audit" / verifier)
        assert report["spec_sha256"] == summary["spec_sha256"] == sha(summary["spec_file"])
        assert all(s["failed"] == 0 for s in sections(report).values())
    assert temporal["failed"] == 0 and temporal["checks"] == temporal["passed"]
    with (td / "temporal_assertions_v29.csv").open(encoding="utf-8-sig", newline="") as stream:
        assertions = list(csv.DictReader(stream))
    assert len(assertions) == temporal["checks"] and all(r["passed"] in ("1", "true") for r in assertions)
    rejected = [r for r in temporal["records"] if r["expected_outcome"] == "runtime_rejection"]
    controls = [r for r in temporal["records"] if r["expected_outcome"] == "complete"]
    assert temporal["cases"] == len(temporal["records"]) == 12 and len(rejected) == 10 and len(controls) == 2
    assert all(r["valid_prefix_matches"] and r["timing_matches"] and r["cause_matches"] for r in temporal["records"])
    assert monitor["cases"] == monitor["rejected"] == monitor["expected_gate_observed"] == 13
    assert monitor["captured_runtime_rejections"] == 13 and monitor["compilation_failures"] == 0
    assert monitor["accepted_invalid_traces"] == 0 and monitor["embedded_source_restored"]
    assert len(monitor["records"]) == 13
    verify_receipt(receipt, td, md)
    assert args.peer_review.is_file() and args.peer_review.resolve().is_relative_to(ROOT / "audit")
    peer_review = read(args.peer_review)
    assert peer_review["version"] == "0.29" and peer_review["failed"] == 0
    assert peer_review["checks"] == peer_review["passed"] and peer_review["review_type"]
    assert peer_review["dynamic_model_execution_this_review"] is False
    assert peer_review["primary_text_verified_this_review"] is False
    assert peer_review["physical_validation"] is False
    old = read(ROOT / "audit/Stateflow_manifest_v28_20261009T153508_918445Z.json")
    for row in old["files"]:
        assert sha(ROOT / row["path"]) == row["sha256"], row["path"]
        assert (ROOT / row["path"]).stat().st_size == row["bytes"], row["path"]
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    breakdown = qa_breakdown((("temporal", tq), ("monitor", mq)))
    actual = sum(v["passed"] for v in breakdown.values() if v["evidence_class"] == "actual_evidence")
    synthetic = sum(v["passed"] for v in breakdown.values() if v["evidence_class"] == "synthetic_reviewer_self_test")
    static = sum(v["passed"] for v in breakdown.values() if v["evidence_class"] == "static_specification")
    if args.check_only:
        print(json.dumps(dict(check_only=True, passed=True, independent_actual_checks=actual,
                              separate_synthetic_checks=synthetic, separate_static_specification_checks=static,
                              prior_files_preserved=len(old["files"])), indent=2))
        return
    assert not (ROOT / "STATUS_stateflow_v29.json").exists(), "Refuse checkpoint overwrite"
    assert not (ROOT / "MASTER_STAGEBOARD_stateflow_v29.md").exists(), "Refuse stageboard overwrite"
    limits = [
        "Temporal tests cover finite delayed source/demand/temperature-domain faults; delayed NaN/Inf ingestion timing remains untested.",
        "Actual captured/thrown Simulink diagnostics flatten nested host causes; original nested causes are checked in separately labelled component calls.",
        "Monitor faults corrupt allocation outputs in memory and test numerical contract rejection; equipment/sensor faults, hysteresis, dwell and cycling are not implemented.",
        "The production model remains release 0.28; checkpoint 0.29 adds actual execution evidence rather than a new physical model.",
        "Tests use normal-mode host MATLAB HP calls, and do not establish standalone generated-code deployment.",
        "Exponential retention is exact only for passive constant-coefficient ambient-referenced energy; active ports retain approximate loss-first splitting.",
        "The scalar TES has no temperature/cutoff state or ambient offset; scenario COP, loss coefficients and efficiencies are not equipment calibration.",
        "No primary text was newly verified, no article replication or measured-system physical validation; full primary signoffs remain 0/31.",
        "Nonfatal Stateflow allocator-output shadow warnings remain recorded in the execution logs.",
        "A dispatch sample represents a complete following dt interval, including the sample at StopTime; metadata records sample times rather than continuous plant event integration.",
    ]
    next_task = ("Derive and independently test a temperature/cutoff-aware TES model with the ambient-loss offset and "
                 "exact constant-flow integration; specify capacity and cutoff events before a new Stateflow physical version. Preserve v24 and v28.")
    status = dict(
        version="0.29", inherits="STATUS_stateflow_v28.json", research_inherits="STATUS_v25.json",
        checkpoint="Executed monitor-corruption and finite delayed-domain timing gates on saved exponential TES Stateflow v28",
        timestamp_utc=now.isoformat(), stateflow_acceptance="PASS", temporal_acceptance_v28="PASS",
        monitor_corruption_acceptance_v28="PASS", generated_model=rel(model), model_version="0.28",
        model_sha256=sha(model), model_modified_this_run=False,
        preserved_v24_sha256=sha(ROOT / "matlab/simulink/DCHR_Dispatch_Stateflow_v24.slx"),
        matlab_version=temporal["matlab_version"], matlab_batch_exit_codes=[0, 0],
        temporal_result_directory=rel(td), monitor_result_directory=rel(md), execution_receipt=rel(args.receipt),
        independent_temporal_qa=rel(args.temporal_qa), independent_monitor_qa=rel(args.monitor_qa),
        peer_review=rel(args.peer_review), temporal_matlab_checks_passed=temporal["passed"], temporal_matlab_checks_failed=0,
        monitor_rejections=13, finite_temporal_rejections=10, completed_future_input_controls=2,
        accepted_invalid_dispatches=0, model_sample_intervals_h=sorted({r["dt_h"] for r in temporal["records"]}),
        independent_actual_checks_passed=actual, independent_synthetic_checks_passed=synthetic,
        independent_static_specification_checks_passed=static,
        independent_checks_failed=0, independent_breakdown=breakdown,
        inherited_six_mode_acceptance=dict(status="PASS", source="STATUS_stateflow_v28.json",
            result_directory=prior["result_directory"], matlab_checks_passed=prior["matlab_checks_passed"],
            rerun_this_run=False),
        previous_manifest_preserved_count=len(old["files"]), primary_text_verified_this_run=False,
        primary_source_signoffs=0, total_sources=31, primary_paper_replication=False,
        independent_physical_validation="NOT_TESTED", standalone_codegen=False, limitations=limits, next=next_task,
    )
    status_path = ROOT / "STATUS_stateflow_v29.json"
    write(status_path, status)
    stage_path = ROOT / "MASTER_STAGEBOARD_stateflow_v29.md"
    stage = ("# v29: executed fault gates for preserved Stateflow model v28\n\n"
             f"PASS: {temporal['passed']}/{temporal['checks']} MATLAB temporal assertions, 10 delayed finite domain faults, "
             f"2 future-input controls and 13/13 actual monitor-corruption rejections. Independent evidence QA "
             f"{actual}/{actual} PASS; separate synthetic reviewer checks {synthetic}/{synthetic} PASS; "
             f"static specification checks {static}/{static} PASS.\n\n"
             "The model remains `matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx` (release 0.28). "
             "Checkpoint 0.29 closes the two NOT_TESTED fields in v28 status. The saved model and v24 baseline are unchanged. "
             "Prior six-mode/1221 dispatch/105 experiment/46 domain acceptance is inherited and not rerun here.\n\n"
             "Delayed faults reject in Execution at the first predicted sampled invalid input, with exactly the valid accepted "
             "prefix. Clean v28 MATLAB-reference ports and independently derived fixed-COP/exponential TES anchors agree. "
             "Monitor mutations reject at execution time zero with no accepted invalid dispatch; unmutated and restored "
             "two-sample baselines agree. Sources, saved model, diagnostics and traces are hashed and snapshotted.\n\n"
             f"Evidence: `{rel(td)}`, `{rel(md)}`, `{rel(args.temporal_qa)}`, `{rel(args.monitor_qa)}`, "
             f"`{rel(args.receipt)}`, `{rel(args.peer_review)}`.\n\n"
             "Reproduce: `matlab -batch \"addpath('matlab','matlab/simulink'); "
             "run_stateflow_temporal_acceptance_v29; run_stateflow_monitor_faults_v29;\"`. "
             "Run both `audit/verify_stateflow_*_v29.py --help` reviewers on fresh evidence.\n\n"
             "Implementation acceptance only. " + " ".join(limits) + "\n\nNext: " + next_task + "\n")
    with stage_path.open("x", encoding="utf-8") as out:
        out.write(stage)
    progress = (f"\n\n## {now.isoformat()} — v29 saved v28 actual fault/timing gates\n\n"
                "Read STATUS/stageboards v25/v28, acceptance, frontier and relevant production/reference/test sources before edits. "
                "Resumed the unfinished v29 harnesses to close the two explicitly NOT_TESTED v28 evidence gaps. "
                "Independent review strengthened artifact/clock checks, corrected finalizer schema and evidence classifications, "
                "and required one observed successful batch receipt for each harness. "
                "Saved models and production physics are unchanged.\n\n"
                f"Pass/fail: local MATLAB batch exits 0/0; temporal {temporal['passed']}/{temporal['checks']} PASS, "
                f"10/10 timed finite fault rejections, 2/2 future-input controls, monitor 13/13 actual rejections; "
                f"independent evidence QA {actual} PASS, {synthetic} separate synthetic reviewer checks PASS, "
                f"{static} static specification checks PASS. "
                "An inherited sandbox MATLAB startup failed before tests (filesystem inconsistency); fresh authorized local batches were used. "
                "Earlier completed temporal evidence and empty unfinished monitor directory were preserved; prior exit/interrupt cause is unverified. "
                "The first fresh monitor batch passed all numerical gates but emitted an invalid-helper cleanup warning; "
                "guarded the restore callback against an already closed model and reran the harness. "
                "All startup and execution logs are retained. Exact attempt/exit/log provenance is in the receipt.\n\n"
                "Files changed: audit/verify_stateflow_temporal_v29.py, audit/verify_stateflow_gate_evidence_v29.py, "
                "audit/finalize_stateflow_checkpoint_v29.py and matlab/simulink/run_stateflow_monitor_faults_v29.m; "
                "new independent reviews, timestamped QA tests/receipts/logs; "
                f"`{rel(td)}` and `{rel(md)}` contain actual SimulationOutput MATs, numeric traces, configured inputs, "
                "diagnostics and executable source/model snapshots; STATUS_stateflow_v29.json and MASTER_STAGEBOARD_stateflow_v29.md. "
                "Existing edits: append this mutable progress ledger and acceptance ledger.\n\n"
                "Remaining limits: " + " ".join(limits) + "\n\nNext actionable task: " + next_task + "\n\n"
                "Run stops at this coherent acceptance checkpoint and handoff. Scheduler, runner, user settings, Jarvice, "
                "unrelated files and external publication were not touched.\n")
    with (ROOT / "automation/engineering_progress.md").open("a", encoding="utf-8") as out:
        out.write(progress)
    with (ROOT / "automation/STATEFLOW_ACCEPTANCE.md").open("a", encoding="utf-8") as out:
        out.write(f"\n\n## Saved-v28 monitor and temporal acceptance — {now.isoformat()} / checkpoint v29\n\n"
                  "The saved v28 exponential TES model now has executed 13 monitor-corruption rejections, 10 delayed finite "
                  f"domain rejections and 2 future-input controls, with {actual} independent evidence checks and {synthetic} "
                  f"separate synthetic reviewer self-checks plus {static} static specification checks. "
                  "Model release remains 0.28 and all baselines are preserved. "
                  "Authoritative checkpoint: STATUS_stateflow_v29.json and MASTER_STAGEBOARD_stateflow_v29.md. "
                  "Implementation QA only; temperature/cutoff physics and measured validation remain open.\n")
    files = {status_path, stage_path, Path(__file__).resolve(), args.receipt.resolve(), args.peer_review.resolve(),
             args.temporal_qa.resolve(), args.monitor_qa.resolve(), model}
    for execution in receipt["executions"]:
        files.update((ROOT / execution["log_file"], ROOT / execution["console_file"]))
    for directory in (td, md):
        files.update(p for p in directory.rglob("*") if p.is_file() and not {"cache", "codegen"}.intersection(p.relative_to(directory).parts))
    for parent in (ROOT / "audit", ROOT / "automation/logs", ROOT / "matlab/simulink"):
        files.update(p for p in parent.glob("*v29*") if p.is_file() and p != Path(__file__).resolve())
    # The finalizer console is still open; ledgers are intentionally mutable.
    files = {p for p in files if "checkpoint_close" not in p.name}
    manifest = dict(version="0.29", timestamp_utc=now.isoformat(), prior_manifest_preserved_count=len(old["files"]),
                    mutable_exclusions=["automation/engineering_progress.md", "automation/STATEFLOW_ACCEPTANCE.md", "active finalizer console"],
                    files=[dict(path=rel(p), sha256=sha(p), bytes=p.stat().st_size) for p in sorted(files)])
    manifest_path = ROOT / "audit" / f"Stateflow_fault_manifest_v29_{stamp}.json"
    write(manifest_path, manifest)
    integrity = [dict(path=r["path"], passed=sha(ROOT / r["path"]) == r["sha256"] and
                      (ROOT / r["path"]).stat().st_size == r["bytes"]) for r in manifest["files"]]
    integrity_report = dict(timestamp_utc=now.isoformat(), manifest=rel(manifest_path), checks=len(integrity),
                            passed=sum(r["passed"] for r in integrity), failed=sum(not r["passed"] for r in integrity),
                            prior_manifest_preserved_count=len(old["files"]), assertions=integrity)
    write(ROOT / "audit" / f"stateflow_fault_integrity_v29_{stamp}.json", integrity_report)
    assert integrity_report["failed"] == 0
    print(json.dumps(dict(status=rel(status_path), manifest=rel(manifest_path),
                          independent_actual_checks=actual, separate_synthetic_checks=synthetic,
                          separate_static_specification_checks=static,
                          immutable_files_passed=integrity_report["passed"], prior_files_preserved=len(old["files"])), indent=2))


if __name__ == "__main__":
    main()
