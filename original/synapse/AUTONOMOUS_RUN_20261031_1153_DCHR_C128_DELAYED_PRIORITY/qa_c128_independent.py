"""C128 CSV-only independent verifier; imports no simulation code."""
import csv,gzip,hashlib,json,math,datetime
from collections import defaultdict,deque
from pathlib import Path
D=Path(__file__).resolve().parent
DATA=D/"C128_DELAYED_PRIORITY.csv.gz"
CAP=500.*997.*4.186;M=3540.;P=101.325;EPS=.62198
SC={}
for cap in (20.,25.):
 for priority in ("water_first","air_first"):
  for delay in (0,2):SC[f"{priority}_{int(cap)}kW_d{delay}"]=(priority,cap,delay)
for priority in ("water_first","air_first"):SC[f"{priority}_150kW_d0"]=(priority,150.,0)
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def sat(t):return .61094*math.exp(17.625*t/(t+243.04))
def w_from(t,rh):
 pv=rh*sat(t);return EPS*pv/(P-pv)
WS=w_from(26.,.55)
def enthalpy(t,w):return M*(1.006*t+w*(2501.+1.86*t))
def check(r,queues):
 f=lambda k:float(r[k])
 name=r["scenario"];assert name in SC
 priority,kw,delay=SC[name]
 assert r["priority"]==priority and abs(f("source_kw")-kw)<1e-9 and int(r["delay_quarters"])==delay
 assert 0<=int(r["quarter"])<4 and 0<f("pool_T1")<45 and -20<f("air_T1")<70
 assert 0<=f("RH1")<=1+1e-8
 assert abs(f("RH1")-P*f("w1")/(EPS+f("w1"))/sat(f("air_T1")))<1e-8
 if delay:
  lagp,laga=queues[name].popleft()
  queues[name].append((f("pool_req_kJ"),f("air_req_kJ")))
 else:lagp,laga=f("pool_req_kJ"),f("air_req_kJ")
 assert abs(f("lag_pool_kJ")-lagp)<1e-6 and abs(f("lag_air_kJ")-laga)<1e-6
 reqa=max(0.,min(15.,5.*(29.-f("air_T0"))))*900.
 assert abs(f("air_req_kJ")-reqa)<1e-7
 safea=min(laga,reqa)
 assert abs(f("safe_air_kJ")-safea)<1e-7
 on=f("thermostat_on");assert on in (0.,1.)
 if f("pool_T0")<=27.95:assert on==1.
 if f("pool_T0")>=28.05:assert on==0.
 reqp=max(0.,f("pool_loss_kJ")+.35*CAP*(28.-f("pool_T0"))) if on else 0.
 assert abs(f("pool_req_kJ")-reqp)<1e-6
 cap=kw*900.;assert abs(f("source_cap_kJ")-cap)<1e-7
 if priority=="water_first":
  qp=min(lagp,cap);qa=min(safea,max(0.,cap-qp))
 else:
  qa=min(safea,cap);qp=min(lagp,max(0.,cap-qa))
 assert abs(f("pool_heat_kJ")-qp)<1e-6 and abs(f("air_heat_kJ")-qa)<1e-6
 assert qp+qa<=cap+1e-7 and abs(f("source_unused_kJ")-(cap-qp-qa))<1e-7
 assert abs(f("latent_kJ")-f("evap_kg")*(2501.-2.361*f("pool_T0")))<1e-7
 assert abs(f("pool_loss_kJ")-f("latent_kJ")-f("makeup_kJ")-f("other_loss_kJ"))<1e-7
 assert abs(f("makeup_kJ")-f("evap_kg")*4.186*(f("pool_T0")-12.))<1e-7
 assert abs(CAP*(f("pool_T1")-f("pool_T0"))-(qp-f("pool_loss_kJ")))<1e-5
 hvac=f("hvac_kJ")
 if f("air_T0")<29.:assert abs(hvac-qa)<1e-7
 else:assert -13500.000001<=hvac<=1e-7 and qa==0.
 assert abs(f("air_evap_kJ")-f("latent_kJ"))<1e-7
 flow=f("air_evap_kJ")+f("vent_kJ")+hvac-f("dehum_kJ")+f("humid_kJ")-f("cond_kJ")
 assert abs(enthalpy(f("air_T1"),f("w1"))-enthalpy(f("air_T0"),f("w0"))-flow)<1e-5
 vapor_vent=885.*(WS-f("w0"))
 vapor_dehum=f("dehum_kJ")/(2501.+1.86*f("air_T0"))
 vapor_humid=f("humid_kJ")/(2501.+1.86*f("air_T0"))
 vapor_cond=f("cond_kJ")/(4.186*f("air_T1")) if f("cond_kJ") else 0.
 assert abs(M*(f("w1")-f("w0"))-(f("evap_kg")+vapor_vent-vapor_dehum+vapor_humid-vapor_cond))<3e-7
 for k in ("pool_residual_kJ","air_residual_kJ","combined_residual_kJ"):assert abs(f(k))<1e-5
 assert abs(f("air_mass_residual_kg"))<1e-7
 return True
