"""Independent actual-v28 Stateflow sampled failure-timing evidence QA, v29.

The oracle uses only the separately specified fixed-COP hand case. It imports
no production MATLAB, Stateflow or prior acceptance implementation. Synthetic
self-tests exercise this reviewer and are not executed model evidence.
"""
from __future__ import annotations

import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MODEL_HASH = "30ea3701f2f04d293d6c9bf528dc625762bf69db9a06c9d6d384293a98497a1d"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def near(a, b):
    try:
        a, b = float(a), float(b)
        return math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-10 + 1e-11*abs(b)
    except (TypeError, ValueError, OverflowError):
        return False


def result(checks, synthetic_only=False, evidence_class="actual_evidence"):
    return {"checks": len(checks), "passed": sum(c["passed"] for c in checks),
            "failed": sum(not c["passed"] for c in checks), "assertions": checks,
            "synthetic_only": synthetic_only, "evidence_class": evidence_class}


def expected_times(case):
    """Integer solver ticks; all specified StopTimes lie exactly on ticks."""
    dt = case["dt_h"]
    count = int(round(case["stop_time_h"]/dt)) + 1
    return [i*dt for i in range(count)]


def verify_spec(spec):
    checks = []
    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
    baseline = spec.get("baseline", {})
    check("independent_fixed_COP_baseline", baseline == dict(
        x=[6, 35, 70, 5], E=1, p=[1, 10, 3, 4, .9, .8, .01, 2],
        h=[8, .45, 1.2, 8, 0, 1, 4, 0, 0], model_dt=1))
    check("model_hash_is_existing_v28", spec.get("model_sha256") == MODEL_HASH)
    check("reference_is_existing_v28_dispatch", spec.get("reference") == "dchr.simulate_dispatch_v28")
    cases = spec.get("cases", [])
    check("unique_case_ids", len({c["id"] for c in cases}) == len(cases))
    rejected = [c for c in cases if c["expected_outcome"] == "runtime_rejection"]
    complete = [c for c in cases if c["expected_outcome"] == "complete"]
    check("ten_preserved_finite_delayed_faults", len(rejected) == 10)
    check("two_preserved_future_invalid_controls", len(complete) == 2)
    check("four_sample_intervals", {c["dt_h"] for c in cases} == {.25, .5, 1, 2})
    for c in cases:
        label = c["id"]+":"
        dt, tau, stop = c["dt_h"], c["invalid_input_time_h"], c["stop_time_h"]
        first_invalid = math.ceil(tau/dt)*dt
        full = expected_times(c)
        check(label+"strictly_positive_finite_invalid_timestamp", math.isfinite(tau) and tau > 0)
        check(label+"finite_mutation", math.isfinite(c["invalid_value"]))
        check(label+"sampled_clock_parameter", dt > 0 and math.isfinite(.01*dt))
        check(label+"stop_time_on_solver_grid", near(stop/dt, round(stop/dt)))
        check(label+"specified_prefix_from_independent_clock", c["expected_valid_times_h"] ==
              [t for t in full if t < first_invalid])
        if c["expected_outcome"] == "runtime_rejection":
            check(label+"specified_rejection_at_first_sampled_invalid", near(c["expected_failure_time_h"], first_invalid))
            check(label+"fault_reached_within_run", first_invalid <= stop)
            check(label+"specified_physical_cause", c["expected_identifier"] == "DCHR:v28:PhysicalDomain" and
                  c["expected_inner_identifier"].startswith("DCHR:"))
        else:
            check(label+"bad_row_outside_requested_run", tau > stop and first_invalid > stop)
            check(label+"no_expected_error", c["expected_failure_time_h"] is None and
                  c["expected_identifier"] == c["expected_inner_identifier"] == "")
    return result(checks, evidence_class="static_specification")


