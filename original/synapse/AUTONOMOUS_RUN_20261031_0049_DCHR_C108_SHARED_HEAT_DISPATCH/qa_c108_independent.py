"""Independent QA for C108. Recomputes UA/NTU, allocations and balances without importing C108."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
META=D/"C108_METADATA.json"
HOURLY=D/"C108_SHARED_HOURLY.csv.gz"
SUMMARY=D/"C108_SUMMARY.csv"
C106=D.parent/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
CAP=500*997*4.186/3600000
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def near(a,b,tol=2e-9):
 if not math.isfinite(a) or not math.isfinite(b) or abs(a-b)>tol:raise AssertionError(f"NOT_CLOSE {a} {b}")
def check(row):
 v={k:float(x) for k,x in row.items() if k not in ("scenario","time","policy")}
 if min(v.values())<-50:raise AssertionError("RANGE")
 hot=v["hot_in_C"];flow=v["hot_flow_kg_s"];ua=v["UA_kW_K"]
 ch=flow*4.18;cc=2*4.18;cmin=min(ch,cc);cmax=max(ch,cc)
 ntu=ua/cmin;cr=cmin/cmax
 eps=ntu/(1+ntu) if abs(cr-1)<1e-12 else (1-math.exp(-ntu*(1-cr)))/(1-cr*math.exp(-ntu*(1-cr)))
 cap=min(v["source_rejected_MWh"],eps*cmin*(hot-15)/1000,ch*(hot-12)/1000)
 near(v["source_cap_MWh"],cap)
 req=v["pool_request_MWh"];areq=v["air_heat_request_MWh"]
 water_need=min(req,.3,.075*2.2)*(1-1/2.2)
 air_need=min(areq,.1)*(1-1/3)
 if row["policy"]=="water_first":
  ws=min(cap,water_need);asrc=min(cap-ws,air_need)
 elif row["policy"]=="air_first":
  asrc=min(cap,air_need);ws=min(cap-asrc,water_need)
 else:raise AssertionError("POLICY")
 near(v["pool_source_MWh"],ws)
 near(v["air_source_MWh"],asrc)
 near(v["pool_HP_heat_MWh"],ws/(1-1/2.2))
 near(v["air_HP_heat_MWh"],asrc/(1-1/3))
 near(v["pool_HP_electric_MWh"],v["pool_HP_heat_MWh"]/2.2)
 near(v["air_HP_electric_MWh"],v["air_HP_heat_MWh"]/3)
 near(v["air_unmet_MWh"],areq-v["air_HP_heat_MWh"])
 near(v["unused_source_cap_MWh"],cap-ws-asrc)
 near(v["pool_storage_delta_MWh"],CAP*(v["pool_end_C"]-v["pool_start_C"]))
 near(v["pool_storage_delta_MWh"],v["pool_HP_heat_MWh"]-v["pool_loss_MWh"])
 pump=((30*flow+40*2)/(.60*1e6)) if ws+asrc>1e-12 else 0
 near(v["source_pump_electric_MWh"],pump)
 near(v["total_electric_MWh"],v["HVAC_base_electric_MWh"]+
  v["pool_HP_electric_MWh"]+v["air_HP_electric_MWh"]+pump)
 if not 0<v["pool_end_C"]<45 or ws+asrc>cap+1e-10:raise AssertionError("PHYSICAL")
 return v
def run():
 meta=json.loads(META.read_text(encoding="utf-8"))
 assert meta["synthetic"] and not meta["field_validated"] and meta["source_signoffs_added"]==0
 assert sha(HOURLY)==meta["hourly_sha256"]
 assert sha(SUMMARY)==meta["summary_sha256"]
 assert sha(C106)==meta["source_pins"][str(C106)]
 expected={}
 with gzip.open(C106,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["scenario"] in meta["assumptions"]["air_scenarios"]:
    expected[(row["scenario"],row["time"])]=(
     float(row["controlled_external_heat_MWh_th"]),float(row["controlled_electric_MWh"]))
 assert len(expected)==3*8760
 counts=defaultdict(int);prev={};active=defaultdict(bool)
 sums=defaultdict(lambda:defaultdict(float))
 mins=defaultdict(lambda:100.0);low=defaultdict(int);unmet=defaultdict(int)
 first={};last={}
 assertions=0
 with gzip.open(HOURLY,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   v=check(row);assertions+=17
   name=row["scenario"]
   if name not in first:first[name]=v["pool_start_C"]
   if name in prev:near(prev[name],v["pool_start_C"]);assertions+=1
   prev[name]=v["pool_end_C"];last[name]=v["pool_end_C"]
   counts[name]+=1
   airname=name.split("_RHout")[1].split("_water_first")[0].split("_air_first")[0]
   airname="RHout"+airname
   e=expected[(airname,row["time"])]
   near(v["air_heat_request_MWh"],e[0]);near(v["HVAC_base_electric_MWh"],e[1]);assertions+=2
   if v["pool_start_C"]<=27.85:active[name]=True
   elif v["pool_start_C"]>=28.05:active[name]=False
   request=max(0.0,v["pool_loss_MWh"]+(28.05-v["pool_start_C"])*CAP) if active[name] else 0.0
   near(v["pool_request_MWh"],request);assertions+=1
   for k in ("pool_loss_MWh","pool_HP_heat_MWh","pool_HP_electric_MWh",
    "pool_storage_delta_MWh","air_heat_request_MWh","air_HP_heat_MWh",
    "air_unmet_MWh","air_HP_electric_MWh","source_pump_electric_MWh",
    "HVAC_base_electric_MWh","total_electric_MWh","source_cap_MWh"):
    sums[name][k]+=v[k]
   sums[name]["source_extracted_MWh"]+=v["pool_source_MWh"]+v["air_source_MWh"]
   mins[name]=min(mins[name],v["pool_end_C"])
   low[name]+=int(v["pool_end_C"]<27.5)
   unmet[name]+=int(v["air_unmet_MWh"]>1e-9)
 assert len(counts)==12 and all(n==8760 for n in counts.values())
 with SUMMARY.open(encoding="utf-8",newline="") as f:
  summary=list(csv.DictReader(f))
 assert len(summary)==12
 for row in summary:
  name=row["scenario"];assert int(row["hours"])==counts[name]
  near(float(row["min_pool_C"]),mins[name],1e-8)
  near(float(row["final_pool_C"]),last[name],1e-8)
  assert int(row["hours_below_27p5"])==low[name]
  assert int(row["air_unmet_hours"])==unmet[name]
  near(sums[name]["pool_storage_delta_MWh"],CAP*(last[name]-first[name]),1e-8)
  for k,v in sums[name].items():near(float(row[k]),v,1e-7);assertions+=1
 # negative controls: corrupt electric and source capacity, both must be detected
 with gzip.open(HOURLY,"rt",encoding="utf-8",newline="") as f:
  original=next(csv.DictReader(f))
 negative=0
 for key,delta in (("total_electric_MWh",.01),("source_cap_MWh",.01)):
  bad=dict(original);bad[key]=str(float(bad[key])+delta)
  try:check(bad)
  except AssertionError:negative+=1
  else:raise AssertionError("CORRUPTION_NOT_DETECTED_"+key)
 assert negative==2
 report={"schema":"C108_INDEPENDENT_QA_V1","status":"PASS",
  "rows":sum(counts.values()),"scenarios":len(counts),
  "independent_assertions":assertions,"annual_summaries_checked":len(summary),
  "negative_controls":negative,"source_SHA_verified":True,
  "hourly_SHA":sha(HOURLY)}
 with (D/"C108_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
  json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":run()
