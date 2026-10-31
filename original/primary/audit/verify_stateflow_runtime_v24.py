"""Independent v24 executable-domain evidence and saved-model graph audit.

Numerical valid-trace QA explicitly reuses the already independent v22 oracle.
No MATLAB production implementation is imported or executed by this script.
Static ZIP provenance is distinct from simulation rejection evidence.
"""
import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import verify_stateflow_trace_v22 as numeric_v22

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prop(element, name, default=""):
    value = element.find("P[@Name='" + name + "']")
    return value.text if value is not None and value.text is not None else default


def result(checks):
    return dict(checks=len(checks), passed=sum(c["passed"] for c in checks),
                failed=sum(not c["passed"] for c in checks), assertions=checks)


def verify_rejections(spec, evidence):
    checks = []

    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    records = evidence if isinstance(evidence, list) else evidence.get("records", evidence.get("cases", []))
    expected = spec["cases"]
    ids = [r.get("id") for r in records]
    check("one_actual_record_per_independent_case", len(records) == len(expected) and
          len(set(ids)) == len(ids) and set(ids) == {c["id"] for c in expected})
    mapped = {r.get("id"): r for r in records}
    for case in expected:
        record = mapped.get(case["id"], {})
        prefix = case["id"] + ":"
        check(prefix + "matches_independent_expected_identifier",
              record.get("expected_identifier") == case["expected_identifier"])
        check(prefix + "actual_simulation_attempted", record.get("simulation_attempted") is True)
        check(prefix + "rejected", record.get("rejected") is True)
        check(prefix + "no_accepted_invalid_trace", record.get("accepted_invalid_trace") is False)
        causes = record.get("cause_identifiers", [])
        causes = [causes] if isinstance(causes, str) else causes
        found = [record.get("actual_identifier", "")] + causes
        check(prefix + "specific_runtime_domain_or_clock_cause",
              case["expected_identifier"] in found)
        check(prefix + "executed_input_tick_matches_case", record.get("tick") == case["tick"])
        check(prefix + "diagnostic_saved", isinstance(record.get("message"), str) and
              bool(record.get("message")))
    output = result(checks)
    output["cases"] = len(records)
    output["second_tick_cases"] = [c["id"] for c in expected if c["tick"] == 1]
    output["timing_limit"] = (
        "The tick field identifies intended invalid-input placement. Unknown started_at_h "
        "does not prove an earlier tick completed; per-case traces/logs must support that claim.")
    return output


def verify_clock_probe(path):
    """Recompute the .5 h-versus-1 h defect from the actual old-model CSV."""
    with path.open(newline="", encoding="utf-8") as stream:
        rows = [{k: float(v) for k, v in r.items()} for r in csv.DictReader(stream)]
    checks = []

    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    check("two_actual_samples", len(rows) == 2)
    check("actual_one_hour_sample_grid", [r["Time_h"] for r in rows] == [0.0, 1.0])
    for index, row in enumerate(rows):
        prefix = "sample_" + str(index) + ":"
        # Independently stated probe: no HP, boiler or standing loss, etaD=.8,
        # one MW useful TES demand. Physics over model interval=1 h consumes1.25 MWh.
        next_physical_half_hour = row["Energy_Start_MWh"] - row["Discharge_MW"] * 0.5 / 0.8
        correct_full_hour_loss = (1 / 0.8 - 1) * row["Discharge_MW"] * 1.0
        actual_grid_residual = row["Energy_Start_MWh"] - row["Discharge_MW"] * 1.0 - row["Energy_Next_MWh"] - correct_full_hour_loss
        check(prefix + "one_MW_useful_discharge", row["Discharge_MW"] == 1)
        check(prefix + "old_next_state_uses_half_hour", abs(row["Energy_Next_MWh"] - next_physical_half_hour) < 1e-12)
        check(prefix + "old_loss_uses_half_hour", abs(row["Discharge_Loss_MWh"] - correct_full_hour_loss * 0.5) < 1e-12)
        check(prefix + "misleading_reported_closure", abs(row["Reported_Residual_MWh"]) < 1e-12)
        check(prefix + "independent_actual_time_residual_minus_0625_MWh", abs(actual_grid_residual + 0.625) < 1e-12)
        check(prefix + "reported_defect_matches_independent_residual", abs(actual_grid_residual - row["Clock_Correct_Residual_MWh"]) < 1e-12)
    output = result(checks)
    output["scope"] = "Independent arithmetic on actual v22 probe samples, not equipment validation"
    return output