def oracle(dt, times):
    """Loss-first recurrence and closed-form fixed-COP condenser allocation.

    Source=6 MW and COP=4 permit at most 8 MW condenser heat. Demand=5 MW
    leaves at most 3 MW charging, equal to the declared charge limit. The
    Define r=exp(-.01*dt), b=.9*3*dt. The unsaturated energy at the start
    of tick n is r**n*E0+b*(1-r**n)/(1-r), independently summed from a
    geometric series. Saturation clips this monotonically rising sequence
    at 10 MWh; it remains there because the cap refill fits the 3 MW limit.
    The charge request is min(3,(10-r*E_n)/(.9*dt)); therefore no boiler
    or discharge is needed. No production recurrence or numerical HP solve
    is imported. This reproduces the reduced loss-first assumption only.
    """
    rows = []
    a = .01*dt
    for n, time in enumerate(times):
        energy = min(10., math.exp(-a*n) + 2.7*dt*(-math.expm1(-a*n))/(-math.expm1(-a)))
        after = energy*math.exp(-a)
        charge = min(3., max(0., (10.-after)/(.9*dt)))
        heat = 5.+charge
        next_energy = after+.9*charge*dt
        rows.append(dict(Time_h=time, Source_Heat_MW=6, Source_C=35, Sink_C=70,
                         Heat_Demand_MW=5, HP_Request_MW=heat, HP_Heat_MW=heat,
                         HP_Direct_MW=5, HP_Electric_MW=heat/4,
                         HP_Source_Used_MW=.75*heat, COP=4, HP_Available=1,
                         Source_Unused_MW=6-.75*heat, Storage_Charge_MW=charge,
                         Storage_Discharge_MW=0, Storage_E_Start_MWh=energy,
                         Storage_E_After_Loss_MWh=after, Storage_E_Next_MWh=next_energy,
                         Storage_Standing_Loss_MWh=-energy*math.expm1(-a),
                         Storage_Charge_Loss_MWh=.1*charge*dt, Storage_Discharge_Loss_MWh=0,
                         Gas_Heat_MW=0, Unmet_Heat_MW=0, Supplied_Heat_MW=5,
                         System_Balance_Residual_MWh=0, Mode=2))
    return rows


def verify_trace(rows, expected, dt, label):
    checks = []
    def check(name, value):
        checks.append(dict(name=label+":"+name, passed=bool(value)))
    check("exact_accepted_interval_count", len(rows) == len(expected))
    for i, target in enumerate(expected):
        row = rows[i] if i < len(rows) else {}
        for field, value in target.items():
            check(f"tick_{i}:{field}:independent_oracle", near(row.get(field), value))
        try:
            r = {field: float(row[field]) for field in target}
            tes = (r["Storage_E_Start_MWh"] +
                   (r["Storage_Charge_MW"]-r["Storage_Discharge_MW"])*dt -
                   r["Storage_E_Next_MWh"] - r["Storage_Standing_Loss_MWh"] -
                   r["Storage_Charge_Loss_MWh"] - r["Storage_Discharge_Loss_MWh"])
            system = ((r["HP_Source_Used_MW"]+r["HP_Electric_MW"]+r["Gas_Heat_MW"]-
                       r["Supplied_Heat_MW"])*dt + r["Storage_E_Start_MWh"] -
                      r["Storage_E_Next_MWh"] - r["Storage_Standing_Loss_MWh"] -
                      r["Storage_Charge_Loss_MWh"] - r["Storage_Discharge_Loss_MWh"])
            check(f"tick_{i}:independent_TES_energy_closure", near(tes, 0))
            check(f"tick_{i}:independent_whole_system_closure", near(system, 0))
            check(f"tick_{i}:reported_residual_matches_recomputed", near(system, r["System_Balance_Residual_MWh"]))
            check(f"tick_{i}:storage_bounds", 0 <= r["Storage_E_Next_MWh"] <= 10+1e-10)
            check(f"tick_{i}:no_charge_discharge_overlap", r["Storage_Charge_MW"]*r["Storage_Discharge_MW"] == 0)
        except (KeyError, ValueError, TypeError):
            check(f"tick_{i}:recomputable_accepted_trace", False)
        if i and i < len(rows):
            check(f"tick_{i}:actual_unit_delay_memory", near(row.get("Storage_E_Start_MWh"),
                  rows[i-1].get("Storage_E_Next_MWh")))
    return result(checks)


