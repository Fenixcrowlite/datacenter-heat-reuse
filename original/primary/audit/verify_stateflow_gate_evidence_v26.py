"""Independent audit of executed v24 runtime-monitor fault evidence, v26.

No MATLAB production algorithm is imported. A two-interval fixed-COP hand
case anchors accepted traces; rejection diagnostics and hashes anchor fault
provenance. This is implementation QA, not physical or primary-paper validation.
"""
from __future__ import annotations

import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL_HASH = "1f1c826f0f61d04bea58c2ab39d607268ac273bad9564e69bec89e361c461389"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def result(checks):
    return {"checks": len(checks), "passed": sum(c["passed"] for c in checks),
            "failed": sum(not c["passed"] for c in checks), "assertions": checks}


def near(a, b):
    try:
        a, b = float(a), float(b)
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-10 + 1e-11*abs(b)
    except (TypeError, ValueError):
        return False


def expected_baseline():
    """Independent arithmetic from the declared hand case, with no bisection.

    COP=4 and source=6 MW imply H<=6/(1-1/4)=8 MW. Request and HP cap
    also equal 8 MW. Five MW serve demand; 3 MW charge at etaC=.9.
    E[n+1]=.99 E[n]+2.7 MWh, starting at E[0]=1 MWh.
    """
    energy = 1.0
    rows = []
    for time in (0.0, 1.0):
        after = .99*energy
        next_energy = after + .9*3
        rows.append(dict(Time_h=time, Mode=2, HP_Request_MW=8, HP_Heat_MW=8,
                         HP_Electric_MW=2, HP_Source_Used_MW=6, COP=4,
                         Storage_E_Start_MWh=energy, Storage_E_After_Loss_MWh=after,
                         Storage_E_Next_MWh=next_energy, HP_Direct_MW=5,
                         Storage_Charge_MW=3, Storage_Discharge_MW=0,
                         Gas_Heat_MW=0, Unmet_Heat_MW=0,
                         Storage_Standing_Loss_MWh=energy-after,
                         Storage_Charge_Loss_MWh=.3, Storage_Discharge_Loss_MWh=0,
                         Supplied_Heat_MW=5, System_Balance_Residual_MWh=0))
        energy = next_energy
    return rows


def verify_baseline(rows, label):
    checks = []

    def check(name, ok):
        checks.append(dict(name=label+":"+name, passed=bool(ok)))

    expected = expected_baseline()
    check("exactly_two_accepted_intervals", len(rows) == 2)
    for index, target in enumerate(expected):
        row = rows[index] if index < len(rows) else {}
        for field, value in target.items():
            check(f"tick_{index}:{field}:independent_anchor", near(row.get(field), value))
        try:
            r = {field: float(row[field]) for field in target}
            tes = (r["Storage_E_Start_MWh"] + r["Storage_Charge_MW"] - r["Storage_Discharge_MW"]
                   - r["Storage_E_Next_MWh"] - r["Storage_Standing_Loss_MWh"]
                   - r["Storage_Charge_Loss_MWh"] - r["Storage_Discharge_Loss_MWh"])
            system = (r["HP_Source_Used_MW"] + r["HP_Electric_MW"] + r["Gas_Heat_MW"]
                      + r["Storage_E_Start_MWh"] - r["Supplied_Heat_MW"]
                      - r["Storage_E_Next_MWh"] - r["Storage_Standing_Loss_MWh"]
                      - r["Storage_Charge_Loss_MWh"] - r["Storage_Discharge_Loss_MWh"])
            check(f"tick_{index}:recomputed_TES_closure_MWh", near(tes, 0))
            check(f"tick_{index}:recomputed_system_closure_MWh", near(system, 0))
            check(f"tick_{index}:reported_residual_matches_recomputed", near(r["System_Balance_Residual_MWh"], system))
        except (KeyError, TypeError, ValueError):
            check(f"tick_{index}:recomputable_trace", False)
    if len(rows) >= 2:
        check("actual_TES_feedback_memory", near(rows[1].get("Storage_E_Start_MWh"), rows[0].get("Storage_E_Next_MWh")))
    return result(checks)


