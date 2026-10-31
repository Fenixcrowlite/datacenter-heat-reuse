"""Independent Python reproduction of early MATLAB dchr.simulate_system_v2.
Source provenance: run_experiment_v2.m, default_config[_v2].m and +dchr/+components.
No MATLAB execution or claim of Simulink equivalence. CSV values are synthetic.
"""
from __future__ import annotations
import csv, hashlib, json, math
from pathlib import Path

ROOT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
HERE=Path(__file__).resolve().parent
INPUT=ROOT/"results"/"warm45_storage100_timeseries.csv"
ORACLE=ROOT/"results"/"best_scenario_v2_timeseries.csv"
SUMMARY=ROOT/"results"/"scenario_summary_v2.csv"
OUTPUT=HERE/"Warm45_Storage100_v2_PYTHON_REPLAY.csv"
RESULT=HERE/"C37_REPLAY_RESULTS.json"
COLS=("Time,Tout_C,IT_Util,IT_MW,DC_Total_MW,Heat_Demand_MW,DH_Supply_C,"
      "DH_Return_C,Source_Heat_Available_MW,HX_Heat_to_HP_MW,HX_Rejected_MW,"
      "Temperature_Lift_K,COP,HP_Heat_MW,HP_Heat_Used_MW,HP_Electric_MW,"
      "HP_Source_Used_MW,Storage_Charge_MW,Storage_Discharge_MW,Storage_E_MWh,"
      "Gas_Heat_MW,Curtailed_HP_Heat_MW,Useful_Heat_Exergy_MW").split(",")

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1048576),b""): h.update(block)
    return h.hexdigest()

def clamp(x,lo,hi): return min(hi,max(lo,x))
def compute(row,energy,scenario):
    """One-hour source-code-equivalent dispatch, no external packages."""
    tout=float(row["Tout_C"])
    it=float(row["IT_MW"])
    demand=float(row["Heat_Demand_MW"])
    if scenario=="Warm45_Storage100":
        src_temp,recovery,supply_min,supply_max,return_min,return_max=45.,.90,55.,80.,35.,50.
    elif scenario=="Liquid35_LowTempDH":
        src_temp,recovery,supply_min,supply_max,return_min,return_max=35.,.85,45.,65.,30.,40.
    else: raise ValueError("unknown scenario")
    f=clamp((16.-tout)/(16.-(-12.)),0.,1.)
    supply=supply_min+f*(supply_max-supply_min)
    ret=return_min+f*(return_max-return_min)
    source=max(0.,it)*recovery
    hx=max(0.,min(source*.97,20.))
    rejected=max(0.,source-hx)
    evaporator=src_temp-3.
    lift=max(1.,supply-evaporator)
    th=supply+273.15
    tc=evaporator+273.15
    cop_nom=clamp(.45*th/max(1.,th-tc),2.2,7.)
    potential=min(12.,max(0.,hx*cop_nom/max(1e-6,cop_nom-1.)))
    direct=min(potential,demand)
    surplus=max(0.,potential-demand)
    deficit=max(0.,demand-potential)
    e0=max(0.,energy*(1.-1e-4))
    charge=discharge=0.
    if surplus>0.:
        room=max(0.,100.-e0)
        charge=min(surplus,5.,room/.95)
        next_e=e0+.95*charge
    elif deficit>0.:
        discharge=min(deficit,5.,e0*.95)
        next_e=max(0.,e0-discharge/.95)
    else: next_e=e0
    used=direct+charge
    gas=max(0.,demand-direct-discharge)
    curtailed=max(0.,potential-used)
    plr=clamp(used/12.,0.,1.)
    cop=clamp(cop_nom*(1.-.08*max(0.,1.-plr)),2.2,7.)
    electric=used/max(math.ulp(1.0),cop)
    source_used=max(0.,used-electric)
    useful=direct+discharge
    exergy=useful*max(0.,1.-(10.+273.15)/(supply+273.15))
    out=dict(
        Time=row["Time"],Tout_C=tout,IT_Util=float(row["IT_Util"]),IT_MW=it,
        DC_Total_MW=float(row["DC_Total_MW"]),Heat_Demand_MW=demand,
        DH_Supply_C=supply,DH_Return_C=ret,Source_Heat_Available_MW=source,
        HX_Heat_to_HP_MW=hx,HX_Rejected_MW=rejected,Temperature_Lift_K=lift,
        COP=cop,HP_Heat_MW=potential,HP_Heat_Used_MW=used,HP_Electric_MW=electric,
        HP_Source_Used_MW=source_used,Storage_Charge_MW=charge,
        Storage_Discharge_MW=discharge,Storage_E_MWh=energy,Gas_Heat_MW=gas,
        Curtailed_HP_Heat_MW=curtailed,Useful_Heat_Exergy_MW=exergy)
    return out,next_e

