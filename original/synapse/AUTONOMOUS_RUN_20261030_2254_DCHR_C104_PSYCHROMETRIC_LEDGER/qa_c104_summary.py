"""Independent dimensional and annual aggregation check of canonical C104 summary."""
import csv,gzip,json,hashlib,math
from collections import defaultdict
from pathlib import Path
D=Path(__file__).resolve().parent
R=D.parent
P=D/"C104_PHYSICAL_SUMMARY.csv"
S=D/"C104_PSYCHROMETRIC_HOURLY.csv.gz"
B=R/"AUTONOMOUS_RUN_20261030_2148_DCHR_C102_HVAC_AUX_ENERGY"/"C102_AUX_HOURLY.csv.gz"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 assert P.exists() and S.exists()
 with P.open(encoding="utf-8",newline="") as f:rows=list(csv.DictReader(f))
 assert len(rows)==9 and len({x["scenario"] for x in rows})==9
 forbidden=("precoil_C","coil_out_C","Tout_C","moisture_residual_kg","coil_enthalpy_residual_MWh")
 assert not any(k in rows[0] for k in forbidden)
 sums=defaultdict(lambda:defaultdict(float))
 with gzip.open(S,"rt",encoding="utf-8",newline="") as f,gzip.open(B,"rt",encoding="utf-8",newline="") as g:
  for a,b in zip(csv.DictReader(f),csv.DictReader(g)):
   assert a["scenario"]==b["scenario"] and a["time"]==b["time"]
   d=sums[a["scenario"]];d["hours"]+=1
   d["coil_active_hours"]+=int(float(a["outdoor_condensate_kg"])>1e-8)
   for k in ("coil_cooling_MWh_th","total_HVAC_electric_MWh","air_external_heat_MWh_th","outdoor_condensate_kg","humidification_kg"):
    d[k]+=float(a[k])
   d["baseline_C102_electric_MWh"]+=float(b["total_HVAC_electric_MWh"])
 for row in rows:
  x=sums[row["scenario"]]
  for k in x:assert abs(float(row[k])-x[k])<1e-6,(row["scenario"],k)
  assert abs(float(row["delta_electric_MWh"])-(x["total_HVAC_electric_MWh"]-x["baseline_C102_electric_MWh"]))<1e-6
  assert int(row["hours"])==8760
  assert float(row["moisture_max_abs_kg"])<1e-7
  assert float(row["coil_enthalpy_max_abs_MWh"])<1e-9
 report={"status":"PASS","scenarios":9,"rows":sum(int(r["hours"]) for r in rows),
         "annual_comparisons":9*len(next(iter(sums.values())))+9,
         "dimensional_schema_check":True,"sha256":sha(P)}
 with (D/"C104_SUMMARY_QA.json").open("x",encoding="utf-8") as f:json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
 print(json.dumps(report,indent=2))
if __name__=="__main__":run()