def verify_records(spec, evidence, read_artifact):
    """read_artifact(record, field) returns (contents, actual_sha256)."""
    checks = []
    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
    records = evidence.get("records", [])
    ids = [r.get("id") for r in records]
    cases = spec["cases"]
    check("exact_independent_case_set", len(ids) == len(cases) == len(set(ids)) and
          set(ids) == {c["id"] for c in cases})
    mapped = {r.get("id"): r for r in records}
    for c in cases:
        label = c["id"]+":"
        r = mapped.get(c["id"], {})
        for field in ("dt_h", "invalid_input_time_h", "stop_time_h"):
            check(label+"specified_"+field, near(r.get(field), c[field]))
        check(label+"actual_simulation_attempted", r.get("simulation_attempted") is True)
        check(label+"capture_errors_requested", r.get("capture_errors") == "on")
        check(label+"independently_expected_outcome", r.get("expected_outcome") == c["expected_outcome"])
        check(label+"actual_valid_prefix_not_merely_placement", r.get("valid_prefix_matches") is True)
        d = r.get("diagnostic", {})
        configured, configured_hash = read_artifact(r, "configured_input_file")
        check(label+"configured_input_file_hash", bool(configured_hash) and
              r.get("configured_input_sha256") == configured_hash)
        expected_input = [dict(Time_h=0, Source_Heat_MW=6, Source_C=35, Sink_C=70, Heat_Demand_MW=5),
                          dict(Time_h=c["invalid_input_time_h"], Source_Heat_MW=6,
                               Source_C=35, Sink_C=70, Heat_Demand_MW=5)]
        input_fields = ("Source_Heat_MW", "Source_C", "Sink_C", "Heat_Demand_MW")
        expected_input[1][input_fields[c["target_index"]-1]] = c["invalid_value"]
        check(label+"actual_input_schedule_matches_independent_spec", isinstance(configured, list) and
              len(configured) == 2 and all(near(a.get(f), b[f]) for a, b in zip(configured, expected_input)
                                           for f in expected_input[0]))
        full = oracle(c["dt_h"], expected_times(c))
        prefix = oracle(c["dt_h"], c["expected_valid_times_h"])
        trace_rows = {}
        for name, expected in (("clean", full), ("reference", full), ("partial", prefix)):
            rows, actual_hash = read_artifact(r, name+"_trace_file")
            rows = rows if isinstance(rows, list) else []
            trace_rows[name] = rows
            check(label+name+"_trace_file_present", bool(actual_hash))
            check(label+name+"_trace_sha256_matches_file", bool(actual_hash) and
                  r.get(name+"_trace_sha256") == actual_hash)
            # The v28 reference returns all physical ports but has no mode port.
            targets = [{k: v for k, v in row.items() if k != "Mode"} for row in expected] if name == "reference" else expected
            checks.extend(verify_trace(rows, targets, c["dt_h"], c["id"]+":"+name)["assertions"])
        check(label+"partial_matches_clean_prefix", len(trace_rows["partial"]) == len(prefix) and
              len(trace_rows["clean"]) >= len(prefix) and all(
                  near(a.get(f), b.get(f)) for a, b in zip(trace_rows["partial"], trace_rows["clean"])
                  for f in prefix[0]))
        check(label+"recorded_partial_interval_count", r.get("partial_intervals") == len(prefix))
        check(label+"recorded_clean_interval_count", r.get("clean_intervals") == len(full))
        raw, raw_hash = read_artifact(r, "raw_trace_times_file")
        check(label+"raw_signal_times_hash", bool(raw_hash) and r.get("raw_trace_times_sha256") == raw_hash)
        check(label+"raw_signal_times_equal_record", isinstance(raw, dict) and raw == r.get("raw_trace_times"))
        raw = raw if isinstance(raw, dict) else {}
        dispatch_times = raw.get("dispatch_times_h", [])
        if isinstance(dispatch_times, (float, int)):
            dispatch_times = [dispatch_times]
        check(label+"raw_accepted_dispatch_prefix", dispatch_times == c["expected_valid_times_h"])
        check(label+"raw_accepted_signals_joined", raw.get("joined") is True)
        for port in ("hp_times_h", "energy_start_times_h"):
            times = raw.get(port, [])
            if isinstance(times, (float, int)):
                times = [times]
            prefix_times = c["expected_valid_times_h"]
            check(label+port+":ordered_finite_unique_samples", isinstance(times, list) and
                  all(math.isfinite(t) for t in times) and all(a < b for a, b in zip(times, times[1:])))
            check(label+port+":all_accepted_samples_present", all(t in times for t in prefix_times))
            allowed = prefix_times + ([c["expected_failure_time_h"]] if c["expected_outcome"] == "runtime_rejection" else [])
            check(label+port+":extras_only_partial_failed_tick_evaluation", all(t in allowed for t in times))
        diagnostic_saved, diagnostic_hash = read_artifact(r, "diagnostic_file")
        check(label+"saved_diagnostic_hash", bool(diagnostic_hash) and r.get("diagnostic_sha256") == diagnostic_hash)
        check(label+"saved_diagnostic_matches_record", diagnostic_saved == d)
        if c["expected_outcome"] == "runtime_rejection":
            check(label+"diagnostic_execution_phase", d.get("error_phase") == "Execution")
            check(label+"diagnostic_at_first_sampled_invalid_time", near(d.get("error_time_h"), c["expected_failure_time_h"]))
            check(label+"stop_event_at_first_sampled_invalid_time", near(d.get("stop_event_time_h"), c["expected_failure_time_h"]))
            check(label+"diagnostic_error_stop", d.get("stop_event") == "DiagnosticError")
            cause_ids = d.get("cause_identifiers", [])
            check(label+"original_physical_wrapper_preserved", c["expected_identifier"] in cause_ids)
            check(label+"nonempty_runtime_diagnostic", bool(d.get("error_message", "").strip()))
            check(label+"captured_specific_invalid_domain_message", c["runtime_message_fragment"] in d.get("error_message", ""))
            replay = r.get("uncaptured_exception", {})
            check(label+"uncaptured_identical_input_replay_attempted", replay.get("simulation_attempted") is True)
            check(label+"uncaptured_replay_rejected", replay.get("rejected") is True)
            check(label+"uncaptured_physical_wrapper_preserved", c["expected_identifier"] in replay.get("cause_identifiers", []))
            check(label+"thrown_specific_invalid_domain_message", c["runtime_message_fragment"] in replay.get("message", ""))
            report, report_hash = read_artifact(replay, "report_file")
            check(label+"saved_failure_report_present", isinstance(report, str) and bool(report.strip()))
            check(label+"saved_failure_report_sha256", bool(report_hash) and replay.get("report_sha256") == report_hash)
            host = r.get("host_adapter_validation", {})
            check(label+"separate_host_component_call_attempted", host.get("component_call_attempted") is True)
            check(label+"separate_host_component_rejected", host.get("rejected") is True)
            check(label+"separate_host_physical_wrapper_preserved", c["expected_identifier"] in host.get("cause_identifiers", []))
            check(label+"separate_host_specific_component_cause_preserved", c["expected_inner_identifier"] in host.get("cause_identifiers", []))
            host_report, host_hash = read_artifact(host, "report_file")
            check(label+"separate_host_report_present", isinstance(host_report, str) and bool(host_report.strip()))
            check(label+"separate_host_report_hash", bool(host_hash) and host.get("report_sha256") == host_hash)
            check(label+"no_accepted_output_at_or_after_rejection", all(
                float(row.get("Time_h", "nan")) < c["expected_failure_time_h"] for row in trace_rows["partial"]))
        else:
            check(label+"reached_requested_stop_time", d.get("stop_event") == "ReachedStopTime")
            check(label+"actual_stop_time_matches_requested", near(d.get("stop_event_time_h"), c["stop_time_h"]))
            check(label+"future_invalid_input_has_no_diagnostic", not d.get("error_message") and
                  not d.get("error_phase") and not d.get("cause_identifiers"))
    return result(checks)


