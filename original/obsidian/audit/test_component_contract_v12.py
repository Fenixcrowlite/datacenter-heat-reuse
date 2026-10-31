"""Independent Python reference property gate v0.12.
Not a MATLAB execution and not validation against original publications.
Creates new versioned JSON evidence; never changes baseline models.
"""
from pathlib import Path
import importlib.util
import hashlib
import json
import math
import random
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("reference_physics_v07", ROOT/"audit/reference_physics_v07.py")
mod = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
P, step = mod.Parameters, mod.dispatch_step
rng = random.Random(12026)
checks = []
def check(name, predicate, detail=""):
    checks.append({"name":name,"pass":bool(predicate),"detail":detail})
    if not predicate:
        raise AssertionError(name+": "+detail)

p = P()
for i in range(3000):
    demand = rng.uniform(0,200)
    source = rng.uniform(0,50)
    cop = rng.uniform(1.01,12)
    e0 = rng.uniform(0,p.storage_capacity_mwh)
    s = step(p,demand,source,cop,e0)
    check_ok = lambda v: math.isfinite(v) and v >= -1e-8
    if not all(check_ok(v) for v in (s.hp_heat_mw,s.evaporator_mw,s.compressor_mw,
                  s.direct_mw,s.charge_mw,s.discharge_mw,s.boiler_mw,s.unmet_mw,s.storage_end_mwh)):
        raise AssertionError(f"nonfinite/negative flow at random case {i}")
    if abs(s.hp_heat_mw - s.evaporator_mw - s.compressor_mw) > 1e-8:
        raise AssertionError(f"HP first law at {i}")
    if s.evaporator_mw > source + 1e-8:
        raise AssertionError(f"source constraint at {i}")
    if abs(demand - s.direct_mw - s.discharge_mw - s.boiler_mw - s.unmet_mw)>1e-8:
        raise AssertionError(f"district demand closure at {i}")
    ecalc=e0-s.storage_loss_mwh+p.charge_efficiency*s.charge_mw*p.dt_h-s.discharge_mw*p.dt_h/p.discharge_efficiency
    if abs(ecalc-s.storage_end_mwh)>1e-8 or not -1e-8<=s.storage_end_mwh<=p.storage_capacity_mwh+1e-8:
        raise AssertionError(f"storage closure at {i}")
    if s.charge_mw*s.discharge_mw>1e-8 or s.boiler_mw>p.boiler_capacity_mw+1e-8:
        raise AssertionError(f"dispatch bounds at {i}")
check("3000_randomized_first_law_demand_storage_source_boiler", True, "seed=12026; 3000 cases; strict 1e-8")
for label,kw in [
    ("negative_demand",{"demand_mw":-1}),("negative_source",{"source_available_mw":-1}),
    ("negative_storage",{"storage_start_mwh":-1}),("overfilled_storage",{"storage_start_mwh":83}),
    ("cop_one",{"hp_cop":1}),("cop_nan",{"hp_cop":float('nan')}),
]:
    args={"p":p,"demand_mw":5,"source_available_mw":5,"hp_cop":3,"storage_start_mwh":10}
    args.update(kw)
    rejected=False
    try: step(**args)
    except ValueError: rejected=True
    check("reject_"+label,rejected)
for label,kw in [("zero_dt",{"dt_h":0}),("zero_charge_eff",{"charge_efficiency":0}),
                 ("negative_loss",{"standing_loss_fraction_per_hour":-0.01}),
                 ("loss_over_100_percent",{"standing_loss_fraction_per_hour":1.1})]:
    rejected=False
    try: P(**kw)
    except ValueError: rejected=True
    check("reject_"+label,rejected)
src=(ROOT/"matlab/+dchr/simulate_system_v2.m").read_text(encoding="utf-8")
storage=(ROOT/"matlab/+dchr/+components/storage_step.m").read_text(encoding="utf-8")
hp=(ROOT/"matlab/+dchr/+components/heat_pump.m").read_text(encoding="utf-8")
findings=[
 {"id":"F12-01","severity":"HIGH","location":"matlab/+dchr/simulate_system_v2.m",
  "evidence":"qGas(k)=max(0,qNeed-qDirect-qDis(k));",
  "issue":"No finite boiler capacity is enforced in this dispatch; a missing capacity parameter prevents credible unmet-load calculations.",
  "confirmed_static": "qGas(k)=max(0,qNeed-qDirect-qDis(k));" in src},
 {"id":"F12-02","severity":"MEDIUM","location":"matlab/+dchr/+components/storage_step.m",
  "evidence":"room/(cfg.storage.eta_charge*dt)",
  "issue":"No explicit positive dt and efficiency input validation; zero values can yield invalid numerical states.",
  "confirmed_static":"room/(cfg.storage.eta_charge*dt)" in storage and "validateattributes" not in storage},
 {"id":"F12-03","severity":"MEDIUM","location":"matlab/+dchr/+components/heat_pump.m",
  "evidence":"lift = max(1,sink_C-source_C);",
  "issue":"Nonpositive temperature lift is silently converted to 1 K. Model domain/mode selection must be specified.",
  "confirmed_static":"lift = max(1,sink_C-source_C);" in hp},
]
check("three_static_matlab_risks_located",all(x["confirmed_static"] for x in findings))
result={"version":"0.12","category":"independent_reference_property_tests_and_static_matlab_audit",
        "not_matlab_runtime_validation":True,"not_primary_paper_replication":True,
        "timestamp_utc":datetime.now(timezone.utc).isoformat(),"tests":checks,
        "passed":sum(x["pass"] for x in checks),"failed":sum(not x["pass"] for x in checks),
        "findings":findings,"source_sha256":{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
        for f in [ROOT/"audit/reference_physics_v07.py",ROOT/"matlab/+dchr/simulate_system_v2.m",
                  ROOT/"matlab/+dchr/+components/storage_step.m",ROOT/"matlab/+dchr/+components/heat_pump.m"]}}
out=ROOT/"audit/component_contract_reference_tests_v12.json"
if out.exists(): raise FileExistsError("Versioned evidence exists: "+str(out))
out.write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({"passed":result["passed"],"failed":result["failed"],
                  "findings":[x["id"] for x in findings],"evidence":str(out)},ensure_ascii=False))
