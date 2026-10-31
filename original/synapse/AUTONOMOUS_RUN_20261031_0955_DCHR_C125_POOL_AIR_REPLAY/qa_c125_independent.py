"""Independent CSV-only C125 QA: no imports from C125/C124/C93."""
import csv,gzip,hashlib,json,math,datetime
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
DATA=D/"C125_POOL_AIR_QUARTER.csv.gz"
SOURCE=D.parent/"AUTONOMOUS_RUN_20261031_0446_DCHR_C116_RH_EVAP_COUPLED"/"C116_TWO_WAY_HOURLY.csv.gz"
CAP_KJ=500.*997.*4.186
M=3540.;P=101.325;EPS=.62198
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def w_supply():
 t=26.;rh=.55
 pv=rh*.61094*math.exp(17.625*t/(t+243.04))
 return EPS*pv/(P-pv)
WS=w_supply()
def h(t,w):return M*(1.006*t+w*(2501.+1.86*t))
def check(r):
 f=lambda k:float(r[k])
 assert r["mode"] in ("fixed_RH","feedback_RH")
 assert 0<=int(r["quarter"])<4
 assert 0<f("pool_T0")<45 and 0<f("pool_T1")<45
 assert 0<=f("RH0")<=1.000001 and 0<=f("RH1")<=1.000001
 assert f("evap_kg")>=0
 assert abs(f("latent_kJ")-f("air_evap_kJ"))<1e-6
 assert abs(f("latent_kJ")-f("evap_kg")*(2501.-2.361*f("pool_T0")))<1e-6
 assert abs(f("pool_loss_kJ")-f("latent_kJ")-f("makeup_kJ")-f("other_loss_kJ"))<1e-6
 assert abs(f("air_H0_kJ")-h(f("air_T0"),f("w0")))<3e-5
 assert abs(f("air_H1_kJ")-h(f("air_T1"),f("w1")))<3e-5
 assert abs(f("pool_residual_kJ"))<1e-5 and abs(f("air_residual_kJ"))<1e-5
 assert abs(f("combined_residual_kJ"))<1e-5
 pool=CAP_KJ*(f("pool_T1")-f("pool_T0"))-f("pool_heat_kJ")+f("pool_loss_kJ")
 air=f("air_H1_kJ")-f("air_H0_kJ")-(f("air_evap_kJ")+f("vent_kJ")+f("hvac_kJ")-f("dehum_kJ")+f("humid_kJ")-f("cond_kJ"))
 assert abs(pool)<1e-5 and abs(air)<1e-5
 combined=CAP_KJ*(f("pool_T1")-f("pool_T0"))+f("air_H1_kJ")-f("air_H0_kJ")-(f("pool_heat_kJ")-f("makeup_kJ")-f("other_loss_kJ")+f("vent_kJ")+f("hvac_kJ")-f("dehum_kJ")+f("humid_kJ")-f("cond_kJ"))
 assert abs(combined)<1e-5
 qvap=2501.+1.86*f("air_T0")
 dehum=f("dehum_kJ")/qvap
 humid=f("humid_kJ")/qvap
 cond=f("cond_kJ")/(4.186*f("air_T1")) if f("cond_kJ") else 0.
 vent=885.*(WS-f("w0"))
 assert abs(M*(f("w1")-f("w0"))-(f("evap_kg")+vent-dehum+humid-cond))<2e-7
 assert abs(f("air_mass_residual_kg"))<1e-7
 return 1
def negative_controls(example):
 def reject(k,v):
  d=dict(example);d[k]=v
  try:check(d)
  except (AssertionError,ValueError,OverflowError):return True
  return False
 assert reject("latent_kJ",str(float(example["latent_kJ"])+1))
 assert reject("pool_heat_kJ",str(float(example["pool_heat_kJ"])+10))
 assert reject("RH1","1.2")
 assert reject("evap_kg","-1")
 assert reject("air_H1_kJ",str(float(example["air_H1_kJ"])+100))
 return 5
def main():
 meta=json.loads((D/"C125_METADATA.json").read_text(encoding="utf-8"))
 assert meta["data_sha256"]==sha(DATA) and meta["summary_sha256"]==sha(D/"C125_SUMMARY.json")
 assert meta["source_sha256"]["source"]==sha(SOURCE)
 expected={}
 with gzip.open(SOURCE,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["policy"]=="water_first" and r["control"]=="ideal":
    expected[r["time"]]=float(r["pool_HP_heat_MWh"])*3600000.
 assert len(expected)==8760
 prev={};counts=defaultdict(int);heats=defaultdict(float);example=None
 with gzip.open(DATA,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   check(r);example=example or r
   mode=r["mode"];q=int(r["quarter"]);time=r["time"]
   assert time in expected
   if mode in prev:
    old=prev[mode]
    assert (time==old["time"] and q==int(old["quarter"])+1) or (q==0 and int(old["quarter"])==3 and datetime.datetime.fromisoformat(time)-datetime.datetime.fromisoformat(old["time"])==datetime.timedelta(hours=1))
    for a,b in (("pool_T0","pool_T1"),("air_T0","air_T1"),("w0","w1")):
     assert abs(float(r[a])-float(old[b]))<2e-10
   prev[mode]=r;counts[mode]+=1;heats[(mode,time)]+=float(r["pool_heat_kJ"])
 for mode in ("fixed_RH","feedback_RH"):
  assert counts[mode]==35040
  assert sum(abs(heats[(mode,t)]-h) for t,h in expected.items())<1e-4
 neg=negative_controls(example)
 result={"status":"PASS","rows":sum(counts.values()),"per_mode":dict(counts),
         "negative_controls":neg,"source_hours":len(expected),
         "data_sha256":sha(DATA),"source_sha256":sha(SOURCE),
         "mass_and_energy_checks":sum(counts.values()),"independent":True}
 (D/"C125_INDEPENDENT_QA.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(result,indent=2))
if __name__=="__main__":main()
