"""C114: symmetric equipment capacity needed to keep synthetic pool-room RH within 45-65%.
One-way replay of SHA-pinned C111/C106. Not a manufacturer equipment sizing claim.
"""
from __future__ import annotations
import csv, hashlib, importlib.util, json, math
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
PREV=REC/"AUTONOMOUS_RUN_20261031_0251_DCHR_C112_FINITE_HUMIDITY"
C112=PREV/"c112_finite_humidity.py"
C112_SUMMARY=PREV/"C112_SUMMARY.csv"
TASK="scc-2aab24704c2bd0"
PINS={"C112":"6dc6c77adc479f9bdbfcc2c5937aee6b8f31b6b02764d93b0ffefab95b84ebc8","C112_SUMMARY":"8104d9e18c0debc630c61bcbe926a76bfa1cdc2935af9c71c8ce8455fd7bb72f"}
LOW=.45
HIGH=.65
TOL=.01

def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()

def guard():
 for root in (D,REC,REC.parent,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse")):
  for flag in ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE"):
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))

def load(path,name):
 spec=importlib.util.spec_from_file_location(name,path)
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def series(c112,c104):
 policies,weather=c112.read_inputs()
 out={}
 for policy,rows in policies.items():
  xs=[]
  for r in rows:
   stamp=r["time"]
   o=weather[stamp]
   wo=c104.w_ratio(float(o["Tout_C"]),float(o["RH_out"]))
   xs.append((float(r["air_evap_kg"]),min(wo,c104.W_IN)))
  if len(xs)!=8760:raise AssertionError("SOURCE_HOURS")
  out[policy]=xs
 return out

def replay(c112,c104,forcing,cap):
 if not math.isfinite(cap) or cap<0:raise ValueError("INVALID_CAP")
 w=c104.W_IN
 lo=1.0;hi=0.0
 below=above=sat=0
 e=cond=0.0
 peak_d=peak_h=0.0
 for i,(evap,supply) in enumerate(forcing):
  if i%720==0:guard()
  r=c112.step(c104,w,supply,evap,cap,cap)
  w=r[0];rh=c112.rh_from_w(c104,w)
  lo=min(lo,rh);hi=max(hi,rh)
  below+=rh<LOW-1e-10
  above+=rh>HIGH+1e-10
  sat+=rh>=1-1e-10
  peak_d=max(peak_d,r[1]);peak_h=max(peak_h,r[2])
  cond+=r[7];e+=r[-1]
 return {"min_RH":lo,"max_RH":hi,"hours_below_45":below,
         "hours_above_65":above,"hours_saturated":sat,
         "electric_MWh":e,"condensate_kg":cond,
         "peak_dehum_request_kg_h":peak_d,"peak_humid_request_kg_h":peak_h}

def passes(x):
 return x["hours_below_45"]==0 and x["hours_above_65"]==0

def find_threshold(c112,c104,forcing):
 lo=0.0;low=replay(c112,c104,forcing,lo)
 if passes(low):return 0.0,0.0,low,low,0
 hi=5.0;high=replay(c112,c104,forcing,hi)
 doublings=0
 while not passes(high) and hi<1280:
  lo=hi;low=high;hi*=2;high=replay(c112,c104,forcing,hi);doublings+=1
 if not passes(high):raise RuntimeError("NO_FEASIBLE_CAP_BELOW_1280")
 iters=0
 while hi-lo>TOL:
  mid=(hi+lo)/2
  v=replay(c112,c104,forcing,mid)
  if passes(v):hi=mid;high=v
  else:lo=mid;low=v
  iters+=1
 return lo,hi,low,high,iters+doublings

def run():
 guard()
 if PINS["C112"]!="6dc6c77adc479f9bdbfcc2c5937aee6b8f31b6b02764d93b0ffefab95b84ebc8" and sha(C112)!=PINS["C112"]:raise RuntimeError("C112_SOURCE_DRIFT")
 if sha(C112_SUMMARY)!=PINS["C112_SUMMARY"]:raise RuntimeError("C112_SUMMARY_DRIFT")
 c112=load(C112,"c112_c114")
 for k,p in (("C111",c112.C111),("C106",c112.C106),("C104",c112.C104)):
  if sha(p)!=c112.PINS[k]:raise RuntimeError("SOURCE_DRIFT_"+k)
 c104=load(c112.C104,"c104_c114")
 selftests=c112.selftest(c104)
 if selftests!=21:raise AssertionError("C112_SELFTEST_DRIFT")
 forcing=series(c112,c104)
 with C112_SUMMARY.open(encoding="utf-8",newline="") as f:
  baseline={(r["scenario"],r["control"]):r for r in csv.DictReader(f)}
 rows=[];thresholds=[]
 for policy,xs in forcing.items():
  for label,cap in (("limited5",5.0),("balanced20",20.0),("ideal",1e9)):
   v=replay(c112,c104,xs,cap)
   old=baseline[(policy,label)]
   for a,b in (("min_RH","min_RH"),("max_RH","max_RH")):
    if abs(v[a]-float(old[b]))>2e-9:raise RuntimeError("C112_BASELINE_DRIFT_"+label)
   for a,b in (("hours_below_45","hours_RH_below_45"),("hours_above_65","hours_RH_above_65"),("hours_saturated","hours_at_saturation")):
    if v[a]!=int(float(old[b])):raise RuntimeError("C112_COUNT_DRIFT_"+label)
   rows.append({"policy":policy,"label":label,"capacity_kg_h":cap,**v})
  lowcap,highcap,low,high,n=find_threshold(c112,c104,xs)
  if not passes(high) or (lowcap>0 and passes(low)) or highcap-lowcap>TOL+1e-8:
   raise AssertionError("THRESHOLD_BRACKET_INVALID")
  rows.append({"policy":policy,"label":"threshold_lower_fails","capacity_kg_h":lowcap,**low})
  rows.append({"policy":policy,"label":"threshold_upper_passes","capacity_kg_h":highcap,**high})
  thresholds.append({"policy":policy,"lower_failing_cap_kg_h":lowcap,
                     "upper_passing_cap_kg_h":highcap,"search_iterations":n,
                     "upper_min_RH":high["min_RH"],"upper_max_RH":high["max_RH"]})
 out=D/"C114_CAPACITY_ENVELOPE.csv"
 if out.exists():raise RuntimeError("OUTPUT_EXISTS")
 with out.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 meta={"schema":"C114_RH_CAPACITY_ENVELOPE_V1","task_id":TASK,"synthetic":True,
       "field_validated":False,"source_signoffs_added":0,"RH_band":[LOW,HIGH],
       "cap_tolerance_kg_h":TOL,"hours_per_policy":8760,
       "policies":list(forcing),"baseline_selftests":selftests,
       "source_sha256":{"C112":sha(C112),"C112_SUMMARY":sha(C112_SUMMARY),**c112.PINS},
       "results":thresholds,"envelope_sha256":sha(out),
       "limitations":["Symmetric identical maximum dehumidification and humidification rates; not a vendor unit specification.",
         "Hourly endpoint RH only; transient within-hour excursions are not evaluated.",
         "One-way C111 evaporation forcing, no RH-to-evaporation feedback.",
         "Coil pre-drying remains idealized and unconstrained; dry-air inventory and ventilation are assumed.",
         "No measured climate, pool geometry, HVAC performance curves or primary-source signoffs."]}
 with (D/"C114_METADATA.json").open("x",encoding="utf-8") as f:json.dump(meta,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"selftests":selftests,"thresholds":thresholds,"sha256":meta["envelope_sha256"]},indent=2))
if __name__=="__main__":run()
