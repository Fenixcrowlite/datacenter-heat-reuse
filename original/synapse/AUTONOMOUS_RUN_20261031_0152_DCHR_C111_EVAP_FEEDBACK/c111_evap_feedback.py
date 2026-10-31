"""C111: synthetic water-temperature -> evaporation -> psychrometric HVAC -> shared-source feedback.
Read-only SHA-pinned C93/C104/C106/C108. No SCADA/Simulink changes.
"""
import csv,gzip,hashlib,importlib.util,json,math,os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
P={
"C93":REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py",
"C104":REC/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"c104_psychrometric.py",
"C108":REC/"AUTONOMOUS_RUN_20261031_0049_DCHR_C108_SHARED_HEAT_DISPATCH"/"c108_shared_dispatch.py",
"C106":REC/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz",
"C108_DATA":REC/"AUTONOMOUS_RUN_20261031_0049_DCHR_C108_SHARED_HEAT_DISPATCH"/"C108_SHARED_HOURLY.csv.gz"}
PINS={
"C93":"0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923",
"C104":"1bbe6dbbf18f04c5bc0ef7b407efdbbebbf60ec496a1b5178ee66ab3bf7a1600",
"C108":"e3695e53d9365b9420d18e44eac0a7ba00223c02b892712dec6f6caff6164417",
"C106":"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
"C108_DATA":"7b243871e1ab13abc4c35e6ee8ae9bf85950bc546adf39c5f5383f1d54ac24d4"}
TASK="scc-2aab24704c2bd0"
TARGETS=("constrained_RHout70_HRV50_water_first",
"constrained_RHout70_HRV50_air_first",
"ample_RHout70_HRV50_water_first",
"ample_RHout70_HRV50_air_first")
MODES=("fixed_28C_evap","dynamic_Tpool_evap")
COLS=("scenario","mode","time","policy","pool_start_C","pool_end_C",
"pool_loss_MWh","pool_evap_kg","air_evap_kg","air_dehum_kg","air_humid_kg",
"air_external_heat_MWh","air_unmet_MWh","air_HP_heat_MWh",
"air_HVAC_electric_MWh","pool_HP_heat_MWh","pool_HP_electric_MWh",
"air_HP_electric_MWh","source_pump_electric_MWh","total_electric_MWh",
"source_cap_MWh","source_pool_MWh","source_air_MWh",
"pool_storage_delta_MWh","air_moisture_residual_kg","air_coil_enthalpy_residual_MWh")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,REC,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for f in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def loadmod(name):
 spec=importlib.util.spec_from_file_location("c111_"+name,P[name])
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def getrows():
 d={name:[] for name in TARGETS}
 with gzip.open(P["C108_DATA"],"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["scenario"] in d:d[row["scenario"]].append(row)
 for name,rows in d.items():
  if len(rows)!=8760:raise RuntimeError("SOURCE_LENGTH_"+name)
 return d
def getweather():
 d={}
 with gzip.open(P["C106"],"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["scenario"]=="RHout70_HRV50":
    if row["time"] in d:raise RuntimeError("DUPLICATE_WEATHER")
    d[row["time"]]=row
 if len(d)!=8760:raise RuntimeError("WEATHER_LENGTH")
 return d
def air(c104,weather,evap):
 tout=float(weather["Tout_C"]);rh=float(weather["RH_out"])
 eff=float(weather["active_eff"])
 delta=evap+c104.M_DRY*(c104.w_ratio(tout,rh)-c104.W_IN)
 dehum=max(0,delta);humid=max(0,-delta)
 result=c104.calc(tout,rh,eff,evap,dehum,humid)
 assert abs(result[17])<1e-7 and abs(result[18])<1e-10
 return result
def selftest(c93,c104,c91,c92):
 n=0
 def ck(x):
  nonlocal n
  if not x:raise AssertionError("SELFTEST_"+str(n+1))
  n+=1
 for h in (2,12,22):
  _,e28=c93.loss_components(c91,c92,28,h,.55,.15)
  _,e29=c93.loss_components(c91,c92,29,h,.55,.15)
  ck(e29>=e28>=0)
 weather={"Tout_C":"5","RH_out":"0.7","active_eff":"0.5"}
 a=air(c104,weather,0);b=air(c104,weather,4)
 ck(abs(a[17])<1e-7 and abs(b[17])<1e-7)
 ck(a[16]>=0 and b[16]>=0)
 ck(a[15]>=0 and b[15]>=0)
 try:air(c104,weather,-100)
 except (ValueError,RuntimeError,AssertionError):n+=1
 else:raise AssertionError("NEGATIVE_EVAP_ACCEPTED")
 return n
def simulate(c93,c104,c108,c96,c91,c92,source,weather,mode,writer):
 name=source[0]["scenario"];policy=source[0]["policy"]
 t=28.0;active=False;stats=defaultdict(float);minimum=99;below=0
 for i,row in enumerate(source):
  if i%720==0:guard()
  stamp=row["time"];w=weather[stamp]
  assert stamp==source[i]["time"]
  loss,evap_pool=c93.loss_components(c91,c92,t,int(stamp[11:13]),.55,.15)
  _,evap_fixed=c93.loss_components(c91,c92,28,int(stamp[11:13]),.55,.15)
  evap_air=evap_pool if mode=="dynamic_Tpool_evap" else evap_fixed
  r=air(c104,w,evap_air)
  air_req=r[15];hvac_el=r[16]
  if t<=c91.ON_C:active=True
  elif t>=c91.OFF_C:active=False
  pool_req=max(0,loss+(c91.OFF_C-t)*c91.CAP) if active else 0
  cap=float(row["source_cap_MWh"])
  ps,ats,ph,ah=c108.allocate(cap,pool_req,air_req,policy)
  pool_el=ph/c108.POOL_COP;air_el=ah/c108.AIR_COP
  pump=float(row["source_pump_electric_MWh"]) if ps+ats>1e-12 else 0.0
  # C108 pump can be zero on a given hour despite new dispatch; use physical C96 function instead.
  if ps+ats>1e-12:
   pump=c96.pump_power_mw(float(row["hot_flow_kg_s"]))
  end=t+(ph-loss)/c91.CAP
  unmet=max(0,air_req-ah)
  storage=c91.CAP*(end-t)
  total=hvac_el+pool_el+air_el+pump
  if not (0<end<45 and 0<=ps+ats<=cap+1e-9
   and abs(storage-(ph-loss))<1e-10
   and abs((ph-pool_el)-ps)<1e-10
   and abs((ah-air_el)-ats)<1e-10
   and abs(air_req-ah-unmet)<1e-10 and total>=0):
   raise RuntimeError("COUPLED_BALANCE_FAILURE")
  vals=(name,mode,stamp,policy,t,end,loss,evap_pool,evap_air,r[3],r[4],
    air_req,unmet,ah,hvac_el,ph,pool_el,air_el,pump,total,cap,ps,ats,storage,r[17],r[18])
  writer.writerow([v if isinstance(v,str) else f"{v:.12f}" for v in vals])
  for key,val in zip(COLS[6:],vals[6:]):
   if key not in ("air_moisture_residual_kg","air_coil_enthalpy_residual_MWh"):
    stats[key]+=val
  minimum=min(minimum,end);below+=int(end<27.5);t=end
 if abs(stats["pool_storage_delta_MWh"]-c91.CAP*(t-28))>1e-8:
  raise RuntimeError("YEAR_BALANCE")
 return dict(scenario=name,mode=mode,hours=8760,min_pool_C=minimum,final_pool_C=t,
  hours_below_27p5=below,**stats)
def run():
 guard()
 for name,p in P.items():
  if sha(p)!=PINS[name]:raise RuntimeError("SOURCE_DRIFT "+name)
 c93=loadmod("C93");c104=loadmod("C104");c108=loadmod("C108")
 c91,c92,rows,times=c93.load();c96=c108.module(c108.C96,"c96_c111")
 n=selftest(c93,c104,c91,c92)
 sources=getrows();weather=getweather()
 for name,source in sources.items():
  assert all(row["time"]==t.isoformat() for row,t in zip(source,times))
  assert all(row["policy"]==name.split("_")[-2]+"_"+name.split("_")[-1] for row in source)
 out=D/"C111_COUPLED_HOURLY.csv.gz";tmp=D/"C111_COUPLED.partial.csv.gz"
 summary=D/"C111_SUMMARY.csv";meta=D/"C111_METADATA.json"
 if any(p.exists() for p in (out,tmp,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
 results=[]
 with gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
  w=csv.writer(f);w.writerow(COLS)
  for name in TARGETS:
   for mode in MODES:
    guard();results.append(simulate(c93,c104,c108,c96,c91,c92,sources[name],weather,mode,w))
 guard();os.replace(tmp,out)
 with summary.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
 metadata={"schema":"C111_SYNTHETIC_EVAP_HVAC_COUPLING_V1","task_id":TASK,
  "synthetic":True,"field_validated":False,"source_signoffs_added":0,
  "source_sha256":PINS,"rows":len(results)*8760,"scenarios":len(results),
  "selftests":n,"hourly_sha256":sha(out),"summary_sha256":sha(summary),
  "modes":MODES,"limitations":[
   "Air RH and temperature held at controlled setpoints 55% and 29 C; HVAC response changes, not room humidity dynamics.",
   "Fixed C106 HRV bypass decisions and fixed C108 UA/NTU source cap; no new frost or return-water recalculation.",
   "C93 evaporation and C104 moisture ledger are synthetic with assumed coverage, occupancy and weather.",
   "No manufacturer COP map or measured equipment data; not a Simulink integration.",
   "Fixed-vs-dynamic evaporation comparison uses common C93 evaporation law, not C106 original fixed-28C moisture baseline."]}
 with meta.open("x",encoding="utf-8") as f:json.dump(metadata,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"selftests":n,"scenarios":len(results),"rows":metadata["rows"],
  "sha256":metadata["hourly_sha256"],"summary":[{k:v for k,v in s.items()
   if k in ("scenario","mode","min_pool_C","air_unmet_MWh","air_HVAC_electric_MWh")}
   for s in results]},indent=2))
if __name__=="__main__":run()

