"""C90 follow-on: time-aligned minimum recoverability and actual-use dispatch.
Uses the already generated C90 hourly table; no edits to native MATLAB or SCADA.
"""
import csv, json, math
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parent
COP=4.0
FRACTIONS=(0.0,0.05,0.10,0.15,0.20,0.25,0.50,1.0)
rows=defaultdict(list)
for r in csv.DictReader((ROOT/"C90_POOL_HOURLY.csv").open(encoding="utf-8",newline="")):
    rows[r["scenario"]].append(r)
report={"schema":"C90_TIME_ALIGNED_RECOVERY_THRESHOLD_V1",
        "not_field_validated":True,"recoverability_not_proven":True,
        "extra_HP_COP_assumed":COP,"heat_cap_MW":0.30,
        "electric_cap_MW":0.075,"scenarios":{}}
for name,records in rows.items():
    assert len(records)==8760
    scenarios={}
    for include_air in (False,True):
        key="water_plus_air_HVAC_hypothetical" if include_air else "pool_water_only"
        demands=[float(r["pool_load_MW"])+(float(r["air_ventilation_separate_MW"]) if include_air else 0.0) for r in records]
        rejected=[float(r["HX_rejected_MW"]) for r in records]
        thresholds=[q*0.75/h if h>0 else math.inf for q,h in zip(demands,rejected)]
        cap_feasible=all(q<=0.30+1e-10 for q in demands)
        exact_fraction=max(thresholds) if cap_feasible else math.inf
        stats={}
        for fraction in FRACTIONS:
            delivered=[min(q,max(0.0,h)*fraction*COP/(COP-1),0.30) for q,h in zip(demands,rejected)]
            unmet=[max(0.0,q-d) for q,d in zip(demands,delivered)]
            source_used=sum(d*0.75 for d in delivered)
            stats[f"{fraction:.2f}"]={"delivered_MWh":sum(delivered),
                "unmet_MWh":sum(unmet),"hours_unmet":sum(x>1e-9 for x in unmet),
                "energy_coverage_pct":100*sum(delivered)/sum(demands),
                "actual_HP_electric_MWh":sum(delivered)/COP,
                "actual_recovered_source_MWh":source_used}
        scenarios[key]={"annual_demand_MWh":sum(demands),
            "peak_demand_MW":max(demands),
            "minimum_fraction_for_zero_hourly_deficit":exact_fraction if math.isfinite(exact_fraction) else None,
            "max_HP_capacity_feasible":cap_feasible,
            "fraction_sweep":stats}
        assert all(stats[f"{x:.2f}"]["energy_coverage_pct"]<=stats[f"{y:.2f}"]["energy_coverage_pct"]+1e-9 for x,y in zip(FRACTIONS,FRACTIONS[1:]))
        assert all(abs(v["delivered_MWh"]+v["unmet_MWh"]-sum(demands))<1e-6 for v in stats.values())
    report["scenarios"][name]=scenarios
with (ROOT/"C90_RECOVERY_THRESHOLDS.json").open("x",encoding="utf-8") as f:
    json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
for name in ("covered_no_extra","uncovered_50pct","covered_dry_air_50pct"):
    for key,scenario in report["scenarios"][name].items():
        print(name,key,"required_fraction",round(scenario["minimum_fraction_for_zero_hourly_deficit"] or -1,4),
              "25pct_coverage",round(scenario["fraction_sweep"]["0.25"]["energy_coverage_pct"],2),
              "25pct_unmet_h",scenario["fraction_sweep"]["0.25"]["hours_unmet"])