def verify_structure(model):
    checks = []

    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    with ZipFile(model) as zipped:
        root = ET.fromstring(zipped.read("simulink/systems/system_root.xml"))
        blocks = {b.attrib["Name"]: b for b in root.findall("Block")}
        sids = {name: block.attrib["SID"] for name, block in blocks.items()}
        edges = set()
        for line in root.findall("Line"):
            source = prop(line, "Src")
            for destination in line.iter("P"):
                if destination.attrib.get("Name") == "Dst":
                    edges.add((source, destination.text))
        connections = [
            ("Scenario_Input", 1, "Verified_HP_Component", 1),
            ("Verified_HP_Component", 1, "Thermal_Dispatch", 1),
            ("TES_Energy_Memory", 1, "Verified_HP_Component", 2),
            ("TES_Energy_Memory", 1, "Thermal_Dispatch", 2),
            ("TES_and_Boiler_Parameters", 1, "Verified_HP_Component", 3),
            ("TES_and_Boiler_Parameters", 1, "Thermal_Dispatch", 3),
            ("HP_Parameters", 1, "Verified_HP_Component", 4),
            ("Integration_Step", 1, "Verified_HP_Component", 5),
            ("Integration_Step", 1, "Runtime_Contract_Gate", 5),
            ("Thermal_Dispatch", 1, "Runtime_Contract_Gate", 1),
            ("Verified_HP_Component", 1, "Runtime_Contract_Gate", 2),
            ("TES_Energy_Memory", 1, "Runtime_Contract_Gate", 3),
            ("TES_and_Boiler_Parameters", 1, "Runtime_Contract_Gate", 4),
            ("Runtime_Contract_Gate", 1, "Next_TES_Energy", 1),
            ("Runtime_Contract_Gate", 1, "Dispatch_Trace", 1),
            ("Next_TES_Energy", 1, "TES_Energy_Memory", 1),
            ("Verified_HP_Component", 1, "HP_Trace", 1),
            ("TES_Energy_Memory", 1, "Energy_Start_Trace", 1)]
        for source, source_port, target, target_port in connections:
            check(source + "_to_" + target + "_port_" + str(target_port),
                  (sids.get(source, "MISSING") + "#out:" + str(source_port),
                   sids.get(target, "MISSING") + "#in:" + str(target_port)) in edges)
        chart_out = sids["Thermal_Dispatch"] + "#out:1"
        check("unchecked_chart_output_has_no_trace_or_memory_bypass",
              {dst for src, dst in edges if src == chart_out} ==
              {sids["Runtime_Contract_Gate"] + "#in:1"})
        check("integration_constant_uses_same_model_time",
              prop(blocks["Integration_Step"], "Value") == "dchr_dt_v24")
        check("discrete_energy_memory", blocks["TES_Energy_Memory"].attrib["BlockType"] == "UnitDelay")
        check("energy_feedback_index_8", prop(blocks["Next_TES_Energy"], "Indices") == "8")
        check("input_interpolation_disabled", prop(blocks["Scenario_Input"], "Interpolate") == "off")
        check("initial_energy_configurable", prop(blocks["TES_Energy_Memory"], "InitialCondition") == "dchr_E0_v24")
        charts = [ET.fromstring(zipped.read(name)) for name in zipped.namelist()
                  if name.startswith("simulink/stateflow/chart_") and name.endswith(".xml")]
        candidates = [c for c in charts if prop(c, "name") == "Thermal_Dispatch"]
        check("single_operational_stateflow_chart", len(candidates) == 1)
        chart = candidates[0]
        check("discrete_chart_updates", prop(chart, "updateMethod") == "DISCRETE")
        check("common_sampling_interval", prop(chart, "sampleTime") ==
              prop(blocks["TES_Energy_Memory"], "SampleTime") ==
              prop(blocks["Scenario_Input"], "SampleTime") == "dchr_dt_v24")
        children = chart.find("Children")
        states = [s for s in children.findall("state") if prop(s, "type") == "OR_STATE"]
        names = ["IDLE", "HEAT_RECOVERY", "STORAGE_CHARGE", "STORAGE_DISCHARGE", "BACKUP", "UNMET_DEMAND"]
        state_modes = {}
        for state in states:
            label = prop(state, "labelString")
            name = label.splitlines()[0]
            if name in names:
                code = names.index(name)
                state_modes[state.attrib["SSID"]] = code
                check(name + "_entry_and_during_allocate_ports",
                      label == name + "\nen,du:\ny=stateflow_allocate_v24(" + str(code) + ",u,E,p);")
        check("six_required_operating_states", len(states) == len(state_modes) == 6)
        state_edges, initial_edges, defaults = set(), set(), []
        transitions = children.findall("transition")
        for transition in transitions:
            source = prop(transition.find("src"), "SSID")
            target = prop(transition.find("dst"), "SSID")
            guard = prop(transition, "labelString")
            if target in state_modes:
                check("mode_guard_destination_" + transition.attrib["SSID"],
                      guard == "[stateflow_choose_mode_v24(u,E,p)==" + str(state_modes[target]) + "]")
                if source in state_modes:
                    state_edges.add((state_modes[source], state_modes[target]))
                else:
                    initial_edges.add((source, state_modes[target]))
            elif not source:
                defaults.append((target, guard))
        check("all_30_guarded_changes", state_edges == {(a, b) for a in range(6) for b in range(6) if a != b})
        check("six_guarded_startup_choices", len(initial_edges) == 6 and
              {m for _, m in initial_edges} == set(range(6)) and len({s for s, _ in initial_edges}) == 1)
        check("single_default_into_startup_junction", len(defaults) == 1 and defaults[0][1] == "" and
              {defaults[0][0]} == {s for s, _ in initial_edges} and len(transitions) == 37)
        for helper in ["stateflow_choose_mode_v24", "stateflow_allocate_v24", "stateflow_contract_gate_v24"]:
            scripts = [prop(e, "script") for c in charts for e in c.iter("eml")
                       if helper in prop(e, "script").partition("\n")[0]]
            expected = (model.parent / (helper + ".m")).read_text(encoding="utf-8")
            check("embedded_" + helper + "_matches_reviewed_source", len(scripts) == 1 and scripts[0] == expected)
        hp_charts = [c for c in charts if prop(c, "name") == "Verified_HP_Component"]
        check("single_host_hp_adapter", len(hp_charts) == 1)
        hp_script = [prop(e, "script") for e in hp_charts[0].iter("eml")]
        check("hp_adapter_passes_model_dt_into_versioned_runtime_domain_function", any(
            "u=dchr_stateflow_hp_v24(x,E,p,h,model_dt);" in script and
            "coder.extrinsic('dchr_stateflow_hp_v24');" in script for script in hp_script))
    return result(checks)


