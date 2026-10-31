"""C121: sensor latency and dehumidifier response sensitivity, isolated synthetic replay.
One-way C116 hourly evaporation forcing. No hardware, GUI or shared project changes.
"""
import csv,gzip,hashlib,importlib.util,json,math,os
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent; R=D.parent; S=R.parent
C120=R/"AUTONOMOUS_RUN_20261031_0653_DCHR_C120_QUARTER_CONTROL"
C116=R/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
C106=R/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
C104=R/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"c104_psychrometric.py"
C118=R/"AUTONOMOUS_RUN_20261031_0550_DCHR_C118_SUBHOUR_RH"/"c118_subhour_rh.py"
PINS={C116:"6f8fa6a7c8d6927811e02b3c8d3a970a3f6216022a7d03ed012e26da3b14e6bf",
C106:"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
C104:"1bbe6dbbf18f04c5bc0ef7b407efdbbebbf60ec496a1b5178ee66ab3bf7a1600",
C118:"a2fa7fb4d45f3c020813c6cd67059e1fad11c380a558afc5e4235f15e4e693ce",
C120/"c120_quarter_control.py":"d3392778eaf6046646cf503656603d5768484beffbf714cefe91d93ef21a9a66",
C120/"C120_QUARTER_CONTROL.csv.gz":"8eddd1fcd5d5a456deaf4dd8994c38b063089dd0a405dae1e43761ace19b0f4c"}
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
TASK="scc-2aab24704c2bd0"
FIELDS=("mode","sensor_delay_quarters","actuator_tau_h","time","RH_start","RH_peak","RH_end",
"evap_kg","dehum_kg","humid_kg","vent_kg","condensate_kg","storage_kg","mass_residual_kg",
"high_quarters","switches","energy_proxy_kWh")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,R,S,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def load(p,name):
 sp=importlib.util.spec_from_file_location(name,p)
 m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
def actuator(desired,previous,tau):
 if tau<0 or not all(map(math.isfinite,(desired,previous,tau))):raise ValueError("INVALID_ACTUATOR")
 return desired if tau==0 else previous+(desired-previous)*(-math.expm1(-.25/tau))
def selftest():
 assert actuator(10,2,0)==10
 assert abs(actuator(10,2,.25)-(2+8*(1-math.exp(-1))))<1e-12
 assert actuator(-4,5,.5)<5
 for x in (-1,float("nan")):
  try:actuator(1,0,x)
  except ValueError:pass
  else:raise AssertionError("INVALID_TAU_ACCEPTED")
 return 5
