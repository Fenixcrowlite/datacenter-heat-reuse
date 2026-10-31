"""Independent numerical QA for C114. Does not call C112.step or C114.replay."""
import csv, json, math
from pathlib import Path
import c114_capacity_search as b
D=Path(__file__).resolve().parent

def check(a,v,tol=1e-8):
 if not math.isfinite(float(a)) or abs(float(a)-float(v))>tol:
  raise AssertionError(f"QA_MISMATCH actual={a} expected={v}")

def reference(c104,forcing,d_cap,h_cap):
 if min(d_cap,h_cap)<0:raise ValueError("NEGATIVE_CAP")
 mass=3540.0
 vent=3540.0
 decay=math.exp(-1)
 target=c104.W_IN
 sat=c104.w_ratio(c104.T_IN,1)
 w=target
 mn=1.;mx=0.
 low=high=saturation=0
 elec=cond=d_total=h_total=0.0
 for evap,supply in forcing:
  req=evap+vent*(supply-(target-decay*w)/(1-decay))
  d=min(max(req,0.),d_cap)
  h=min(max(-req,0.),h_cap)
  equilibrium=supply+(evap-d+h)/vent
  predicted=equilibrium+(w-equilibrium)*decay
  drop=mass*max(predicted-sat,0.)
  w=min(predicted,sat)
  pv=101.325*w/(.62198+w)
  rh=pv/c104.sat(c104.T_IN)
  mn=min(mn,rh);mx=max(mx,rh)
  low+=rh<.45-1e-10
  high+=rh>.65+1e-10
  saturation+=rh>=1-1e-10
  d_total+=d;h_total+=h;cond+=drop
  elec+=(d*c104.DEHUM_KWH_KG+h*c104.STEAM_KWH_KG)/1000.
 return {"min_RH":mn,"max_RH":mx,"hours_below_45":low,
         "hours_above_65":high,"hours_saturated":saturation,
         "electric_MWh":elec,"condensate_kg":cond,
         "d_total":d_total,"h_total":h_total}

def run():
 b.guard()
 meta=json.loads((D/"C114_METADATA.json").read_text(encoding="utf-8"))
 asym=json.loads((D/"C114_ASYMMETRIC_METADATA.json").read_text(encoding="utf-8"))
 if b.sha(D/"C114_CAPACITY_ENVELOPE.csv")!=meta["envelope_sha256"]:raise AssertionError("SYM_HASH")
 if b.sha(D/"C114_ASYMMETRIC_CAPACITY.csv")!=asym["data_sha256"]:raise AssertionError("ASYM_HASH")
 if b.sha(b.C112)!=meta["source_sha256"]["C112"]:raise AssertionError("SOURCE_HASH")
 c112=b.load(b.C112,"c112_qa_c114")
 c104=b.load(c112.C104,"c104_qa_c114")
 forcing=b.series(c112,c104)
 checks=0;hours=0
 with (D/"C114_CAPACITY_ENVELOPE.csv").open(encoding="utf-8",newline="") as f:
  rows=list(csv.DictReader(f))
 for row in rows:
  r=reference(c104,forcing[row["policy"]],float(row["capacity_kg_h"]),float(row["capacity_kg_h"]))
  hours+=8760
  for key in ("min_RH","max_RH","electric_MWh","condensate_kg"):
   check(r[key],row[key],2e-8);checks+=1
  for key in ("hours_below_45","hours_above_65","hours_saturated"):
   check(r[key],row[key],0);checks+=1
 for row in asym["rows"]:
  p=row["policy"]
  r=reference(c104,forcing[p],row["dehum_upper_passing_kg_h"],row["humid_upper_passing_kg_h"])
  hours+=8760
  for actual,expected in (("min_RH","joint_min_RH"),("max_RH","joint_max_RH"),
                          ("hours_below_45","joint_below_45_h"),("hours_above_65","joint_above_65_h"),
                          ("d_total","joint_dehumidified_kg_year"),("h_total","joint_humidified_kg_year")):
   check(r[actual],row[expected],2e-7);checks+=1
  if r["hours_below_45"] or r["hours_above_65"]:raise AssertionError("JOINT_CAP_FAIL")
  for side,other,lo,hi in (("dehum",1000.,row["dehum_lower_failing_kg_h"],row["dehum_upper_passing_kg_h"]),
                            ("humid",1000.,row["humid_lower_failing_kg_h"],row["humid_upper_passing_kg_h"])):
   if not 0<hi-lo<=.01000001:raise AssertionError("BAD_BRACKET")
   d,h=(lo,other) if side=="dehum" else (other,lo)
   fail=reference(c104,forcing[p],d,h);hours+=8760
   if fail["hours_below_45"]==0 and fail["hours_above_65"]==0:raise AssertionError("LOWER_SHOULD_FAIL")
   checks+=3
 negatives=0
 for bad in (lambda:reference(c104,forcing["water_first"][:1],-1,10),
             lambda:check(0.6,0.7,1e-10),
             lambda:check("nan",1)):
  try:bad()
  except (ValueError,AssertionError):negatives+=1
  else:raise AssertionError("NEGATIVE_CONTROL_MISSED")
 result={"schema":"C114_INDEPENDENT_QA_V1","status":"PASS","reference":"independent closed-form room mixing, no C112.step","annual_reference_hours":hours,
         "numeric_checks":checks,"negative_controls":negatives,"symmetric_rows":len(rows),
         "asymmetric_rows":len(asym["rows"]),"field_validated":False}
 with (D/"C114_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(result,indent=2))
if __name__=="__main__":run()
