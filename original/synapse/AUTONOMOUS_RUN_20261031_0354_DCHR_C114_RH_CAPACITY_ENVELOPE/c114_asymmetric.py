"""C114 extension: independently bracket dehumidifier and humidifier capacity.
Keep symmetric search unchanged and check the combined asymmetric pair.
"""
import csv, json, math
from pathlib import Path
import c114_capacity_search as base
D=Path(__file__).resolve().parent

def replay2(c112,c104,forcing,d_cap,h_cap):
 if min(d_cap,h_cap)<0 or not all(map(math.isfinite,(d_cap,h_cap))):raise ValueError("BAD_CAP")
 w=c104.W_IN
 lo=1.0;hi=0.0;below=above=0
 ed=eh=0.0
 for i,(evap,supply) in enumerate(forcing):
  if i%720==0:base.guard()
  r=c112.step(c104,w,supply,evap,d_cap,h_cap)
  w=r[0];rh=c112.rh_from_w(c104,w)
  lo=min(lo,rh);hi=max(hi,rh)
  below+=rh<base.LOW-1e-10
  above+=rh>base.HIGH+1e-10
  ed+=r[3];eh+=r[4]
 return {"min_RH":lo,"max_RH":hi,"below_45_h":below,"above_65_h":above,
         "dehumidified_kg_year":ed,"humidified_kg_year":eh}

def pass_band(x):return x["below_45_h"]==0 and x["above_65_h"]==0

def bracket(c112,c104,forcing,which):
 def evaluate(v):
  return replay2(c112,c104,forcing,v,1000.0) if which=="dehum" else replay2(c112,c104,forcing,1000.0,v)
 lo=0.0;fail=evaluate(lo)
 if pass_band(fail):return 0.0,0.0,fail,fail,0
 hi=5.0;good=evaluate(hi);n=0
 while not pass_band(good) and hi<1280:
  lo=hi;fail=good;hi*=2;good=evaluate(hi);n+=1
 if not pass_band(good):raise RuntimeError("NO_FEASIBLE_"+which)
 while hi-lo>base.TOL:
  mid=(lo+hi)/2;v=evaluate(mid);n+=1
  if pass_band(v):hi=mid;good=v
  else:lo=mid;fail=v
 if pass_band(fail) or not pass_band(good):raise AssertionError("INVALID_BRACKET")
 return lo,hi,fail,good,n

def run():
 base.guard()
 for name,p in (("C112",base.C112),("C112_SUMMARY",base.C112_SUMMARY)):
  if base.sha(p)!=base.PINS[name]:raise RuntimeError("SOURCE_DRIFT_"+name)
 c112=base.load(base.C112,"c112_asym")
 c104=base.load(c112.C104,"c104_asym")
 forcing=base.series(c112,c104)
 symmetric=json.loads((D/"C114_METADATA.json").read_text(encoding="utf-8"))
 rows=[]
 for policy,forcing_rows in forcing.items():
  dl,du,df,dg,dn=bracket(c112,c104,forcing_rows,"dehum")
  hl,hu,hf,hg,hn=bracket(c112,c104,forcing_rows,"humid")
  both=replay2(c112,c104,forcing_rows,du,hu)
  if not pass_band(both):raise AssertionError("ASYMMETRIC_PAIR_NOT_FEASIBLE")
  sym=next(x for x in symmetric["results"] if x["policy"]==policy)
  if du>sym["upper_passing_cap_kg_h"]+base.TOL or hu>sym["upper_passing_cap_kg_h"]+base.TOL:
   raise AssertionError("ASYMMETRIC_WORSE_THAN_SYMMETRIC")
  rows.append({"policy":policy,"dehum_lower_failing_kg_h":dl,
   "dehum_upper_passing_kg_h":du,"humid_lower_failing_kg_h":hl,
   "humid_upper_passing_kg_h":hu,"joint_min_RH":both["min_RH"],
   "joint_max_RH":both["max_RH"],"joint_below_45_h":both["below_45_h"],
   "joint_above_65_h":both["above_65_h"],"dehum_search_iterations":dn,
   "humid_search_iterations":hn,"joint_dehumidified_kg_year":both["dehumidified_kg_year"],
   "joint_humidified_kg_year":both["humidified_kg_year"]})
 out=D/"C114_ASYMMETRIC_CAPACITY.csv"
 with out.open("x",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 meta={"schema":"C114_ASYMMETRIC_CAPACITY_V1","synthetic":True,
  "task_id":base.TASK,"rows":rows,"source_sha256":{"c114_capacity_search.py":base.sha(D/"c114_capacity_search.py"),
  "C114_METADATA.json":base.sha(D/"C114_METADATA.json")},
  "data_sha256":base.sha(out),
  "limitations":["Separate capacity minima computed with other actuator at 1000 kg/h; combined pair verified for full annual endpoint RH band.",
  "No RH feedback to evaporation, no within-hour RH guarantee, no equipment sizing without actual room/HVAC measurements."]}
 with (D/"C114_ASYMMETRIC_METADATA.json").open("x",encoding="utf-8") as f:json.dump(meta,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"asymmetric":rows,"sha256":meta["data_sha256"]},indent=2))
if __name__=="__main__":run()
