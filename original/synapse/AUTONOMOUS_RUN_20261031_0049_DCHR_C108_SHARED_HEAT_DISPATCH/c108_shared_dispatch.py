"""C108: synthetic joint source-cap dispatch for pool water and ventilation.
Sidecar only. No change to original Simulink, SCADA or C96/C106 data.
C106 HVAC ledger already includes electric auxiliaries; external air heat is residual demand.
"""
import csv,gzip,hashlib,importlib.util,json,math,os,sys
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C93=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
C96=REC/"AUTONOMOUS_RUN_20261030_1850_DCHR_C96_UA_NTU_PUMP_ENVELOPE"/"c96_ua_ntu_pool.py"
C106=REC/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
PINS={
 str(C93):"0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923",
 str(C106):"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
}
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
TASK="scc-2aab24704c2bd0"
POOL_COP=2.2
AIR_COP=3.0
AIR_HP_CAP_MW=0.100
POOL_HP_CAP_MW=0.300
POOL_HP_ELECTRIC_CAP_MW=0.075
AIR_NAMES=("RHout40_HRV50","RHout70_HRV50","RHout90_HRV50")
CONFIGS={"constrained":(35.0,0.5,2.0),"ample":(38.0,2.0,10.0)}
POLICIES=("water_first","air_first")
COLS=("scenario","time","policy","hot_in_C","hot_flow_kg_s","UA_kW_K",
 "pool_start_C","pool_end_C","pool_loss_MWh","pool_request_MWh",
 "air_heat_request_MWh","source_rejected_MWh","source_cap_MWh",
 "pool_source_MWh","air_source_MWh","unused_source_cap_MWh",
 "pool_HP_heat_MWh","air_HP_heat_MWh","air_unmet_MWh",
 "pool_HP_electric_MWh","air_HP_electric_MWh","source_pump_electric_MWh",
 "HVAC_base_electric_MWh","total_electric_MWh","pool_storage_delta_MWh")
def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
 return h.hexdigest()
