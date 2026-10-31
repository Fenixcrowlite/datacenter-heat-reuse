"""Independent C120 QA: source/legacy regression, mass closure, capacity, summary, negative controls."""
import csv,gzip,hashlib,json,math
from pathlib import Path
from collections import defaultdict
D=Path(__file__).resolve().parent;R=D.parent
OUT=D/"C120_QUARTER_CONTROL.csv.gz";SUM=D/"C120_SUMMARY.csv";META=D/"C120_METADATA.json"
REF=R/"AUTONOMOUS_RUN_20261031_0550_DCHR_C118_SUBHOUR_RH"/"C118_SUBHOUR_STRESS.csv.gz"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def check_row(r):
 for k in ("RH_start","RH_peak","RH_end","RH_min"):
  v=float(r[k])
  if not 0<=v<=1.000000001:raise ValueError("RH_RANGE")
 if float(r["RH_peak"])+1e-10<float(r["RH_end"]):raise ValueError("PEAK_ORDER")
 if float(r["RH_min"])-1e-10>float(r["RH_end"]):raise ValueError("MIN_ORDER")
 for k in ("evap_kg","dehum_kg","humid_kg","condensate_kg"):
  if float(r[k])< -1e-10:raise ValueError("NEGATIVE_MASS")
 residual=(float(r["storage_kg"])-(float(r["evap_kg"])-float(r["dehum_kg"])+float(r["humid_kg"])+float(r["vent_kg"])-float(r["condensate_kg"])))
 if abs(residual)>1e-7 or abs(float(r["mass_residual_kg"]))>1e-7:raise ValueError("MASS_CLOSURE")
 if r["mode"]!="legacy_fixed":
  if float(r["dehum_kg"])>45.66+1e-9 or float(r["humid_kg"])>29.70+1e-9:raise ValueError("CAPACITY")
 if float(r["dehum_kg"])>1e-9 and float(r["humid_kg"])>1e-9:
  # Different quarters can legitimately use opposite actuators.
  pass
 if int(r["hidden_high65"])!=int(float(r["RH_start"])<=.65 and float(r["RH_end"])<=.65 and float(r["RH_peak"])>.65):raise ValueError("HIDDEN_FLAG")
 return True
def run():
 m=json.loads(META.read_text(encoding="utf-8"))
 assert sha(OUT)==m["hourly_sha256"] and sha(SUM)==m["summary_sha256"]
 for p,h in m["source_sha256"].items():assert sha(Path(p))==h
 baseline={}
 with gzip.open(REF,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   if r["policy"]=="water_first" and r["control"] in ("ideal","capacity_C114") and r["pattern"] in ("flat","front_loaded"):
    baseline[(r["policy"],r["control"],r["pattern"],r["time"])]=r
 assert len(baseline)==35040
 stats=defaultdict(lambda:defaultdict(float)); counts=defaultdict(int); checked=0; legacy=0
 with gzip.open(OUT,"rt",encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   check_row(r);checked+=1
   key=(r["policy"],r["control"],r["pattern"],r["mode"]);counts[key]+=1
   s=stats[key];s["hours"]+=1
   s["max_RH"]=max(s.get("max_RH",0.),float(r["RH_peak"]))
   s["min_RH"]=min(s.get("min_RH",1.),float(r["RH_min"]))
   for k in ("hidden_high65","high_quarters","dehum_capacity_quarters"):
    s[{"dehum_capacity_quarters":"capacity_quarters"}.get(k,k)]+=int(r[k])
   for k in ("dehum_kg","humid_kg","condensate_kg"):
    s[k]+=float(r[k])
   s["mass_abs_residual_kg"]+=abs(float(r["mass_residual_kg"]))
   if r["mode"]=="legacy_fixed":
    ref=baseline[(r["policy"],r["control"],r["pattern"],r["time"])]
    for a,b in (("RH_start","RH_start"),("RH_peak","RH_peak_15m"),("RH_end","RH_end_15m"),
                ("condensate_kg","condensate_kg"),("vent_kg","vent_net_kg"),("storage_kg","storage_delta_kg")):
     if abs(float(r[a])-float(ref[b]))>1e-8:raise AssertionError("C118_REGRESSION "+a)
    legacy+=1
 assert checked==140160 and legacy==35040 and len(counts)==16 and all(v==8760 for v in counts.values())
 with SUM.open(encoding="utf-8",newline="") as f:
  summary=list(csv.DictReader(f))
 assert len(summary)==16
 for r in summary:
  key=(r["policy"],r["control"],r["pattern"],r["mode"]);s=stats[key]
  for k in ("hours","min_RH","max_RH","hidden_high65","high_quarters","capacity_quarters","dehum_kg","humid_kg","condensate_kg","mass_abs_residual_kg"):
   tol=1e-7 if k in ("dehum_kg","humid_kg","condensate_kg") else 1e-8
   if abs(float(r[k])-s[k])>tol:raise AssertionError("SUMMARY "+k)
 negatives=0
 with gzip.open(OUT,"rt",encoding="utf-8",newline="") as f:
  sample=next(csv.DictReader(f))
 for field,value in (("RH_end","1.5"),("dehum_kg","-1"),("storage_kg","1000"),("RH_peak","0"),("hidden_high65","1")):
  bad=dict(sample);bad[field]=value
  try:check_row(bad)
  except ValueError:negatives+=1
  else:raise AssertionError("NEGATIVE_FAILED "+field)
 assert negatives==5
 report={"status":"PASS","rows":checked,"legacy_C118_rows_crosschecked":legacy,
         "scenario_count":len(counts),"source_sha_pins":len(m["source_sha256"]),
         "mass_balance_rows":checked,"capacity_rows":checked-legacy,
         "summary_scenarios":len(summary),"negative_controls":negatives,
         "output_sha256":sha(OUT)}
 p=D/"C120_INDEPENDENT_QA.json"
 if p.exists():raise RuntimeError("QA_EXISTS")
 p.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":run()
