"""C104: alternate, synthetic psychrometric outdoor-air conditioning ledger.
Immutable SHA-pinned C100/C102 sources. NOT an equipment or pool-system validation.
This is an ALTERNATIVE to C102 totals, not an additive correction.
"""
import csv, gzip, hashlib, json, math, os, sys
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C100=REC/"AUTONOMOUS_RUN_20261030_2052_DCHR_C100_POOL_AIR_HVAC"/"C100_AIR_HOURLY.csv.gz"
C102=REC/"AUTONOMOUS_RUN_20261030_2148_DCHR_C102_HVAC_AUX_ENERGY"/"C102_AUX_HOURLY.csv.gz"
SHA100="8ce8e04be652540eb635afb75958077c716220a26f3471526264985e0862fff4"
SHA102="7758cda64fb64840d249cceb9d9fa59d63fc17310d7a4c1a9a32fde46e5f275f"
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
P=101.325
T_IN=29.0
W_IN=0.62198*(0.55*0.61094*math.exp(17.625*T_IN/(T_IN+243.04)))/(P-0.55*0.61094*math.exp(17.625*T_IN/(T_IN+243.04)))
M_DRY=3000.0*1.18
COP=3.0
FAN_MWH=3000.0/3600*1.5/1000
STEAM_KWH_KG=0.75
DEHUM_KWH_KG=0.5
COND_CREDIT_FRACTION=0.5
FIELDS=("scenario","time","Tout_C","RH_out","HRV_eff","precoil_C","coil_out_C",
 "outdoor_condensate_kg","room_dehum_kg","humidification_kg",
 "coil_cooling_MWh_th","coil_condensate_enthalpy_MWh","coil_electric_MWh",
 "room_dehum_electric_MWh","fan_electric_MWh","steam_electric_MWh",
 "steam_ideal_MWh","steam_loss_MWh","air_reheat_gross_MWh_th",
 "room_condenser_credit_MWh_th","air_external_heat_MWh_th",
 "total_HVAC_electric_MWh","moisture_residual_kg","coil_enthalpy_residual_MWh")

def sha(path):
 h=hashlib.sha256()
 with path.open("rb") as f:
  for block in iter(lambda:f.read(1048576),b""):h.update(block)
 return h.hexdigest()

def guard():
 for root in (D,REC,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))

def sat(t):
 if not math.isfinite(t) or not -50<t<80:raise ValueError("INVALID_T")
 return 0.61094*math.exp(17.625*t/(t+243.04))

def w_ratio(t,rh):
 if not math.isfinite(rh) or not 0<=rh<=1:raise ValueError("INVALID_RH")
 pv=rh*sat(t)
 if not 0<=pv<P:raise ValueError("INVALID_PV")
 return 0.62198*pv/(P-pv)

def dewpoint(w):
 if not math.isfinite(w) or w<=0:raise ValueError("INVALID_W")
 pv=P*w/(0.62198+w)
 z=math.log(pv/0.61094)
 t=243.04*z/(17.625-z)
 if not -50<t<80:raise ValueError("DEWPOINT_RANGE")
 return t

def enthalpy(t,w):
 return 1.006*t+w*(2501+1.86*t) # kJ/kg dry air