def load_csv(path):
    with path.open(newline="",encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def run_scenario(inputs,scenario):
    energy=0.
    for row in inputs:
        out,energy=compute(row,energy,scenario)
        yield out
    if abs(energy)>1e-7: raise AssertionError(f"nonzero year-end energy {energy}")

def compare_oracle(inputs,oracle):
    assert len(inputs)==len(oracle)==8760
    mismatches=[]
    worst=(0.,None,None)
    comparisons=0
    for k,(i,expected) in enumerate(zip(inputs,oracle)):
        actual=compute(i, float(expected["Storage_E_MWh"]), "Liquid35_LowTempDH")[0]
        # State uses the oracle's pre-step energy. A separate rolling-state check follows.
        for field in COLS:
            if field=="Time":
                if actual[field]!=expected[field]: mismatches.append([k,field,"time"])
                continue
            delta=abs(actual[field]-float(expected[field]))
            comparisons+=1
            if delta>worst[0]: worst=(delta,k,field)
            if delta>2e-9: mismatches.append([k,field,delta])
    energy=0.
    rolling_worst=0.
    for k,row in enumerate(inputs):
        actual,energy=compute(row,energy,"Liquid35_LowTempDH")
        rolling_worst=max(rolling_worst,abs(actual["Storage_E_MWh"]-float(oracle[k]["Storage_E_MWh"])))
    if mismatches or rolling_worst>2e-9:
        raise AssertionError(f"Oracle mismatch {mismatches[:5]} rolling={rolling_worst}")
    return {"hourly_comparisons":comparisons,"max_absolute_field_error":worst[0],
            "max_storage_state_error_MWh":rolling_worst,"oracle_rows":len(oracle)}

def main():
    inputs=load_csv(INPUT)
    oracle=load_csv(ORACLE)
    if len(inputs)!=8760 or len(oracle)!=8760: raise AssertionError("invalid input row count")
    for k,(a,b) in enumerate(zip(inputs,oracle)):
        for field in ("Time","Tout_C","IT_Util","IT_MW","DC_Total_MW","Heat_Demand_MW"):
            if a[field]!=b[field]:
                raise AssertionError(f"shared synthetic inputs differ {k} {field}")
    oracle_qa=compare_oracle(inputs,oracle)
    rows=list(run_scenario(inputs,"Warm45_Storage100"))
    with OUTPUT.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=COLS)
        writer.writeheader()
        for row in rows: writer.writerow(row)
    summary={x["Scenario"]:x for x in load_csv(SUMMARY)}
    expected=summary["Warm45_Storage100"]
    sums={
        "HeatDemand_MWh":math.fsum(x["Heat_Demand_MW"] for x in rows),
        "ReusedHeat_MWh":math.fsum(x["HP_Heat_Used_MW"]-x["Storage_Charge_MW"]+x["Storage_Discharge_MW"] for x in rows),
        "HPElectric_MWh":math.fsum(x["HP_Electric_MW"] for x in rows),
        "GasHeat_MWh":math.fsum(x["Gas_Heat_MW"] for x in rows),
        "CurtailedHPHeat_MWh":math.fsum(x["Curtailed_HP_Heat_MW"] for x in rows),
    }
    keymap={"HeatDemand_MWh":"HeatDemand_MWh","ReusedHeat_MWh":"ReusedHeat_MWh",
            "HPElectric_MWh":"HPElectric_MWh","GasHeat_MWh":"GasHeat_MWh",
            "CurtailedHPHeat_MWh":"CurtailedHPHeat_MWh"}
    errors={k:abs(v-float(expected[keymap[k]])) for k,v in sums.items()}
    if max(errors.values())>2e-7: raise AssertionError(f"MATLAB summary mismatch {errors}")
    coverage=sums["ReusedHeat_MWh"]/sums["HeatDemand_MWh"]
    if abs(coverage-float(expected["Coverage"]))>1e-11: raise AssertionError("coverage mismatch")
    result={
        "scope":"DCHR_C37_V2_PYTHON_REPLAY","scenario":"Warm45_Storage100",
        "simulation_engine":"Python port of MATLAB source; MATLAB NOT run",
        "source_model":"dchr.simulate_system_v2, energy-only 100 MWh, no physical stratification",
        "synthetic_data":True,"hours":len(rows),"source_v1_csv_sha256":sha(INPUT),
        "source_v2_oracle_sha256":sha(ORACLE),"source_v2_summary_sha256":sha(SUMMARY),
        "oracle_validation":oracle_qa,"summary_errors_MWh":errors,"annual":sums,
        "coverage":coverage,"output_file":OUTPUT.name,"output_sha256":sha(OUTPUT),
        "v85_stateflow_parity":False,"physical_validation":False,"primary_source_signoffs":0}
    with RESULT.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
    print(json.dumps({"result":"PASS","hours":len(rows),"oracle":oracle_qa,
        "summary_max_error_MWh":max(errors.values()),"gas_MWh":sums["GasHeat_MWh"],
        "output_sha256":result["output_sha256"]},ensure_ascii=False))
if __name__=="__main__":main()
