"""Independent ledger QA for C111, including exact C108 fixed-evap regression."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
REC=D.parent
DATA=D/"C111_COUPLED_HOURLY.csv.gz"
SUMMARY=D/"C111_SUMMARY.csv"
META=D/"C111_METADATA.json"
BASE=REC/"AUTONOMOUS_RUN_20261031_0049_DCHR_C108_SHARED_HEAT_DISPATCH"/"C108_SHARED_HOURLY.csv.gz"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def validate(row):
 f={k:float(v) for k,v in row.items() if k not in ("scenario","mode","time","policy")}
 for v in f.values():assert math.isfinite(v)
 def close(a,b,tol=5e-9):assert abs(a-b)<=tol,(a,b)
 close(f["pool_storage_delta_MWh"],f["pool_HP_heat_MWh"]-f["pool_loss_MWh"])
 close(f["source_pool_MWh"],f["pool_HP_heat_MWh"]-f["pool_HP_electric_MWh"])
 close(f["source_air_MWh"],f["air_HP_heat_MWh"]-f["air_HP_electric_MWh"])
 close(f["air_external_heat_MWh"],f["air_HP_heat_MWh"]+f["air_unmet_MWh"])
 close(f["total_electric_MWh"],f["air_HVAC_electric_MWh"]+
  f["pool_HP_electric_MWh"]+f["air_HP_electric_MWh"]+f["source_pump_electric_MWh"])
 close(f["air_moisture_residual_kg"],0,1e-7)
 close(f["air_coil_enthalpy_residual_MWh"],0,1e-9)
 assert f["source_pool_MWh"]+f["source_air_MWh"]<=f["source_cap_MWh"]+1e-9
 assert 0<f["pool_start_C"]<45 and 0<f["pool_end_C"]<45
 assert all(f[k]>=-1e-9 for k in ("pool_loss_MWh","pool_evap_kg","air_evap_kg",
  "air_dehum_kg","air_humid_kg","air_external_heat_MWh","air_unmet_MWh",
  "total_electric_MWh","source_cap_MWh"))
 return f
def run():
 meta=json.loads(META.read_text(encoding="utf-8"))
 assert sha(DATA)==meta["hourly_sha256"] and sha(SUMMARY)==meta["summary_sha256"]
 assert meta["scenarios"]==8 and meta["rows"]==70080 and meta["source_signoffs_added"]==0
 base={}
 with gzip.open(BASE,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["scenario"] in (
    "constrained_RHout70_HRV50_water_first","constrained_RHout70_HRV50_air_first",
    "ample_RHout70_HRV50_water_first","ample_RHout70_HRV50_air_first"):
    key=(r["scenario"],r["time"])
    assert key not in base
    base[key]=r
 assert len(base)==35040
 checks=0;count=defaultdict(int);sums=defaultdict(lambda:defaultdict(float))
 previous={};nonzero_dynamic=0;fixed_matches=0
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   v=validate(r);checks+=19
   key=(r["scenario"],r["mode"]);count[key]+=1
   old=previous.get(key)
   if old is not None:
    assert abs(v["pool_start_C"]-old)<5e-9;checks+=1
   previous[key]=v["pool_end_C"]
   for field in ("pool_loss_MWh","pool_evap_kg","air_evap_kg","air_dehum_kg",
    "air_humid_kg","air_external_heat_MWh","air_unmet_MWh",
    "air_HVAC_electric_MWh","total_electric_MWh","pool_storage_delta_MWh"):
    sums[key][field]+=v[field]
   if r["mode"]=="fixed_28C_evap":
    b=base[(r["scenario"],r["time"])]
    for field,newfield in (("pool_start_C","pool_start_C"),("pool_end_C","pool_end_C"),
      ("air_heat_request_MWh","air_external_heat_MWh"),
      ("air_unmet_MWh","air_unmet_MWh"),("HVAC_base_electric_MWh","air_HVAC_electric_MWh"),
      ("total_electric_MWh","total_electric_MWh")):
     assert abs(float(b[field])-v[newfield])<5e-9,(r["scenario"],r["time"],field)
     fixed_matches+=1
   else:
    nonzero_dynamic+=int(abs(v["air_evap_kg"]-v["pool_evap_kg"])<1e-9)
 assert len(count)==8 and all(n==8760 for n in count.values())
 assert fixed_matches==35040*6 and nonzero_dynamic==35040
 with SUMMARY.open(encoding="utf-8",newline="") as f:
  summaries=list(csv.DictReader(f))
 assert len(summaries)==8
 for s in summaries:
  key=(s["scenario"],s["mode"])
  assert int(s["hours"])==count[key]
  for field,total in sums[key].items():
   assert abs(float(s[field])-total)<5e-7,(key,field)
  assert abs(float(s["final_pool_C"])-previous[key])<5e-9
 # Verify actual feedback is not an accidental identical copy.
 differences=[]
 for scenario in sorted({k[0] for k in count}):
  fixed=sums[(scenario,"fixed_28C_evap")]
  dynamic=sums[(scenario,"dynamic_Tpool_evap")]
  differences.append(dynamic["air_HVAC_electric_MWh"]-fixed["air_HVAC_electric_MWh"])
 assert any(abs(x)>0.01 for x in differences)
 negatives=0
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  sample=next(csv.DictReader(f))
 for change in ({"source_pool_MWh":"1000"},{"air_moisture_residual_kg":"1"},
                {"pool_storage_delta_MWh":"1"}):
  bad=dict(sample,**change)
  try:validate(bad)
  except AssertionError:negatives+=1
 assert negatives==3
 result={"status":"PASS","rows":sum(count.values()),"scenarios":len(count),
  "checks_ledger_min":checks,"baseline_C108_field_matches":fixed_matches,
  "dynamic_evap_matches_pool":nonzero_dynamic,
  "negative_controls":negatives,"hourly_sha256":sha(DATA),
  "annual_electric_deltas_MWh":differences,"physical_validation":False}
 (D/"C111_INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2,sort_keys=True))
if __name__=="__main__":run()
