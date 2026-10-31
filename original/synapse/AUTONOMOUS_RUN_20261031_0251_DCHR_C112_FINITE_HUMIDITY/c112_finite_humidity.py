"""C112: bounded room humidity response to C111 synthetic evaporation forcing.
An independent, one-way sensitivity overlay. NOT a validated pool/HVAC feedback model.
"""
from __future__ import annotations
import csv, gzip, hashlib, importlib.util, json, math, os
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C111=REC/"AUTONOMOUS_RUN_20261031_0152_DCHR_C111_EVAP_FEEDBACK"/"C111_COUPLED_HOURLY.csv.gz"
C106=REC/"AUTONOMOUS_RUN_20261030_2348_DCHR_C106_HRV_FROST_BYPASS"/"C106_BYPASS_HOURLY.csv.gz"
C104=REC/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"c104_psychrometric.py"
PINS={"C111":"a803e82edd355be9f35dc9208173650ccd8dbbbdf39c7333c54e493a89677c1e",
      "C106":"e0dd2fbe552861d635e51797a85a50ccb6ca36408928910ac45122ce46b0a8cf",
      "C104":"1bbe6dbbf18f04c5bc0ef7b407efdbbebbf60ec496a1b5178ee66ab3bf7a1600"}
TASK="scc-2aab24704c2bd0"
M_ROOM=3000.0*1.18
M_VENT=3000.0*1.18
DT_H=1.0
A=math.exp(-M_VENT/M_ROOM*DT_H)
CAPS={"ideal":{"dehum":1e9,"humid":1e9},
      "balanced20":{"dehum":20.0,"humid":20.0},
      "limited5":{"dehum":5.0,"humid":5.0},
      "no_humid10":{"dehum":10.0,"humid":0.0}}
