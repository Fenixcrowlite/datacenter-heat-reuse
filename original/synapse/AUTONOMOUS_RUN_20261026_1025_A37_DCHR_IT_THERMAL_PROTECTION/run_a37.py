"""Replay verified A36 synthetic 15-min demand through source-backed v07 IT thermal law."""
import csv, hashlib, json
from pathlib import Path
from thermal_n1 import CAPACITIES, POLICIES, simulate

HERE=Path(__file__).resolve().parent
A36=HERE.parent/"AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"
V08=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
V07=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_redundancy_v07\fyzikalne_ochrany_v07.txt")
FIELDS=["cas_h","fault_capacity_W","shed_W","Q_DC_after_shed_W",
        "reject_required_after_shed_W","reject_actual_W","unhandled_W",
        "passive_W","T_IT_start_C","T_IT_next_C","alarm_next","balance_residual_W"]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_inputs():
    meta=json.loads((A36/"RESULTS.json").read_text(encoding="utf8"))
    if sha(V08)!=meta["source_sha256"]:
        raise RuntimeError("V08_SHA_CHANGED")
    source_file=A36/meta["scenarios"]["both_off"]["output"]
    if sha(source_file)!=meta["scenarios"]["both_off"]["output_sha256"]:
        raise RuntimeError("A36_CSV_SHA_CHANGED")
    with V08.open(encoding="utf-8-sig",newline="") as f:
        original=list(csv.DictReader(f))
    with source_file.open(encoding="utf8",newline="") as f:
        dispatch=list(csv.DictReader(f))
    if len(original)!=672 or len(dispatch)!=672:
        raise RuntimeError("EXPECTED_672")
    merged=[]
    for i,(raw,derived) in enumerate(zip(original,dispatch)):
        if abs(float(raw["cas_h"])-float(derived["cas_h"]))>1e-9:
            raise RuntimeError(f"TIMESTAMP_MISMATCH_{i}")
        if float(raw["Q_IT_shed_W"])!=0:
            raise RuntimeError("BASELINE_IT_SHED_NOT_ZERO")
        merged.append({**derived,"Q_DC_eff_W":raw["Q_DC_eff_W"]})
    model=V07.read_text(encoding="utf-8-sig")
    for signature in ["dt=900; Cw=997*500*4182; Cit=8e6;",
                      "passive=max(0,2000*(Tit-30));",
                      "TitNext=max(30,Tit+dt*(Qunhandled-passive)/Cit);",
                      "mainCap=180000*", "backupCap=150000*",
                      "TitNext>=42"]:
        if signature not in model:
            raise RuntimeError("V07_EQUATION_CHANGED "+signature)
    return merged,meta,source_file

def main():
    merged,meta,source_file=read_inputs()
    report={
        "status":"SYNTHETIC_THERMAL_SENSITIVITY_ONLY",
        "physical_release_allowed":False,
        "hardware_control":False,
        "model":"v07 IT thermal capacitance/passive cooling recurrence, NOT full Stateflow",
        "assumptions":"1:1 IT shedding -> DC waste heat reduction -> reject demand reduction; unchanged A36 HX/HP/TES; hypothetical 40% shedding and 15kW/15min ramp",
        "limitations":["no IT service availability model","no heat pump/TES feedback","no calibrated hardware ratings","no protection latency or power dynamics","no real equipment safety conclusion"],
        "fault_hour":24.0,"dt_seconds":900,"samples":672,
        "source_v08_sha256":sha(V08),"source_v07_sha256":sha(V07),
        "source_a36_results_sha256":sha(A36/"RESULTS.json"),
        "source_a36_both_off_sha256":sha(source_file),
        "cases":{},
    }
    for label,cap in CAPACITIES.items():
        for name,policy in POLICIES.items():
            result=simulate(merged,policy,cap)
            filename=f"trace_{label}_{name}.csv"
            path=HERE/filename
            with path.open("w",encoding="utf8",newline="") as f:
                w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(result)
            alarms=[r["cas_h"] for r in result if r["alarm_next"]]
            post=[r for r in result if r["cas_h"]>=24]
            report["cases"][f"{label}/{name}"]={
                "reject_capacity_after_fault_kW":cap/1000,
                "max_T_IT_C":round(max(r["T_IT_next_C"] for r in result),6),
                "first_alarm_hour":min(alarms) if alarms else None,
                "alarm_intervals":len(alarms),
                "shed_kWh":round(sum(r["shed_W"] for r in post)*0.25/1000,6),
                "unhandled_kWh":round(sum(r["unhandled_W"] for r in post)*0.25/1000,6),
                "max_shed_kW":round(max(r["shed_W"] for r in post)/1000,6),
                "max_balance_residual_W":max(abs(r["balance_residual_W"]) for r in result),
                "trace":filename,"trace_sha256":sha(path),
            }
    (HERE/"RESULTS_A37.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({k:{x:v[x] for x in ["max_T_IT_C","first_alarm_hour","alarm_intervals","shed_kWh","unhandled_kWh"]} for k,v in report["cases"].items()},ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
