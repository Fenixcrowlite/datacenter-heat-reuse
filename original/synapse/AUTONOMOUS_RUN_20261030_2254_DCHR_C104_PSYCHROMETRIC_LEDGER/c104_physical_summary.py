"""Canonical C104 annual summary. Never sum state temperatures or residuals."""
import csv,gzip,hashlib,json,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
R=D.parent
SRC=D/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
BASE=R/"AUTONOMOUS_RUN_20261030_2148_DCHR_C102_HVAC_AUX_ENERGY"/"C102_AUX_HOURLY.csv.gz"
OUT=D/"C104_PHYSICAL_SUMMARY.csv"
ENERGY=("coil_cooling_MWh_th","coil_condensate_enthalpy_MWh","coil_electric_MWh",
 "room_dehum_electric_MWh","fan_electric_MWh","steam_electric_MWh","steam_ideal_MWh",
 "steam_loss_MWh","air_reheat_gross_MWh_th","room_condenser_credit_MWh_th",
 "air_external_heat_MWh_th","total_HVAC_electric_MWh")
MASS=("outdoor_condensate_kg","room_dehum_kg","humidification_kg")
HEAD=("scenario","hours","coil_active_hours")+ENERGY+MASS+("moisture_max_abs_kg",
 "coil_enthalpy_max_abs_MWh","baseline_C102_electric_MWh","delta_electric_MWh")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def run():
 m=json.loads((D/"C104_METADATA.json").read_text(encoding="utf-8"))
 assert sha(SRC)==m["hourly_sha256"] and sha(BASE)==m["source_C102_sha256"]
 for root in (D,D.parent,D.parent.parent,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
  for f in ("STOP","STOP.flag","PAUSE","PAUSE.flag"):
   if (root/f).exists():raise RuntimeError("STOP_ACTIVE")
 agg=defaultdict(lambda:defaultdict(float))
 with gzip.open(SRC,"rt",encoding="utf-8",newline="") as a,gzip.open(BASE,"rt",encoding="utf-8",newline="") as b:
  for x,y in zip(csv.DictReader(a),csv.DictReader(b)):
   assert x["scenario"]==y["scenario"] and x["time"]==y["time"]
   z=agg[x["scenario"]];z["hours"]+=1
   z["coil_active_hours"]+=int(float(x["outdoor_condensate_kg"])>1e-8)
   for k in ENERGY+MASS:z[k]+=float(x[k])
   z["moisture_max_abs_kg"]=max(z["moisture_max_abs_kg"],abs(float(x["moisture_residual_kg"])))
   z["coil_enthalpy_max_abs_MWh"]=max(z["coil_enthalpy_max_abs_MWh"],abs(float(x["coil_enthalpy_residual_MWh"])))
   z["baseline_C102_electric_MWh"]+=float(y["total_HVAC_electric_MWh"])
 assert len(agg)==9 and all(int(x["hours"])==8760 for x in agg.values())
 with OUT.open("x",encoding="utf-8",newline="") as f:
  w=csv.writer(f);w.writerow(HEAD)
  for name in sorted(agg):
   x=agg[name];x["delta_electric_MWh"]=x["total_HVAC_electric_MWh"]-x["baseline_C102_electric_MWh"]
   w.writerow([name]+[int(x[k]) if k in ("hours","coil_active_hours") else f"{x[k]:.9f}" for k in HEAD[1:]])
 print(json.dumps({"physical_summary_sha256":sha(OUT),"scenarios":len(agg),
 "anchor":{k:round(v,6) for k,v in agg["RHout70_HRV50"].items() if k in
 ("total_HVAC_electric_MWh","baseline_C102_electric_MWh","delta_electric_MWh","coil_active_hours","coil_cooling_MWh_th")}},indent=2))
if __name__=="__main__":run()
