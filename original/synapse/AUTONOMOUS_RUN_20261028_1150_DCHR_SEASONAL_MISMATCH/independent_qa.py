"""Independent decimal re-computation; does not import implementation under test."""
import csv
import hashlib
import json
from decimal import Decimal
from pathlib import Path

H=Path(__file__).resolve().parent
SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
raw=SOURCE.read_bytes()
result=json.loads((H/"SEASONAL_MISMATCH.json").read_text(encoding="utf-8"))
assert hashlib.sha256(raw).hexdigest()==result["source_sha256"]
rows=list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
assert len(rows)==result["rows"]==8760
pairs=[]
monthly={m:[Decimal(0),Decimal(0)] for m in range(1,13)}
overlap=0
for row in rows:
    q=Decimal(row["Curtailed_HP_Heat_MW"])
    g=Decimal(row["Gas_Heat_MW"])
    month=int(__import__("datetime").datetime.strptime(row["Time"],"%d-%b-%Y %H:%M:%S").month)
    monthly[month][0]+=q
    monthly[month][1]+=g
    overlap+=int(q>0 and g>0)
    pairs.append((q,g))
assert overlap==result["simultaneous_curtailment_gas_hours"]==0
assert abs(float(sum(q for q,_ in pairs))-result["curtailed_potential_mwh"])<1e-6
assert abs(float(sum(g for _,g in pairs))-result["gas_heat_mwh"])<1e-6
for m,(q,g) in monthly.items():
    assert abs(float(q)-result["monthly"][str(m)]["curtailed_potential_mwh"])<1e-6
    assert abs(float(g)-result["monthly"][str(m)]["gas_heat_mwh"])<1e-6
checks=0
for cap_str,actual in result["ideal_counterfactual_capacities_mwh"].items():
    cap=Decimal(cap_str)
    inventory=Decimal(0)
    for year in range(3):
        begin=inventory
        received=delivered=spilled=Decimal(0)
        for q,g in pairs:
            room=cap-inventory
            take=min(room,q)
            inventory+=take
            use=min(g,inventory)
            inventory-=use
            received+=take
            delivered+=use
            spilled+=q-take
        check=actual[year]
        for key,expected in (("initial_soc_mwh",begin),("charged_mwh",received),
                             ("saved_gas_heat_mwh",delivered),
                             ("unused_potential_mwh",spilled),
                             ("final_soc_mwh",inventory)):
            assert abs(float(expected)-check[key])<1e-6,(cap,year,key)
            checks+=1
        assert begin+received-delivered==inventory
assert result["primary_source_signoffs"]==0 and result["production_modified"] is False
out={"status":"PASS","source_rows":len(rows),"months_checked":12,
     "counterfactual_fields_checked":checks,
     "decimal_recomputed":True,"overlap_hours":overlap,
     "baseline_simulated":True,"not_measured":True}
(H/"QA_INDEPENDENT.json").write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(out))
