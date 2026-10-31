"""Compare native MATLAB Warm45 v2 export against C37 Python replay.
--self-test is NOT a native MATLAB execution or parity proof.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,hashlib,json,math,tempfile
from pathlib import Path
H=Path(__file__).resolve().parent
C37=H.parent/"AUTONOMOUS_RUN_20261028_1858_DCHR_C37_V2_REPLAY"
REFERENCE=C37/"Warm45_Storage100_v2_PYTHON_REPLAY.csv"
NATIVE=H/"Warm45_Storage100_v2_MATLAB_NATIVE.csv"
EXPECTED=["Time","Tout_C","IT_Util","IT_MW","DC_Total_MW","Heat_Demand_MW",
"DH_Supply_C","DH_Return_C","Source_Heat_Available_MW","HX_Heat_to_HP_MW",
"HX_Rejected_MW","Temperature_Lift_K","COP","HP_Heat_MW","HP_Heat_Used_MW",
"HP_Electric_MW","HP_Source_Used_MW","Storage_Charge_MW","Storage_Discharge_MW",
"Storage_E_MWh","Gas_Heat_MW","Curtailed_HP_Heat_MW","Useful_Heat_Exergy_MW"]
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1048576),b""):h.update(b)
 return h.hexdigest()
def compare(left,right,expected_rows=8760,tolerance=2e-8):
 with left.open(newline="",encoding="utf-8-sig") as a,right.open(newline="",encoding="utf-8-sig") as b:
  la=csv.DictReader(a);rb=csv.DictReader(b)
  if la.fieldnames!=EXPECTED or rb.fieldnames!=EXPECTED:raise AssertionError("SCHEMA_MISMATCH")
  worst=0.;n=0;rows=0
  from itertools import zip_longest
  for x,y in zip_longest(la,rb):
   if x is None or y is None:raise AssertionError("ROW_COUNT_MISMATCH")
   if x["Time"]!=y["Time"]:raise AssertionError("TIME_MISMATCH at "+str(rows))
   for col in EXPECTED[1:]:
    u=float(x[col]);v=float(y[col])
    if not math.isfinite(u) or not math.isfinite(v):raise AssertionError("NONFINITE "+col)
    delta=abs(u-v);worst=max(worst,delta);n+=1
    if delta>tolerance:raise AssertionError(f"NUMERIC_MISMATCH {rows} {col} {delta}")
   rows+=1
  if rows!=expected_rows:raise AssertionError(f"WRONG_HOURS {rows}")
 return {"hours":rows,"numeric_comparisons":n,"max_absolute_error":worst,
         "tolerance":tolerance,"reference_sha256":sha(left),"candidate_sha256":sha(right)}
def self_test():
 assert REFERENCE.is_file()
 with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp);x=d/"x.csv";y=d/"y.csv"
  def write(p,rows):
   with p.open("w",newline="",encoding="utf-8") as f:
    w=csv.DictWriter(f,fieldnames=EXPECTED);w.writeheader();w.writerows(rows)
  r={col:("2026-01-01 00:00:00" if col=="Time" else "1.0") for col in EXPECTED}
  write(x,[r]);write(y,[dict(r)])
  assert compare(x,y,1)["numeric_comparisons"]==22
  count=1
  bad=dict(r);bad["COP"]="2.0";write(y,[bad])
  try:compare(x,y,1);raise AssertionError("NUMERIC_FAIL_OPEN")
  except AssertionError as e:
   if "NUMERIC_MISMATCH" not in str(e):raise
  count+=1
  bad=dict(r);bad["Time"]="2026-01-01 01:00:00";write(y,[bad])
  try:compare(x,y,1);raise AssertionError("TIME_FAIL_OPEN")
  except AssertionError as e:
   if "TIME_MISMATCH" not in str(e):raise
  count+=1
  write(y,[r,r])
  try:compare(x,y,1);raise AssertionError("ROWS_FAIL_OPEN")
  except AssertionError as e:
   if "ROW_COUNT_MISMATCH" not in str(e):raise
  count+=1
  write(y,[r])
  try:compare(x,y,2);raise AssertionError("HOURS_FAIL_OPEN")
  except AssertionError as e:
   if "WRONG_HOURS" not in str(e):raise
  count+=1
 identity=compare(REFERENCE,REFERENCE)
 assert identity["hours"]==8760 and identity["numeric_comparisons"]==192720
 count+=1
 result={"scope":"DCHR_C40_NATIVE_EXPORT_HARNESS_SELFTEST",
   "observed_local":dt.datetime.now().astimezone().isoformat(timespec="seconds"),
   "status":"PASS","self_tests":count,"self_identity_comparisons":identity["numeric_comparisons"],
   "c37_reference_sha256":identity["reference_sha256"],
   "native_matlab_executed":False,"native_parity_verified":False,
   "interpretation":"Comparator functionality only, not MATLAB/Stateflow or physical validation."}
 with (H/"C40_HARNESS_SELFTEST.json").open("xb") as f:
  f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf-8"))
 print(json.dumps(result))
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--self-test",action="store_true")
 ap.add_argument("--native",type=Path,default=NATIVE)
 args=ap.parse_args()
 if args.self_test:self_test();return
 if not args.native.is_file():raise SystemExit("NATIVE_EXPORT_MISSING; MATLAB has not been run")
 result=compare(REFERENCE,args.native)
 with (H/"C40_NATIVE_PARITY_RESULT.json").open("xb") as f:
  f.write((json.dumps(result,sort_keys=True,indent=2)+"\n").encode("utf-8"))
 print(json.dumps(result))
if __name__=="__main__":main()