COLS=("scenario","control","time","pool_end_C","evap_kg_h","outdoor_RH",
      "supply_w","room_w_start","room_w_end","room_RH_start","room_RH_end",
      "dehum_req_kg_h","humid_req_kg_h","dehum_actual_kg_h","humid_actual_kg_h",
      "unmet_dehum_kg_h","unmet_humid_kg_h","room_condensate_kg",
      "room_storage_delta_kg","vent_net_kg","moisture_residual_kg",
      "humidity_control_electric_MWh")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in (D,REC,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def module(path):
 spec=importlib.util.spec_from_file_location("c104_c112",path)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def rh_from_w(c104,w):
 pv=c104.P*w/(0.62198+w)
 return pv/c104.sat(c104.T_IN)
def step(c104,w_start,w_supply,evap,cap_dehum,cap_humid):
 vals=(w_start,w_supply,evap,cap_dehum,cap_humid)
 if not all(math.isfinite(x) for x in vals) or min(vals)<0 or w_start>0.1 or w_supply>0.1:
  raise ValueError("INVALID_MOISTURE_INPUT")
 # Exact well-mixed room ODE solution with hourly constant rates and ventilation.
 # Choose control rate to reach 55% RH at END of the hour if capacities permit.
 target=c104.W_IN
 needed=evap+M_VENT*(w_supply-(target-A*w_start)/(1-A))
 d_req=max(0.0,needed);h_req=max(0.0,-needed)
 d=min(d_req,cap_dehum);h=min(h_req,cap_humid)
 net=evap-d+h
 w_eq=w_supply+net/M_VENT
 w_pred=w_eq+(w_start-w_eq)*A
 if w_pred<0:raise RuntimeError("NEGATIVE_ROOM_HUMIDITY")
 w_sat=c104.w_ratio(c104.T_IN,1.0)
 cond=M_ROOM*max(0.0,w_pred-w_sat)
 w_end=min(w_pred,w_sat)
 # Integrate the ventilation exhaust exactly; condensate clips the end state.
 k=M_VENT/M_ROOM
 w_avg=w_eq+(w_start-w_eq)*(1-A)/(k*DT_H)
 vent_net=M_VENT*DT_H*(w_supply-w_avg)
 storage=M_ROOM*(w_end-w_start)
 residual=storage-(vent_net+net*DT_H-cond)
 electric=(d*c104.DEHUM_KWH_KG+h*c104.STEAM_KWH_KG)/1000.0
 if abs(residual)>1e-8 or not 0<=rh_from_w(c104,w_end)<=1+1e-10:
  raise RuntimeError("MOISTURE_BALANCE_FAILURE")
 return (w_end,d_req,h_req,d,h,d_req-d,h_req-h,cond,storage,vent_net,residual,electric)
def selftest(c104):
 n=0
 def ck(ok):
  nonlocal n
  if not ok:raise AssertionError("SELFTEST_"+str(n+1))
  n+=1
 for evap in (0.0,4.2,25.0,50.0):
  s=step(c104,c104.W_IN,c104.W_IN,evap,1e9,1e9)
  ck(abs(s[0]-c104.W_IN)<1e-12)
  ck(abs(s[1]-evap)<1e-9 and s[2]<1e-9)
  ck(abs(s[-2])<1e-9)
  limited=step(c104,c104.W_IN,c104.W_IN,evap,5,5)
  ck(limited[3]<=5 and limited[4]<=5)
 wet=step(c104,c104.W_IN,c104.W_IN,200,0,0)
 ck(abs(rh_from_w(c104,wet[0])-1)<1e-10 and wet[7]>0)
 dry=step(c104,c104.W_IN,0.001,0,0,0)
 ck(dry[0]<c104.W_IN)
 for invalid in ((-1,.01,1,1,1),(.01,.01,-1,1,1),(.01,.01,1,-1,1)):
  try:step(c104,*invalid)
  except ValueError:n+=1
  else:raise AssertionError("INVALID_ACCEPTED")
 return n
def read_inputs():
 policies={"water_first":[],"air_first":[]}
 with gzip.open(C111,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["mode"]=="dynamic_Tpool_evap" and r["scenario"].startswith("constrained_"):
    policies[r["policy"]].append(r)
 for p,rows in policies.items():
  if len(rows)!=8760 or len({r["time"] for r in rows})!=8760:
   raise RuntimeError("SOURCE_LENGTH_"+p)
 weather={}
 with gzip.open(C106,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["scenario"]=="RHout70_HRV50":
    if r["time"] in weather:raise RuntimeError("DUPLICATE_WEATHER")
    weather[r["time"]]=r
 if len(weather)!=8760:raise RuntimeError("WEATHER_LENGTH")
 return policies,weather
def simulate(c104,policy,source,weather,cap_name,writer):
 cap=CAPS[cap_name]
 w=c104.W_IN
 stats=defaultdict(float);rh_min=1.0;rh_max=0.0
 for i,r in enumerate(source):
  if i%720==0:guard()
  stamp=r["time"];out=weather[stamp]
  evap=float(r["air_evap_kg"]);wo=c104.w_ratio(float(out["Tout_C"]),float(out["RH_out"]))
  supply=min(wo,c104.W_IN) # frozen C104 outdoor-coil setpoint
  start=w;rh_start=rh_from_w(c104,start)
  result=step(c104,start,supply,evap,cap["dehum"],cap["humid"])
  w=result[0];rh=rh_from_w(c104,w)
  if cap_name=="ideal":
   if abs(result[3]-float(r["air_dehum_kg"]))>2e-8 or abs(result[4]-float(r["air_humid_kg"]))>2e-8:
    raise RuntimeError("IDEAL_C111_REGRESSION")
   if abs(w-c104.W_IN)>1e-10:raise RuntimeError("IDEAL_SETPOINT")
  vals=(policy,cap_name,stamp,float(r["pool_end_C"]),evap,float(out["RH_out"]),
        supply,start,w,rh_start,rh,*result[1:])
  writer.writerow([v if isinstance(v,str) else f"{v:.12f}" for v in vals])
  stats["hours"]+=1
  stats["hours_RH_below_45"]+=int(rh<.45)
  stats["hours_RH_above_65"]+=int(rh>.65)
  stats["hours_at_saturation"]+=int(rh>1-1e-10)
  for key,value in zip(COLS[11:],vals[11:]):stats[key]+=value
  rh_min=min(rh_min,rh);rh_max=max(rh_max,rh)
 return {"scenario":policy,"control":cap_name,"min_RH":rh_min,"max_RH":rh_max,**stats}
def run():
 guard()
 for key,p in (("C111",C111),("C106",C106),("C104",C104)):
  if sha(p)!=PINS[key]:raise RuntimeError("SOURCE_DRIFT_"+key)
 c104=module(C104);tests=selftest(c104)
 policies,weather=read_inputs()
 out=D/"C112_ROOM_HUMIDITY_HOURLY.csv.gz";tmp=D/"C112_ROOM_HUMIDITY.partial.csv.gz"
 summ=D/"C112_SUMMARY.csv";meta=D/"C112_METADATA.json"
 if any(p.exists() for p in (out,tmp,summ,meta)):raise RuntimeError("OUTPUT_EXISTS")
 results=[]
 with gzip.open(tmp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
  writer=csv.writer(f);writer.writerow(COLS)
  for policy,rows in policies.items():
   for name in CAPS:
    guard();results.append(simulate(c104,policy,rows,weather,name,writer))
 guard();os.replace(tmp,out)
 with summ.open("x",encoding="utf-8",newline="") as f:
  writer=csv.DictWriter(f,fieldnames=list(results[0]));writer.writeheader();writer.writerows(results)
 metadata={"schema":"C112_FINITE_ROOM_HUMIDITY_V1","task_id":TASK,"synthetic":True,
   "field_validated":False,"source_signoffs_added":0,"rows":len(results)*8760,
   "scenarios":len(results),"selftests":tests,"source_sha256":PINS,
   "hourly_sha256":sha(out),"summary_sha256":sha(summ),
   "room_dry_air_kg":M_ROOM,"vent_dry_air_kg_h":M_VENT,
   "indoor_air_C":c104.T_IN,"RH_setpoint":.55,"control_caps_kg_h":CAPS,
   "limitations":[
    "One-way humidity overlay: pool temperature, evaporation, ventilation supply and heat allocation replay immutable C111/C106; humidity DOES NOT feed back to evaporation or COP.",
    "C104 outdoor coil dehumidifies to 55% RH target when outdoor is wetter; coil capacity unlimited and not recalculated for actual room humidity.",
    "Well-mixed room, fixed 29 C, constant ventilation, exact first-order hourly solution; endpoint saturation condensation is a simplified clip.",
    "No latent condensation heat recovery, no fan changes, no HVAC heat rebalance; only dehumidifier and humidifier electricity is recalculated.",
    "No equipment datasheets, no measured air volumes, no physical validation or MATLAB integration."]}
 with meta.open("x",encoding="utf-8") as f:json.dump(metadata,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"tests":tests,"rows":metadata["rows"],"sha256":metadata["hourly_sha256"],
  "results":[{k:r[k] for k in ("scenario","control","min_RH","max_RH","hours_RH_below_45","hours_RH_above_65","hours_at_saturation")} for r in results]},indent=2))
if __name__=="__main__":run()
