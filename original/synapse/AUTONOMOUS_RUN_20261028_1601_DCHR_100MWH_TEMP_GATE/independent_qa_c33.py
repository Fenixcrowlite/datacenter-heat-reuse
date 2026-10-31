"""Independent Decimal thermodynamic check of 100MWh capacity definitions."""
from __future__ import annotations
import csv,hashlib,json,math
from decimal import Decimal,getcontext
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=H.parent.parent
SRC=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
MODEL=H.parent/"AUTONOMOUS_RUN_20261028_1451_DCHR_STRATIFIED_TANK_GATE"/"stratified_tank.py"
EXPECTED_SOURCE="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
EXPECTED_MODEL="e6a551b359823046c0623b1089920b20be4d5ffc915dade9694dff99b378e582"
getcontext().prec=40
D=Decimal
CHECKS=[]
def check(name,condition,detail):
    CHECKS.append({"name":name,"pass":bool(condition),"detail":detail})
    if not condition:raise AssertionError(name+": "+str(detail))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    r=json.loads((H/"C33_100MWH_GATE_RESULTS.json").read_text(encoding="utf-8"))
    check("source data SHA",sha(SRC)==EXPECTED_SOURCE,r["source_data_sha256"])
    check("source model SHA",sha(MODEL)==EXPECTED_MODEL,r["source_model_sha256"])
    with SRC.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        peak=max(D(row["DH_Supply_C"]) for row in reader)
    check("max DH supply independently recomputed",abs(peak-D(str(r["max_synthetic_dh_supply_c"])))<D("1e-10"),str(peak))
    check("four cases present",len(r["cases"])==4,len(r["cases"]))
    check("source is synthetic",r["synthetic_not_metered"] is True and r["physical_validation"] is False,True)
    check("no unsupported savings",r["incremental_gas_savings_verified"] is False and r["simulink_baseline_compared_dynamically"] is False,True)
    for case in r["cases"]:
        hot=D(str(case["hot_c"]))
        ref=D("35") if case["capacity_definition"]=="NOMINAL_RETURN_35C" else peak+D("3")
        volume=D(str(case["volume_m3"]))
        calculated=volume*D("1000")*D("4180")*(hot-ref)/D("3600000000")
        label=str(case["hot_c"])+"/"+case["capacity_definition"]
        check(label+" reference",abs(ref-D(str(case["reference_cold_c"])))<D("1e-10"),str(ref))
        check(label+" independent 100MWh capacity",abs(calculated-D("100"))<D("0.00000001"),str(calculated))
        radius=math.sqrt(float(volume)/(math.pi*10))
        area=2*math.pi*radius*10+2*math.pi*radius*radius
        ua=area*0.15/1000
        check(label+" UA geometry",abs(ua-case["ua_kw_per_k"])<1e-9,ua)
        check(label+" year3 energy balance",abs(case["year3_balance_residual_mwh"])<1e-5,case["year3_balance_residual_mwh"])
        check(label+" nonnegative thermal and electric",all(case[k]>=0 for k in ("year3_delivered_mwh","year3_added_electric_mwh","year3_loss_mwh","year3_charge_mwh")),True)
    for hot in (72.0,80.0):
        nominal=next(x for x in r["cases"] if x["hot_c"]==hot and x["capacity_definition"]=="NOMINAL_RETURN_35C")
        gate=next(x for x in r["cases"] if x["hot_c"]==hot and x["capacity_definition"]=="SUPPLY_GATE_MAX_PLUS_3K")
        ratio=(hot-35)/(hot-float(peak)-3)
        check(f"{hot}C ratio",abs(gate["volume_m3"]/nominal["volume_m3"]-ratio)<1e-10,ratio)
    result={"status":"PASS","passed":len(CHECKS),"failed":0,"checks":CHECKS,
        "source_data_sha256":sha(SRC),"source_model_sha256":sha(MODEL),
        "note":"Independent Decimal capacity math; dynamic model was tested separately in C31; no Simulink equivalence asserted."}
    (H/"QA_INDEPENDENT_C33.json").write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","checks":len(CHECKS),"peak_dh_c":str(peak)},ensure_ascii=False))
if __name__=="__main__":main()