def verify_records(spec, evidence, diagnostics):
    """diagnostics(record) returns file text and its SHA256 or empty values."""
    checks = []

    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    expected = spec["cases"]
    records = evidence.get("records", [])
    ids = [r.get("id") for r in records]
    check("exact_independently_specified_fault_set", len(ids) == len(expected) and
          len(set(ids)) == len(ids) and set(ids) == {r["id"] for r in expected})
    mapped = {r.get("id"): r for r in records}
    for case in expected:
        record = mapped.get(case["id"], {})
        prefix = case["id"]+":"
        check(prefix+"specified_mutation_executed", record.get("mutation") == case["mutation"])
        check(prefix+"specific_expected_assertion", record.get("expected_message") == case["expected_message"])
        for field, expected_value in (("simulation_attempted", True), ("rejected", True),
                                      ("accepted_invalid_trace", False), ("restored_source", True)):
            check(prefix+field, record.get(field) is expected_value)
        report, report_hash = diagnostics(record)
        check(prefix+"nonempty_actual_failure_diagnostic", bool(report.strip()))
        check(prefix+"actual_runtime_contract_gate_in_diagnostic", "Runtime_Contract_Gate" in report)
        check(prefix+"exact_assertion_in_actual_diagnostic", case["expected_message"] in report)
        check(prefix+"diagnostic_hash_matches_saved_file", bool(report_hash) and
              record.get("failure_report_sha256") == report_hash)
        check(prefix+"diagnostic_not_compilation_failure", not any(token in report for token in
              ("Errors occurred during parsing", "Error evaluating parameter", "Compilation of model")))
    for field, value in (("cases", len(expected)), ("rejected", len(expected)),
                         ("expected_gate_observed", len(expected)), ("accepted_invalid_traces", 0)):
        check("summary_"+field+"_matches_independent_case_count", evidence.get(field) == value)
    return result(checks)


def self_test(spec):
    """Corrupted synthetic fixtures check the reviewer, not the actual plant."""
    records = []
    for case in spec["cases"]:
        report = "Synthetic fixture; no MATLAB execution. Runtime_Contract_Gate\n"+case["expected_message"]
        records.append(dict(case, simulation_attempted=True, rejected=True, accepted_invalid_trace=False,
                            restored_source=True, failure_report_sha256=hashlib.sha256(report.encode()).hexdigest(),
                            synthetic_report=report))
    evidence = dict(records=records, cases=len(records), rejected=len(records),
                    expected_gate_observed=len(records), accepted_invalid_traces=0)

    def diag(record):
        report = record.get("synthetic_report", "")
        return report, hashlib.sha256(report.encode()).hexdigest() if report else ""

    checks = [dict(name="synthetic_valid_schema", passed=verify_records(spec, evidence, diag)["failed"] == 0)]
    for field, value in (("mutation", "unrelated"), ("simulation_attempted", False), ("rejected", False),
                         ("accepted_invalid_trace", True), ("restored_source", False),
                         ("failure_report_sha256", "incorrect"), ("synthetic_report", "Compile error")):
        broken = copy.deepcopy(evidence)
        broken["records"][0][field] = value
        checks.append(dict(name="reject_corrupted_"+field,
                           passed=verify_records(spec, broken, diag)["failed"] > 0))
    for label, records in (("missing_case", evidence["records"][:-1]),
                           ("duplicate_case", evidence["records"]+evidence["records"][:1])):
        broken = dict(evidence, records=records)
        checks.append(dict(name="reject_"+label, passed=verify_records(spec, broken, diag)["failed"] > 0))
    anchors = expected_baseline()
    checks.append(dict(name="synthetic_hand_case_passes", passed=verify_baseline(anchors, "synthetic")["failed"] == 0))
    for field, value in (("Time_h", .5), ("Storage_E_Next_MWh", 4.375), ("Mode", 1),
                         ("System_Balance_Residual_MWh", float("nan")), ("Storage_Discharge_MW", .1)):
        broken = copy.deepcopy(anchors)
        broken[1][field] = value
        checks.append(dict(name="reject_corrupted_trace_"+field,
                           passed=verify_baseline(broken, "synthetic")["failed"] > 0))
    return result(checks)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def resolve_workspace_path(value, default):
    path = Path(value) if value else default
    return path if path.is_absolute() else ROOT/path


