"""Independent audit of executed v28 runtime-monitor fault evidence, v29.

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
import re
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL_HASH = "30ea3701f2f04d293d6c9bf528dc625762bf69db9a06c9d6d384293a98497a1d"
RUNTIME_IDENTIFIER = "Stateflow:Runtime"
MONITOR_CASES = [
    ("false_system_residual", "y(13)=y(13)+.1;", "System first-law failure or false residual."),
    ("false_next_energy", "y(8)=y(8)+.1;", "TES first-law failure."),
    ("negative_backup_flow", "y(5)=-1;", "Negative dispatch/HP port."),
    ("wrong_active_mode", "y(1)=5;", "Active state does not match delivered flows."),
    ("false_standing_loss", "y(9)=y(9)+.1;", "TES loss reporting mismatch."),
    ("unallocated_hp_heat", "y(2)=y(2)-.1;", "Unallocated HP condenser heat."),
    ("simultaneous_tes_ports", "y(4)=.1;", "Simultaneous TES charge and discharge."),
    ("false_useful_heat", "y(12)=y(12)+.1;", "Useful heat mismatch."),
    ("nonfinite_dispatch", "y(13)=NaN;", "Accepted dispatch and parameters must be finite."),
    ("undefined_nonintegral_mode", "y(1)=2.5;", "Undefined mode."),
    ("backup_above_capacity", "y(5)=3;", "TES/backup power limit exceeded."),
    ("tes_state_above_capacity", "y(8)=11;", "TES state outside capacity."),
    ("false_exponential_retention", "y(7)=y(7)+.1;", "Standing-retention mismatch."),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def result(checks, synthetic_only=False, evidence_class="actual_evidence"):
    return {"checks": len(checks), "passed": sum(c["passed"] for c in checks),
            "failed": sum(not c["passed"] for c in checks), "assertions": checks,
            "synthetic_only": synthetic_only, "evidence_class": evidence_class}


def near(a, b):
    try:
        a, b = float(a), float(b)
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-10 + 1e-11*abs(b)
    except (TypeError, ValueError):
        return False


def verify_spec(spec):
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    check("specified_existing_v28_model", spec.get("model_file") ==
          "matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx" and spec.get("model_sha256") == MODEL_HASH)
    check("specified_existing_v28_helper", spec.get("helper") == "stateflow_allocate_v28")
    check("independently_declared_fixed_COP_anchor", spec.get("baseline") == dict(
        model_dt_h=1, stop_time_h=1, input_x=[6,35,70,5], p=[1,10,3,4,.9,.8,.01,2],
        h=[8,.45,1.2,8,0,1,4,0,0], initial_energy_MWh=1))
    cases = spec.get("cases", [])
    check("thirteen_unique_monitor_cases", len(cases) == len({c["id"] for c in cases}) == 13)
    check("complete_independently_anchored_mutations_and_assertions", cases == [
        dict(id=id_, mutation=mutation, expected_message=message)
        for id_, mutation, message in MONITOR_CASES])
    check("independent_exponential_retention_gate_case", dict(
        id="false_exponential_retention", mutation="y(7)=y(7)+.1;",
        expected_message="Standing-retention mismatch.") in cases)
    return result(checks, evidence_class="static_specification")


def expected_baseline():
    """Independent arithmetic from the declared hand case, with no bisection.

    COP=4 and source=6 MW imply H<=6/(1-1/4)=8 MW. Request and HP cap
    also equal 8 MW. Five MW serve demand; 3 MW charge at etaC=.9.
    Let r=exp(-lambda*dt)=exp(-.01). Passive energy solves dE/dt=-lambda E.
    Loss-first charge adds .9*3*1=2.7 MWh AFTER the passive step. Thus
    E[n]=r**n*E[0]+2.7*(1-r**n)/(1-r), E[0]=1 MWh. Both ticks remain
    below 10 MWh. The rate .01 h^-1 is a scenario assumption, not calibration.
    """
    rows = []
    for n, time in enumerate((0.0, 1.0)):
        energy = math.exp(-.01*n) + 2.7*(-math.expm1(-.01*n))/(-math.expm1(-.01))
        after = math.exp(-.01)*energy
        next_energy = after + .9*3
        rows.append(dict(Time_h=time, Mode=2, HP_Request_MW=8, HP_Heat_MW=8,
                         HP_Electric_MW=2, HP_Source_Used_MW=6, COP=4,
                         Storage_E_Start_MWh=energy, Storage_E_After_Loss_MWh=after,
                         Storage_E_Next_MWh=next_energy, HP_Direct_MW=5,
                         Storage_Charge_MW=3, Storage_Discharge_MW=0,
                         Gas_Heat_MW=0, Unmet_Heat_MW=0,
                         Storage_Standing_Loss_MWh=-energy*math.expm1(-.01),
                         Storage_Charge_Loss_MWh=.3, Storage_Discharge_Loss_MWh=0,
                         Supplied_Heat_MW=5, System_Balance_Residual_MWh=0))
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
                                      ("accepted_invalid_trace", False), ("restored_source", True),
                                      ("captured_runtime_rejection", True), ("expected_gate_observed", True),
                                      ("compilation_failure_detected", False)):
            check(prefix+field, record.get(field) is expected_value)
        check(prefix+"actual_runtime_assertion_identifier", record.get("actual_identifier") == RUNTIME_IDENTIFIER)
        check(prefix+"actual_cause_identifier", RUNTIME_IDENTIFIER in record.get("cause_identifiers", []))
        check(prefix+"capture_errors_enabled", record.get("capture_errors") == "on")
        diagnostic = record.get("diagnostic", {})
        check(prefix+"captured_actual_execution_phase", diagnostic.get("error_phase") == "Execution")
        check(prefix+"captured_first_tick_error_time", near(diagnostic.get("error_time_h"), 0))
        check(prefix+"captured_first_tick_stop_time", near(diagnostic.get("stop_event_time_h"), 0))
        check(prefix+"captured_diagnostic_error_stop", diagnostic.get("stop_event") == "DiagnosticError")
        check(prefix+"captured_exact_runtime_contract_gate", "Runtime_Contract_Gate" in diagnostic.get("error_message", ""))
        check(prefix+"captured_exact_assertion", case["expected_message"] in diagnostic.get("error_message", ""))
        check(prefix+"captured_runtime_assertion_identifier", RUNTIME_IDENTIFIER in diagnostic.get("cause_identifiers", []))
        tree = diagnostic.get("diagnostic_tree", {})
        check(prefix+"captured_diagnostic_tree_runtime_gate", isinstance(tree, dict) and
              tree.get("identifier") == RUNTIME_IDENTIFIER and
              "Runtime_Contract_Gate" in tree.get("message", "") and
              case["expected_message"] in tree.get("message", ""))
        raw = record.get("raw_trace_times", {})
        check(prefix+"no_captured_accepted_dispatch_samples", isinstance(raw, dict) and raw.get("dispatch_times_h") == [])
        report, report_hash = diagnostics(record)
        check(prefix+"nonempty_actual_failure_diagnostic", bool(report.strip()))
        check(prefix+"actual_runtime_contract_gate_in_diagnostic", "Runtime_Contract_Gate" in report)
        check(prefix+"exact_assertion_in_actual_diagnostic", case["expected_message"] in report)
        check(prefix+"diagnostic_hash_matches_saved_file", bool(report_hash) and
              record.get("failure_report_sha256") == report_hash)
        check(prefix+"diagnostic_not_compilation_failure", not any(token in report.lower() for token in
              ("errors occurred during parsing", "error evaluating parameter", "compilation of model",
               "error compiling", "parse error", "syntax error")))
    for field, value in (("cases", len(expected)), ("rejected", len(expected)),
                         ("expected_gate_observed", len(expected)), ("accepted_invalid_traces", 0),
                         ("captured_runtime_rejections", len(expected)), ("compilation_failures", 0)):
        check("summary_"+field+"_matches_independent_case_count", evidence.get(field) == value)
    return result(checks)


def verify_record_artifacts(spec, evidence, load_artifact, original):
    """Bind summary claims to saved bytes; MAT payloads are hashed, not decoded.

    load_artifact(record, field, basename, kind) returns payload, hash and
    whether the file is exactly the expected artifact within the evidence dir.
    """
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    mapped = {record.get("id"): record for record in evidence.get("records", [])}
    for case in spec["cases"]:
        record = mapped.get(case["id"], {})
        prefix = case["id"]+":"
        for field, suffix, kind in (
            ("failure_report", "_rejection.txt", "text"),
            ("diagnostic", "_diagnostic.json", "json"),
            ("raw_trace_times", "_raw_trace_times.json", "json"),
            ("mutation_source", "_in_memory_allocation.m", "text"),
            ("captured_simulation", "_captured_simulation.mat", "mat"),
        ):
            path_field = field if field == "failure_report" else field+"_file"
            payload, actual_hash, bounded = load_artifact(record, path_field, case["id"]+suffix, kind)
            check(prefix+field+":expected_local_artifact", bounded)
            check(prefix+field+":saved_bytes_match_reported_hash", bool(actual_hash) and
                  record.get(field+"_sha256") == actual_hash)
            if kind == "json":
                check(prefix+field+":saved_JSON_matches_embedded_summary", isinstance(payload, dict) and
                      payload == record.get(field))
            elif field == "mutation_source":
                expected = re.sub(r"\nend\s*$", "\n% Independent QA in-memory corruption\n"+
                                  case["mutation"]+"\nend\n", original)
                check(prefix+"saved_exact_independent_mutation_of_original_helper", payload == expected and
                      expected != original)
            elif kind == "mat":
                check(prefix+"saved_captured_simulation_is_MAT_container", payload is True)
    return result(checks)


def self_test(spec):
    """Corrupted synthetic fixtures check the reviewer, not the actual plant."""
    records = []
    for case in spec["cases"]:
        report = "Synthetic fixture; no MATLAB execution. Runtime_Contract_Gate\n"+case["expected_message"]
        records.append(dict(case, simulation_attempted=True, rejected=True, accepted_invalid_trace=False,
                            restored_source=True, failure_report_sha256=hashlib.sha256(report.encode()).hexdigest(),
                            captured_runtime_rejection=True, expected_gate_observed=True,
                            compilation_failure_detected=False, actual_identifier=RUNTIME_IDENTIFIER,
                            cause_identifiers=[RUNTIME_IDENTIFIER], capture_errors="on",
                            diagnostic=dict(stop_event="DiagnosticError", stop_event_time_h=0,
                                            error_time_h=0, error_phase="Execution", error_message=report,
                                            cause_identifiers=[RUNTIME_IDENTIFIER],
                                            diagnostic_tree=dict(identifier=RUNTIME_IDENTIFIER,
                                                                 message=report, cause=[])),
                            raw_trace_times=dict(dispatch_times_h=[]),
                            synthetic_report=report))
    evidence = dict(records=records, cases=len(records), rejected=len(records),
                    expected_gate_observed=len(records), accepted_invalid_traces=0,
                    captured_runtime_rejections=len(records), compilation_failures=0)

    def diag(record):
        report = record.get("synthetic_report", "")
        return report, hashlib.sha256(report.encode()).hexdigest() if report else ""

    checks = [dict(name="synthetic_valid_schema", passed=verify_records(spec, evidence, diag)["failed"] == 0)]
    for field, value in (("mutation", "unrelated"), ("simulation_attempted", False), ("rejected", False),
                         ("accepted_invalid_trace", True), ("restored_source", False),
                         ("failure_report_sha256", "incorrect"), ("synthetic_report", "Compile error"),
                         ("actual_identifier", "Unrelated:Runtime"), ("cause_identifiers", []),
                         ("capture_errors", "off"), ("expected_gate_observed", False),
                         ("compilation_failure_detected", True)):
        broken = copy.deepcopy(evidence)
        broken["records"][0][field] = value
        checks.append(dict(name="reject_corrupted_"+field,
                           passed=verify_records(spec, broken, diag)["failed"] > 0))
    for label, records in (("missing_case", evidence["records"][:-1]),
                           ("duplicate_case", evidence["records"]+evidence["records"][:1])):
        broken = dict(evidence, records=records)
        checks.append(dict(name="reject_"+label, passed=verify_records(spec, broken, diag)["failed"] > 0))
    for field, value in (("error_phase", "Compilation"), ("error_time_h", 1),
                         ("stop_event_time_h", 1), ("stop_event", "ReachedStopTime"),
                         ("error_message", "Unrelated runtime error"), ("cause_identifiers", []),
                         ("diagnostic_tree", dict(identifier="Unrelated:Runtime", message="", cause=[]))):
        broken = copy.deepcopy(evidence)
        broken["records"][0]["diagnostic"][field] = value
        checks.append(dict(name="reject_corrupted_captured_"+field,
                           passed=verify_records(spec, broken, diag)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["raw_trace_times"]["dispatch_times_h"] = [0]
    checks.append(dict(name="reject_captured_failed_tick_output", passed=verify_records(spec, broken, diag)["failed"] > 0))
    anchors = expected_baseline()
    checks.append(dict(name="synthetic_hand_case_passes", passed=verify_baseline(anchors, "synthetic")["failed"] == 0))
    for field, value in (("Time_h", .5), ("Storage_E_Next_MWh", 4.375), ("Mode", 1),
                         ("System_Balance_Residual_MWh", float("nan")), ("Storage_Discharge_MW", .1)):
        broken = copy.deepcopy(anchors)
        broken[1][field] = value
        checks.append(dict(name="reject_corrupted_trace_"+field,
                           passed=verify_baseline(broken, "synthetic")["failed"] > 0))
    broken = copy.deepcopy(anchors)
    broken[0]["Storage_E_After_Loss_MWh"] = .99
    checks.append(dict(name="reject_obsolete_linear_retention_anchor", passed=verify_baseline(broken, "synthetic")["failed"] > 0))
    original = "function y=synthetic_helper()\ny=zeros(13,1);\nend\n"
    fixture = copy.deepcopy(evidence)
    for record in fixture["records"]:
        record["artifact_payloads"] = {
            "failure_report": record["synthetic_report"],
            "diagnostic_file": record["diagnostic"],
            "raw_trace_times_file": record["raw_trace_times"],
            "mutation_source_file": re.sub(r"\nend\s*$", "\n% Independent QA in-memory corruption\n"+
                                          record["mutation"]+"\nend\n", original),
            "captured_simulation_file": True,
        }
        for field, payload in record["artifact_payloads"].items():
            hash_field = (field[:-5] if field.endswith("_file") else field)+"_sha256"
            record[hash_field] = hashlib.sha256(json.dumps(payload).encode()).hexdigest()
    def synthetic_load(record, field, basename, kind):
        payload = record.get("artifact_payloads", {}).get(field)
        digest = hashlib.sha256(json.dumps(payload).encode()).hexdigest() if payload is not None else ""
        return payload, digest, record.get("artifact_bounded", True)
    checks.append(dict(name="synthetic_artifact_binding_passes", passed=
                       verify_record_artifacts(spec, fixture, synthetic_load, original)["failed"] == 0))
    for field, wrong in (("diagnostic_file", {}), ("raw_trace_times_file", {"dispatch_times_h": [0]}),
                         ("mutation_source_file", original), ("captured_simulation_file", False)):
        broken = copy.deepcopy(fixture)
        broken["records"][0]["artifact_payloads"][field] = wrong
        checks.append(dict(name="reject_corrupted_saved_"+field, passed=
                           verify_record_artifacts(spec, broken, synthetic_load, original)["failed"] > 0))
        hash_field = field[:-5]+"_sha256"
        broken["records"][0][hash_field] = hashlib.sha256(json.dumps(wrong).encode()).hexdigest()
        checks.append(dict(name="reject_rehashed_semantically_wrong_saved_"+field, passed=
                           verify_record_artifacts(spec, broken, synthetic_load, original)["failed"] > 0))
    broken = copy.deepcopy(fixture)
    broken["records"][0]["artifact_bounded"] = False
    checks.append(dict(name="reject_crosscase_or_external_artifact_path", passed=
                       verify_record_artifacts(spec, broken, synthetic_load, original)["failed"] > 0))
    for field in ("mutation_source", "diagnostic", "raw_trace_times", "captured_simulation"):
        broken = copy.deepcopy(fixture)
        broken["records"][0][field+"_sha256"] = "wrong"
        checks.append(dict(name="reject_corrupted_artifact_hash_"+field, passed=
                           verify_record_artifacts(spec, broken, synthetic_load, original)["failed"] > 0))
    broken_spec = copy.deepcopy(spec)
    broken_spec["cases"][0]["mutation"] = "y(12)=y(12)+.1;"
    checks.append(dict(name="reject_mutually_consistent_wrong_case_specification", passed=
                       verify_spec(broken_spec)["failed"] > 0))
    return result(checks, synthetic_only=True, evidence_class="synthetic_reviewer_self_test")


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def resolve_workspace_path(value, default):
    path = Path(value) if value else default
    return path if path.is_absolute() else ROOT/path


def verify_actual(summary_path, spec, spec_path):
    evidence = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    directory = summary_path.parent

    def diagnostic(record):
        path = resolve_workspace_path(record.get("failure_report"), directory/"MISSING")
        if not path.is_file():
            return "", ""
        return path.read_text(encoding="utf-8-sig"), sha(path)

    output = {"fault_rejections": verify_records(spec, evidence, diagnostic)}
    def load_artifact(record, field, basename, kind):
        expected = directory/basename
        path = resolve_workspace_path(record.get(field), directory/"MISSING")
        bounded = path.resolve() == expected.resolve() and path.resolve().is_relative_to(directory.resolve())
        if not path.is_file():
            return None, "", False
        try:
            if kind == "json":
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
            elif kind == "mat":
                with path.open("rb") as stream:
                    header = stream.read(128)
                payload = len(header) == 128 and header.startswith(b"MATLAB ") and b"MAT-file" in header
            else:
                payload = path.read_text(encoding="utf-8-sig")
        except (UnicodeError, json.JSONDecodeError):
            payload = None
        return payload, sha(path), bounded
    output["runtime_artifact_bindings"] = verify_record_artifacts(
        spec, evidence, load_artifact, (ROOT/"matlab/simulink/stateflow_allocate_v28.m").read_text(encoding="utf-8-sig"))
    integrity = []

    def check(name, ok):
        integrity.append(dict(name=name, passed=bool(ok)))

    model = ROOT/spec["model_file"]
    current_model_hash = sha(model)
    check("preserved_v28_model_has_preexisting_immutable_hash", current_model_hash == MODEL_HASH)
    check("reported_before_hash_matches_actual_model", evidence.get("model_sha256_before") == current_model_hash)
    check("reported_after_hash_matches_actual_model", evidence.get("model_sha256_after") == current_model_hash)
    check("reported_model_path_matches_actual_model", resolve_workspace_path(evidence.get("model_path"), directory/"MISSING").resolve() == model.resolve())
    check("independent_case_spec_hash_matches_actual", evidence.get("spec_sha256") == sha(spec_path))
    for field in ("unmutated_baseline_executed", "restored_baseline_executed", "embedded_source_restored"):
        check(field, evidence.get(field) is True)
    check("saved_model_modified_false", evidence.get("saved_model_modified") is False)
    runner = resolve_workspace_path(evidence.get("runner_file"), ROOT/"matlab/simulink/run_stateflow_monitor_faults_v29.m")
    check("actual_runner_path", runner.resolve() == (ROOT/"matlab/simulink/run_stateflow_monitor_faults_v29.m").resolve())
    check("actual_runner_sha256", runner.is_file() and evidence.get("runner_sha256") == sha(runner))
    allocation = ROOT/"matlab/simulink/stateflow_allocate_v28.m"
    check("allocation_source_before_matches_actual", evidence.get("allocation_source_sha256_before") == sha(allocation))
    check("allocation_source_after_matches_actual", evidence.get("allocation_source_sha256_after") == sha(allocation))
    for field in ("simulink_executed", "stateflow_executed", "stateflow_license"):
        check(field, evidence.get(field) in (True, 1))
    check("normal_simulation_scope", evidence.get("simulation_mode") == "normal")
    for field in ("standalone_codegen", "primary_paper_replication", "equipment_validation"):
        check("scope_"+field+"_false", evidence.get(field) is False)
    check("reported_saved_model_release", evidence.get("model_release") == "0.28")
    manifest_path = resolve_workspace_path(evidence.get("snapshot_manifest_file"), directory/"MISSING")
    check("snapshot_manifest_present", manifest_path.is_file())
    check("snapshot_manifest_is_local_expected_artifact", manifest_path.resolve() == (directory/"source_snapshot_manifest_v29.json").resolve())
    check("snapshot_manifest_hash_matches_saved_bytes", manifest_path.is_file() and evidence.get("snapshot_manifest_sha256") == sha(manifest_path))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig")) if manifest_path.is_file() else {}
    check("manifest_declares_sources_and_snapshots_unchanged", manifest.get("all_sources_and_snapshots_unchanged") is True)
    source_records = manifest.get("files", [])
    source_records = source_records if isinstance(source_records, list) else []
    normal = lambda value: str(value).replace("\\", "/")
    mapped_sources = {normal(r.get("project_relative_path")): r for r in source_records}
    expected_sources = required_snapshot_sources(runner, spec_path)
    check("complete_unique_source_snapshot_closure", len(source_records) == len(mapped_sources) == len(expected_sources)
          and set(mapped_sources) == expected_sources)
    check("manifest_declares_created_before_simulations", manifest.get("created_before_simulations") is True)
    for field in ("source_snapshot_complete", "source_snapshots_unchanged"):
        check(field, evidence.get(field) is True)
    for relative in sorted(expected_sources):
        record = mapped_sources.get(relative, {})
        path = ROOT/relative
        current_hash = sha(path) if path.is_file() else ""
        snapshot_path = directory/normal(record.get("snapshot_relative_path", "MISSING"))
        snapshot_hash = sha(snapshot_path) if snapshot_path.is_file() else ""
        check(relative+":before_hash_matches_actual_source", bool(current_hash) and record.get("sha256_before") == current_hash)
        check(relative+":after_hash_matches_actual_source", bool(current_hash) and record.get("sha256_after") == current_hash)
        check(relative+":snapshot_recorded_hash_matches_file", bool(snapshot_hash) and record.get("snapshot_sha256") == snapshot_hash)
        check(relative+":snapshot_matches_before_and_current_source", bool(current_hash) and snapshot_hash == current_hash == record.get("sha256_before"))
        check(relative+":declared_unchanged", record.get("unchanged") is True)
        check(relative+":snapshot_inside_evidence_directory", snapshot_path.resolve().is_relative_to(directory.resolve()))
    before_path = resolve_workspace_path(evidence.get("source_snapshot_manifest_before_file"), directory/"MISSING")
    check("before_manifest_is_local_expected_artifact", before_path.resolve() == (directory/"source_snapshot_manifest_before_v29.json").resolve())
    check("before_manifest_hash_matches_saved_bytes", before_path.is_file() and
          evidence.get("source_snapshot_manifest_before_sha256") == sha(before_path))
    before_manifest = json.loads(before_path.read_text(encoding="utf-8-sig")) if before_path.is_file() else {}
    before_records = before_manifest.get("files", [])
    before_sources = {normal(record.get("project_relative_path")): record for record in before_records}
    check("before_manifest_complete_unique_source_closure", len(before_records) == len(before_sources) == len(expected_sources)
          and set(before_sources) == expected_sources and before_manifest.get("created_before_simulations") is True)
    for relative in sorted(expected_sources):
        record = before_sources.get(relative, {})
        final_record = mapped_sources.get(relative, {})
        check(relative+":before_manifest_matches_final_preexecution_snapshot", all(record.get(field) == final_record.get(field)
              for field in ("project_relative_path", "snapshot_relative_path", "sha256_before", "snapshot_sha256")))
    binding_path = resolve_workspace_path(evidence.get("saved_model_binding_file"), directory/"MISSING")
    check("saved_binding_is_local_expected_artifact", binding_path.resolve() == (directory/"saved_model_binding_v29.json").resolve())
    check("saved_binding_hash_matches_actual_file", binding_path.is_file() and evidence.get("saved_model_binding_sha256") == sha(binding_path))
    binding = json.loads(binding_path.read_text(encoding="utf-8-sig")) if binding_path.is_file() else {}
    check("saved_binding_has_exact_model_release_and_hash", binding.get("model_release") == "0.28" and binding.get("model_sha256") == current_model_hash)
    check("saved_binding_has_exact_chart_and_clock", binding.get("chart_path") == "DCHR_Dispatch_Stateflow_v28/Thermal_Dispatch" and binding.get("sample_time") == "dchr_dt_v28")
    for field in ("saved_embedded_sources_match", "contract_gate_drives_feedback_and_trace"):
        check("saved_binding_"+field, binding.get(field) is True and evidence.get(field) is True)
    for name, field in (("stateflow_allocate_v28", "embedded_allocate_script"),
                        ("stateflow_choose_mode_v28", "embedded_choose_script"),
                        ("stateflow_contract_gate_v28", "embedded_contract_gate_script")):
        source = (ROOT/"matlab/simulink"/(name+".m")).read_text(encoding="utf-8-sig")
        check("saved_binding_exact_"+name, isinstance(binding.get(field), str) and
              binding[field].replace("\r\n", "\n") == source)
    output["saved_model_structure"] = verify_saved_model_structure(model)
    output["provenance_limit"] = ("Saved-model scripts and stored source snapshots are independently parsed/hashed. "
                                  "Runtime JSON and mutation artifacts are parsed and bound to summary/file hashes; captured MAT containers are hashed, not decoded. "
                                  "Before/after labels and simulation chronology remain local runner evidence without external attestation.")
    traces = {}
    for name, field in (("baseline", "baseline_trace_file"), ("restored", "restored_trace_file")):
        path = resolve_workspace_path(evidence.get(field), directory/(name+"_trace_v29.csv"))
        rows = read_csv(path) if path.is_file() else []
        traces[name] = rows
        output[name+"_trace"] = verify_baseline(rows, name)
        check(name+"_trace_file_exists", path.is_file())
        check(name+"_trace_is_local_expected_artifact", path.resolve() == (directory/(name+"_trace_v29.csv")).resolve())
        output[name+"_trace_sha256"] = sha(path) if path.is_file() else None
        check(name+"_trace_reported_hash_matches_file", path.is_file() and
              evidence.get(name+"_trace_sha256") == sha(path))
    check("restored_trace_numerically_matches_unmutated_baseline", len(traces["baseline"]) == len(traces["restored"]) == 2 and all(
        near(a.get(field), b.get(field)) for a, b in zip(traces["baseline"], traces["restored"])
        for field in expected_baseline()[0]))
    check("no_unexpected_acceptance_artifact", not list(directory.glob("*UNEXPECTED_ACCEPTANCE*")))
    check("reported_clean_and_restored_interval_counts", evidence.get("baseline_intervals") == evidence.get("restored_intervals") == 2)
    for field in ("baseline_matlab_reference_matches", "restored_baseline_matches"):
        check(field, evidence.get(field) is True)
    output["integrity"] = result(integrity)
    output["evidence_summary_sha256"] = sha(summary_path)
    output["actual_model_sha256"] = current_model_hash
    return output



def verify_saved_model_structure(model):
    """Parse the saved SLX archive; never execute/import production equations."""
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    scripts = []
    with zipfile.ZipFile(model) as archive:
        for name in archive.namelist():
            if name.startswith("simulink/stateflow/chart_") and name.endswith(".xml"):
                chart = ET.fromstring(archive.read(name))
                scripts.extend(p.text or "" for p in chart.findall(".//P[@Name='script']"))
        for name in ("stateflow_allocate_v28", "stateflow_choose_mode_v28", "stateflow_contract_gate_v28"):
            source = (ROOT/"matlab/simulink"/(name+".m")).read_text(encoding="utf-8-sig")
            check(name+":saved_script_exactly_matches_current_source", sum(s == source for s in scripts) == 1)
        check("saved_HP_adapter_calls_v28_host_component", any(
            "coder.extrinsic('dchr_stateflow_hp_v28')" in s and "u=dchr_stateflow_hp_v28(x,E,p,h,model_dt);" in s
            for s in scripts))
        system = ET.fromstring(archive.read("simulink/systems/system_root.xml"))
        blocks = {b.get("Name"): b.get("SID") for b in system.findall("Block")}
        edges = set()
        for line in system.findall("Line"):
            src = line.find("P[@Name='Src']")
            if src is not None:
                edges.update((src.text, p.text) for p in line.findall(".//P[@Name='Dst']"))
        for source, target in (("Thermal_Dispatch", "Runtime_Contract_Gate"),
                               ("Runtime_Contract_Gate", "Dispatch_Trace"),
                               ("Runtime_Contract_Gate", "Next_TES_Energy"),
                               ("Next_TES_Energy", "TES_Energy_Memory")):
            check(source+"_connected_to_"+target, (blocks.get(source,"MISSING")+"#out:1",
                  blocks.get(target,"MISSING")+"#in:1") in edges)
        check("ungated_dispatch_cannot_bypass_accepted_trace", (blocks.get("Thermal_Dispatch", "MISSING")+"#out:1",
              blocks.get("Dispatch_Trace", "MISSING")+"#in:1") not in edges)
    return result(checks)


def required_snapshot_sources(runner, spec_path):
    return {runner.relative_to(ROOT).as_posix(), spec_path.resolve().relative_to(ROOT).as_posix(),
            "matlab/simulink/DCHR_Dispatch_Stateflow_v28.slx", "matlab/simulink/build_dispatch_stateflow_v28.m",
            "matlab/simulink/stateflow_allocate_v28.m", "matlab/simulink/stateflow_choose_mode_v28.m",
            "matlab/simulink/stateflow_contract_gate_v28.m", "matlab/simulink/dchr_stateflow_hp_v28.m",
            "matlab/+dchr/simulate_dispatch_v28.m", "matlab/+dchr/+components/storage_step_v28.m",
            "matlab/+dchr/+components/heat_pump_step_v14.m", "matlab/default_config_v2.m", "matlab/default_config.m"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=HERE/"stateflow_monitor_fault_cases_v29.json")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--result-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.result_dir:
        if args.summary:
            parser.error("Provide only one of --summary or --result-dir")
        args.summary = args.result_dir/"gate_fault_rejections_v29.json"
    if not (args.summary or args.self_test):
        parser.error("Provide actual --summary and/or synthetic --self-test")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    output = dict(version="0.29", timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  scope=__doc__, primary_text_verified=False, primary_paper_replication=False,
                  equipment_validation=False, spec_sha256=sha(args.spec), verifier_sha256=sha(Path(__file__)),
                  specification=verify_spec(spec))
    if args.self_test:
        output["synthetic_verifier_self_test"] = self_test(spec)
    if args.summary:
        output.update(verify_actual(args.summary, spec, args.spec))
    for metric in ("checks", "passed", "failed"):
        output[metric] = sum(value.get(metric, 0) for value in output.values() if isinstance(value, dict))
    for category in ("actual_evidence", "synthetic_reviewer_self_test", "static_specification"):
        for metric in ("checks", "passed", "failed"):
            output[category+"_"+metric] = sum(value.get(metric, 0) for value in output.values()
                if isinstance(value, dict) and value.get("evidence_class") == category)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: ({k: v for k, v in value.items() if k != "assertions"}
                           if isinstance(value, dict) else value) for key, value in output.items()}, indent=2, allow_nan=False))
    raise SystemExit(bool(output["failed"]))


if __name__ == "__main__":
    main()
