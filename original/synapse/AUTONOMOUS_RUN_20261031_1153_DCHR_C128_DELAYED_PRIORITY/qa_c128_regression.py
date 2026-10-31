"""Cross-version regression: C128 zero-delay 150kW must reproduce C127 first week."""
import csv,gzip,json,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent
OLD=D.parent/"AUTONOMOUS_RUN_20261031_1049_DCHR_C127_BOUNDED_DISPATCH"/"C127_BOUNDED_QUARTER.csv.gz"
NEW=D/"C128_DELAYED_PRIORITY.csv.gz"
FIELDS=("pool_T1","air_T1","w1","pool_heat_kJ","air_heat_kJ")
def main():
 old={};new={}
 with gzip.open(OLD,"rt",encoding="utf-8") as f:
  for r in csv.DictReader(f):
   if r["scenario"] not in ("water_150kW","air_150kW"):continue
   name=("water_first" if r["scenario"]=="water_150kW" else "air_first")+"_150kW_d0"
   key=(name,r["time"],int(r["quarter"]))
   if len(old)>=1344:break
   old[key]=r
 with gzip.open(NEW,"rt",encoding="utf-8") as f:
  for r in csv.DictReader(f):
   if r["scenario"].endswith("150kW_d0"):new[(r["scenario"],r["time"],int(r["quarter"]))]=r
 assert len(old)==len(new)==1344 and old.keys()==new.keys()
 diff=0.
 for k in old:
  for f in FIELDS:
   e=abs(float(old[k][f])-float(new[k][f]));diff=max(diff,e)
   assert e<2e-9,(k,f,e)
 res={"status":"PASS","baseline":"C127","matched_quarters":1344,"matched_numeric_fields":1344*len(FIELDS),"max_abs_difference":diff,
 "baseline_sha256":hashlib.sha256(OLD.read_bytes()).hexdigest()}
 (D/"C128_REGRESSION_QA.json").write_text(json.dumps(res,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(res,indent=2))
if __name__=="__main__":main()