def verify_actual(summary_path, spec, spec_path):
    evidence = json.loads(summary_path.read_text(encoding="utf-8"))
    directory = summary_path.parent

    def diagnostic(record):
        path = resolve_workspace_path(record.get("failure_report"), directory/"MISSING")
        if not path.is_file():
            return "", ""
        return path.read_text(encoding="utf-8-sig"), sha(path)

    output = {"fault_rejections": verify_records(spec, evidence, diagnostic)}
    integrity = []

    def check(name, ok):
        integrity.append(dict(name=name, passed=bool(ok)))

    model = ROOT/spec["model_file"]
    current_model_hash = sha(model)
    check("preserved_v24_model_has_preexisting_immutable_hash", current_model_hash == MODEL_HASH)
    check("reported_before_hash_matches_actual_model", evidence.get("model_sha256_before") == current_model_hash)
    check("reported_after_hash_matches_actual_model", evidence.get("model_sha256_after") == current_model_hash)
    check("independent_case_spec_hash_matches_actual", evidence.get("spec_sha256") == sha(spec_path))
    for field in ("unmutated_baseline_executed", "restored_baseline_executed", "embedded_source_restored"):
        check(field, evidence.get(field) is True)
    check("saved_model_modified_false", evidence.get("saved_model_modified") is False)
    runner = resolve_workspace_path(evidence.get("runner_file"), ROOT/"matlab/simulink/run_stateflow_monitor_faults_v26.m")
    check("actual_runner_sha256", runner.is_file() and evidence.get("runner_sha256") == sha(runner))
    allocation = ROOT/"matlab/simulink/stateflow_allocate_v24.m"
    check("allocation_source_before_matches_actual", evidence.get("source_sha256_before") == sha(allocation))
    check("allocation_source_after_matches_actual", evidence.get("source_sha256_after") == sha(allocation))
    for field in ("simulink_executed", "stateflow_executed", "stateflow_license"):
        check(field, evidence.get(field) in (True, 1))
    check("normal_simulation_scope", evidence.get("simulation_mode") == "normal")
    for field in ("standalone_codegen", "primary_paper_replication", "equipment_validation"):
        check("scope_"+field+"_false", evidence.get(field) is False)
    required_sources = ("stateflow_allocate_v24.m", "stateflow_choose_mode_v24.m",
                        "stateflow_contract_gate_v24.m", "dchr_stateflow_hp_v24.m", "dchr_stateflow_hp_v22.m")
    output["inspected_current_source_hashes"] = {name: sha(ROOT/"matlab/simulink"/name) for name in required_sources}
    output["provenance_limit"] = ("The runner records allocation-source before/after hashes; the other current source hashes "
                                  "are inspection provenance and do not independently prove historical before/after identity.")
    traces = {}
    for name, field in (("baseline", "baseline_trace_file"), ("restored", "restored_trace_file")):
        path = resolve_workspace_path(evidence.get(field), directory/(name+"_trace_v26.csv"))
        rows = read_csv(path) if path.is_file() else []
        traces[name] = rows
        output[name+"_trace"] = verify_baseline(rows, name)
        check(name+"_trace_file_exists", path.is_file())
        output[name+"_trace_sha256"] = sha(path) if path.is_file() else None
    check("restored_trace_numerically_matches_unmutated_baseline", len(traces["baseline"]) == len(traces["restored"]) == 2 and all(
        near(a.get(field), b.get(field)) for a, b in zip(traces["baseline"], traces["restored"])
        for field in expected_baseline()[0]))
    check("no_unexpected_acceptance_artifact", not list(directory.glob("*UNEXPECTED_ACCEPTANCE*")))
    output["integrity"] = result(integrity)
    output["evidence_summary_sha256"] = sha(summary_path)
    output["actual_model_sha256"] = current_model_hash
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=HERE/"stateflow_monitor_fault_cases_v26.json")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.result_dir:
        if args.summary:
            parser.error("Provide only one of --summary or --result-dir")
        args.summary = args.result_dir/"gate_fault_rejections_v26.json"
    if not (args.summary or args.self_test):
        parser.error("Provide actual --summary and/or synthetic --self-test")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    output = dict(version="0.26", timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  scope=__doc__, primary_text_verified=False, primary_paper_replication=False,
                  equipment_validation=False, spec_sha256=sha(args.spec), verifier_sha256=sha(Path(__file__)))
    if args.self_test:
        output["synthetic_verifier_self_test"] = self_test(spec)
    if args.summary:
        output.update(verify_actual(args.summary, spec, args.spec))
    for metric in ("checks", "passed", "failed"):
        output[metric] = sum(value.get(metric, 0) for value in output.values() if isinstance(value, dict))
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: ({k: v for k, v in value.items() if k != "assertions"}
                           if isinstance(value, dict) else value) for key, value in output.items()}, indent=2, allow_nan=False))
    raise SystemExit(bool(output["failed"]))


if __name__ == "__main__":
    main()
