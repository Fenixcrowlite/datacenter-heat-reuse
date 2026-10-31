"""Independent C98 output QA. Does not import C98 implementation."""
from __future__ import annotations
import csv,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
UP=D.parent/"AUTONOMOUS_RUN_20261030_1850_DCHR_C96_UA_NTU_PUMP_ENVELOPE"/"c96_ua_ntu_pool.py"
UP_SHA="c084e706fc79c635856df6ba6223c1fed1cb9b8c7c72c5aba0e67ae38b8700d9"

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(data,rows):
    n=0
    def ck(condition,message):
        nonlocal n
        if not condition:raise AssertionError(message)
        n+=1
    ck(data["schema"]=="C98_SYNTHETIC_UA_FEASIBILITY_V1","schema")
    ck(data["synthetic"] and not data["field_validated"] and not data["vendor_COP"],"provenance")
    ck(data["source_signoffs_added"]==0,"signoffs")
    ck(data["cases"]==8 and len(data["boundaries"])==8,"cases")
    ck(data["unique_simulations"]==len(rows)==127,"count")
    ck(data["hour_steps"]==127*8760,"steps")
    ck(sha(UP)==UP_SHA==data["upstream_C96_sha256"],"upstream")
    ck(sha(D/"C98_SWEEP.csv")==data["sweep_sha256"],"sha")
    bycase=defaultdict(list);keys=set()
    for r in rows:
        case=tuple(float(r[k]) for k in ("hot_in_C","hot_flow_kg_s","cold_in_C","COP_assumed"))
        ua=float(r["UA_kW_K"]);key=(case,round(ua,10))
        ck(key not in keys,"duplicate");keys.add(key)
        ck(all(math.isfinite(float(r[k])) for k in ("min_pool_C","hp_heat_MWh","hx_extracted_MWh","hp_electric_MWh","pump_electric_MWh","energy_residual_MWh")),"finite")
        ck(abs(float(r["energy_residual_MWh"]))<1e-7,"energy")
        ck(float(r["hx_extracted_MWh"])<=float(r["hp_heat_MWh"])+1e-7,"hx_hp")
        ck(float(r["hp_electric_MWh"])>=0 and float(r["pump_electric_MWh"])>=0,"electric")
        expected=float(r["min_pool_C"])>=27.5 and int(r["hours_below_27p5"])==0
        ck((r["feasible"]=="True")==expected,"feasible_flag")
        bycase[case].append(r)
    ck(len(bycase)==8,"case_groups")
    bracketed=0;no_feasible=0
    for b in data["boundaries"]:
        c=b["case"];case=tuple(float(c[k]) for k in ("hot_in_C","hot_flow_kg_s","cold_in_C","COP_assumed"))
        group=bycase[case]
        ck(len(group)>=8,"group_min")
        byua={round(float(r["UA_kW_K"]),10):r for r in group}
        coarse=[byua[round(float(ua),10)] for ua in data["UA_grid"]]
        vals=[r["feasible"]=="True" for r in coarse]
        ck(not any(a and not z for a,z in zip(vals,vals[1:])),"coarse_monotonic")
        ck(abs(float(coarse[-1]["min_pool_C"])-b["max_UA_min_pool_C"])<1e-9,"max_min")
        if b["status"]=="BRACKETED":
            bracketed+=1
            lo=b["bracket_fail_kW_K"];hi=b["bracket_pass_kW_K"]
            ck(lo<hi and hi/lo<1.004,"bracket_width")
            ck(byua[round(lo,10)]["feasible"]=="False","lo_fails")
            ck(byua[round(hi,10)]["feasible"]=="True","hi_passes")
        elif b["status"]=="NO_FEASIBLE_UA_IN_GRID":
            no_feasible+=1
            ck(not any(vals),"none_pass")
        else:raise AssertionError("unexpected status")
    ck(bracketed==7 and no_feasible==1,"status_counts")
    # Physical trend under identical source 35C, 0.5 kg/s, COP 2.2:
    cases=[b for b in data["boundaries"] if b["case"]["hot_in_C"]==35 and b["case"]["hot_flow_kg_s"]==0.5 and b["case"]["COP_assumed"]==2.2]
    cases.sort(key=lambda b:b["case"]["cold_in_C"])
    ck([x["case"]["cold_in_C"] for x in cases]==[15.,25.,32.],"cold_cases")
    ck(cases[0]["bracket_pass_kW_K"]<cases[1]["bracket_fail_kW_K"] and cases[2]["status"]=="NO_FEASIBLE_UA_IN_GRID","cold_sensitivity")
    return n

def main():
    data=json.loads((D/"C98_THRESHOLDS.json").read_text(encoding="utf-8"))
    with (D/"C98_SWEEP.csv").open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
    checks=validate(data,rows)
    corrupted=[dict(r) for r in rows]
    corrupted[0]["energy_residual_MWh"]="999"
    try:validate(data,corrupted)
    except AssertionError:negative_energy=True
    else:raise AssertionError("NEGATIVE_ENERGY_UNDETECTED")
    corrupted2=[dict(r) for r in rows]
    corrupted2[0]["feasible"]="False" if corrupted2[0]["feasible"]=="True" else "True"
    try:validate(data,corrupted2)
    except AssertionError:negative_flag=True
    else:raise AssertionError("NEGATIVE_FLAG_UNDETECTED")
    result={"status":"PASS","independent_assertions":checks,
            "rows_checked":len(rows),"case_groups":8,"bracketed":7,
            "no_feasible_grid":1,"negative_energy_detected":negative_energy,
            "negative_feasibility_detected":negative_flag,
            "upstream_sha256":sha(UP),"sweep_sha256":sha(D/"C98_SWEEP.csv")}
    with (D/"C98_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(result,indent=2))
if __name__=="__main__":main()