def guard():
 for root in (D,REC,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 obj=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(obj)
 return obj
def allocate(cap,water_request,air_request,policy):
 vals=(cap,water_request,air_request)
 if not all(math.isfinite(v) and v>=0 for v in vals):raise ValueError("INVALID_ALLOCATION")
 if policy not in POLICIES:raise ValueError("INVALID_POLICY")
 pool_max=min(water_request,POOL_HP_CAP_MW,POOL_HP_ELECTRIC_CAP_MW*POOL_COP)
 air_max=min(air_request,AIR_HP_CAP_MW)
 pool_need=pool_max*(1-1/POOL_COP)
 air_need=air_max*(1-1/AIR_COP)
 if policy=="water_first":
  pool_source=min(cap,pool_need)
  air_source=min(max(0,cap-pool_source),air_need)
 else:
  air_source=min(cap,air_need)
  pool_source=min(max(0,cap-air_source),pool_need)
 pool_heat=pool_source/(1-1/POOL_COP)
 air_heat=air_source/(1-1/AIR_COP)
 return pool_source,air_source,pool_heat,air_heat
def selftest():
 checks=0
 def ck(cond):
  nonlocal checks
  if not cond:raise AssertionError("SELFTEST_"+str(checks+1))
  checks+=1
 w=allocate(.01,.1,.1,"water_first")
 a=allocate(.01,.1,.1,"air_first")
 ck(w[0]>a[0]);ck(a[1]>w[1])
 ck(abs(sum(w[:2])-.01)<1e-12)
 ck(abs(sum(a[:2])-.01)<1e-12)
 ck(allocate(0,.1,.1,"air_first")== (0,0,0,0))
 ck(allocate(.1,0,0,"water_first")== (0,0,0,0))
 ck(allocate(.1,.1,.1,"water_first")[0]<=.1)
 ck(allocate(.1,.1,.1,"air_first")[1]<=.1)
 ck(allocate(.1,.1,.1,"water_first")[2]<=POOL_HP_ELECTRIC_CAP_MW*POOL_COP+1e-12)
 for bad in ((-1,1,1,"water_first"),(1,float("nan"),1,"water_first"),(1,1,1,"invalid")):
  try:allocate(*bad)
  except ValueError:checks+=1
  else:raise AssertionError("BAD_INPUT_ACCEPTED")
 return checks
def read_air():
 out={name:{} for name in AIR_NAMES}
 with gzip.open(C106,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   name=row["scenario"]
   if name in out:
    t=row["time"]
    if t in out[name]:raise RuntimeError("DUPLICATE_AIR_TIME")
    out[name][t]=(float(row["controlled_external_heat_MWh_th"]),
      float(row["controlled_electric_MWh"]),float(row["bypass"]))
 for name,data in out.items():
  if len(data)!=8760:raise RuntimeError("AIR_HOURS_"+name)
 return out
def simulate(c93,c96,c91,c92,rows,times,air,config,policy,writer):
 label,hot,flow,ua=config
 name=label+"_"+air[0]+"_"+policy
 t=28.0;active=False;stats=defaultdict(float)
 min_temp=100.0;low_hours=0;unmet_hours=0
 for i,(stamp,source_row) in enumerate(zip(times,rows)):
  if i%720==0:guard()
  time=stamp.isoformat()
  if time not in air[1]:raise RuntimeError("AIR_TIME_MISMATCH")
  air_req,hvac_el,_=air[1][time]
  if min(air_req,hvac_el)<-1e-12:raise RuntimeError("NEGATIVE_AIR_LOAD")
  loss,_=c93.loss_components(c91,c92,t,stamp.hour,.55,.15)
  if t<=c91.ON_C:active=True
  elif t>=c91.OFF_C:active=False
  pool_req=max(0.0,loss+(c91.OFF_C-t)*c91.CAP) if active else 0.0
  rejected=float(source_row["HX_rejected_MW"])
  cap,_,_,_=c96.hx_limit(rejected,hot,flow,ua)
  ps,ats,ph,ah=allocate(cap,pool_req,air_req,policy)
  pool_el=ph/POOL_COP
  air_el=ah/AIR_COP
  pump=c96.pump_power_mw(flow) if ps+ats>1e-12 else 0.0
  end=t+(ph-loss)/c91.CAP
  storage=c91.CAP*(end-t)
  unmet=max(0.0,air_req-ah)
  unused=max(0.0,cap-ps-ats)
  total=hvac_el+pool_el+air_el+pump
  if not (0<end<45 and ps+ats<=cap+1e-10
   and abs(storage-(ph-loss))<1e-10
   and abs((ph-pool_el)-ps)<1e-10
   and abs((ah-air_el)-ats)<1e-10
   and abs(ah+unmet-air_req)<1e-10
   and total>=0):
   raise RuntimeError("C108_BALANCE_FAILURE")
  vals=(name,time,policy,hot,flow,ua,t,end,loss,pool_req,air_req,
   rejected,cap,ps,ats,unused,ph,ah,unmet,pool_el,air_el,pump,
   hvac_el,total,storage)
  writer.writerow([x if isinstance(x,str) else f"{x:.12f}" for x in vals])
  for key,val in (("pool_loss_MWh",loss),("pool_HP_heat_MWh",ph),
   ("pool_HP_electric_MWh",pool_el),("pool_storage_delta_MWh",storage),
   ("air_heat_request_MWh",air_req),("air_HP_heat_MWh",ah),
   ("air_unmet_MWh",unmet),("air_HP_electric_MWh",air_el),
   ("source_extracted_MWh",ps+ats),("source_cap_MWh",cap),
   ("source_pump_electric_MWh",pump),("HVAC_base_electric_MWh",hvac_el),
   ("total_electric_MWh",total)):
   stats[key]+=val
  min_temp=min(min_temp,end)
  low_hours+=int(end<27.5)
  unmet_hours+=int(unmet>1e-9)
  t=end
 if abs(stats["pool_storage_delta_MWh"]-c91.CAP*(t-28))>1e-8:
  raise RuntimeError("YEAR_STORAGE_FAILURE")
 return dict(scenario=name,policy=policy,config=label,air_scenario=air[0],
  hours=8760,min_pool_C=min_temp,final_pool_C=t,
  hours_below_27p5=low_hours,air_unmet_hours=unmet_hours,**stats)
def run():
 guard()
 for p,expected in PINS.items():
  if sha(p)!=expected:raise RuntimeError("SOURCE_SHA_DRIFT "+p)
 tests=selftest()
 c93=module(C93,"c93_c108")
 c96=module(C96,"c96_c108")
 c91,c92,rows,times=c93.load()
 air=read_air()
 if len(times)!=8760:raise RuntimeError("TIME_LENGTH")
 targets=[D/"C108_SHARED_HOURLY.csv.gz",D/"C108_SUMMARY.csv",D/"C108_METADATA.json"]
 if any(p.exists() for p in targets):raise RuntimeError("OUTPUT_EXISTS")
 tmp=D/"C108_SHARED_HOURLY.partial.csv.gz"
 if tmp.exists():raise RuntimeError("PARTIAL_EXISTS")
 summaries=[]
 with gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
  wr=csv.writer(f);wr.writerow(COLS)
  for label,(hot,flow,ua) in CONFIGS.items():
   for airname in AIR_NAMES:
    for policy in POLICIES:
     guard()
     summaries.append(simulate(c93,c96,c91,c92,rows,times,
      (airname,air[airname]),(label,hot,flow,ua),policy,wr))
 guard()
 os.replace(tmp,targets[0])
 with targets[1].open("x",encoding="utf-8",newline="") as f:
  wr=csv.DictWriter(f,fieldnames=list(summaries[0]))
  wr.writeheader();wr.writerows(summaries)
 meta={"schema":"C108_SHARED_SOURCE_ALLOCATION_V1","task_id":TASK,
  "synthetic":True,"field_validated":False,"source_signoffs_added":0,
  "source_pins":PINS,"source_C96_script_sha256":sha(C96),
  "scenarios":len(summaries),"rows":len(summaries)*8760,"selftests":tests,
  "hourly_sha256":sha(targets[0]),"summary_sha256":sha(targets[1]),
  "assumptions":{"source_configurations":CONFIGS,"air_scenarios":AIR_NAMES,
   "policies":POLICIES,"pool_HP_COP":POOL_COP,"air_HP_COP":AIR_COP,
   "air_HP_cap_MW":AIR_HP_CAP_MW,"pool_HP_cap_MW":POOL_HP_CAP_MW,
   "pool_HP_electric_cap_MW":POOL_HP_ELECTRIC_CAP_MW,
   "backup_heat_MW":0},
  "scope":"Independent allocation sidecar: C96 UA/NTU finite source cap shared by two assumed heat pumps. Air demand and baseline HVAC electric come from C106; pool losses recomputed at dynamic pool temperature.",
  "accounting":"Source extracted = pool heat - pool HP electricity + air heat - air HP electricity. C106 HVAC electricity is counted once. Pool latent evaporation remains in water loss; air external heating is residual C106 demand. Pump electricity charged once when any source is used.",
  "limitations":["C106 air loads assume fixed pool temperature 28 C, so air humidity is not dynamically recoupled to water temperature.",
   "Both heat pumps share a hypothetical source-side UA/NTU capacity; no piping topology or return temperature recalculation.",
   "COPs, weather, UA, temperatures, flow and air loads are assumed, not manufacturer or measured values.",
   "No air heat backup; unmet air heat is a service failure, not free energy.",
   "No vendor frost/defrost curves, measured weather or primary-source signoffs.",
   "This is not a validated integrated MATLAB/Simulink model."]}
 with targets[2].open("x",encoding="utf-8") as f:
  json.dump(meta,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"selftests":tests,"scenarios":len(summaries),
  "rows":meta["rows"],"hourly_sha256":meta["hourly_sha256"],
  "anchors":[{k:s[k] for k in ("scenario","min_pool_C","hours_below_27p5",
   "air_unmet_MWh","air_unmet_hours","total_electric_MWh")}
   for s in summaries if s["air_scenario"]=="RHout70_HRV50"]},indent=2))
if __name__=="__main__":
 if "--selftest" in sys.argv:print("SELFTEST",selftest())
 else:run()
