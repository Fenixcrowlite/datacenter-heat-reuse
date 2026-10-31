"""A52 synthetic sensor-lag x trip-delay sensitivity, no MATLAB or hardware."""
from pathlib import Path
import json,sys,hashlib
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A49=D.parent/"AUTONOMOUS_RUN_20261027_0245_A49_FAULT_INJECTION"
sys.path[:0]=[str(A45),str(A49)]
import finite_trip_a45 as plant
from a49_independent_audit import independent_audit
def analyze():
 rows=plant.verified_inputs()[:240]
 cases=[]
 for scenario in ("neither","backup_only"):
  for sensor in (0,1,4):
   for trip in (0,2,4):
    trace=plant.simulate(rows,scenario,sensor_lag_steps=sensor,trip_delay_steps=trip)
    ledger=independent_audit(trace,sensor_lag_steps=sensor)
    assert ledger["first_trip_index"] is not None
    unhandled_kwh=sum(r["unhandled_W"]*900/3600000 for r in trace)
    unmet_kwh=sum(r["pool_dh_unmet_W"]*900/3600000 for r in trace)
    cases.append({"scenario":scenario,"sensor_lag_steps":sensor,"trip_delay_steps":trip,
      "first_trip_index":ledger["first_trip_index"],
      "max_temperature_C":ledger["max_temperature_C"],
      "unhandled_heat_kWh":unhandled_kwh,
      "unmet_heat_kWh":unmet_kwh,
      "max_flow_residual_W":ledger["max_reported_flow_residual_W"]})
 return {"status":"A52_SYNTHETIC_CROSSPRODUCT_REFERENCE_PASS","synthetic_only":True,
         "matlab_crossproduct_executed":False,"physical_release":False,
         "step_seconds":900,"cases":cases}
if __name__=="__main__":
 report=analyze()
 p=D/"SENSITIVITY_A52.json"
 if p.exists():raise SystemExit("REFUSE_OVERWRITE")
 p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 for row in report["cases"]:print(row["scenario"],row["sensor_lag_steps"],row["trip_delay_steps"],row["first_trip_index"],round(row["max_temperature_C"],4))
