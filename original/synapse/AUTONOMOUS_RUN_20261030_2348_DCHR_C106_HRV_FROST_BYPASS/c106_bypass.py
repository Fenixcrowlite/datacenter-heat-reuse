"""C106 synthetic HRV frost-risk bypass. Reuses immutable C104 rows, no physical validation."""
import csv,gzip,hashlib,json,math,os,sys
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
SCC=D.parent.parent
SRC=D.parent/"AUTONOMOUS_RUN_20261030_2254_DCHR_C104_PSYCHROMETRIC_LEDGER"/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
SOURCE_SHA="15547bfd196152440ec1870af182ef20a79ab1004790cf71d1de9869b447228d"
ROOTS=(D,D.parent,SCC,Path("C:/Users/Lysda/OneDrive/Projects/DataCenter_Heat_Reuse"))
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
TIN=29.0
TRIGGER=2.0
RELEASE=4.0
MIN_DWELL=3
TASK="scc-2aab24704c2bd0"
FIELDS=("scenario","time","Tout_C","RH_out","nominal_eff","active_eff","bypass",
 "baseline_exhaust_C","controlled_exhaust_C","baseline_frost_risk","controlled_frost_risk",
 "baseline_electric_MWh","controlled_electric_MWh","delta_electric_MWh",
 "baseline_external_heat_MWh_th","controlled_external_heat_MWh_th","delta_external_heat_MWh_th",
 "baseline_coil_cooling_MWh_th","controlled_coil_cooling_MWh_th",
 "baseline_dehum_kg","controlled_dehum_kg","baseline_humid_kg","controlled_humid_kg")
