"""Independent output-based QA for C91. Does not import the implementation module."""
import csv, datetime as dt, hashlib, json, math
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
checks={}
def check(name, condition):
    if not condition: raise AssertionError("FAILED "+name)
    checks[name]="PASS"
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

s=json.loads((D/"C91_DYNAMIC_SUMMARY.json").read_text(encoding="utf-8"))
source=D.parent/"AUTONOMOUS_RUN_20261030_1452_DCHR_C90_POOL_COUNTERFACTUAL"/"C90_POOL_HOURLY.csv"
check("pinned_source",sha(source)==s["source_C90_sha256"])
check("synthetic_not_validated",s["synthetic"] is True and s["physical_validation"] is False)
check("source_recovery_unverified",s["source_recoverability_not_verified"] is True)
check("model_schema",s["schema"]=="C91_POOL_DYNAMIC_THERMOSTAT_V1")
check("pool_capacity",0.579<s["heat_capacity_MWh_per_C"]<0.581)
check("thermostat_hysteresis",s["thermostat_on_below_C"]<s["thermostat_off_above_C"])
check("scenario_count",len(s["scenarios"])==6)
CAP=s["heat_capacity_MWh_per_C"]
monthly=defaultdict(lambda:defaultdict(float))
totals=defaultdict(lambda:defaultdict(float))
times=defaultdict(list)
minimum=defaultdict(lambda:100.0)
below=defaultdict(int)
backup_positive=defaultdict(int)
count=0
with (D/"C91_DYNAMIC_HOURLY.csv").open("r",encoding="utf-8",newline="") as f:
    for r in csv.DictReader(f):
        count+=1
        name=r["scenario"]
        assert name in s["scenarios"],name
        scenario=s["scenarios"][name]
        stamp=dt.datetime.fromisoformat(r["time"])
        times[name].append(stamp)
        a=float(r["temp_start_C"]); b=float(r["temp_end_C"])
        q=float(r["pool_loss_MW"]); hp=float(r["HP_heat_MW"])
        el=float(r["HP_electric_MW"]); hx=float(r["HX_extracted_MW"])
        backup=float(r["backup_MW"]); src=float(r["source_HX_rejected_MW"])
        assert all(math.isfinite(v) for v in (a,b,q,hp,el,hx,backup,src))
        assert 0<=a<=45 and 0<=b<=45
        assert hp>=-1e-10 and el>=-1e-10 and hx>=-1e-10 and backup>=-1e-10 and src>=0
        assert abs(CAP*(b-a)-(hp+backup-q))<3e-9
        assert abs(hp-el-hx)<3e-9
        assert abs(el-hp/4)<3e-9
        assert hx<=src*scenario["fraction_assumed"]+3e-9
        assert hp<=0.30+3e-9
        assert backup<=scenario["backup_cap_MW"]+3e-9
        if r["thermostat_on"]=="0": assert hp==0 and backup==0
        else: assert r["thermostat_on"]=="1"
        if backup>1e-9: backup_positive[name]+=1
        below[name]+=int(b<27.5)
        minimum[name]=min(minimum[name],b)
        vals={"pool_loss_MWh":q,"HP_heat_MWh":hp,"HP_electric_MWh":el,
              "HX_extracted_MWh":hx,"backup_MWh":backup,
              "net_storage_change_MWh":CAP*(b-a)}
        for k,v in vals.items():
            totals[name][k]+=v
            monthly[(name,stamp.strftime("%Y-%m"))][k]+=v
check("hourly_row_count",count==6*8760)
check("six_complete_scenarios",all(len(v)==8760 for v in times.values()))
check("timestamps_complete",all(v[0]==dt.datetime(2026,1,1) and
    v[-1]==dt.datetime(2026,12,31,23) and
    all((y-x)==dt.timedelta(hours=1) for x,y in zip(v,v[1:]))
    for v in times.values()))
check("yearly_energy_totals",all(abs(v-s["scenarios"][name][k])<5e-6
    for name,vals in totals.items() for k,v in vals.items()))
check("yearly_storage_balance",all(abs(vals["net_storage_change_MWh"]-
    CAP*(s["scenarios"][name]["final_temp_C"]-s["initial_C"]))<5e-6
    for name,vals in totals.items()))
check("minimum_temperature",all(abs(v-s["scenarios"][name]["min_temp_C"])<1e-8
    for name,v in minimum.items()))
check("comfort_hours",all(v==s["scenarios"][name]["hours_below_27p5_C"]
    for name,v in below.items()))
check("no_source_zero_hp",abs(totals["no_recovery"]["HP_heat_MWh"])<1e-9)
check("no_source_zero_backup",abs(totals["no_recovery"]["backup_MWh"])<1e-9)
check("backup_only_authorized",all(totals[name]["backup_MWh"]<1e-8
    for name in s["scenarios"] if s["scenarios"][name]["backup_cap_MW"]==0))
check("backup_10pct_actually_used",backup_positive["fraction_10pct_backup50kW"]>0)
check("backup_25pct_unnecessary",backup_positive["fraction_25pct_backup50kW"]==0)
check("10pct_backup_improves_comfort",
    below["fraction_10pct_backup50kW"]<below["fraction_10pct"])
check("25pct_meets_27p5",below["fraction_25pct"]==0)
check("no_recovery_not_comfortable",below["no_recovery"]>8000)
check("more_source_no_worse_min",
    minimum["fraction_50pct"]>=minimum["fraction_25pct"]-1e-7)
with (D/"C91_DYNAMIC_MONTHLY.csv").open("r",encoding="utf-8",newline="") as f:
    month_rows=list(csv.DictReader(f))
check("monthly_row_count",len(month_rows)==6*12)
check("monthly_unique",len({(r["scenario"],r["month"]) for r in month_rows})==72)
check("monthly_reconciliation",all(abs(float(r[k])-monthly[(r["scenario"],r["month"])][k])<5e-6
    for r in month_rows for k in ("pool_loss_MWh","HP_heat_MWh","HP_electric_MWh",
                                   "HX_extracted_MWh","backup_MWh","net_storage_change_MWh")))
check("no_unapproved_source_claim",
    any("hypothetical" in str(v).lower() or "not a plant" in str(v).lower()
        for v in s["limitations"]))
check("six_scenarios_named",set(s["scenarios"])==set(times))
out={"schema":"C91_INDEPENDENT_QA_V1","checks":checks,
     "passed":len(checks),"failed":0,"hourly_rows":count,
     "monthly_rows":len(month_rows),"input_sha256":s["source_C90_sha256"],
     "dynamic_hourly_sha256":sha(D/"C91_DYNAMIC_HOURLY.csv")}
with (D/"C91_INDEPENDENT_QA.json").open("x",encoding="utf-8") as f:
    json.dump(out,f,indent=2,sort_keys=True);f.write("\n")
print("C91 INDEPENDENT QA",len(checks),"/",len(checks),"PASS")