def calc(tout,rh,hrv,evap,legacy_dehum,legacy_humid):
 vals=(tout,rh,hrv,evap,legacy_dehum,legacy_humid)
 if not all(math.isfinite(x) for x in vals):raise ValueError("NONFINITE")
 if not -40<tout<60 or not 0<=rh<=1 or not 0<=hrv<=1 or min(evap,legacy_dehum,legacy_humid)<0:
  raise ValueError("OUT_OF_RANGE")
 wo=w_ratio(tout,rh)
 # Sensible-only HRV cannot cool humid air below its own dewpoint without condensation.
 pre=max(tout+hrv*(T_IN-tout),dewpoint(wo))
 if wo>W_IN:
  tc=dewpoint(W_IN)
  wc=W_IN
  mcond=M_DRY*(wo-W_IN)
 else:
  tc=min(pre,T_IN)
  wc=wo
  mcond=0.0
 # Condensate leaves the coil as liquid, so its sensible enthalpy is explicit.
 condensate_h=mcond*4.186*tc/3_600_000
 hin=M_DRY*enthalpy(pre,wo)/3_600_000
 hout=M_DRY*enthalpy(tc,wc)/3_600_000
 cool=max(0.0,hin-hout-condensate_h)
 residual=hin-hout-condensate_h-cool
 room_net=evap+M_DRY*(wc-W_IN)
 room_dehum=max(0.0,room_net)
 humid=max(0.0,-room_net)
 moisture=evap+M_DRY*(wo-W_IN)-mcond-room_dehum+humid
 legacy_residual=legacy_dehum-legacy_humid-(room_dehum+mcond-humid)
 if abs(moisture)>1e-7 or abs(legacy_residual)>1e-7:raise RuntimeError("MOISTURE_CLOSURE")
 if abs(residual)>1e-10:raise RuntimeError("COIL_ENTHALPY_CLOSURE")
 reheat=max(0.0,M_DRY*(enthalpy(T_IN,wc)-enthalpy(tc,wc))/3_600_000)
 dehum_el=room_dehum*DEHUM_KWH_KG/1000
 room_latent=room_dehum*(2501-2.361*T_IN)/3_600_000
 credit=min(reheat,COND_CREDIT_FRACTION*(room_latent+dehum_el))
 heat=reheat-credit
 steam_el=humid*STEAM_KWH_KG/1000
 steam_ideal=humid*(2676-4.186*20)/3_600_000
 steam_loss=steam_el-steam_ideal
 if steam_loss < -1e-10:raise RuntimeError("STEAM_ENERGY_DEFICIT")
 cool_el=cool/COP
 electric=cool_el+dehum_el+FAN_MWH+steam_el
 return (pre,tc,mcond,room_dehum,humid,cool,condensate_h,cool_el,dehum_el,
         FAN_MWH,steam_el,steam_ideal,steam_loss,reheat,credit,heat,electric,moisture,residual)

def selftest():
 n=0
 def check(cond):
  nonlocal n
  if not cond:raise AssertionError("SELFTEST_"+str(n+1))
  n+=1
 for t in (-10,0,15,25,35):
  check(abs(dewpoint(w_ratio(t,1))-t)<1e-9)
 a=calc(35,.9,0,5,5+M_DRY*(w_ratio(35,.9)-W_IN),0)
 check(a[2]>0 and a[5]>0 and a[7]>0) # hot-humid coil
 check(a[3]>0 and a[4]==0)
 check(abs(a[-1])<1e-12 and abs(a[-2])<1e-7)
 b=calc(-10,.4,.5,5,0,max(0,M_DRY*(W_IN-w_ratio(-10,.4))-5))
 check(b[5]==0 and b[15]>0)
 check(b[4]>0 and b[11]>0 and b[12]>=0)
 c=calc(35,.1,0,5,max(0,5+M_DRY*(w_ratio(35,.1)-W_IN)),max(0,-5-M_DRY*(w_ratio(35,.1)-W_IN)))
 check(c[5]>0 and c[2]==0) # hot-dry sensible cooling
 d=calc(35,.9,.8,5,5+M_DRY*(w_ratio(35,.9)-W_IN),0)
 check(d[0]>=dewpoint(w_ratio(35,.9))-1e-10) # HRV no impossible supersaturation
 check(abs(a[16]-(a[7]+a[8]+a[9]+a[10]))<1e-12)
 for bad in ((35,1.2,0,0,0,0),(35,.5,1.2,0,0,0),(35,.5,0,-1,0,0),(float("nan"),.5,0,0,0,0)):
  try:calc(*bad)
  except ValueError:n+=1
  else:raise AssertionError("INVALID_ACCEPTED")
 print(f"C104 SELFTEST {n}/{n} PASS")
 return n

