"""C112 independent QA: rederive room ODE, bounds and source alignment without importing C112."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
REC=D.parent
SRC=REC/"AUTONOMOUS_RUN_20261031_0152_DCHR_C111_EVAP_FEEDBACK"/"C111_COUPLED_HOURLY.csv.gz"
DATA=D/"C112_ROOM_HUMIDITY_HOURLY.csv.gz"
SUMMARY=D/"C112_SUMMARY.csv"
META=D/"C112_METADATA.json"
M=3540.0;V=3540.0;a=math.exp(-1)
P=101.325;T=29.0
def sat(t):return .61094*math.exp(17.625*t/(t+243.04))
def w_rh(rh):
 p=rh*sat(T)
 return .62198*p/(P-p)
def rh_w(w):return (P*w/(.62198+w))/sat(T)
TARGET=w_rh(.55);SAT=w_rh(1.0)
CAP={"ideal":(1e9,1e9),"balanced20":(20.,20.),"limited5":(5.,5.),"no_humid10":(10.,0.)}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b,tol=2e-8):return abs(a-b)<=tol
def validate(row,source):
 f=lambda k:float(row[k])
 capd,caph=CAP[row["control"]]
 evap=f("evap_kg_h");start=f("room_w_start");supply=f("supply_w")
 d=f("dehum_actual_kg_h");h=f("humid_actual_kg_h")
 if not (0<=d<=capd+1e-9 and 0<=h<=caph+1e-9):raise AssertionError("CAPACITY")
 if not close(evap,float(source["air_evap_kg"])):raise AssertionError("EVAP_SOURCE")
 if not close(f("pool_end_C"),float(source["pool_end_C"])):raise AssertionError("POOL_SOURCE")
 needed=evap+V*(supply-(TARGET-a*start)/(1-a))
 dr=max(0,needed);hr=max(0,-needed)
 if not (close(f("dehum_req_kg_h"),dr) and close(f("humid_req_kg_h"),hr)):raise AssertionError("DEMAND")
 if not (close(d,min(dr,capd)) and close(h,min(hr,caph))):raise AssertionError("DISPATCH")
 eq=supply+(evap-d+h)/V
 pred=eq+(start-eq)*a
 cond=M*max(0,pred-SAT)
 end=min(pred,SAT)
 if not (close(f("room_w_end"),end) and close(f("room_condensate_kg"),cond)):raise AssertionError("SATURATION")
 avg=eq+(start-eq)*(1-a)
 vent=V*(supply-avg)
 storage=M*(end-start)
 if not (close(f("vent_net_kg"),vent) and close(f("room_storage_delta_kg"),storage)):raise AssertionError("STORAGE")
 if abs(storage-(vent+evap-d+h-cond))>2e-8:raise AssertionError("MASS")
 if abs(f("moisture_residual_kg"))>2e-8:raise AssertionError("RESIDUAL")
 if not (close(f("room_RH_end"),rh_w(end)) and 0<=f("room_RH_end")<=1.00000001):raise AssertionError("RH")
 if not close(f("humidity_control_electric_MWh"),(d*.5+h*.75)/1000):raise AssertionError("ELECTRIC")
 if row["control"]=="ideal":
  if not (close(d,float(source["air_dehum_kg"])) and close(h,float(source["air_humid_kg"])) and close(end,TARGET)):
   raise AssertionError("IDEAL_C111")
 return 14
def run():
 meta=json.loads(META.read_text(encoding="utf-8"))
 assert meta["synthetic"] and not meta["field_validated"] and meta["source_signoffs_added"]==0
 assert meta["rows"]==70080 and meta["scenarios"]==8 and meta["source_sha256"]["C111"]==sha(SRC)
 assert meta["hourly_sha256"]==sha(DATA) and meta["summary_sha256"]==sha(SUMMARY)
 sources={}
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["mode"]=="dynamic_Tpool_evap" and row["scenario"].startswith("constrained_"):
    sources[(row["policy"],row["time"])]=row
 assert len(sources)==17520
 counts=defaultdict(int);last={};minrh=defaultdict(lambda:1.0);maxrh=defaultdict(float)
 totals=defaultdict(lambda:defaultdict(float));checks=0
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   key=(row["scenario"],row["control"])
   assert row["control"] in CAP and row["scenario"] in ("water_first","air_first")
   assert (row["scenario"],row["time"]) in sources
   if key in last:assert close(float(row["room_w_start"]),last[key],2e-10)
   else:assert close(float(row["room_w_start"]),TARGET,2e-10)
   checks+=validate(row,sources[(row["scenario"],row["time"])])+2
   last[key]=float(row["room_w_end"]);counts[key]+=1
   rh=float(row["room_RH_end"]);minrh[key]=min(minrh[key],rh);maxrh[key]=max(maxrh[key],rh)
   totals[key]["hours_RH_below_45"]+=int(rh<.45)
   totals[key]["hours_RH_above_65"]+=int(rh>.65)
   totals[key]["hours_at_saturation"]+=int(rh>1-1e-10)
   for col in ("room_condensate_kg","dehum_actual_kg_h","humid_actual_kg_h","humidity_control_electric_MWh"):
    totals[key][col]+=float(row[col])
 assert len(counts)==8 and all(n==8760 for n in counts.values())
 with SUMMARY.open(encoding="utf-8",newline="") as f:
  rows=list(csv.DictReader(f))
 assert len(rows)==8
 for row in rows:
  key=(row["scenario"],row["control"])
  assert close(float(row["hours"]),counts[key])
  assert close(float(row["min_RH"]),minrh[key]) and close(float(row["max_RH"]),maxrh[key])
  for col,val in totals[key].items():
   assert close(float(row[col]),val,2e-6),(key,col,val,row[col])
  checks+=8
 # Negative controls must be rejected, not silently accepted.
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  sample=next(csv.DictReader(f))
 src=sources[(sample["scenario"],sample["time"])]
 negative=0
 for k,value in (("dehum_actual_kg_h","100000"),("room_storage_delta_kg","9999"),("humidity_control_electric_MWh","999")):
  bad=dict(sample);bad[k]=value
  try:validate(bad,src)
  except AssertionError:negative+=1
  else:raise AssertionError("NEGATIVE_CONTROL_NOT_DETECTED_"+k)
 assert negative==3
 report={"schema":"C112_INDEPENDENT_QA_V1","status":"PASS","rows":sum(counts.values()),
  "scenarios":len(counts),"checks":checks,"negative_controls":negative,
  "source_sha256":sha(SRC),"data_sha256":sha(DATA),"summary_sha256":sha(SUMMARY),
  "limitations":"Independent numeric replay validates model equations and input trace, not real-world HVAC physics."}
 with (D/"C112_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
  json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":run()
