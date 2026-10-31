"""Independent C106 QA: source-row equivalence, frost gate, dwell, annual ledger."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
SRC=D.parent/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
OUT=D/"C106_BYPASS_HOURLY.csv.gz"
SUMMARY=D/"C106_SUMMARY.csv"
META=D/"C106_METADATA.json"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def close(x,y,tol=3e-9):
 return math.isfinite(x) and math.isfinite(y) and abs(x-y)<=tol
def check_row(a,b,z,old,age):
 n=0
 def ck(test):
  nonlocal n
  if not test:raise AssertionError(f"BAD_ROW {b['scenario']} {b['time']} assertion {n+1}")
  n+=1
 ck(a["scenario"]==b["scenario"] and a["time"]==b["time"])
 ck(z["time"]==a["time"])
 t=float(a["Tout_C"]);eff=float(a["HRV_eff"])
 bypass=int(float(b["bypass"]))
 base_ex=29-eff*(29-t)
 selected_ex=29-(0 if bypass else eff)*(29-t)
 should=old
 if eff==0:should=0
 elif not old and base_ex<2:should=1
 elif old and age>=3 and base_ex>4:should=0
 ck(bypass==should)
 ck(close(float(b["baseline_exhaust_C"]),base_ex))
 ck(close(float(b["controlled_exhaust_C"]),selected_ex))
 ck(int(float(b["baseline_frost_risk"]))==int(base_ex<2))
 ck(int(float(b["controlled_frost_risk"]))==int(selected_ex<2)==0)
 ck(close(float(b["nominal_eff"]),eff))
 ck(close(float(b["active_eff"]),0 if bypass else eff))
 ck(close(float(b["Tout_C"]),t))
 ck(close(float(b["RH_out"]),float(a["RH_out"])))
 src=z if bypass else a
 for prefix,key in (("electric_MWh","total_HVAC_electric_MWh"),
                    ("external_heat_MWh_th","air_external_heat_MWh_th"),
                    ("coil_cooling_MWh_th","coil_cooling_MWh_th"),
                    ("dehum_kg","room_dehum_kg"),
                    ("humid_kg","humidification_kg")):
  ck(close(float(b["baseline_"+prefix]),float(a[key])))
  ck(close(float(b["controlled_"+prefix]),float(src[key])))
 for key in ("electric_MWh","external_heat_MWh_th"):
  ck(close(float(b["delta_"+key]),float(b["controlled_"+key])-float(b["baseline_"+key])))
 ck(float(b["controlled_electric_MWh"])>=0)
 ck(float(b["controlled_external_heat_MWh_th"])>=0)
 return n,should,0 if should!=old else age+1
def run():
 m=json.loads(META.read_text(encoding="utf-8"))
 assert m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert sha(SRC)==m["source_C104_sha256"] and sha(OUT)==m["hourly_sha256"]
 assert sha(SUMMARY)==m["summary_sha256"]
 zero={}
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["scenario"].endswith("_HRV0"):
    zero[(row["scenario"].split("_HRV")[0],row["time"])]=row
 assert len(zero)==26280
 sums=defaultdict(lambda:defaultdict(float))
 state={};age={};checks=0;rows=0;sample=None
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f,gzip.open(OUT,"rt",encoding="utf-8",newline="") as g:
  a=csv.DictReader(f);b=csv.DictReader(g)
  for x,y in zip(a,b):
   key=x["scenario"];ref=zero[(key.split("_HRV")[0],x["time"])]
   old=state.get(key,0);elapsed=age.get(key,3)
   n,new,newage=check_row(x,y,ref,old,elapsed)
   if old!=new:sums[key]["switches"]+=1
   state[key]=new;age[key]=newage
   checks+=n;rows+=1
   if sample is None and new:sample=(x.copy(),y.copy(),ref.copy(),old,elapsed)
   d=sums[key];d["hours"]+=1
   d["bypass_hours"]+=new
   for k in ("baseline_frost_risk","controlled_frost_risk"):
    d[k+"_hours"]+=int(float(y[k]))
   for k in ("baseline_electric_MWh","controlled_electric_MWh",
             "baseline_external_heat_MWh_th","controlled_external_heat_MWh_th",
             "baseline_coil_cooling_MWh_th","controlled_coil_cooling_MWh_th"):
    d[k]+=float(y[k])
  assert next(a,None) is None and next(b,None) is None
 assert rows==78840 and len(sums)==9
 with SUMMARY.open(encoding="utf-8",newline="") as f:
  annual=list(csv.DictReader(f))
 assert len(annual)==9
 annual_checks=0
 for x in annual:
  d=sums[x["scenario"]]
  for k in ("hours","bypass_hours","switches","baseline_frost_risk_hours",
            "controlled_frost_risk_hours","baseline_electric_MWh","controlled_electric_MWh",
            "baseline_external_heat_MWh_th","controlled_external_heat_MWh_th",
            "baseline_coil_cooling_MWh_th","controlled_coil_cooling_MWh_th"):
   assert close(float(x[k]),d[k],1e-6);annual_checks+=1
  for k in ("electric_MWh","external_heat_MWh_th"):
   assert close(float(x["delta_"+k]),d["controlled_"+k]-d["baseline_"+k],1e-6);annual_checks+=1
 assert all(sums[k]["controlled_frost_risk_hours"]==0 for k in sums)
 assert all(sums[k]["bypass_hours"]==0 for k in sums if k.endswith("_HRV0") or k.endswith("_HRV50"))
 assert all(sums[k]["bypass_hours"]>0 for k in sums if k.endswith("_HRV80"))
 assert sample is not None
 x,y,z,old,elapsed=sample
 caught=0
 for key in ("bypass","controlled_electric_MWh"):
  tamper=dict(y)
  tamper[key]=str(1-int(float(y[key]))) if key=="bypass" else str(float(y[key])+0.1)
  try:check_row(x,tamper,z,old,elapsed)
  except AssertionError:caught+=1
 assert caught==2
 result={"status":"PASS","rows":rows,"scenarios":len(sums),"independent_assertions":checks,
  "annual_comparisons":annual_checks,"negative_controls":caught,"source_sha_verified":True,
  "hourly_sha_verified":True,"summary_sha_verified":True,
  "RHout70_HRV80":{k:round(v,6) for k,v in sums["RHout70_HRV80"].items()}}
 with (D/"C106_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
  json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(result,indent=2))
if __name__=="__main__":run()
