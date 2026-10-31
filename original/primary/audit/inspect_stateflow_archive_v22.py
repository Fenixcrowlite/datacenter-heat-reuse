"""Read-only structural/provenance review of the generated v22 SLX archive.

Independent of MATLAB/Stateflow runtime APIs and the dispatch QA oracle.
This verifies generated artifact structure and copied helper source, not execution.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "matlab/simulink/DCHR_Dispatch_Stateflow_v22.slx"
HERE = ROOT / "matlab/simulink"
MODES = ["IDLE", "HEAT_RECOVERY", "STORAGE_CHARGE", "STORAGE_DISCHARGE",
         "BACKUP", "UNMET_DEMAND"]


def prop(element, name, default=""):
    return element.findtext(f"P[@Name='{name}']", default=default)


def main():
    checks = []

    def check(name, ok, detail):
        checks.append(dict(name=name, passed=bool(ok), detail=detail))

    with ZipFile(MODEL) as archive:
        charts = [(member, ET.fromstring(archive.read(member)))
                  for member in archive.namelist()
                  if member.startswith("simulink/stateflow/chart_") and member.endswith(".xml")]
        system = ET.fromstring(archive.read("simulink/systems/system_root.xml"))
    chart_matches = [(member, chart) for member, chart in charts
                     if prop(chart, "name") == "Thermal_Dispatch"]
    check("unique_actual_dispatch_chart", len(chart_matches) == 1,
          f"Dispatch chart matches: {len(chart_matches)}")
    if len(chart_matches) != 1:
        raise RuntimeError("Expected one actual generated dispatch chart")
    member, chart = chart_matches[0]
    children = chart.find("Children")
    operating = [state for state in children.findall("state")
                 if prop(state, "type") == "OR_STATE"]
    labels = [prop(state, "labelString") for state in operating]
    names = [label.splitlines()[0] for label in labels]
    check("six_expected_operating_states", len(operating) == 6 and sorted(names) == sorted(MODES), names)
    for mode, name in enumerate(MODES):
        expected = f"{name}\nen,du:\ny=stateflow_allocate_v22({mode},u,E,p);"
        check(f"{name}_executes_mode_allocation", expected in labels, expected)
    transitions = children.findall("transition")
    guards = [prop(transition, "labelString") for transition in transitions]
    check("37_transitions_36_guarded", len(transitions) == 37 and
          sum("stateflow_choose_mode_v22" in guard for guard in guards) == 36,
          dict(transitions=len(transitions), guarded=sum(bool(guard) for guard in guards)))
    check("no_unconditional_test_guards", not any("[true]" in g or "[false]" in g for g in guards),
          "One unlabeled default transition is distinct from unconditional test guards.")
    mode_by_id = {state.get("SSID"): MODES.index(prop(state, "labelString").splitlines()[0])
                  for state in operating}
    junctions = children.findall("junction")
    junction_id = junctions[0].get("SSID") if len(junctions) == 1 else None
    actual_pairs = {(t.findtext("src/P[@Name='SSID']"), t.findtext("dst/P[@Name='SSID']"))
                    for t in transitions if prop(t, "labelString")}
    expected_pairs = {(src, dst) for src in mode_by_id for dst in mode_by_id if src != dst}
    expected_pairs |= {(junction_id, dst) for dst in mode_by_id}
    check("all_mode_changes_and_initial_choices", len(junctions) == 1 and actual_pairs == expected_pairs,
          "All 30 ordered mode changes and six initial choices exist, with no guarded duplicate pairs.")
    check("guards_select_destination_mode", all(
        prop(t, "labelString") == f"[stateflow_choose_mode_v22(u,E,p)=={mode_by_id[t.findtext('dst/P[@Name=\"SSID\"]')]}]"
        for t in transitions if prop(t, "labelString") and t.findtext("dst/P[@Name='SSID']") in mode_by_id),
        "Each guarded transition selects the mode allocated by its destination operating state.")
    check("discrete_parameterized_sample_time", prop(chart, "updateMethod") == "DISCRETE"
          and prop(chart, "sampleTime") == "dchr_dt_v22",
          dict(update=prop(chart, "updateMethod"), sample=prop(chart, "sampleTime")))
    for filename in ["stateflow_choose_mode_v22.m", "stateflow_allocate_v22.m"]:
        source = (HERE / filename).read_text(encoding="utf-8")
        embedded = [state.findtext("eml/P[@Name='script']", default="")
                    for state in children.findall("state")]
        check(f"embedded_{filename}_equals_source", source in embedded,
              "XML normalizes newlines; compare exact normalized Unicode source including final newline.")
    blocks = {block.get("Name"): block for block in system.findall("Block")}
    edges = {(prop(line, "Src"), node.text) for line in system.findall("Line")
             for node in line.findall(".//P[@Name='Dst']")}

    def edge(src_name, dst_name, inport=1):
        return (f"{blocks[src_name].get('SID')}#out:1",
                f"{blocks[dst_name].get('SID')}#in:{inport}") in edges

    check("chart_output_feedback_to_TES_memory", edge("Thermal_Dispatch", "Next_TES_Energy")
          and edge("Next_TES_Energy", "TES_Energy_Memory")
          and edge("TES_Energy_Memory", "Thermal_Dispatch", 2)
          and edge("TES_Energy_Memory", "Verified_HP_Component", 2),
          "Chart E_next feeds Unit Delay, and its E_start feeds both chart and HP request.")
    check("memory_parameters_and_energy_index", blocks["TES_Energy_Memory"].get("BlockType") == "UnitDelay"
          and prop(blocks["TES_Energy_Memory"], "InitialCondition") == "dchr_E0_v22"
          and prop(blocks["TES_Energy_Memory"], "SampleTime") == "dchr_dt_v22"
          and prop(blocks["Next_TES_Energy"], "Indices") == "8",
          "Memory stores allocation output 8, with parameterized initial energy and sample duration.")
    check("input_HP_chart_numeric_trace_path", edge("Scenario_Input", "Verified_HP_Component")
          and edge("Verified_HP_Component", "Thermal_Dispatch")
          and edge("Thermal_Dispatch", "Dispatch_Trace"),
          "No substitute controller lies on the scenario-to-chart-to-trace signal path.")
    model_hash = hashlib.sha256(MODEL.read_bytes()).hexdigest()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    failed = sum(not check["passed"] for check in checks)
    payload = dict(version="0.22", timestamp_utc=stamp,
                   scope="Independent ZIP/XML generated-model structure and source provenance only",
                   model_file=str(MODEL.relative_to(ROOT)).replace("\\", "/"), model_sha256=model_hash,
                   dispatch_xml_member=member, total=len(checks), passed=len(checks)-failed, failed=failed,
                   matlab_executed_by_this_inspection=False, physical_validation=False,
                   primary_source_verified=False, checks=checks,
                   source_sha256={filename: hashlib.sha256((HERE / filename).read_bytes()).hexdigest()
                                  for filename in ["stateflow_choose_mode_v22.m", "stateflow_allocate_v22.m"]})
    report = ROOT / "audit" / f"stateflow_archive_review_v22_{stamp}.json"
    log = ROOT / "automation/logs" / f"stateflow_archive_review_v22_{stamp}.log"
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.write_text(f"UTC {stamp}\n{payload['scope']}\n"
                   f"PASS {payload['passed']}/{payload['total']}; FAIL {failed}\n"
                   f"Model SHA256 {model_hash}\nReport {report.relative_to(ROOT)}\n", encoding="utf-8")
    print(json.dumps(dict(passed=payload["passed"], total=payload["total"], failed=failed,
                          report=str(report.relative_to(ROOT)).replace("\\", "/"),
                          log=str(log.relative_to(ROOT)).replace("\\", "/")), indent=2))
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
