"""Independent C104 physics and source QA. No import from c104_psychrometric."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
REC=D.parent
C100=REC/"AUTONOMOUS_RUN_20261030_2052_DCHR_C100_POOL_AIR_HVAC"/"C100_AIR_HOURLY.csv.gz"
C102=REC/"AUTONOMOUS_RUN_20261030_2148_DCHR_C102_HVAC_AUX_ENERGY"/"C102_AUX_HOURLY.csv.gz"
C104=D/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
P=101.325; M=3540.0; T=29.0
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def sat(t):return .61094*math.exp((17.625*t)/(243.04+t))
def w(t,r):return .62198*r*sat(t)/(P-r*sat(t))
def dp(ww):
 pv=P*ww/(.62198+ww);z=math.log(pv/.61094)
 return 243.04*z/(17.625-z)
def h(t,ww):return (1.006+1.86*ww)*t+2501*ww
def ok(a,b,tol=2e-8):
 return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=tol
def inspect(a,b,c):
 checks=0
 def ck(x):
  nonlocal checks
  if not x:raise AssertionError("QA_FAILED at "+str((c.get("scenario"),c.get("time"),checks)))
  checks+=1
 for key in ("scenario","time"):ck(a[key]==b[key]==c[key])
 for key in ("Tout_C",):ck(ok(float(a[key]),float(c[key]),1e-8))
 rh=float(a["RH_out_assumed"]);eta=float(a["HRV_sensible_eff"]);tout=float(c["Tout_C"])
 wo=w(tout,rh);wi=w(29,.55)
 evap=float(a["evap_kg"]);cget=lambda name:float(c[name])
 pre=max(tout+eta*(29-tout),dp(wo))
 ck(ok(cget("precoil_C"),pre))
 ck(cget("precoil_C")>=dp(wo)-2e-8)
 wet=wo>wi
 coil_t=dp(wi) if wet else min(pre,29)
 condensate=M*max(wo-wi,0)
 w_coil=min(wo,wi)
 room_net=evap+M*(w_coil-wi)
 room_dehum=max(0,room_net);humid=max(0,-room_net)
 ck(ok(cget("coil_out_C"),coil_t))
 ck(ok(cget("outdoor_condensate_kg"),condensate))
 ck(ok(cget("room_dehum_kg"),room_dehum))
 ck(ok(cget("humidification_kg"),humid))
 ck(ok(cget("outdoor_condensate_kg")+cget("room_dehum_kg")-cget("humidification_kg"),
       float(a["dehum_kg"])-float(a["humidification_kg"]),1e-7))
 ck(abs(cget("moisture_residual_kg"))<1e-7)
 qcond=condensate*4.186*coil_t/3600000
 qcoil=M*(h(pre,wo)-h(coil_t,w_coil))/3600000-qcond
 ck(qcoil>=-1e-9)
 ck(ok(cget("coil_condensate_enthalpy_MWh"),qcond))
 ck(ok(cget("coil_cooling_MWh_th"),max(0,qcoil)))
 ck(ok(cget("coil_electric_MWh"),max(0,qcoil)/3))
 ck(abs(cget("coil_enthalpy_residual_MWh"))<1e-9)
 reheat=max(0,M*(h(29,w_coil)-h(coil_t,w_coil))/3600000)
 room_el=room_dehum*.5/1000
 room_latent=room_dehum*(2501-2.361*29)/3600000
 credit=min(reheat,.5*(room_latent+room_el))
 ck(ok(cget("air_reheat_gross_MWh_th"),reheat))
 ck(ok(cget("room_dehum_electric_MWh"),room_el))
 ck(ok(cget("room_condenser_credit_MWh_th"),credit))
 ck(ok(cget("air_external_heat_MWh_th"),reheat-credit))
 steam_el=humid*.75/1000
 steam_ideal=humid*(2676-4.186*20)/3600000
 ck(ok(cget("steam_electric_MWh"),steam_el))
 ck(ok(cget("steam_ideal_MWh"),steam_ideal))
 ck(ok(cget("steam_loss_MWh"),steam_el-steam_ideal))
 ck(cget("steam_loss_MWh")>=-1e-9)
 ck(ok(cget("fan_electric_MWh"),1.25/1000))
 ck(ok(cget("total_HVAC_electric_MWh"),steam_el+room_el+1.25/1000+max(0,qcoil)/3))
 ck(cget("air_external_heat_MWh_th")>=-1e-10)
 ck(cget("total_HVAC_electric_MWh")>=0)
 return checks

def run():
 m=json.loads((D/"C104_METADATA.json").read_text(encoding="utf-8"))
 assert m["synthetic"] and not m["field_validated"] and m["source_signoffs_added"]==0
 assert digest(C100)==m["source_C100_sha256"]
 assert digest(C102)==m["source_C102_sha256"]
 assert digest(C104)==m["hourly_sha256"]
 totals=defaultdict(lambda:defaultdict(float));count=defaultdict(int);n=0;wet=0
 with gzip.open(C100,"rt",encoding="utf-8",newline="") as f1,gzip.open(C102,"rt",encoding="utf-8",newline="") as f2,gzip.open(C104,"rt",encoding="utf-8",newline="") as f3:
  r1=csv.DictReader(f1);r2=csv.DictReader(f2);r3=csv.DictReader(f3)
  for a,b,c in zip(r1,r2,r3):
   n+=inspect(a,b,c)
   scenario=c["scenario"];count[scenario]+=1
   wet+=int(float(c["outdoor_condensate_kg"])>1e-8)
   for k in ("coil_cooling_MWh_th","total_HVAC_electric_MWh","air_external_heat_MWh_th","outdoor_condensate_kg"):
    totals[scenario][k]+=float(c[k])
   totals[scenario]["baseline_electric_MWh"]+=float(b["total_HVAC_electric_MWh"])
  assert next(r1,None) is None and next(r2,None) is None and next(r3,None) is None
 assert len(count)==9 and all(x==8760 for x in count.values())
 with (D/"C104_PSYCHROMETRIC_SUMMARY.csv").open(encoding="utf-8",newline="") as f:
  rows=list(csv.DictReader(f))
 assert len(rows)==9
 for row in rows:
  name=row["scenario"];assert int(row["hours"])==count[name]
  for k in ("coil_cooling_MWh_th","total_HVAC_electric_MWh","air_external_heat_MWh_th","outdoor_condensate_kg"):
   assert ok(float(row[k]),totals[name][k],3e-7)
 assert wet>0 and totals["RHout70_HRV50"]["coil_cooling_MWh_th"]>0
 # Negative controls deliberately tamper with two independent conservation equations.
 with gzip.open(C104,"rt",encoding="utf-8",newline="") as f:
  orig=next(csv.DictReader(f))
 with gzip.open(C100,"rt",encoding="utf-8",newline="") as f:
  a=next(csv.DictReader(f))
 with gzip.open(C102,"rt",encoding="utf-8",newline="") as f:
  b=next(csv.DictReader(f))
 caught=0
 for field in ("total_HVAC_electric_MWh","room_dehum_kg"):
  broken=dict(orig);broken[field]=str(float(broken[field])+0.123)
  try:inspect(a,b,broken)
  except AssertionError:caught+=1
 assert caught==2
 result={"status":"PASS","rows_checked":sum(count.values()),"scenarios":len(count),
  "assertions":n,"negative_controls":caught,"outdoor_coil_active_hours":wet,
  "anchor_RHout70_HRV50":{k:round(v,6) for k,v in totals["RHout70_HRV50"].items()},
  "source_sha_verified":True,"hourly_sha_verified":True,"summary_sha_verified":digest(D/"C104_PSYCHROMETRIC_SUMMARY.csv")==m["summary_sha256"],
  "notes":"Independent psychrometric formulas; C104 is an alternative, not additive, to C102."}
 assert result["summary_sha_verified"]
 p=D/"C104_INDEPENDENT_QA.json"
 with p.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(result,indent=2))
if __name__=="__main__":run()