def negatives(sample):
 variants=(("source_kw",21),("delay_quarters",1),("lag_pool_kJ",1234),
 ("pool_heat_kJ",float(sample["pool_heat_kJ"])+100),
 ("air_heat_kJ",float(sample["air_heat_kJ"])+100),
 ("pool_T1",float(sample["pool_T1"])+.1),
 ("RH1",1.2),("latent_kJ",float(sample["latent_kJ"])+10),
 ("priority","invalid"))
 passed=0
 for k,v in variants:
  bad=dict(sample);bad[k]=str(v)
  queues={n:deque([(0.,0.)]*dd) for n,(_,_,dd) in SC.items()}
  try:check(bad,queues)
  except (AssertionError,ValueError,OverflowError):passed+=1
  else:raise AssertionError("NEGATIVE_NOT_CAUGHT "+k)
 return passed
def main():
 meta=json.loads((D/"C128_METADATA.json").read_text(encoding="utf-8"))
 assert meta["data_sha256"]==sha(DATA) and meta["summary_sha256"]==sha(D/"C128_SUMMARY.json")
 assert meta["synthetic"] and not meta["field_validated"] and meta["rows"]==6720
 queues={n:deque([(0.,0.)]*delay) for n,(_,_,delay) in SC.items()}
 prev={};counts=defaultdict(int);sample=None;maxres=0.
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if sample is None:sample=r
   check(r,queues);name=r["scenario"];counts[name]+=1
   if name in prev:
    old=prev[name];q=int(r["quarter"]);oq=int(old["quarter"])
    assert (r["time"]==old["time"] and q==oq+1) or (q==0 and oq==3 and datetime.datetime.fromisoformat(r["time"])-datetime.datetime.fromisoformat(old["time"])==datetime.timedelta(hours=1))
    for a,b in (("pool_T0","pool_T1"),("air_T0","air_T1"),("w0","w1")):
     assert abs(float(r[a])-float(old[b]))<2e-9
   prev[name]=r
   maxres=max(maxres,abs(float(r["combined_residual_kJ"])))
 assert len(counts)==len(SC) and all(counts[n]==672 for n in SC)
 s=json.loads((D/"C128_SUMMARY.json").read_text(encoding="utf-8"))
 assert s["water_first_20kW_d0"]["cap_binding_quarters"]>0
 assert s["air_first_20kW_d0"]["cap_binding_quarters"]>0
 assert s["water_first_20kW_d0"]["air_heat_MWh"]<s["air_first_20kW_d0"]["air_heat_MWh"]
 assert s["water_first_20kW_d0"]["final_pool_C"]>s["air_first_20kW_d0"]["final_pool_C"]
 for key in ("final_pool_C","final_air_C","pool_heat_MWh","air_heat_MWh"):
  assert abs(s["water_first_150kW_d0"][key]-s["air_first_150kW_d0"][key])<1e-8
 neg=negatives(sample)
 result={"status":"PASS","independent":True,"rows":sum(counts.values()),"scenarios":len(counts),
 "counts":dict(counts),"negative_controls":neg,"max_combined_residual_kJ":maxres,
 "data_sha256":sha(DATA),"checks":["lag_FIFO","air_safety_gate","priority","source_cap","thermostat",
 "pool_energy","air_enthalpy","air_mass","state_continuity","priority_competition"]}
 (D/"C128_INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__":main()
