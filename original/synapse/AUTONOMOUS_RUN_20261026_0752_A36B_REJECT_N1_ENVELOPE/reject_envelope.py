"""Source-backed synthetic REJECT redundancy N-1 envelope, no hardware control."""
import csv
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
A36=HERE.parent/"AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"
MODEL=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\matlab\pool_redundancy_v07\fyzikalne_ochrany_v07.txt")
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def capacity_from_model():
    text=MODEL.read_text(encoding="utf-8-sig")
    # This is a synthetic scenario rating in the v07 source, NOT certified equipment.
    assert "scenarove hodnoty" in text, "MISSING_SYNTHETIC_DISCLAIMER"
    a=re.search(r"\bmainCap\s*=\s*(\d+)\s*\*",text)
    b=re.search(r"\bbackupCap\s*=\s*(\d+)\s*\*",text)
    if not a or not b:
        raise RuntimeError("CAPACITY_NOT_EXPLICIT_IN_V07")
    return int(a.group(1)),int(b.group(1))

def evaluate(required, cap):
    excess=[max(0.0,x-cap) for x in required]
    return {
        "capacity_kW":cap/1000,
        "unsafe_intervals":sum(x>1e-7 for x in excess),
        "unsafe_hours":round(sum(x>1e-7 for x in excess)*0.25,3),
        "unhandled_kWh":round(sum(excess)*0.25/1000,6),
        "max_excess_kW":round(max(excess)/1000,6),
        "max_required_kW":round(max(required)/1000,6),
    }

def main():
    main_cap,backup_cap=capacity_from_model()
    assert main_cap==180000 and backup_cap==150000, "V07_CAP_CHANGED_REVIEW_REQUIRED"
    a36=json.loads((A36/"RESULTS.json").read_text(encoding="utf8"))
    for n,entry in a36["scenarios"].items():
        if sha(A36/entry["output"])!=entry["output_sha256"]:
            raise RuntimeError("A36_INPUT_CHANGED "+n)
    cases={"both_available":main_cap+backup_cap,"main_only":main_cap,
           "backup_only":backup_cap,"neither_available":0}
    results={}
    for scenario,meta in a36["scenarios"].items():
        with (A36/meta["output"]).open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        if len(rows)!=672:
            raise RuntimeError("EXPECTED_672")
        required=[float(x["Q_reject_required_W"]) for x in rows]
        results[scenario]={label:evaluate(required,cap) for label,cap in cases.items()}
    report={
        "source_v07":str(MODEL),"source_v07_sha256":sha(MODEL),
        "source_v08_sha256":a36["source_sha256"],
        "a36_results_sha256":sha(A36/"RESULTS.json"),
        "main_reject_synthetic_W":main_cap,
        "backup_reject_synthetic_W":backup_cap,
        "disclaimer":"V07 explicitly calls capacities SCENARIO values, NOT certified hardware.",
        "physical_release_allowed":False,
        "IT_shedding_and_TES_dynamics":"NOT RECOMPUTED",
        "scenarios":results,
    }
    (HERE/"RESULTS_N1.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    with (HERE/"N1_ENVELOPE.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.writer(f)
        w.writerow(["scenario","availability","capacity_kW","unsafe_intervals",
                    "unsafe_hours","unhandled_kWh","max_excess_kW","max_required_kW"])
        for s,cases in results.items():
            for availability,values in cases.items():
                w.writerow([s,availability]+[values[k] for k in (
                    "capacity_kW","unsafe_intervals","unsafe_hours","unhandled_kWh",
                    "max_excess_kW","max_required_kW")])
    print(json.dumps({
        "v07_sha256":report["source_v07_sha256"],
        "caps_kW":[main_cap/1000,backup_cap/1000],
        "both_off":results["both_off"],
    },ensure_ascii=False,indent=2))
if __name__=="__main__":
    main()
