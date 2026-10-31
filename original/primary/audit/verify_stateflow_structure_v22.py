"""Read-only independent inspection of the actual saved v22 SLX ZIP/XML.

This verifies connectivity and embedded controller provenance, not execution.
Actual simulation evidence is assessed separately by the trace verifier.
"""
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile


def prop(element, name, default=""):
    value = element.find("P[@Name='"+name+"']")
    return value.text if value is not None and value.text is not None else default


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    checks = []

    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))

    with ZipFile(args.model) as zipped:
        root = ET.fromstring(zipped.read("simulink/systems/system_root.xml"))
        blocks = {b.attrib["Name"]: b for b in root.findall("Block")}
        sids = {name: block.attrib["SID"] for name, block in blocks.items()}
        edges = set()
        for line in root.findall("Line"):
            src = prop(line, "Src")
            for dst in line.iter("P"):
                if dst.attrib.get("Name") == "Dst":
                    edges.add((src, dst.text))
        connections = [
            ("Scenario_Input", 1, "Verified_HP_Component", 1),
            ("Verified_HP_Component", 1, "Thermal_Dispatch", 1),
            ("TES_Energy_Memory", 1, "Verified_HP_Component", 2),
            ("TES_Energy_Memory", 1, "Thermal_Dispatch", 2),
            ("TES_and_Boiler_Parameters", 1, "Verified_HP_Component", 3),
            ("TES_and_Boiler_Parameters", 1, "Thermal_Dispatch", 3),
            ("HP_Parameters", 1, "Verified_HP_Component", 4),
            ("Thermal_Dispatch", 1, "Next_TES_Energy", 1),
            ("Next_TES_Energy", 1, "TES_Energy_Memory", 1),
            ("Thermal_Dispatch", 1, "Dispatch_Trace", 1),
            ("TES_Energy_Memory", 1, "Energy_Start_Trace", 1),
            ("Verified_HP_Component", 1, "HP_Trace", 1)]
        for source, sp, target, tp in connections:
            check(source+"_to_"+target,
                  (sids[source]+"#out:"+str(sp), sids[target]+"#in:"+str(tp)) in edges)
        check("discrete_energy_memory", blocks["TES_Energy_Memory"].attrib["BlockType"] == "UnitDelay")
        check("energy_feedback_index_8", prop(blocks["Next_TES_Energy"], "Indices") == "8")
        check("input_interpolation_disabled", prop(blocks["Scenario_Input"], "Interpolate") == "off")
        check("initial_energy_configurable", prop(blocks["TES_Energy_Memory"], "InitialCondition") == "dchr_E0_v22")
        charts = [ET.fromstring(zipped.read(name)) for name in zipped.namelist()
                  if name.startswith("simulink/stateflow/chart_") and name.endswith(".xml")]
        candidates = [c for c in charts if prop(c, "name") == "Thermal_Dispatch"]
        check("single_operational_chart", len(candidates) == 1)
        chart = candidates[0]
        check("discrete_chart_updates", prop(chart, "updateMethod") == "DISCRETE")
        check("common_sample_time", prop(chart, "sampleTime") ==
              prop(blocks["TES_Energy_Memory"], "SampleTime") ==
              prop(blocks["Scenario_Input"], "SampleTime") == "dchr_dt_v22")
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
                check(name+"_entry_during_allocates_ports",
                      label == name+"\nen,du:\ny=stateflow_allocate_v22("+str(code)+",u,E,p);")
        check("six_required_operating_states", len(states) == 6 and len(state_modes) == 6)
        transitions = children.findall("transition")
        state_edges, initial_edges, defaults = set(), set(), []
        for transition in transitions:
            source = prop(transition.find("src"), "SSID")
            target = prop(transition.find("dst"), "SSID")
            guard = prop(transition, "labelString")
            if target in state_modes:
                check("guard_targets_correct_mode_"+transition.attrib["SSID"],
                      guard == "[stateflow_choose_mode_v22(u,E,p)=="+str(state_modes[target])+"]")
                if source in state_modes:
                    state_edges.add((state_modes[source], state_modes[target]))
                else:
                    initial_edges.add((source, state_modes[target]))
            elif not source:
                defaults.append((target, guard))
        check("all_30_guarded_mode_changes", state_edges == {(a,b) for a in range(6) for b in range(6) if a != b})
        check("six_guarded_startup_choices", len(initial_edges) == 6 and
              {m for _, m in initial_edges} == set(range(6)) and len({s for s, _ in initial_edges}) == 1)
        check("single_default_to_initial_junction", len(defaults) == 1 and defaults[0][1] == "" and
              {defaults[0][0]} == {s for s, _ in initial_edges} and len(transitions) == 37)
        for helper in ["stateflow_choose_mode_v22", "stateflow_allocate_v22"]:
            scripts = [prop(e, "script") for e in children.iter("eml")
                       if helper in prop(e, "script").partition("\n")[0]]
            # Each helper appears in its own embedded function, not chart actions.
            expected = (args.model.parent/(helper+".m")).read_text(encoding="utf-8")
            check("embedded_"+helper+"_matches_source", len(scripts) == 1 and scripts[0] == expected)
    result = dict(scope="Independent saved-SLX static graph and embedded-source verification",
        model=str(args.model.resolve()), model_sha256=hashlib.sha256(args.model.read_bytes()).hexdigest(),
        verifier_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        checks=len(checks), passed=sum(c["passed"] for c in checks),
        failed=sum(not c["passed"] for c in checks), assertions=checks)
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps({k:v for k,v in result.items() if k != "assertions"}, indent=2))
    raise SystemExit(bool(result["failed"]))


if __name__ == "__main__":
    main()
