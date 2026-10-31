"""Independent checks of threshold and capacity logic."""
import csv,json,math
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parent
j=json.loads((R/"C90_RECOVERY_THRESHOLDS.json").read_text(encoding="utf-8"))
r=defaultdict(list)
for x in csv.DictReader((R/"C90_POOL_HOURLY.csv").open(encoding="utf-8",newline="")):
    r[x["scenario"]].append(x)
checks={}
def ck(name,ok):
    checks[name]=bool(ok)
    if not ok:raise AssertionError(name)
ck("all_scenarios_covered",len(j["scenarios"])==6)
for name in r:
    for air in (False,True):
        key="water_plus_air_HVAC_hypothetical" if air else "pool_water_only"
        x=j["scenarios"][name][key]
        demand=[float(a["pool_load_MW"])+(float(a["air_ventilation_separate_MW"]) if air else 0) for a in r[name]]
        rejected=[float(a["HX_rejected_MW"]) for a in r[name]]
        exact=max((q*.75/h if h>0 else math.inf) for q,h in zip(demand,rejected))
        ck("exact_threshold_"+name+"_"+str(air),abs(exact-x["minimum_fraction_for_zero_hourly_deficit"])<1e-12)
        ck("actual_dispatch_energy_"+name+"_"+str(air),all(abs(v["actual_HP_electric_MWh"]*4-v["delivered_MWh"])<1e-6 for v in x["fraction_sweep"].values()))
ck("pool_covered_lower_than_dry",j["scenarios"]["covered_no_extra"]["pool_water_only"]["minimum_fraction_for_zero_hourly_deficit"]<j["scenarios"]["covered_dry_air_50pct"]["pool_water_only"]["minimum_fraction_for_zero_hourly_deficit"])
ck("air_requires_more_source",all(v["water_plus_air_HVAC_hypothetical"]["minimum_fraction_for_zero_hourly_deficit"]>=v["pool_water_only"]["minimum_fraction_for_zero_hourly_deficit"] for v in j["scenarios"].values()))
ck("25pct_pool_covered_fully_met",j["scenarios"]["covered_25pct"]["pool_water_only"]["fraction_sweep"]["0.25"]["hours_unmet"]==0)
ck("25pct_air_not_fully_met",j["scenarios"]["covered_25pct"]["water_plus_air_HVAC_hypothetical"]["fraction_sweep"]["0.25"]["hours_unmet"]>0)
print(json.dumps({"qa":"PASS","checks":len(checks),"all_pass":all(checks.values())},indent=2))
