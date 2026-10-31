"""Independent float-based verification; deliberately does not import audit module."""
import csv, datetime as dt, hashlib, json, math
from pathlib import Path
H=Path(__file__).resolve().parent
r=json.loads((H/"SIM_ENERGY_AUDIT.json").read_text(encoding="utf-8"))
p=Path(r["source_path"])
assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==r["source_sha256"]
keys=list(r["integrated_mwh"])
vals={k:[] for k in keys}
count=0; curtailed_intervals=0; bad_used_balance=0; bad_produced_balance=0
with p.open(encoding="utf-8-sig",newline="") as f:
 reader=csv.DictReader(f)
 for row in reader:
  count+=1
  x={k:float(row[k]) for k in keys}
  assert all(math.isfinite(v) and v>=0 for v in x.values())
  for k in keys:vals[k].append(x[k])
  if x["Curtailed_HP_Heat_MW"]>1e-9:curtailed_intervals+=1
  if abs(x["HP_Heat_Used_MW"]-x["HP_Source_Used_MW"]-x["HP_Electric_MW"])>1e-6:bad_used_balance+=1
  if abs(x["HP_Heat_MW"]-x["HP_Heat_Used_MW"]-x["Curtailed_HP_Heat_MW"])>1e-6:bad_produced_balance+=1
assert count==8760==r["rows"]
sums={k:math.fsum(v) for k,v in vals.items()}
diffs={k:abs(sums[k]-float(r["integrated_mwh"][k])) for k in keys}
assert all(v<1e-6 for v in diffs.values()),diffs
pue=sums["DC_Total_MW"]/sums["IT_MW"]
assert abs(pue-float(r["PUE_simulated"]))<1e-12
assert bad_used_balance==bad_produced_balance==0
assert curtailed_intervals==4587
assert r["ERF"] is None and r["REF"] is None and r["WUE"] is None
assert r["data_class"]=="SIMULATED_MODEL_OUTPUT_NOT_METERED"
curtailed_fraction=sums["Curtailed_HP_Heat_MW"]/sums["HP_Heat_MW"]
out={"status":"PASS","independent_method":"math.fsum float, no import of audit module",
     "rows_checked":count,"energy_fields_checked":len(keys),
     "max_energy_difference_mwh":max(diffs.values()),
     "pue_float":pue,"curtailed_intervals":curtailed_intervals,
     "curtailed_fraction_of_potential_hp_heat":curtailed_fraction,
     "used_heat_balance_failures":bad_used_balance,
     "potential_heat_balance_failures":bad_produced_balance,
     "full_primary_signoff":False,"measured_site_data":False}
(H/"QA_INDEPENDENT.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out))