def self_test(spec):
    """Never write or label a synthetic fixture as actual MATLAB evidence."""
    records = []
    for c in spec["cases"]:
        rejected = c["expected_outcome"] == "runtime_rejection"
        diagnostic = dict(stop_event="DiagnosticError" if rejected else "ReachedStopTime",
                          stop_event_time_h=c["expected_failure_time_h"] if rejected else c["stop_time_h"],
                          error_phase="Execution" if rejected else "",
                          error_time_h=c["expected_failure_time_h"],
                          error_message="Synthetic runtime error fixture" if rejected else "",
                          cause_identifiers=[c["expected_identifier"]] if rejected else [])
        raw = dict(dispatch_times_h=c["expected_valid_times_h"], hp_times_h=c["expected_valid_times_h"],
                   energy_start_times_h=c["expected_valid_times_h"], joined=True)
        r = dict(c, simulation_attempted=True, capture_errors="on", valid_prefix_matches=True,
                 diagnostic=diagnostic, diagnostic_file=diagnostic, diagnostic_sha256="synthetic_hash",
                 raw_trace_times=raw, raw_trace_times_file=raw, raw_trace_times_sha256="synthetic_hash")
        r["partial_intervals"] = len(c["expected_valid_times_h"])
        r["clean_intervals"] = len(expected_times(c))
        diagnostic["error_message"] = c.get("runtime_message_fragment", "")
        input_fields = ("Source_Heat_MW", "Source_C", "Sink_C", "Heat_Demand_MW")
        configured = [dict(Time_h=0, Source_Heat_MW=6, Source_C=35, Sink_C=70, Heat_Demand_MW=5),
                      dict(Time_h=c["invalid_input_time_h"], Source_Heat_MW=6,
                           Source_C=35, Sink_C=70, Heat_Demand_MW=5)]
        configured[1][input_fields[c["target_index"]-1]] = c["invalid_value"]
        r["configured_input_file"] = configured
        r["configured_input_sha256"] = "synthetic_hash"
        r["uncaptured_exception"] = dict(simulation_attempted=True, rejected=True,
            cause_identifiers=[c["expected_identifier"]], message=c.get("runtime_message_fragment", ""),
            report_file="Synthetic fixture: not executed model evidence", report_sha256="synthetic_hash")
        r["host_adapter_validation"] = dict(component_call_attempted=True, rejected=True,
            cause_identifiers=[c["expected_identifier"], c["expected_inner_identifier"]],
            report_file="Synthetic host fixture: component evidence only", report_sha256="synthetic_hash")
        for name, times in (("clean", expected_times(c)), ("reference", expected_times(c)),
                            ("partial", c["expected_valid_times_h"])):
            rows = oracle(c["dt_h"], times)
            r[name+"_trace_file"] = ([{k: v for k, v in row.items() if k != "Mode"} for row in rows]
                                     if name == "reference" else rows)
            r[name+"_trace_sha256"] = "synthetic_hash"
        records.append(r)
    evidence = dict(records=records)
    def read_fixture(record, field):
        return record.get(field, ""), "synthetic_hash"
    checks = [dict(name="synthetic_valid_evidence_passes", passed=
                   verify_records(spec, evidence, read_fixture)["failed"] == 0)]
    mutations = (("simulation_attempted", False), ("capture_errors", "off"),
                 ("expected_outcome", "complete"), ("valid_prefix_matches", False),
                 ("invalid_input_time_h", 0), ("partial_trace_sha256", "incorrect"))
    for field, value in mutations:
        broken = copy.deepcopy(evidence)
        broken["records"][0][field] = value
        checks.append(dict(name="reject_corrupted_"+field, passed=
                           verify_records(spec, broken, read_fixture)["failed"] > 0))
    for field, value in (("error_time_h", 0), ("stop_event_time_h", 0), ("error_phase", "Compilation"),
                         ("stop_event", "ReachedStopTime"), ("cause_identifiers", [])):
        broken = copy.deepcopy(evidence)
        broken["records"][0]["diagnostic"][field] = value
        checks.append(dict(name="reject_corrupted_diagnostic_"+field, passed=
                           verify_records(spec, broken, read_fixture)["failed"] > 0))
    for field, value in (("cause_identifiers", []),
                         ("simulation_attempted", False), ("rejected", False), ("report_sha256", "wrong")):
        broken = copy.deepcopy(evidence)
        broken["records"][0]["uncaptured_exception"][field] = value
        checks.append(dict(name="reject_corrupted_uncaptured_"+field, passed=
                           verify_records(spec, broken, read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["host_adapter_validation"]["cause_identifiers"] = ["DCHR:v28:PhysicalDomain"]
    checks.append(dict(name="reject_missing_direct_component_inner_cause", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    for field, value in (("Time_h", .25), ("Storage_E_Next_MWh", 2), ("Mode", 1.5),
                         ("HP_Electric_MW", float("nan")), ("Storage_Discharge_MW", .1)):
        broken = copy.deepcopy(evidence)
        broken["records"][0]["partial_trace_file"][0][field] = value
        checks.append(dict(name="reject_corrupted_trace_"+field, passed=
                           verify_records(spec, broken, read_fixture)["failed"] > 0))
    for label, changed in (("missing_case", records[:-1]), ("duplicate_case", records+records[:1])):
        checks.append(dict(name="reject_"+label, passed=
                           verify_records(spec, dict(records=changed), read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["partial_trace_file"].append(oracle(.25, [0, .25])[1])
    checks.append(dict(name="reject_accepted_output_at_invalid_tick", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][-1]["diagnostic"]["error_message"] = "Unexpected future-input rejection"
    checks.append(dict(name="reject_error_in_future_invalid_control", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    for field, value in (("dispatch_times_h", [0, .25]), ("hp_times_h", [.25]),
                         ("energy_start_times_h", [0, 0]), ("joined", False)):
        broken = copy.deepcopy(evidence)
        broken["records"][0]["raw_trace_times"][field] = value
        checks.append(dict(name="reject_corrupted_raw_"+field, passed=
                           verify_records(spec, broken, read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    for field in ("dispatch_times_h", "hp_times_h", "energy_start_times_h"):
        broken["records"][0]["raw_trace_times"][field] = 0
    checks.append(dict(name="accept_MATLAB_singleton_time_serialization", passed=
                       verify_records(spec, broken, read_fixture)["failed"] == 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["raw_trace_times"]["energy_start_times_h"] = [0, .25]
    checks.append(dict(name="accept_upstream_partial_evaluation_at_fault_tick", passed=
                       verify_records(spec, broken, read_fixture)["failed"] == 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["configured_input_file"][1]["Source_Heat_MW"] = 6
    checks.append(dict(name="reject_unexecuted_specified_input_mutation", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["configured_input_file"][1]["Time_h"] = 0
    checks.append(dict(name="reject_wrong_configured_input_timestamp", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    broken = copy.deepcopy(evidence)
    broken["records"][0]["partial_trace_file"][0]["Storage_E_After_Loss_MWh"] = 1-.01*.25
    checks.append(dict(name="reject_obsolete_linear_retention_anchor", passed=
                       verify_records(spec, broken, read_fixture)["failed"] > 0))
    # Build corrupted ZIP archives in memory. These probe the reviewer only;
    # neither the production SLX nor a synthetic model is executed or saved.
    model = ROOT/spec["model_file"]
    with zipfile.ZipFile(model) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    mutations = (
        ("input_interpolation", "simulink/systems/system_root.xml",
         ".//Block[@Name='Scenario_Input']/P[@Name='Interpolate']", "on"),
        ("input_sample_clock", "simulink/systems/system_root.xml",
         ".//Block[@Name='Scenario_Input']/P[@Name='SampleTime']", "1"),
        ("TES_memory_clock", "simulink/systems/system_root.xml",
         ".//Block[@Name='TES_Energy_Memory']/P[@Name='SampleTime']", "1"),
        ("TES_initial_condition", "simulink/systems/system_root.xml",
         ".//Block[@Name='TES_Energy_Memory']/P[@Name='InitialCondition']", "0"),
        ("next_energy_selector", "simulink/systems/system_root.xml",
         ".//Block[@Name='Next_TES_Energy']/P[@Name='Indices']", "7"),
        ("solver_clock", "simulink/configSet0.xml", ".//P[@Name='FixedStep']", "1"),
    )
    dispatch_members = [name for name, content in members.items()
                        if name.startswith("simulink/stateflow/chart_") and
                        ET.fromstring(content).findtext("P[@Name='name']") == "Thermal_Dispatch"]
    if len(dispatch_members) == 1:
        mutations += (("chart_sample_clock", dispatch_members[0],
                       "P[@Name='sampleTime']", "1"),)
    checks.append(dict(name="saved_structure_fixture_has_unique_dispatch_chart",
                       passed=len(dispatch_members) == 1))
    for label, member, selector, value in mutations:
        changed = ET.fromstring(members[member])
        parameter = changed.find(selector)
        if parameter is None:
            checks.append(dict(name="reject_corrupted_saved_"+label, passed=False))
            continue
        parameter.text = value
        memory = io.BytesIO()
        with zipfile.ZipFile(memory, "w") as archive:
            for name, content in members.items():
                archive.writestr(name, ET.tostring(changed) if name == member else content)
        memory.seek(0)
        checks.append(dict(name="reject_corrupted_saved_"+label,
                           passed=verify_saved_model_structure(memory)["failed"] > 0))
    return result(checks, synthetic_only=True, evidence_class="synthetic_reviewer_self_test")


def resolve_path(value, fallback):
    path = Path(value) if isinstance(value, str) and value else fallback
    return path if path.is_absolute() else ROOT/path


def verify_actual(summary_path, spec, spec_path):
    evidence = json.loads(summary_path.read_text(encoding="utf-8-sig"))
    def read_artifact(record, field):
        path = resolve_path(record.get(field), summary_path.parent/"MISSING")
        if not path.is_file():
            return "", ""
        if field.endswith("_trace_file") or field == "configured_input_file":
            with path.open(newline="", encoding="utf-8-sig") as stream:
                value = list(csv.DictReader(stream))
        elif field in ("raw_trace_times_file", "diagnostic_file"):
            value = json.loads(path.read_text(encoding="utf-8-sig"))
        else:
            value = path.read_text(encoding="utf-8-sig")
        return value, sha(path)
    checks = []
    def check(name, value):
        checks.append(dict(name=name, passed=bool(value)))
    model = ROOT/spec["model_file"]
    check("actual_saved_v28_model_preserved", sha(model) == MODEL_HASH)
    check("before_model_hash_matches_saved_v28", evidence.get("model_sha256_before") == MODEL_HASH)
    check("after_model_hash_matches_saved_v28", evidence.get("model_sha256_after") == MODEL_HASH)
    check("actual_independent_spec_hash", evidence.get("spec_sha256") == sha(spec_path))
    check("saved_model_modified_false", evidence.get("saved_model_modified") is False)
    for field in ("simulink_executed", "stateflow_executed", "stateflow_license"):
        check(field, evidence.get(field) in (True, 1))
    for field in ("standalone_codegen", "primary_paper_replication", "equipment_validation"):
        check(field+"_false", evidence.get(field) is False)
    check("normal_simulation_scope", evidence.get("simulation_mode") == "normal")
    runner = resolve_path(evidence.get("runner_file"), ROOT/"matlab/simulink/run_stateflow_temporal_acceptance_v29.m")
    check("actual_runner_hash", runner.is_file() and evidence.get("runner_sha256") == sha(runner))
    check("reported_saved_model_release", evidence.get("model_version") == "0.28")
    check("reported_saved_embedded_sources_match", evidence.get("saved_embedded_sources_match") is True)
    expected_sources = required_snapshot_sources(runner, spec_path)
    before = evidence.get("source_sha256_before", [])
    after = evidence.get("source_sha256_after", [])
    snapshots = evidence.get("source_snapshot_hashes", [])
    before = before if isinstance(before, list) else []
    after = after if isinstance(after, list) else []
    snapshots = snapshots if isinstance(snapshots, list) else []
    normal = lambda value: str(value).replace("\\", "/")
    before_map = {normal(r.get("path")): r.get("sha256") for r in before}
    after_map = {normal(r.get("path")): r.get("sha256") for r in after}
    snapshot_map = {Path(normal(r.get("path"))).name: r for r in snapshots}
    check("complete_unique_before_source_closure", len(before) == len(before_map) == len(expected_sources)
          and set(before_map) == expected_sources)
    check("complete_unique_after_source_closure", len(after) == len(after_map) == len(expected_sources)
          and set(after_map) == expected_sources)
    check("complete_unique_snapshot_closure", len(snapshots) == len(snapshot_map) == len(expected_sources)
          and set(snapshot_map) == {Path(p).name for p in expected_sources})
    snapshot_dir = resolve_path(evidence.get("source_snapshot_directory"), summary_path.parent/"MISSING")
    check("source_snapshot_directory_present", snapshot_dir.is_dir())
    for relative in sorted(expected_sources):
        path = ROOT/relative
        current_hash = sha(path) if path.is_file() else ""
        check(relative+":before_hash_matches_actual_source", bool(current_hash) and before_map.get(relative) == current_hash)
        check(relative+":after_hash_matches_actual_source", bool(current_hash) and after_map.get(relative) == current_hash)
        snap_record = snapshot_map.get(path.name, {})
        snap_path = resolve_path(snap_record.get("path"), snapshot_dir/"MISSING")
        snapshot_hash = sha(snap_path) if snap_path.is_file() else ""
        check(relative+":snapshot_recorded_hash_matches_file", bool(snapshot_hash) and
              snap_record.get("sha256") == snapshot_hash)
        check(relative+":snapshot_matches_before_and_current_source", bool(current_hash) and snapshot_hash == current_hash == before_map.get(relative))
        check(relative+":snapshot_inside_recorded_directory", snap_path.is_relative_to(snapshot_dir))
    check("summary_case_count_matches_independent_spec", evidence.get("cases") == len(spec["cases"]))
    assertions_path = summary_path.parent/"temporal_assertions_v29.csv"
    if assertions_path.is_file():
        with assertions_path.open(newline="", encoding="utf-8-sig") as stream:
            assertions = list(csv.DictReader(stream))
    else:
        assertions = []
    passed_count = sum(row.get("passed") == "1" for row in assertions)
    check("MATLAB_assertion_table_present", bool(assertions))
    check("all_MATLAB_temporal_assertions_pass", bool(assertions) and passed_count == len(assertions))
    check("MATLAB_summary_counts_match_exported_assertions", evidence.get("checks") == len(assertions) and
          evidence.get("passed") == passed_count and evidence.get("failed") == len(assertions)-passed_count)
    final_rows, final_hash = read_artifact(evidence, "final_clean_trace_file")
    final_rows = final_rows if isinstance(final_rows, list) else []
    check("post_fault_restart_trace_hash", bool(final_hash) and evidence.get("final_clean_trace_sha256") == final_hash)
    final_case = spec["cases"][-1]
    final_qa = verify_trace(final_rows, oracle(final_case["dt_h"], expected_times(final_case)),
                            final_case["dt_h"], "post_fault_clean_restart")
    return dict(integrity=result(checks), temporal_evidence=verify_records(spec, evidence, read_artifact),
                saved_model_structure=verify_saved_model_structure(model),
                post_fault_clean_restart=final_qa,
                evidence_summary_sha256=sha(summary_path), actual_model_sha256=sha(model))



def verify_saved_model_structure(model):
    """Parse the saved SLX archive; never execute/import production equations."""
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    scripts = []
    dispatch_charts = []
    with zipfile.ZipFile(model) as archive:
        for name in archive.namelist():
            if name.startswith("simulink/stateflow/chart_") and name.endswith(".xml"):
                chart = ET.fromstring(archive.read(name))
                scripts.extend(p.text or "" for p in chart.findall(".//P[@Name='script']"))
                if chart.findtext("P[@Name='name']") == "Thermal_Dispatch":
                    dispatch_charts.append(chart)
        for name in ("stateflow_allocate_v28", "stateflow_choose_mode_v28", "stateflow_contract_gate_v28"):
            source = (ROOT/"matlab/simulink"/(name+".m")).read_text(encoding="utf-8-sig")
            check(name+":saved_script_exactly_matches_current_source", sum(s == source for s in scripts) == 1)
        check("saved_HP_adapter_calls_v28_host_component", any(
            "coder.extrinsic('dchr_stateflow_hp_v28')" in s and "u=dchr_stateflow_hp_v28(x,E,p,h,model_dt);" in s
            for s in scripts))
        system = ET.fromstring(archive.read("simulink/systems/system_root.xml"))
        blocks = {b.get("Name"): b.get("SID") for b in system.findall("Block")}
        configuration = ET.fromstring(archive.read("simulink/configSet0.xml"))
        for name, expected in (("SolverName", "FixedStepDiscrete"),
                               ("FixedStep", "dchr_dt_v28"), ("StopTime", "dchr_stop_v28")):
            check("saved_solver_"+name, configuration.findtext(".//P[@Name='"+name+"']") == expected)
        parameters = {
            "Scenario_Input": {"VariableName": "dchr_input_v28", "SampleTime": "dchr_dt_v28",
                               "Interpolate": "off", "OutputAfterFinalValue": "Holding final value"},
            "TES_Energy_Memory": {"InitialCondition": "dchr_E0_v28", "SampleTime": "dchr_dt_v28"},
            "Integration_Step": {"Value": "dchr_dt_v28"},
            "Next_TES_Energy": {"Indices": "8", "InputPortWidth": "13"},
        }
        for block, properties in parameters.items():
            for name, expected in properties.items():
                check("saved_"+block+":"+name,
                      system.findtext("Block[@Name='"+block+"']/P[@Name='"+name+"']") == expected)
        check("unique_saved_discrete_dispatch_chart", len(dispatch_charts) == 1)
        if len(dispatch_charts) == 1:
            for name, expected in (("updateMethod", "DISCRETE"), ("sampleTime", "dchr_dt_v28")):
                check("saved_dispatch_chart_"+name,
                      dispatch_charts[0].findtext("P[@Name='"+name+"']") == expected)
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
    parser.add_argument("--spec", type=Path, default=HERE/"stateflow_temporal_cases_v29.json")
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if not (args.summary or args.self_test):
        parser.error("Supply actual --summary and/or synthetic --self-test")
    spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
    output = dict(version="0.29", timestamp_utc=datetime.now(timezone.utc).isoformat(),
                  scope=__doc__, primary_text_verified=False, primary_paper_replication=False,
                  equipment_validation=False, spec_sha256=sha(args.spec), verifier_sha256=sha(__file__),
                  specification=verify_spec(spec))
    if args.self_test:
        output["synthetic_reviewer_self_test"] = self_test(spec)
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
    concise = {key: ({k: v for k, v in value.items() if k != "assertions"}
                     if isinstance(value, dict) else value) for key, value in output.items()}
    print(json.dumps(concise, indent=2, allow_nan=False))
    raise SystemExit(bool(output["failed"]))


if __name__ == "__main__":
    main()
