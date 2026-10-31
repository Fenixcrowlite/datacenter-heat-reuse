"""C127 independent CSV-only QA: no imports of C127, C124 or C93 model code."""
import csv,gzip,hashlib,json,math,datetime
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
DATA=D/"C127_BOUNDED_QUARTER.csv.gz";META=D/"C127_METADATA.json"
CAP=500.*997.*4.186; M=3540.;P=101.325;EPS=.62198
SC={"water_150kW":("water_first",150.,35040),"air_150kW":("air_first",150.,35040),
"water_10kW_7d":("water_first",10.,672),"noheat_7d":("water_first",0.,672)}
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
def check(r):
 f=lambda k:float(r[k])
 name=r["scenario"];assert name in SC
 priority,kw,_=SC[name]
 q=int(r["quarter"]);assert 0<=q<4
 assert abs(f("source_kw")-kw)<1e-9
 assert 0<f("pool_T0")<45 and 0<f("pool_T1")<45
 assert -20<f("air_T1")<70 and 0<=f("RH1")<=1.0000001
 assert abs(f("RH0")-P*f("w0")/(EPS+f("w0"))/sat(f("air_T0")))<1e-8
 assert abs(f("RH1")-P*f("w1")/(EPS+f("w1"))/sat(f("air_T1")))<1e-8
 assert abs(f("latent_kJ")-f("evap_kg")*(2501.-2.361*f("pool_T0")))<1e-7
 assert abs(f("air_evap_kJ")-f("latent_kJ"))<1e-7
 assert abs(f("pool_loss_kJ")-f("latent_kJ")-f("makeup_kJ")-f("other_loss_kJ"))<1e-7
 assert abs(f("makeup_kJ")-f("evap_kg")*4.186*(f("pool_T0")-12.))<1e-7
 on=f("thermostat_on");assert on in (0.,1.)
 if f("pool_T0")<=27.95:assert on==1.
 if f("pool_T0")>=28.05:assert on==0.
 pool_req=max(0.,f("pool_loss_kJ")+.35*CAP*(28.-f("pool_T0"))) if on else 0.
 air_req=max(0.,min(15.,5.*(29.-f("air_T0"))))*900.
 assert abs(f("pool_req_kJ")-pool_req)<1e-6
 assert abs(f("air_req_kJ")-air_req)<1e-7
 capacity=kw*900.
 if priority=="water_first":
  qp=min(pool_req,capacity);qa=min(air_req,max(0.,capacity-qp))
 else:
  qa=min(air_req,capacity);qp=min(pool_req,max(0.,capacity-qa))
 assert abs(f("pool_heat_kJ")-qp)<1e-6 and abs(f("air_heat_kJ")-qa)<1e-6
 assert f("pool_heat_kJ")>=0 and f("air_heat_kJ")>=0
 assert f("pool_heat_kJ")+f("air_heat_kJ")<=capacity+1e-7
 assert abs(f("source_cap_kJ")-capacity)<1e-7
 assert abs(f("source_unused_kJ")-(capacity-qp-qa))<1e-7
 assert abs(f("pool_unmet_kJ")-(pool_req-qp))<1e-6
 assert abs(f("air_unmet_kJ")-(air_req-qa))<1e-7
 assert abs(CAP*(f("pool_T1")-f("pool_T0"))-qp+f("pool_loss_kJ"))<1e-5
 assert abs(f("air_H0_kJ")-enthalpy(f("air_T0"),f("w0")))<3e-5 if "air_H0_kJ" in r else True
 # Air enthalpy balance reconstructed without importing model
 delta=enthalpy(f("air_T1"),f("w1"))-enthalpy(f("air_T0"),f("w0"))
 air_flow=f("air_evap_kJ")+f("vent_kJ")+f("hvac_kJ")-f("dehum_kJ")+f("humid_kJ")-f("cond_kJ")
 assert abs(delta-air_flow)<1e-5
 assert abs(f("pool_residual_kJ"))<1e-5 and abs(f("air_residual_kJ"))<1e-5
 assert abs(f("combined_residual_kJ"))<1e-5
 assert abs(f("air_mass_residual_kg"))<1e-7
 vapor_evap=f("evap_kg")
 vapor_vent=885.*(WS-f("w0"))
 vapor_dehum=f("dehum_kJ")/(2501.+1.86*f("air_T0"))
 vapor_humid=f("humid_kJ")/(2501.+1.86*f("air_T0"))
 vapor_cond=f("cond_kJ")/(4.186*f("air_T1")) if f("cond_kJ") else 0.
 assert abs(M*(f("w1")-f("w0"))-(vapor_evap+vapor_vent-vapor_dehum+vapor_humid-vapor_cond))<3e-7
 if f("air_T0")<29.:assert abs(f("hvac_kJ")-qa)<1e-7
 else:assert f("hvac_kJ")<=1e-7 and f("hvac_kJ")>=-13500.000001
 return True
def negatives(sample):
 def reject(key,value):
  bad=dict(sample);bad[key]=str(value)
  try:check(bad)
  except (AssertionError,ValueError,OverflowError):return True
  return False
 assert reject("source_kw",float(sample["source_kw"])+1)
 assert reject("pool_heat_kJ",float(sample["pool_heat_kJ"])+100)
 assert reject("air_heat_kJ",float(sample["air_heat_kJ"])+100)
 assert reject("pool_T1",float(sample["pool_T1"])+.01)
 assert reject("RH1",1.2)
 assert reject("latent_kJ",float(sample["latent_kJ"])+10)
 return 6
def main():
 meta=json.loads(META.read_text(encoding="utf-8"))
 assert meta["data_sha256"]==sha(DATA) and meta["summary_sha256"]==sha(D/"C127_SUMMARY.json")
 assert meta["synthetic"] and not meta["field_validated"] and meta["rows"]==71424
 counts=defaultdict(int);prev={};examples={};minp={};maxp={}
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   check(r)
   name=r["scenario"];counts[name]+=1;examples.setdefault(name,r)
   if name in prev:
    old=prev[name]
    q=int(r["quarter"]);oq=int(old["quarter"])
    assert (r["time"]==old["time"] and q==oq+1) or (q==0 and oq==3 and datetime.datetime.fromisoformat(r["time"])-datetime.datetime.fromisoformat(old["time"])==datetime.timedelta(hours=1))
    for k0,k1 in (("pool_T0","pool_T1"),("air_T0","air_T1"),("w0","w1")):
     assert abs(float(r[k0])-float(old[k1]))<2e-9
   prev[name]=r
 for name,(_,_,expected) in SC.items():assert counts[name]==expected
 assert float(prev["noheat_7d"]["pool_T1"])<float(prev["water_10kW_7d"]["pool_T1"])
 assert float(prev["water_10kW_7d"]["pool_T1"])<float(prev["water_150kW"]["pool_T1"])
 assert all(abs(float(prev["water_150kW"][k])-float(prev["air_150kW"][k]))<1e-8 for k in ("pool_T1","air_T1","w1"))
 neg=negatives(examples["water_150kW"])
 result={"status":"PASS","independent":True,"rows":sum(counts.values()),"counts":dict(counts),
 "negative_controls":neg,"data_sha256":sha(DATA),"source_sha256":meta["source_sha256"],
 "checks":["dispatch_priority","source_cap","thermostat","pool_energy","air_energy","air_mass","state_continuity","scenario_regression"]}
 (D/"C127_INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__":main()
