"""A54 synthetic uncertainty sweep. Never infer certified safe limits."""
from __future__ import annotations
import json,sys,hashlib
from pathlib import Path
from itertools import product
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A49=D.parent/"AUTONOMOUS_RUN_20261027_0245_A49_FAULT_INJECTION"
A52=D.parent/"AUTONOMOUS_RUN_20261027_0510_A52_SENSOR_TRIP_CROSSPRODUCT"
sys.path[:0]=[str(A45),str(A49)]
import finite_trip_a45 as plant
from a49_independent_audit import independent_audit
SCENARIOS=("neither","backup_only")
SENSORS=(0,4)
TRIPS=(0,4)
CAPS=(6e6,8e6,10e6)
RESIDUALS=(.06,.12,.24)
TAUS=(900.,1800.)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def run_sweep():
 rows=plant.verified_inputs()[:240]
 old=json.loads((A52/"SENSITIVITY_A52.json").read_text(encoding="utf-8"))
 anchors={(x["scenario"],x["sensor_lag_steps"],x["trip_delay_steps"]):x for x in old["cases"]}
 # Baseline reproduces all 18 A52 references before any uncertain-parameter runs.
 for key,ref in anchors.items():
  trace=plant.simulate(rows,key[0],sensor_lag_steps=key[1],trip_delay_steps=key[2])
  audit=independent_audit(trace,sensor_lag_steps=key[1])
  if audit["first_trip_index"]!=ref["first_trip_index"] or abs(audit["max_temperature_C"]-ref["max_temperature_C"])>1e-9:
   raise AssertionError("A52_ANCHOR_MISMATCH "+str(key))
 cases=[]
 for scenario,sensor,trip,capacity,residual,tau in product(SCENARIOS,SENSORS,TRIPS,CAPS,RESIDUALS,TAUS):
  trace=plant.simulate(rows,scenario,sensor_lag_steps=sensor,trip_delay_steps=trip,
   heat_capacity_J_per_C=capacity,residual_fraction=residual,compressor_tau_s=tau)
  audit=independent_audit(trace,sensor_lag_steps=sensor,heat_capacity_J_per_C=capacity,compressor_tau_s=tau)
  cases.append(dict(scenario=scenario,sensor_lag_steps=sensor,trip_delay_steps=trip,
   heat_capacity_J_per_C=capacity,residual_fraction=residual,compressor_tau_s=tau,
   first_trip_index=audit["first_trip_index"],max_temperature_C=audit["max_temperature_C"],
   over_42_steps=sum(r["T_next_C"]>=42 for r in trace),
   over_60_steps=sum(r["T_next_C"]>=60 for r in trace),
   unhandled_heat_kWh=sum(r["unhandled_W"] for r in trace)/4000,
   max_flow_residual_W=audit["max_reported_flow_residual_W"]))
 if len(cases)!=144:raise AssertionError("SWEEP_INCOMPLETE")
 groups={}
 for scenario in SCENARIOS:
  g=[c for c in cases if c["scenario"]==scenario]
  groups[scenario]=dict(min_peak_C=min(c["max_temperature_C"] for c in g),
   max_peak_C=max(c["max_temperature_C"] for c in g),
   earliest_trip_index=min(c["first_trip_index"] for c in g if c["first_trip_index"] is not None),
   latest_trip_index=max(c["first_trip_index"] for c in g if c["first_trip_index"] is not None),
   combinations_above_60_C=sum(c["over_60_steps"]>0 for c in g))
 return dict(status="A54_SYNTHETIC_PARAMETER_UNCERTAINTY_VERIFIED",
  source_A52_sha256=sha(A52/"SENSITIVITY_A52.json"),
  baseline_A52_anchors_checked=len(anchors),cases_checked=len(cases),
  samples_per_case=len(rows),step_seconds=900,parameter_values=dict(
   heat_capacity_J_per_C=CAPS,residual_fraction=RESIDUALS,
   compressor_tau_s=TAUS,sensor_lag_steps=SENSORS,trip_delay_steps=TRIPS),
  assumptions="Parameter ranges are stress-test choices, not measured confidence intervals or manufacturer specifications.",
  not_a_certified_safety_envelope=True,physical_release=False,
  scenarios=groups,cases=cases)
def main():
 result=run_sweep()
 out=D/"A54_UNCERTAINTY_RESULTS.json"
 if out.exists():
  if json.loads(out.read_text(encoding="utf-8"))!=result:raise RuntimeError("EXISTING_RESULT_CONFLICT")
 else:out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print(json.dumps({"status":result["status"],"cases":result["cases_checked"],
  "anchors":result["baseline_A52_anchors_checked"],"groups":result["scenarios"]},ensure_ascii=False))
if __name__=="__main__":main()

