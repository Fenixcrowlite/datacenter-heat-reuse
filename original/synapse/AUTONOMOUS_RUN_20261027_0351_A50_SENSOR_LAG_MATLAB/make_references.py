from pathlib import Path
import csv,hashlib,json,sys
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
sys.path.insert(0,str(A45))
import finite_trip_a45 as plant
rows=plant.verified_inputs()[:240]
cases=[]
for scenario in ("neither","backup_only"):
 for lag in (0,1,4):
  trace=plant.simulate(rows,scenario,sensor_lag_steps=lag)
  filename=f"REF_{scenario}_lag{lag}.csv"
  keys=list(rows[0].keys())+["nominal_cap_W","state","T_next_C","E_next_J","active_it_W","residual_it_W","unhandled_W","pool_dh_served_W","required_reject_W","effective_cap_W","it_balance_W","tes_balance_J"]
  assert len(keys)==len(set(keys)),keys
  with (D/filename).open("w",newline="",encoding="utf-8") as f:
   w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
   for r,t in zip(rows,trace):
    w.writerow({**r,**{k:t[k] for k in keys if k not in r}})
  cases.append({"scenario":scenario,"lag":lag,"file":filename,"samples":len(trace),"first_trip":next((i for i,x in enumerate(trace) if x["state"]=="TRIPPED"),None)})
(D/"REFERENCE_MANIFEST.json").write_text(json.dumps({"cases":cases,"synthetic":True},indent=2)+"\n",encoding="utf-8")
print(json.dumps(cases))