def self_test(spec):
    records = [dict(id=c["id"], expected_identifier=c["expected_identifier"],
                    simulation_attempted=True, rejected=True, actual_identifier="Simulink:Engine:MATLABFcnError",
                    cause_identifiers=[c["expected_identifier"]], tick=c["tick"],
                    accepted_invalid_trace=False, message="Synthetic fixture; no Simulink executed")
               for c in spec["cases"]]
    checks = [dict(name="synthetic_complete_negative_schema", passed=verify_rejections(spec, records)["failed"] == 0)]
    checks.append(dict(name="synthetic_matlab_wrapped_negative_schema",
                       passed=verify_rejections(spec, {"cases": len(records), "records": records})["failed"] == 0))
    for field, value in [("simulation_attempted", False), ("rejected", False),
                         ("accepted_invalid_trace", True), ("cause_identifiers", []),
                         ("tick", 99), ("expected_identifier", "unrelated")]:
        broken = copy.deepcopy(records)
        broken[0][field] = value
        checks.append(dict(name="reject_corrupted_" + field,
                           passed=verify_rejections(spec, broken)["failed"] > 0))
    checks.append(dict(name="reject_missing_case", passed=verify_rejections(spec, records[:-1])["failed"] > 0))
    checks.append(dict(name="reject_duplicate_case", passed=verify_rejections(spec, records + records[:1])["failed"] > 0))
    return result(checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, default=HERE / "stateflow_domain_cases_v24.json")
    parser.add_argument("--model", type=Path)
    parser.add_argument("--rejections", type=Path)
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--clock-trace", type=Path)
    parser.add_argument("--vectors", type=Path, default=HERE / "stateflow_qa_vectors_v22.csv")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    output = dict(version="0.24", scope=__doc__, primary_paper_replication=False,
                  equipment_validation=False, spec_sha256=sha(args.spec), verifier_sha256=sha(Path(__file__)),
                  reused_valid_trace_oracle=str(Path(numeric_v22.__file__).resolve()),
                  reused_valid_trace_oracle_sha256=sha(Path(numeric_v22.__file__)))
    if args.self_test:
        output["self_test"] = self_test(spec)
    if args.model:
        output["structure"] = verify_structure(args.model)
        output["model_sha256"] = sha(args.model)
        output["source_hashes"] = {p.name: sha(p) for p in args.model.parent.glob("*v24.m")}
    if args.rejections:
        output["runtime_rejections"] = verify_rejections(spec, json.loads(args.rejections.read_text(encoding="utf-8")))
        output["rejections_sha256"] = sha(args.rejections)
    if args.trace:
        output["trace_qa"] = numeric_v22.verify_trace(numeric_v22.read_csv(args.trace), numeric_v22.read_csv(args.vectors))
        output["trace_sha256"] = sha(args.trace)
        output["vectors_sha256"] = sha(args.vectors)
    if args.clock_trace:
        output["clock_probe_qa"] = verify_clock_probe(args.clock_trace)
        output["clock_probe_trace_sha256"] = sha(args.clock_trace)
    output["failed"] = sum(v.get("failed", 0) for v in output.values() if isinstance(v, dict))
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: ({q: w for q, w in v.items() if q != "assertions"} if isinstance(v, dict) else v)
                      for k, v in output.items()}, indent=2, allow_nan=False))
    raise SystemExit(bool(output["failed"]))


if __name__ == "__main__":
    main()
