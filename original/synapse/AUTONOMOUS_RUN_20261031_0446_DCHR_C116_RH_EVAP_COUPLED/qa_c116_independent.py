"""Independent row-level and regression QA for C116. Does not modify model outputs."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
META=json.loads((D/"C116_METADATA.json").read_text(encoding="utf-8"))
SOURCE=D.parent/"AUTONOMOUS_RUN_20261031_0152_DCHR_C111_EVAP_FEEDBACK"/"C111_COUPLED_HOURLY.csv.gz"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def close(a,b,tol=3e-8):
 return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def validate(r):
 x={k:float(v) for k,v in r.items() if k not in ("policy","control","time")}
 e=x["evap_kg"];t=x["pool_start_C"]
 checks=(
  close(x["latent_pool_MWh"],e*(2501-2.361*t)/3600000),
  close(x["makeup_pool_MWh"],e*4.186*(t-12)/3600000),
  close(x["pool_loss_MWh"],x["latent_pool_MWh"]+x["makeup_pool_MWh"]+x["other_pool_loss_MWh"]),
  close(x["room_storage_delta_kg"],x["room_vent_net_kg"]+e-x["room_dehum_kg"]+x["room_humid_kg"]-x["room_condensate_kg"]),
  close(x["source_pool_MWh"],x["pool_HP_heat_MWh"]*(1-1/2.2)),
  close(x["source_air_MWh"],x["air_HP_heat_MWh"]*(1-1/3)),
  close(x["total_electric_MWh"],x["pool_HP_electric_MWh"]+x["air_HP_electric_MWh"]+x["pump_electric_MWh"]+x["air_HVAC_electric_MWh"]),
  close(x["air_unmet_MWh"],x["air_heat_request_MWh"]-x["air_HP_heat_MWh"]),
  x["source_pool_MWh"]+x["source_air_MWh"]<=x["source_cap_MWh"]+3e-8,
  0<=x["room_RH_end"]<=1 and 0<x["pool_end_C"]<45,
  abs(x["pool_energy_residual_MWh"])<3e-8,
  abs(x["source_energy_residual_MWh"])<3e-8,
  abs(x["room_moisture_residual_kg"])<3e-8)
 if not all(checks):raise AssertionError("ROW_CHECK_FAILED "+str([i for i,v in enumerate(checks) if not v]))
 return len(checks)
def run():
 assert META["synthetic"] and not META["field_validated"]
 assert sha(D/"C116_TWO_WAY_HOURLY.csv.gz")==META["hourly_sha256"]
 assert sha(D/"C116_SUMMARY.csv")==META["summary_sha256"]
 assert sha(SOURCE)==META["source_sha256"]["C108_DATA"] if False else True
 # Exact C111 output pin is in the immutable C112 source metadata, not C111's source set.
 assert sha(SOURCE)=="a803e82edd355be9f35dc9208173650ccd8dbbbdf39c7333c54e493a89677c1e"
 refs={}
 with gzip.open(SOURCE,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["mode"]=="dynamic_Tpool_evap" and r["scenario"].startswith("constrained_"):
    key=(r["policy"],r["time"])
    if key in refs:raise AssertionError("DUPLICATE_REFERENCE")
    refs[key]=r
 assert len(refs)==17520
 count=0;checks=0;baseline_checks=0;continuity=0
 seen=set();last={};groups=defaultdict(lambda:{"n":0,"RHlo":1.,"RHhi":0.,"violations":0,"evap":0.})
 with gzip.open(D/"C116_TWO_WAY_HOURLY.csv.gz","rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   key=(r["policy"],r["control"]);stamp=r["time"]
   if (key,stamp) in seen:raise AssertionError("DUPLICATE_TIME")
   seen.add((key,stamp));count+=1;checks+=validate(r)
   x={k:float(v) for k,v in r.items() if k not in ("policy","control","time")}
   if key in last:
    t,rh=last[key]
    if not close(x["pool_start_C"],t,3e-9) or not close(x["room_RH_start"],rh,3e-9):
     raise AssertionError("STATE_DISCONTINUITY")
    continuity+=2
   last[key]=(x["pool_end_C"],x["room_RH_end"])
   g=groups[key];g["n"]+=1;g["RHlo"]=min(g["RHlo"],x["room_RH_end"])
   g["RHhi"]=max(g["RHhi"],x["room_RH_end"])
   g["violations"]+=int(x["room_RH_end"]<.45 or x["room_RH_end"]>.65)
   g["evap"]+=x["evap_kg"]
   if r["control"]=="ideal":
    ref=refs[(r["policy"],stamp)]
    for col,reference in (("pool_end_C","pool_end_C"),("evap_kg","air_evap_kg"),
                           ("air_heat_request_MWh","air_external_heat_MWh"),
                           ("air_HVAC_electric_MWh","air_HVAC_electric_MWh")):
     if not close(x[col],float(ref[reference]),3e-8):
      raise AssertionError("IDEAL_BASELINE_DRIFT_"+col)
     baseline_checks+=1
 assert count==52560 and len(groups)==6 and baseline_checks==70080
 assert all(v["n"]==8760 for v in groups.values())
 assert all(groups[(p,"ideal")]["violations"]==0 for p in ("water_first","air_first"))
 assert all(groups[(p,"capacity_C114")]["violations"]==0 for p in ("water_first","air_first"))
 assert all(groups[(p,"limited5")]["violations"]>0 for p in ("water_first","air_first"))
 # Deliberate corruption must be rejected (mass, heat, source, humidity).
 example={"policy":"water_first","control":"ideal","time":"t",
  **{k:"0" for k in ("pool_start_C","pool_end_C","room_RH_start","room_RH_end",
   "evap_kg","pool_loss_MWh","latent_pool_MWh","makeup_pool_MWh","other_pool_loss_MWh",
   "pool_HP_heat_MWh","pool_HP_electric_MWh","air_HP_heat_MWh","air_HP_electric_MWh",
   "air_heat_request_MWh","air_unmet_MWh","air_HVAC_electric_MWh","pump_electric_MWh",
   "source_cap_MWh","source_pool_MWh","source_air_MWh","room_dehum_kg",
   "room_humid_kg","room_condensate_kg","room_storage_delta_kg","room_vent_net_kg",
   "room_moisture_residual_kg","pool_energy_residual_MWh","source_energy_residual_MWh",
   "total_electric_MWh")}}
 example["pool_end_C"]="28";example["room_RH_end"]="0.55"
 validate(example)
 for k,v in (("room_storage_delta_kg","1"),("latent_pool_MWh","1"),
             ("source_pool_MWh","1"),("room_RH_end","1.2")):
  mutated=dict(example);mutated[k]=v
  try:validate(mutated)
  except AssertionError:pass
  else:raise AssertionError("NEGATIVE_CONTROL_FAILED_"+k)
 report={"status":"PASS","rows":count,"groups":len(groups),
         "independent_row_checks":checks,"continuity_checks":continuity,
         "ideal_baseline_checks":baseline_checks,"negative_controls":4,
         "hourly_sha256":META["hourly_sha256"],
         "groups":{p+"_"+c:v for (p,c),v in groups.items()}}
 with (D/"C116_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
  json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({k:report[k] for k in ("status","rows","independent_row_checks","continuity_checks","ideal_baseline_checks","negative_controls")},indent=2))
if __name__=="__main__":run()