def run():
 guard();selftest()
 if sha(C100)!=SHA100 or sha(C102)!=SHA102:raise RuntimeError("SOURCE_SHA_DRIFT")
 out=D/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
 tmp=D/"C104_PSYCHROMETRIC_HOURLY.partial.csv.gz"
 summ=D/"C104_PSYCHROMETRIC_SUMMARY.csv"
 meta=D/"C104_METADATA.json"
 if any(x.exists() for x in (out,tmp,summ,meta)):raise RuntimeError("OUTPUT_EXISTS")
 sums=defaultdict(lambda:defaultdict(float));counts=defaultdict(int)
 with gzip.open(C100,"rt",encoding="utf-8",newline="") as fa,gzip.open(C102,"rt",encoding="utf-8",newline="") as fb,gzip.open(tmp,"wt",encoding="utf-8",newline="",compresslevel=4) as fo:
  ra=csv.DictReader(fa);rb=csv.DictReader(fb);wr=csv.writer(fo);wr.writerow(FIELDS)
  for i,(a,b) in enumerate(zip(ra,rb)):
   if i%720==0:guard()
   if (a["scenario"],a["time"])!=(b["scenario"],b["time"]):raise RuntimeError("SOURCE_ROW_MISALIGN")
   if abs(float(a["Tout_C"])-float(b["Tout_C"]))>1e-7:raise RuntimeError("SOURCE_TEMP_MISMATCH")
   result=calc(float(a["Tout_C"]),float(a["RH_out_assumed"]),float(a["HRV_sensible_eff"]),
               float(a["evap_kg"]),float(a["dehum_kg"]),float(a["humidification_kg"]))
   scenario=a["scenario"];counts[scenario]+=1
   for key,v in zip(FIELDS[5:],result):sums[scenario][key]+=v
   wr.writerow([scenario,a["time"],a["Tout_C"],a["RH_out_assumed"],a["HRV_sensible_eff"]]+[f"{v:.12f}" for v in result])
  if next(ra,None) is not None or next(rb,None) is not None:raise RuntimeError("SOURCE_LENGTH_MISMATCH")
 if len(counts)!=9 or any(v!=8760 for v in counts.values()):raise RuntimeError("ROW_COUNTS")
 guard();os.replace(tmp,out)
 with summ.open("x",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(["scenario","hours"]+list(FIELDS[5:]))
  for scenario in sorted(counts):
   w.writerow([scenario,counts[scenario]]+[f"{sums[scenario][k]:.9f}" for k in FIELDS[5:]])
 m={"schema":"C104_PSYCHROMETRIC_ALTERNATIVE_V1","task_id":TASK,"synthetic":True,
    "field_validated":False,"source_signoffs_added":0,"scenarios":len(counts),"rows":sum(counts.values()),
    "source_C100_sha256":SHA100,"source_C102_sha256":SHA102,"hourly_sha256":sha(out),"summary_sha256":sha(summ),
    "assumptions":{"airflow_m3_h":3000,"dry_air_kg_h":M_DRY,"indoor_T_C":T_IN,"indoor_RH":.55,
      "coil_COP":COP,"dehumidifier_kWh_kg":DEHUM_KWH_KG,"steam_kWh_kg":STEAM_KWH_KG,
      "steam_enthalpy_kJ_kg":2676,"feedwater_T_C":20,"condenser_credit_fraction":COND_CREDIT_FRACTION},
    "boundary":"Alternative C102 conditioning scenario, NOT additive. Outdoor coil removes only outdoor humidity above indoor setpoint; residual room dehumidifier treats pool evaporation. Steam electricity contains steam enthalpy; no duplicate heat credit. Pool evaporation latent remains in water ledger.",
    "limitations":["Steady-state dry-air coil and fixed COP, no manufacturer curves.","C88 synthetic temperatures and scenario-constant RH; not measured.","HRV sensible-only with dewpoint floor, no frost or bypass dynamics.","No real coil sizing, pressure drops, condenser heat recovery verification, or integrated pool heat allocation."]}
 with meta.open("x",encoding="utf-8") as f:json.dump(m,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
 print(json.dumps({"rows":m["rows"],"scenarios":m["scenarios"],"sha256":m["hourly_sha256"],
   "anchor":{k:round(v,5) for k,v in sums["RHout70_HRV50"].items() if k in ("coil_cooling_MWh_th","total_HVAC_electric_MWh","air_external_heat_MWh_th","outdoor_condensate_kg")}},indent=2))
if __name__=="__main__":
 selftest() if "--selftest" in sys.argv else run()