def run():
 guard()
 for p,pin in PINS.items():
  if sha(p)!=pin:raise RuntimeError("SOURCE_DRIFT "+str(p))
 tests=selftest()
 c104=load(C104,"c104_c121");c118=load(C118,"c118_c121");c120=load(C120/"c120_quarter_control.py","c120_c121")
 weather=c120.weather(c104);wsat=c104.w_ratio(c104.T_IN,1)
 target=c104.w_ratio(c104.T_IN,.55)
 keys=[(mode,delay,tau) for mode in ("feedback_capped","predictive_capped") for delay in (0,2) for tau in (0.,.5)]
 states={k:{"w":target,"hist":[target]*k[1],"act":0.} for k in keys}
 stats=defaultdict(lambda:defaultdict(float))
 out=D/"C121_DELAY_HOURLY.csv.gz";tmp=D/"C121_DELAY_HOURLY.partial.csv.gz"
 summ=D/"C121_SUMMARY.csv";meta=D/"C121_METADATA.json"
 if any(p.exists() for p in (out,tmp,summ,meta)):raise RuntimeError("OUTPUT_EXISTS")
 hours=rows=0
 with gzip.open(C116,"rt",encoding="utf-8",newline="") as source,gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as dest:
  wr=csv.writer(dest);wr.writerow(FIELDS)
  for r in csv.DictReader(source):
   if r["policy"]!="water_first" or r["control"]!="ideal":continue
   if hours%720==0:guard()
   stamp=r["time"];evap=float(r["evap_kg"]);bd=float(r["room_dehum_kg"]);bh=float(r["room_humid_kg"])
   ws=weather[stamp]
   for key in keys:
    mode,delay,tau=key;st=states[key];w0=st["w"];peak=c118.rh(c104,w0)
    dehum=humid=vent=cond=high=switch=0
    for weight in (4.,0.,0.,0.):
     w=st["w"];measured=w if delay==0 else st["hist"].pop(0)
     if delay:st["hist"].append(w)
     desired=c120.demand(mode,measured,ws,evap*weight,bd,bh,target)
     actual=actuator(desired,st["act"],tau)
     if abs(actual-st["act"])>5.:switch+=1
     st["act"]=actual
     d=max(0.,actual);h=max(0.,-actual)
     wnew,v,c,res,saturated=c118.exact_quarter(w,ws,evap*weight-d+h,wsat)
     if abs(res)>1e-8:raise AssertionError("QUARTER_MASS")
     st["w"]=wnew
     peak=max(peak,c118.rh(c104,wnew))
     high+=int(c118.rh(c104,wnew)>.65)
     dehum+=d*.25;humid+=h*.25;vent+=v;cond+=c
    storage=c118.M*(st["w"]-w0)
    residual=storage-(evap-dehum+humid+vent-cond)
    if abs(residual)>1e-7:raise AssertionError("HOUR_MASS")
    energy=.5*dehum+.75*humid
    vals=(*key,stamp,c118.rh(c104,w0),peak,c118.rh(c104,st["w"]),
          evap,dehum,humid,vent,cond,storage,residual,high,switch,energy)
    wr.writerow([x if isinstance(x,str) else str(x) if isinstance(x,int) else f"{x:.12f}" for x in vals])
    rows+=1
    s=stats[key];s["hours"]+=1;s["high_quarters"]+=high;s["hidden_high65"]+=int(vals[4]<=.65 and vals[6]<=.65 and peak>.65)
    s["switches"]+=switch;s["energy_proxy_kWh"]+=energy
    s["max_RH"]=max(s.get("max_RH",0),peak)
    s["mass_abs_residual_kg"]+=abs(residual)
   hours+=1
 assert hours==8760 and rows==70080 and len(stats)==8
 guard();os.replace(tmp,out)
 columns=("mode","sensor_delay_quarters","actuator_tau_h","hours","high_quarters","hidden_high65","switches","energy_proxy_kWh","max_RH","mass_abs_residual_kg")
 with summ.open("x",encoding="utf-8",newline="") as f:
  wr=csv.writer(f);wr.writerow(columns)
  for key in sorted(stats):wr.writerow([*key,*[stats[key][c] for c in columns[3:]]])
 m={"schema":"C121_SYNTHETIC_SENSOR_ACTUATOR_DELAY_V1","task_id":TASK,"synthetic":True,
    "field_validated":False,"source_signoffs_added":0,"source_sha256":{str(k):v for k,v in PINS.items()},
    "hours":hours,"rows":rows,"selftests":tests,"scenarios":len(keys),
    "sensor_delay_quarters":(0,2),"actuator_tau_h":(0.,.5),
    "energy_proxy_dehum_kWh_per_kg":.5,"energy_proxy_humid_kWh_per_kg":.75,
    "data_sha256":sha(out),"summary_sha256":sha(summ),
    "limitations":["One-way C116 synthetic evaporation forcing and fixed 29C air.",
    "Delay is a discrete two-quarter (30 minute) sensor lag; actuator is first-order with tau=0.5h.",
    "Energy is a declared proxy, not a measured equipment consumption or a COP curve.",
    "Predictive mode sees quarter-hour evaporation; no forecasting uncertainty.",
    "No vendor curves, thermal enthalpy balance, field validation or primary-source signoffs."]}
 meta.write_text(json.dumps(m,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"status":"PASS","hours":hours,"rows":rows,"selftests":tests,
  "sha256":sha(out),"scenarios":{str(k):{q:round(v[q],4) for q in ("high_quarters","switches","energy_proxy_kWh")} for k,v in stats.items()}},indent=2))
if __name__=="__main__":run()