def digest(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def guard():
 for root in ROOTS:
  for flag in FLAGS:
   if (root/flag).exists():raise RuntimeError("STOP_ACTIVE "+str(root/flag))
def exhaust(tout,eff):return TIN-eff*(TIN-tout)
def choose(bypass,elapsed,tout,eff):
 risk=exhaust(tout,eff)<TRIGGER
 safe=exhaust(tout,eff)>RELEASE
 if eff==0:return False
 if not bypass and risk:return True
 if bypass and elapsed>=MIN_DWELL and safe:return False
 return bypass
def selftest():
 assert choose(False,0,-10,.8) is True
 assert choose(True,1,0,.8) is True
 assert choose(True,3,0,.8) is False
 assert choose(False,0,10,.5) is False
 assert choose(False,0,-30,0) is False
 assert exhaust(-10,0)==TIN
 assert exhaust(-10,.8)<TRIGGER
 assert RELEASE>TRIGGER and MIN_DWELL>=1
 return 8
def run():
 guard();assert digest(SRC)==SOURCE_SHA,"SOURCE_DRIFT"
 assert not any((D/x).exists() for x in ("C106_BYPASS_HOURLY.csv.gz","C106_SUMMARY.csv","C106_METADATA.json"))
 zero={}
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f:
  for row in csv.DictReader(f):
   if row["scenario"].endswith("_HRV0"):
    zero[(row["scenario"].split("_HRV")[0],row["time"])]=row
 assert len(zero)==3*8760
 stats=defaultdict(lambda:defaultdict(float))
 state={};age={};counts=defaultdict(int);prev={}
 tmp=D/"C106_BYPASS_HOURLY.partial.csv.gz"
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as f,gzip.open(tmp,"wt",encoding="utf-8",newline="",compresslevel=4) as o:
  wr=csv.writer(o);wr.writerow(FIELDS)
  for i,a in enumerate(csv.DictReader(f)):
   if i%1000==0:guard()
   name=a["scenario"];group=name.split("_HRV")[0];t=a["time"]
   z=zero[(group,t)]
   tout=float(a["Tout_C"]);eff=float(a["HRV_eff"])
   assert a["time"]==z["time"] and abs(tout-float(z["Tout_C"]))<1e-10
   assert a["RH_out"]==z["RH_out"]
   assert eff in (0.0,0.5,0.8)
   if name in prev:assert t>prev[name]
   prev[name]=t
   old=state.get(name,False)
   elapsed=age.get(name,MIN_DWELL)
   bypass=choose(old,elapsed,tout,eff)
   if bypass!=old:elapsed=0;stats[name]["switches"]+=1
   else:elapsed+=1
   state[name]=bypass;age[name]=elapsed
   selected=z if bypass else a
   active=0.0 if bypass else eff
   base_ex=exhaust(tout,eff);ctrl_ex=exhaust(tout,active)
   risk0=int(base_ex<TRIGGER);risk1=int(ctrl_ex<TRIGGER)
   assert not risk1,"FROST_RISK_UNCONTROLLED"
   def n(r,k):return float(r[k])
   be=n(a,"total_HVAC_electric_MWh");ce=n(selected,"total_HVAC_electric_MWh")
   bh=n(a,"air_external_heat_MWh_th");ch=n(selected,"air_external_heat_MWh_th")
   bc=n(a,"coil_cooling_MWh_th");cc=n(selected,"coil_cooling_MWh_th")
   vals=(name,t,a["Tout_C"],a["RH_out"],eff,active,int(bypass),base_ex,ctrl_ex,risk0,risk1,
    be,ce,ce-be,bh,ch,ch-bh,bc,cc,n(a,"room_dehum_kg"),n(selected,"room_dehum_kg"),
    n(a,"humidification_kg"),n(selected,"humidification_kg"))
   wr.writerow([v if isinstance(v,str) else f"{v:.12f}" for v in vals])
   s=stats[name];counts[name]+=1
   s["bypass_hours"]+=int(bypass);s["baseline_frost_risk_hours"]+=risk0
   s["controlled_frost_risk_hours"]+=risk1
   for k,v in (("baseline_electric_MWh",be),("controlled_electric_MWh",ce),
    ("baseline_external_heat_MWh_th",bh),("controlled_external_heat_MWh_th",ch),
    ("baseline_coil_cooling_MWh_th",bc),("controlled_coil_cooling_MWh_th",cc)):
    s[k]+=v
 assert len(counts)==9 and all(v==8760 for v in counts.values())
 guard();os.replace(tmp,D/"C106_BYPASS_HOURLY.csv.gz")
 keys=("bypass_hours","switches","baseline_frost_risk_hours","controlled_frost_risk_hours",
  "baseline_electric_MWh","controlled_electric_MWh","delta_electric_MWh",
  "baseline_external_heat_MWh_th","controlled_external_heat_MWh_th","delta_external_heat_MWh_th",
  "baseline_coil_cooling_MWh_th","controlled_coil_cooling_MWh_th")
 with (D/"C106_SUMMARY.csv").open("x",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(("scenario","hours")+keys)
  for name in sorted(counts):
   s=stats[name]
   s["delta_electric_MWh"]=s["controlled_electric_MWh"]-s["baseline_electric_MWh"]
   s["delta_external_heat_MWh_th"]=s["controlled_external_heat_MWh_th"]-s["baseline_external_heat_MWh_th"]
   w.writerow([name,counts[name]]+[int(s[k]) if k.endswith("hours") or k=="switches" else f"{s[k]:.9f}" for k in keys])
 meta={"schema":"C106_FROST_BYPASS_V1","task_id":TASK,"synthetic":True,"field_validated":False,
  "source_signoffs_added":0,"source_C104_sha256":SOURCE_SHA,
  "hourly_sha256":digest(D/"C106_BYPASS_HOURLY.csv.gz"),
  "summary_sha256":digest(D/"C106_SUMMARY.csv"),"rows":sum(counts.values()),"scenarios":len(counts),
  "assumptions":{"indoor_C":TIN,"trigger_exhaust_C":TRIGGER,"release_exhaust_C":RELEASE,
   "minimum_bypass_dwell_hours":MIN_DWELL,"exhaust_proxy":"T_exhaust = T_indoor - eta*(T_indoor - T_outdoor)"},
  "boundary":"C104 source rows reused verbatim. Bypass selects the C104 HRV0 case for same RH/time; no added energy terms.",
  "limitations":["Frost threshold and exhaust proxy are hypothetical, not measured manufacturer frost curve.",
   "Bypass is frost-risk protection, not an energy-saving optimizer; increased heating is possible.",
   "No defrost cycle, damper transient, fan pressure change or real weather/flows.",
   "No real plant validation or new primary-source signoffs."]}
 with (D/"C106_METADATA.json").open("x",encoding="utf-8") as f:json.dump(meta,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps({"selftests":selftest(),"rows":meta["rows"],"hourly_sha256":meta["hourly_sha256"],
  "HRV80_RH70":{k:round(v,6) for k,v in stats["RHout70_HRV80"].items()}},indent=2))
if __name__=="__main__":
 selftest() if "--selftest" in sys.argv else run()
