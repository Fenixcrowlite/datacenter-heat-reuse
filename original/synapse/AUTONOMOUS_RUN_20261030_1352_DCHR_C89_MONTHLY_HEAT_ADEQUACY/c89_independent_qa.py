"""Independent C89 report reconciliation against the original C88 CSV."""
import csv, hashlib, json
from collections import defaultdict
from pathlib import Path
P=Path(__file__).resolve().parent
S=P.parents[1]/"recovery"/"AUTONOMOUS_RUN_20261030_1254_DCHR_C88_NATIVE_MATLAB_REPLAY"/"Warm45_Storage100_v2_MATLAB_NATIVE.csv"
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    passed=[]
    def ok(k,v):
        if not v: raise AssertionError(k)
        passed.append(k)
    for root in (P,P.parents[1],P.parents[1]/"recovery"):
        ok("stop_"+root.name,not any((root/x).exists() for x in ("STOP","PAUSE","STOP.flag","PAUSE.flag")))
    r=json.loads((P/"C89_MONTHLY_ADEQUACY.json").read_text(encoding="utf8"))
    with (P/"C89_MONTHLY_ADEQUACY.csv").open(encoding="utf8",newline="") as f: months=list(csv.DictReader(f))
    ok("sha",sha(S)==r["source_sha256"])
    ok("disclaimer",r["synthetic"] and not r["physical_field_validation"] and r["primary_sources_signed"]==0)
    ok("12months",len(months)==len(r["months"])==12)
    ok("csv_json",all(m["month"]==j["month"] and abs(float(m["gas_heat_MWh"])-j["gas_heat_MWh"])<1e-9 for m,j in zip(months,r["months"])))
    ok("hours",sum(int(m["hours"]) for m in months)==8760)
    monthnum={n:i+1 for i,n in enumerate(("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"))}
    vals=defaultdict(lambda:[0,0.,0.,0.])
    with S.open(encoding="utf-8-sig",newline="") as f:
        for row in csv.DictReader(f):
            v=vals[monthnum[row["Time"][3:6]]]
            v[0]+=1
            for j,k in enumerate(("Heat_Demand_MW","Gas_Heat_MW","HP_Electric_MW"),1): v[j]+=float(row[k])
    ok("source_hours",sum(v[0] for v in vals.values())==8760)
    ok("month_reconcile",all(abs(vals[i][j]-r["months"][i-1][k])<1e-4 for i in range(1,13) for j,k in ((1,"demand_MWh"),(2,"gas_heat_MWh"),(3,"hp_electric_MWh"))))
    a=r["annual"]
    ok("annual_gas",abs(sum(v[2] for v in vals.values())-a["gas_heat_MWh"])<1e-4)
    ok("shares",abs(a["gas_fraction_of_heat_demand_pct"]+a["non_gas_fraction_of_heat_demand_pct"]-100)<.002)
    ok("backup_needed",a["hours_gas_needed"]>0 and a["gas_heat_MWh"]>0)
    bad=json.loads(json.dumps(r));bad["months"][0]["gas_heat_MWh"]+=10
    ok("tamper",abs(sum(m["gas_heat_MWh"] for m in bad["months"])-a["gas_heat_MWh"])>9)
    print(json.dumps({"status":"PASS","checks":len(passed),"passed":passed},ensure_ascii=False))
if __name__=="__main__":main()
