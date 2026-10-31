"""Read-only independent audit of Frankfurt v0.4 hourly CSV."""
from pathlib import Path
from collections import Counter
import csv, json
root = Path(__file__).resolve().parents[1]
src = root / "results" / "frankfurt_validation_v4_timeseries.csv"
rows = list(csv.DictReader(src.open(encoding="utf-8-sig",newline="")))
v = lambda r,n: float(r[n])
errors = {key:[] for key in ["network","HP_first_law","HX_balance","source_overuse","storage_step","gas_capacity_20MW","HP_capacity_37MW"]}
totals=Counter()
eta_c,eta_d,loss,dt=0.98,0.98,0.005/24,1
for i,r in enumerate(rows):
    d=v(r,"Heat_Demand_MW");hp=v(r,"HP_Heat_Used_MW");ch=v(r,"Storage_Charge_MW")
    dis=v(r,"Storage_Discharge_MW");gas=v(r,"Gas_Heat_MW");w=v(r,"HP_Electric_MW")
    source=v(r,"HP_Source_Used_MW");hx=v(r,"HX_Heat_to_HP_MW")
    raw=v(r,"Source_Heat_Available_MW");rej=v(r,"HX_Rejected_MW")
    e=v(r,"Storage_E_MWh")
    errors["network"].append(d-(hp-ch+dis+gas))
    errors["HP_first_law"].append(hp-source-w)
    errors["HX_balance"].append(raw-hx-rej)
    errors["source_overuse"].append(max(0,source-hx))
    errors["gas_capacity_20MW"].append(max(0,gas-20))
    errors["HP_capacity_37MW"].append(max(0,hp-37))
    if i+1 < len(rows):
        next_e=e*(1-loss*dt)+eta_c*ch*dt-dis*dt/eta_d
        errors["storage_step"].append(v(rows[i+1],"Storage_E_MWh")-next_e)
    for key,value in [("demand_MWh",d),("gas_MWh",gas),("hp_heat_MWh",hp),("HP_electric_MWh",w),
                      ("HX_MWh",hx),("HP_source_MWh",source),("charge_MWh",ch),("discharge_MWh",dis)]:
        totals[key]+=value*dt
stats={key:{"max_abs":max(map(abs,vals),default=0),
            "count_gt_1e-6":sum(abs(x)>1e-6 for x in vals)} for key,vals in errors.items()}
issues=[
"20 MW gas-boiler limit is declared in the paper but never enforced in dispatch.",
"Storage sweep varies both energy capacity and charge/discharge power limits.",
"Recovery fraction fitted to reproduce 97.5 percent; this is calibration, not independent validation.",
"Source temperature, 300 MWh storage, synthetic weather and electricity prices are assumptions.",
"ERF numerator counts delivered heat with HP electricity; check the mandated reporting boundary.",
"No hourly unmet-demand output if finite gas boiler capacity is enforced.",
"Exergy and economics require paper-by-paper physical-boundary validation."
]
report={"source":str(src),"hours":len(rows),"checks":stats,"totals":dict(totals),
        "max_gas_MW":max(v(r,"Gas_Heat_MW") for r in rows),
        "max_HP_MW":max(v(r,"HP_Heat_Used_MW") for r in rows),"issues":issues}
out=Path(__file__).with_name("physics_audit_v05.json")
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
md=["# Independent physics audit v0.5","", "Original outputs untouched.", "", "## Residual checks",
    "| Check | Worst residual | Count > 1e-6 |","|---|---:|---:|"]
for key,val in stats.items(): md.append(f"| {key} | {val['max_abs']:.8g} | {val['count_gt_1e-6']} |")
md+=["","## Annual energy totals [MWh]"]
for key,val in totals.items():md.append(f"- {key}: {val:,.3f}")
md+=["","## Issues requiring model changes"]
for issue in issues:md.append("- "+issue)
Path(__file__).with_name("physics_audit_v05.md").write_text("\n".join(md)+"\n",encoding="utf-8")
print(json.dumps({"hours":len(rows),"checks":stats,"max_gas_MW":report["max_gas_MW"],
                  "total_gas_MWh":totals["gas_MWh"]},ensure_ascii=False))
