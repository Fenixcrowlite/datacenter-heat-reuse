"""Independent same-input annual comparison of early v1 and v2 Warm45_Storage100 traces."""
import csv,hashlib,json,math
from pathlib import Path
H=Path(__file__).resolve().parent
ROOT=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")/"results"
V1=ROOT/"warm45_storage100_timeseries.csv"
V2=H/"Warm45_Storage100_v2_PYTHON_REPLAY.csv"
def rows(path):
    with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def metrics(rr):
    return {
      "gas_MWh":math.fsum(float(r["Gas_Heat_MW"]) for r in rr),
      "hp_electric_MWh":math.fsum(float(r["HP_Electric_MW"]) for r in rr),
      "heat_demand_MWh":math.fsum(float(r["Heat_Demand_MW"]) for r in rr),
      "reused_heat_MWh":math.fsum(float(r["HP_Heat_Used_MW"])-float(r["Storage_Charge_MW"])+float(r["Storage_Discharge_MW"]) for r in rr),
      "storage_charge_MWh":math.fsum(float(r["Storage_Charge_MW"]) for r in rr),
      "storage_discharge_MWh":math.fsum(float(r["Storage_Discharge_MW"]) for r in rr),
    }
a=rows(V1);b=rows(V2)
assert len(a)==len(b)==8760
for k,(x,y) in enumerate(zip(a,b)):
    for col in ("Time","Tout_C","IT_Util","IT_MW","DC_Total_MW","Heat_Demand_MW"):
        assert x[col]==y[col],(k,col)
m1=metrics(a);m2=metrics(b)
d={k:m2[k]-m1[k] for k in m1}
assert abs(d["heat_demand_MWh"])<1e-8
assert abs(m1["gas_MWh"]-10413.415939069107)<1e-7
assert abs(m2["gas_MWh"]-10542.5482277889)<1e-7
out={"scope":"DCHR_C37_V1_V2_SAME_SYNTHETIC_INPUTS","rows":8760,
 "v1":{"file":V1.name,"sha256":sha(V1),"metrics":m1},
 "v2":{"file":V2.name,"sha256":sha(V2),"metrics":m2},
 "delta_v2_minus_v1":d,
 "interpretation":"Model architecture differences; not measured savings, not a controlled isolated causal effect",
 "stateflow_v85_parity":False,"physical_validation":False}
with (H/"C37_COMPARISON.json").open("x",encoding="utf-8") as f:json.dump(out,f,indent=2);f.write("\n")
print(json.dumps({"status":"PASS","v1_gas_MWh":m1["gas_MWh"],"v2_gas_MWh":m2["gas_MWh"],"delta_gas_MWh":d["gas_MWh"],"delta_electric_MWh":d["hp_electric_MWh"]}))
