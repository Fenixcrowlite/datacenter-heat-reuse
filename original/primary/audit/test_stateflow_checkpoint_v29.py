"""Independent synthetic mutation probes for v29 checkpoint closure helpers.

These tests verify bookkeeping and receipt rejection only. They never execute
MATLAB/Stateflow, alter a saved model or count as actual model evidence.
Synthetic marker fixtures are explicitly labelled and preserved in logs.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FINALIZER = ROOT / "audit/finalize_stateflow_checkpoint_v29.py"
module_spec = importlib.util.spec_from_file_location("checkpoint_under_review_v29", FINALIZER)
closure = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(closure)


def recount(report):
    sections = closure.sections(report)
    for category in ("actual_evidence", "static_specification", "synthetic_reviewer_self_test"):
        for metric in ("checks", "passed", "failed"):
            report[category + "_" + metric] = sum(
                value[metric] for value in sections.values() if value["evidence_class"] == category
            )
    for metric in ("checks", "passed", "failed"):
        report[metric] = sum(value[metric] for value in sections.values())
    return report


def report_fixture():
    report = {}
    for index, (name, category) in enumerate((
        ("specification", "static_specification"),
        ("synthetic_reviewer_self_test", "synthetic_reviewer_self_test"),
        ("integrity", "actual_evidence"),
        ("temporal_evidence", "actual_evidence"),
        ("saved_model_structure", "actual_evidence"),
        ("post_fault_clean_restart", "actual_evidence"),
    ), start=1):
        report[name] = dict(checks=index, passed=index, failed=0,
                            synthetic_only=category == "synthetic_reviewer_self_test",
                            evidence_class=category)
    return recount(report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--log", type=Path, required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    checks = []

    def check(name, callback, reject=False):
        detail = ""
        try:
            value = callback()
            passed = False if reject else bool(value)
            if reject:
                detail = "Corrupted synthetic fixture was accepted."
        except (AssertionError, KeyError, TypeError, ValueError) as error:
            passed = reject
            detail = type(error).__name__ + ": " + str(error)
        except Exception as error:
            passed = False
            detail = "Unexpected " + type(error).__name__ + ": " + str(error)
        checks.append(dict(name=name, passed=passed, detail=detail))

    base = report_fixture()
    check("accept_clean_three_way_evidence_classification", lambda: bool(
        closure.qa_breakdown((("temporal", copy.deepcopy(base)),))))
    check("static_and_synthetic_counts_excluded_from_actual_evidence", lambda:
        sum(value["passed"] for value in closure.qa_breakdown((("temporal", copy.deepcopy(base)),)).values()
            if value["evidence_class"] == "actual_evidence") == 18)

    def corrupt_report(name, mutate, reconcile=False):
        broken = copy.deepcopy(base)
        mutate(broken)
        if reconcile:
            recount(broken)
        check(name, lambda: closure.qa_breakdown((("temporal", broken),)), reject=True)

    corrupt_report("reject_contradictory_total", lambda r: r.__setitem__("passed", r["passed"] + 1))
    corrupt_report("reject_contradictory_category_total", lambda r:
                   r.__setitem__("actual_evidence_passed", r["actual_evidence_passed"] + 1))
    corrupt_report("reject_contradictory_section_total", lambda r: r["integrity"].__setitem__("checks", 99))
    corrupt_report("reject_unknown_evidence_class", lambda r:
                   r["integrity"].__setitem__("evidence_class", "unclassified"))
    corrupt_report("reject_inconsistent_synthetic_flag", lambda r:
                   r["synthetic_reviewer_self_test"].__setitem__("synthetic_only", False))
    corrupt_report("reject_reconciled_static_to_actual_inflation", lambda r:
                   r["specification"].__setitem__("evidence_class", "actual_evidence"), True)
    corrupt_report("reject_reconciled_synthetic_to_actual_inflation", lambda r:
                   r["synthetic_reviewer_self_test"].update(
                       evidence_class="actual_evidence", synthetic_only=False), True)
    corrupt_report("reject_negative_counts", lambda r:
                   r["integrity"].update(checks=-3, passed=-3, failed=0), True)
    corrupt_report("reject_fractional_counts", lambda r:
                   r["integrity"].update(checks=3.5, passed=3.5, failed=0), True)
    corrupt_report("reject_missing_actual_evidence_section", lambda r: r.pop("temporal_evidence"), True)
    corrupt_report("reject_boolean_counts", lambda r:
                   r["specification"].update(checks=True, passed=True, failed=False), True)
    corrupt_report("reject_empty_required_QA_section", lambda r:
                   r["temporal_evidence"].update(checks=0, passed=0, failed=0), True)
    corrupt_report("reject_unknown_injected_actual_section", lambda r:
                   r.__setitem__("unreviewed_extra", dict(checks=1000, passed=1000, failed=0,
                       evidence_class="actual_evidence", synthetic_only=False)), True)
    without_optional = copy.deepcopy(base)
    without_optional.pop("synthetic_reviewer_self_test")
    recount(without_optional)
    check("accept_actual_QA_without_optional_synthetic_self_test", lambda:
          bool(closure.qa_breakdown((("temporal", without_optional),))))
    monitor = {}
    for index, name in enumerate(("specification", "fault_rejections", "runtime_artifact_bindings",
                                  "saved_model_structure", "baseline_trace", "restored_trace", "integrity"), start=1):
        category = "static_specification" if name == "specification" else "actual_evidence"
        monitor[name] = dict(checks=index, passed=index, failed=0,
                             evidence_class=category, synthetic_only=False)
    recount(monitor)
    check("accept_monitor_required_actual_artifact_schema", lambda:
          bool(closure.qa_breakdown((("monitor", monitor),))))
    without_bindings = copy.deepcopy(monitor)
    without_bindings.pop("runtime_artifact_bindings")
    recount(without_bindings)
    check("reject_omitted_monitor_runtime_artifact_bindings", lambda:
          closure.qa_breakdown((("monitor", without_bindings),)), reject=True)

    # Receipt markers contain no simulation evidence. The helper must validate
    # their integrity, harness identity and recorded observation status.
    td = ROOT / "results" / ("SYNTHETIC_checkpoint_temporal_v29_" + stamp)
    md = ROOT / "results" / ("SYNTHETIC_checkpoint_monitor_v29_" + stamp)
    receipt = dict(executions=[])
    fixture_paths = []
    for directory, kind in ((td, "TEMPORAL"), (md, "MONITOR")):
        marker = kind + "_OUTPUT=" + str(directory)
        paths = []
        for suffix in ("log", "console"):
            path = ROOT / "automation/logs" / f"checkpoint_helper_SYNTHETIC_v29_{stamp}_{kind}_{suffix}.log"
            with path.open("x", encoding="utf-8") as stream:
                stream.write("SYNTHETIC RECEIPT HELPER FIXTURE; NO MATLAB OR STATEFLOW EXECUTION.\n" + marker + "\n")
            paths.append(path)
            fixture_paths.append(path.relative_to(ROOT).as_posix())
        receipt["executions"].append(dict(result_directory=closure.rel(directory),
            matlab_batch_exit_code=0, exit_observed=True, output_marker=marker,
            log_file=closure.rel(paths[0]), log_sha256=closure.sha(paths[0]),
            console_file=closure.rel(paths[1]), console_sha256=closure.sha(paths[1])))

    check("accept_consistent_explicitly_synthetic_receipt_fixture", lambda:
          closure.verify_receipt(copy.deepcopy(receipt), td, md) is None)

    def corrupt_receipt(name, mutate):
        broken = copy.deepcopy(receipt)
        mutate(broken)
        check(name, lambda: closure.verify_receipt(broken, td, md), reject=True)

    corrupt_receipt("reject_duplicate_harness_receipt", lambda r:
                    r["executions"][1].update(result_directory=r["executions"][0]["result_directory"]))
    corrupt_receipt("reject_missing_exit_observation", lambda r: r["executions"][0].pop("exit_observed"))
    corrupt_receipt("reject_false_exit_observation", lambda r: r["executions"][0].update(exit_observed=False))
    corrupt_receipt("reject_nonzero_exit", lambda r: r["executions"][0].update(matlab_batch_exit_code=1))
    corrupt_receipt("reject_wrong_harness_marker", lambda r:
                    r["executions"][0].update(output_marker=r["executions"][0]["output_marker"].replace("TEMPORAL", "MONITOR")))
    corrupt_receipt("reject_wrong_result_path_in_marker", lambda r:
                    r["executions"][0].update(output_marker="TEMPORAL_OUTPUT=WRONG_DIRECTORY"))
    corrupt_receipt("reject_duplicate_log_file", lambda r:
                    r["executions"][1].update(log_file=r["executions"][0]["log_file"]))
    corrupt_receipt("reject_duplicate_console_file", lambda r:
                    r["executions"][1].update(console_file=r["executions"][0]["console_file"]))
    corrupt_receipt("reject_wrong_log_hash", lambda r: r["executions"][0].update(log_sha256="0" * 64))
    corrupt_receipt("reject_wrong_console_hash", lambda r: r["executions"][0].update(console_sha256="0" * 64))
    for field, hash_field in (("log_file", "log_sha256"), ("console_file", "console_sha256")):
        path = ROOT / "automation/logs" / f"checkpoint_helper_SYNTHETIC_v29_{stamp}_{field}_missing_marker.log"
        with path.open("x", encoding="utf-8") as stream:
            stream.write("SYNTHETIC RECEIPT HELPER FIXTURE; NO EXECUTION AND NO OUTPUT MARKER.\n")
        fixture_paths.append(closure.rel(path))
        corrupt_receipt("reject_marker_missing_from_" + field, lambda r, path=path, field=field, hash_field=hash_field:
                        r["executions"][0].update({field: closure.rel(path), hash_field: closure.sha(path)}))

    report = dict(version="0.29", timestamp_utc=now.isoformat(),
        review_type="independent_synthetic_checkpoint_helper_mutation_tests",
        scope=__doc__, evidence_class="synthetic_reviewer_self_test", synthetic_only=True,
        dynamic_model_execution_this_review=False, primary_text_verified_this_review=False,
        physical_validation=False, finalizer_sha256=closure.sha(FINALIZER),
        test_source_sha256=closure.sha(Path(__file__)), checks=len(checks),
        passed=sum(r["passed"] for r in checks), failed=sum(not r["passed"] for r in checks),
        assertions=checks, preserved_synthetic_fixture_logs=fixture_paths,
        actual_model_evidence_checks=0)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    with args.log.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps({key: value for key, value in report.items() if key != "assertions"}, indent=2))
        stream.write("\n")
        for row in checks:
            stream.write(("PASS " if row["passed"] else "FAIL ") + row["name"] + " " + row["detail"] + "\n")
    print(json.dumps(dict(report=closure.rel(args.report), log=closure.rel(args.log),
                         checks=report["checks"], passed=report["passed"], failed=report["failed"],
                         failed_tests=[row["name"] for row in checks if not row["passed"]]), indent=2))
    raise SystemExit(bool(report["failed"]))


if __name__ == "__main__":
    main()
