"""Independent C121 row QA, pinned C120 baseline, and mutation-negative tests."""
import csv,gzip,hashlib,json,math
from collections import Counter
from pathlib import Path
D=Path(__file__).resolve().parent;R=D.parent
A=D/"C121_DELAY_HOURLY.csv.gz";M=D/"C121_METADATA.json"
B=R/"AUTONOMOUS_RUN_20261031_0653_DCHR_C120_QUARTER_CONTROL"/"C120_QUARTER_CONTROL.csv.gz"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(r):
 for k,v in r.items():
  if k not in ("mode","time"):
   if not math.isfinite(float(v)):raise ValueError("NONFINITE")
 if not 0<=float(r["RH_start"])<=1.000001 or not 0<=float(r["RH_end"])<=1.000001:raise ValueError("RH_RANGE")
 if float(r["RH_peak"])+1e-10<max(float(r["RH_start"]),float(r["RH_end"])):raise ValueError("PEAK")
 if abs(float(r["storage_kg"])-(float(r["evap_kg"])-float(r["dehum_kg"])+float(r["humid_kg"])+float(r["vent_kg"])-float(r["condensate_kg"])))>2e-8:raise ValueError("MASS")
 if abs(float(r["mass_residual_kg"]))>1e-8:raise ValueError("RESIDUAL")
 if abs(float(r["energy_proxy_kWh"])-(.5*float(r["dehum_kg"])+.75*float(r["humid_kg"])))>2e-8:raise ValueError("ENERGY")
 if not 0<=int(r["high_quarters"])<=4 or not 0<=int(r["switches"])<=4:raise ValueError("COUNT")
 if min(float(r["dehum_kg"]),float(r["humid_kg"]),float(r["condensate_kg"])) < -1e-10:raise ValueError("NEGATIVE")
 return True
def run():
 m=json.loads(M.read_text(encoding="utf-8"))
 assert m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert sha(A)==m["data_sha256"] and m["rows"]==70080
 counts=Counter();data={};checked=0
 with gzip.open(A,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   check(r);checked+=1
   key=(r["mode"],int(r["sensor_delay_quarters"]),float(r["actuator_tau_h"]))
   counts[key]+=1
   if key[1:]==(0,0.):data[(r["mode"],r["time"])]=r
 assert len(counts)==8 and all(n==8760 for n in counts.values())
 assert len(data)==17520
 cross=0
 mapping=(("RH_start","RH_start"),("RH_peak","RH_peak"),("RH_end","RH_end"),
          ("evap_kg","evap_kg"),("dehum_kg","dehum_kg"),("humid_kg","humid_kg"),
          ("vent_kg","vent_kg"),("condensate_kg","condensate_kg"),("storage_kg","storage_kg"),
          ("high_quarters","high_quarters"))
 with gzip.open(B,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["policy"]!="water_first" or r["control"]!="ideal" or r["pattern"]!="front_loaded" or r["mode"] not in ("feedback_capped","predictive_capped"):continue
   own=data.get((r["mode"],r["time"]))
   if own is None:raise AssertionError("MISSING_BASELINE")
   for x,y in mapping:
    if abs(float(own[x])-float(r[y]))>2e-9:raise AssertionError("BASELINE_DRIFT "+x+" "+r["time"])
   cross+=1
 assert cross==17520
 sample=next(iter(data.values()))
 neg=0
 for key,value in (("energy_proxy_kWh","-1"),("storage_kg","999999"),("RH_peak","-0.1"),
                   ("high_quarters","5"),("mass_residual_kg","0.1")):
  x=dict(sample);x[key]=value
  try:check(x)
  except ValueError:neg+=1
  else:raise AssertionError("NEGATIVE_CONTROL_FAILED "+key)
 assert neg==5
 result={"status":"PASS","rows_checked":checked,"baseline_C120_rows_crosschecked":cross,
         "scenario_counts":{str(k):v for k,v in counts.items()},
         "negative_controls":neg,"data_sha256":sha(A)}
 (D/"C121_INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__":run()
