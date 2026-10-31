# -*- coding: utf-8 -*-
"""Read-only audit of the concurrent pool workstream outputs; write only our lane."""
from pathlib import Path
import json
from benchmark_calculator import calculate, Inputs, SK_POOL_MAX_C

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
CURRENT=ROOT/"results"/"pool_500m3_v01"
py_json=CURRENT/"vysledky_bazen_500m3.json"
sl_json=CURRENT/"simulink_scenare_SK.json"
if not py_json.exists() or not sl_json.exists():
    raise FileNotFoundError("Other chat's output unavailable; no synthetic QA pass is assumed")
py=json.loads(py_json.read_text(encoding="utf-8-sig"))
sl=json.loads(sl_json.read_text(encoding="utf-8-sig"))
params=py["params"]
p_cases=py["cases"]
s_cases=sl
calc=calculate(Inputs(target_C=28,switch_off_C=28.2))
checks=[]
def check(name,status,evidence,action):
    checks.append({"name":name,"status":status,"evidence":evidence,"required_action":action})
check("pool geometry","PASS_GEOMETRIC_ONLY",
    {"m3":params["V_m3"],"surface_m2":params["A_m2"],"vol_calculator_m3":calc["pool"]["volume_m3"]},
    "Classify 25x12.5x1.6 geometry against selected public-use, depth, lane and water-treatment requirements")
check("ideal heatup energy","PASS_DIMENSIONAL",
    {"other_chat_MWh":py["E_16_to_28_MWh"],"independent_MWh":calc["pool"]["ideal_heatup_MWh"]},
    "Use for ideal lower-bound heatup only")
check("existing thermostatic limit","NONCOMPLIANT_SCREENING",
    {"setpoint_C":params["Tset_C"],"existing_OFF_C":28.2,"published_limit_C":SK_POOL_MAX_C},
    "Apply max-temp safety guard below 28 C with sensor/inertia allowance after legal-version review")
exc_py=[{"case":r["name"],"last_C":r["T_end_C"]} for r in p_cases if r["T_end_C"]>SK_POOL_MAX_C]
exc_sl=[{"case":r["scenar"],"last_C":r["teplota_na_konci_C"]} for r in s_cases if r["teplota_na_konci_C"]>SK_POOL_MAX_C]
check("logged final-temperature exceedances",
      "FAIL" if exc_py or exc_sl else "PASS_FINAL_SAMPLES_ONLY",
      {"Python_end_over_28":exc_py,"Simulink_end_over_28":exc_sl},
      "Add high-rate max-over-horizon probe and interlock, do not rely on endpoint tests")
py_lookup={r["name"]:r for r in p_cases}
alignment=[]
for s in s_cases:
    p=py_lookup.get(s["scenar"])
    if p is None:continue
    alignment.append({
        "case":s["scenar"],
        "time_to_28_delta_minutes":round((s["prvy_dosiahnuty_28C_h"]-p["target_h"])*60,3),
        "seven_day_heat_delta_MWh":round(s["dodane_teplo_MWh"]-p["heat_MWh"],6),
        "end_temperature_delta_C":round(s["teplota_na_konci_C"]-p["T_end_C"],6)})
check("Python versus Simulink scenario bridge","PASS_NUMERIC_COMPARISON_NOT_CALIBRATION",alignment,
    "Agree tolerances for solver, hysteresis timing and original code's interpolation")
check("PUE external benchmark","SCENARIO_NOT_MEASURED",
    {"model_pue":params["PUE"],"uptime_2026_mean_pue":1.52,
     "IT_MW_at_utilization":calc["datacentre"]["IT_MW"],
     "model_annual_EDC_MWh":calc["datacentre"]["annual_EDC_MWh"],
     "market_PUE_same_IT_EDC_MWh":calc["datacentre"]["reference_PUE_2026_EDC_MWh"]},
    "Treat PUE 1.2 as high-efficiency scenario and 1.52 survey mean as separate case")
check("pool envelope & compressor","UNVERIFIED_REAL_DATA",
    {"loss_avg_kW":py["holding_24h_average_kW"],"COP":params["COP"],
     "cover_evap_reduction":params["cover_evap"]},
    "Acquire actual hall RH, cover performance, manufacturer HP COP map, insulation UAs, heat exchanger performance")
report={"as_of":"2026-10-23","scope":"read-only concurrent-workstream audit",
    "confidence":"software comparison against simulated results, not real-world validation",
    "inputs":[str(py_json),str(sl_json)],"checks":checks,
    "critical_count":sum(x["status"].startswith(("FAIL","NONCOMPLIANT")) for x in checks)}
target=HERE/"pool_existing_QA_20261023.json"
if target.exists():raise FileExistsError(str(target))
target.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({"output":str(target),"critical":report["critical_count"],
 "end_gt28_python":len(exc_py),"end_gt28_simulink":len(exc_sl),
 "matched_models":len(alignment)},ensure_ascii=False))
