"""Independent QA for C37 Python replay. Does not import replay implementation."""
from __future__ import annotations
import csv,hashlib,json,math
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec=40
HERE=Path(__file__).resolve().parent
ROOT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
CSV=HERE/"Warm45_Storage100_v2_PYTHON_REPLAY.csv"
RES=HERE/"C37_REPLAY_RESULTS.json"
ORACLE=ROOT/"results"/"best_scenario_v2_timeseries.csv"
SUMMARY=ROOT/"results"/"scenario_summary_v2.csv"
D=Decimal
TOL=D("2e-8")
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):h.update(chunk)
    return h.hexdigest()
def check(name,cond):
    if not cond: raise AssertionError(name)
def load(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def main():
    data=json.loads(RES.read_text(encoding="utf-8"))
    rows=load(CSV); old=load(ORACLE); summ=load(SUMMARY)
    expected=next(x for x in summ if x["Scenario"]=="Warm45_Storage100")
    check("row_count",len(rows)==8760 and len(old)==8760)
    check("metadata",data["scenario"]=="Warm45_Storage100" and data["synthetic_data"] is True)
    check("source_integrity",sha(CSV)==data["output_sha256"] and sha(ORACLE)==data["source_v2_oracle_sha256"])
    check("not_shared_path",CSV.resolve()!=ORACLE.resolve())
    check("scenario_distinct",abs(float(expected["GasHeat_MWh"])-sum(float(x["Gas_Heat_MW"]) for x in old))>2000)
    check("columns",len(rows[0])==23 and "DH_Supply_C" in rows[0])
    check("model_scope",data["physical_validation"] is False and data["v85_stateflow_parity"] is False)
    check("no_primary_signoffs",data["primary_source_signoffs"]==0)
    sums={key:D(0) for key in ("Gas_Heat_MW","HP_Electric_MW","Heat_Demand_MW","Curtailed_HP_Heat_MW")}
    reused=D(0)
    balance_count=0
    max_balance=D(0)
    prev_time=None
    for k,r in enumerate(rows):
        for key in r:
            if key!="Time": check("finite_"+key,math.isfinite(float(r[key])))
        if prev_time is not None:check("unique_times",r["Time"]!=prev_time)
        prev_time=r["Time"]
        demand=D(r["Heat_Demand_MW"]);potential=D(r["HP_Heat_MW"])
        used=D(r["HP_Heat_Used_MW"]);charge=D(r["Storage_Charge_MW"])
        discharge=D(r["Storage_Discharge_MW"]);energy=D(r["Storage_E_MWh"])
        gas=D(r["Gas_Heat_MW"]);curt=D(r["Curtailed_HP_Heat_MW"])
        direct=used-charge
        check("nonnegative_flows",min(demand,potential,used,charge,discharge,energy,gas,curt)>=-TOL)
        check("capacity",energy<=D("100")+TOL)
        check("power_limits",charge<=D("5")+TOL and discharge<=D("5")+TOL)
        check("mutual_exclusion",charge<TOL or discharge<TOL)
        check("heat_balance",abs(demand-direct-discharge-gas)<TOL)
        check("curtail_balance",abs(potential-used-curt)<TOL)
        check("direct_bound",direct<=demand+TOL and direct<=potential+TOL)
        check("cop_bounds",D("2.2")-TOL<=D(r["COP"])<=D("7")+TOL)
        check("hp_electric_balance",abs(D(r["HP_Electric_MW"])*D(r["COP"])-used)<TOL)
        check("source_balance",abs(used-D(r["HP_Electric_MW"])-D(r["HP_Source_Used_MW"]))<TOL)
        check("hx_balance",abs(D(r["Source_Heat_Available_MW"])-D(r["HX_Heat_to_HP_MW"])-D(r["HX_Rejected_MW"]))<TOL)
        check("input_provenance",r["Time"]==old[k]["Time"] and abs(D(r["Tout_C"])-D(old[k]["Tout_C"]))<TOL)
        check("heat_demand_provenance",abs(demand-D(old[k]["Heat_Demand_MW"]))<TOL)
        next_e=D(rows[k+1]["Storage_E_MWh"]) if k+1<len(rows) else D(0)
        calc=max(D(0),energy*(D(1)-D("0.0001")))+D(".95")*charge-discharge/D(".95")
        diff=abs(calc-next_e)
        max_balance=max(max_balance,diff)
        check("storage_state_conservation",diff<TOL)
        balance_count+=1
        reused+=direct+discharge
        for key in sums:sums[key]+=D(r[key])
    check("annual_gas",abs(sums["Gas_Heat_MW"]-D(expected["GasHeat_MWh"]))<D("0.000001"))
    check("annual_electric",abs(sums["HP_Electric_MW"]-D(expected["HPElectric_MWh"]))<D("0.000001"))
    check("annual_demand",abs(sums["Heat_Demand_MW"]-D(expected["HeatDemand_MWh"]))<D("0.000001"))
    check("annual_curtail",abs(sums["Curtailed_HP_Heat_MW"]-D(expected["CurtailedHPHeat_MWh"]))<D("0.000001"))
    check("annual_reuse",abs(reused-D(expected["ReusedHeat_MWh"]))<D("0.000001"))
    check("annual_coverage",abs(reused/sums["Heat_Demand_MW"]-D(expected["Coverage"]))<D("1e-10"))
    result={"status":"PASS","hours":len(rows),"decimal_storage_balances":balance_count,
        "max_storage_balance_error_MWh":str(max_balance),
        "independent_annual_checks":6,
        "source_oracle_comparisons":data["oracle_validation"]["hourly_comparisons"],
        "qa_type":"independent Decimal CSV/energy balance + MATLAB summary parity",
        "no_matlab_run":True,"no_simulink_parity":True}
    out=HERE/"QA_INDEPENDENT_C37.json"
    with out.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2);f.write("\n")
    print(json.dumps(result))
if __name__=="__main__":main()
