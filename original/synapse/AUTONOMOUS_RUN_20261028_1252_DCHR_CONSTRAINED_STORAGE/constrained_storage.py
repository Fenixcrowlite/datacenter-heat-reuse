"""Bounded thermal-storage sensitivity on SYNTHETIC hourly baseline.
Not a re-dispatch of the existing 100 MWh storage; not a feasibility or savings claim.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
SOURCE_SHA = "8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
COLS = ("COP","Temperature_Lift_K","DH_Supply_C","DC_Total_MW","Source_Heat_Available_MW",
        "HP_Source_Used_MW","HP_Electric_MW","Curtailed_HP_Heat_MW","Gas_Heat_MW")
EPS=1e-8

@dataclass(frozen=True)
class Config:
    capacity_mwh: float = 2500.0
    charge_mw: float = 3.0
    discharge_mw: float = 3.0
    extra_hp_electric_mw: float = 1.5
    site_electric_cap_mw: float = 12.0
    hp_total_electric_cap_mw: float = 2.5
    charge_efficiency: float = 0.95
    discharge_efficiency: float = 0.95
    hourly_loss_fraction: float = 0.00025
    storage_temperature_c: float = 72.0
    hx_approach_k: float = 3.0

def validate(c: Config):
    for name,value in asdict(c).items():
        if not math.isfinite(value): raise ValueError(name+" nonfinite")
    if c.capacity_mwh < 0 or min(c.charge_mw,c.discharge_mw,c.extra_hp_electric_mw,c.site_electric_cap_mw,c.hp_total_electric_cap_mw)<0:
        raise ValueError("negative capacity/power")
    if not (0<c.charge_efficiency<=1 and 0<c.discharge_efficiency<=1 and
            0<=c.hourly_loss_fraction<1):
        raise ValueError("invalid efficiencies or loss")
    if not (-50<c.storage_temperature_c<150 and 0<=c.hx_approach_k<40):
        raise ValueError("invalid thermal temperatures")

def load(path=SOURCE, expected_sha=SOURCE_SHA):
    raw=Path(path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if expected_sha is not None and sha!=expected_sha: raise ValueError("source hash mismatch")
    rows=[];prev=None
    for i,r in enumerate(csv.DictReader(raw.decode("utf-8-sig").splitlines()),2):
        try:
            stamp=dt.datetime.strptime(r["Time"],"%d-%b-%Y %H:%M:%S")
            v={key:float(r[key]) for key in COLS}
        except (ValueError,KeyError,TypeError) as e:
            raise ValueError(f"bad source row {i}") from e
        if prev is not None and stamp-prev!=dt.timedelta(hours=1):
            raise ValueError(f"non-hourly timestamp {i}")
        if any(not math.isfinite(x) for x in v.values()) or any(v[k]<0 for k in COLS if k!="DH_Supply_C"):
            raise ValueError(f"negative/nonfinite source {i}")
        if v["COP"]<=1.01 or v["Temperature_Lift_K"]<=0:
            raise ValueError(f"invalid HP lift/COP {i}")
        rows.append(v);prev=stamp
    if len(rows)!=8760: raise ValueError("expected 8760 synthetic hourly rows")
    return rows,sha

def step(v: dict, soc: float, c: Config):
    """All energies MWh over a fixed 1 h interval; powers MW.
    Charge from CURTAILED thermal potential, not free heat.
    COP adjusted for extra lift using a heuristic inverse-lift model.
    Temperature discharge gate is explicit, not assumed feasible.
    """
    if soc< -EPS or soc>c.capacity_mwh+EPS: raise ValueError("invalid initial SOC")
    initial=soc
    loss=initial*c.hourly_loss_fraction
    soc=initial-loss
    base_cop=v["COP"]
    extra_lift=max(0.0,c.storage_temperature_c+c.hx_approach_k-v["DH_Supply_C"])
    effective_cop=base_cop*v["Temperature_Lift_K"]/(v["Temperature_Lift_K"]+extra_lift)
    charge=added_electric=source_draw=0.0
    source_headroom=max(0.0,v["Source_Heat_Available_MW"]-v["HP_Source_Used_MW"])
    electric_headroom=min(c.extra_hp_electric_mw,
                          max(0.0,c.site_electric_cap_mw-v["DC_Total_MW"]),
                          max(0.0,c.hp_total_electric_cap_mw-v["HP_Electric_MW"]))
    if effective_cop>1.01 and c.capacity_mwh>0:
        thermal_potential=max(0.0,v["Curtailed_HP_Heat_MW"])*min(1.0,effective_cop/base_cop)
        source_ratio=1.0-1.0/effective_cop
        charge=min(thermal_potential, c.charge_mw,
                   electric_headroom*effective_cop,
                   source_headroom/source_ratio,
                   max(0.0,c.capacity_mwh-soc)/c.charge_efficiency)
        charge=max(0.0,charge)
        added_electric=charge/effective_cop
        source_draw=charge-added_electric
        soc+=charge*c.charge_efficiency
    gas=max(0.0,v["Gas_Heat_MW"])
    delivered=0.0
    temperature_ok=c.storage_temperature_c>=v["DH_Supply_C"]+c.hx_approach_k
    if temperature_ok:
        delivered=min(gas,c.discharge_mw,soc*c.discharge_efficiency)
        soc-=delivered/c.discharge_efficiency
    if not (-EPS<=soc<=c.capacity_mwh+EPS):
        raise AssertionError("SOC violation")
    if abs(initial+charge*c.charge_efficiency-loss-delivered/c.discharge_efficiency-soc)>1e-6:
        raise AssertionError("thermal conservation")
    if charge>c.charge_mw+EPS or delivered>c.discharge_mw+EPS:
        raise AssertionError("power constraint")
    if added_electric>electric_headroom+EPS or source_draw>source_headroom+EPS:
        raise AssertionError("HP electric/source constraint")
    if delivered>gas+EPS or (not temperature_ok and delivered>EPS):
        raise AssertionError("demand/temperature constraint")
    return soc,dict(charge_mwh=charge,delivered_mwh=delivered,loss_mwh=loss,
                    additional_electric_mwh=added_electric,source_heat_mwh=source_draw,
                    remaining_gas_heat_mwh=gas-delivered,
                    effective_cop=effective_cop,temperature_gate_open=temperature_ok)

def simulate(rows, c: Config, years=3):
    validate(c)
    if not rows or years<1:raise ValueError("empty data or years")
    soc=0.0;year_results=[]
    for year in range(years):
        begin=soc;totals={k:0.0 for k in
            ("charge_mwh","delivered_mwh","loss_mwh","additional_electric_mwh",
             "source_heat_mwh","remaining_gas_heat_mwh")}
        blocked=0
        for v in rows:
            soc,z=step(v,soc,c)
            for k in totals:totals[k]+=z[k]
            blocked+=int(not z["temperature_gate_open"])
        totals={k:round(v,6) for k,v in totals.items()}
        totals.update(year=year+1,initial_soc_mwh=round(begin,6),
                      final_soc_mwh=round(soc,6),
                      temperature_blocked_hours=blocked)
        year_results.append(totals)
    return {"config":asdict(c),"year_results":year_results,
            "classification":"SYNTHETIC_CONSTRAINED_SENSITIVITY_NOT_INCREMENTAL_SAVINGS",
            "baseline_existing_storage_mwh":100,
            "note":"Parallel counterfactual; baseline gas already includes its 100 MWh storage. No integrated redispatch."}

def run():
    rows,sha=load()
    configs=[
        Config(capacity_mwh=cap,extra_hp_electric_mw=electric,
               charge_mw=3.0,discharge_mw=3.0)
        for cap in (100,500,2500,10000) for electric in (0.5,1.5)
    ]
    results=[simulate(rows,c) for c in configs]
    thermal_cases=[Config(capacity_mwh=2500,extra_hp_electric_mw=1.5,
                          storage_temperature_c=t,hourly_loss_fraction=loss)
                   for t,loss in ((55,0.00025),(65,0.00025),(72,0.00025),
                                  (80,0.00025),(72,0.0))]
    thermal_results=[simulate(rows,c) for c in thermal_cases]
    output={"source_sha256":sha,"rows":len(rows),"interval_hours":1,
            "synthetic_not_metered":True,"primary_source_signoffs":0,
            "models":results,"thermal_sensitivity":thermal_results,
            "assumptions":[
              "Baseline contains a 100 MWh storage; scenarios are parallel sensitivities, NOT incremental gas savings.",
              "Curtailed HP heat is only a potential. Extra heat pump electricity and source-heat headroom are enforced.",
              "Extra HP electricity bounded by configured site MW cap and total HP electric MW cap; both assumed, not measured nameplate limits.",
              "COP extra-lift derating is heuristic (COP * original lift / revised lift), not a manufacturer performance map.",
              "Fixed storage temperature; no stratification, mixing, return-temperature or charging temperature dynamics.",
              "Fixed hourly self-discharge, separate charge/discharge efficiencies and explicit thermal power caps.",
              "Gas heat displacement is theoretical thermal demand coverage; no fuel/electric tariffs or investment economics.",
              "Annual synthetic weather is repeated for 3 years; no metered source, validated thermal design or primary-source signoffs."
            ]}
    here=Path(__file__).resolve().parent
    (here/"CONSTRAINED_SENSITIVITY.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return output

if __name__=="__main__":
    o=run()
    print(json.dumps({"rows":o["rows"],"models":len(o["models"]),
                      "thermal_sensitivity":len(o["thermal_sensitivity"]),
                      "year3":[{"capacity":m["config"]["capacity_mwh"],
                                "extra_hp_mw":m["config"]["extra_hp_electric_mw"],
                                "delivered_mwh":m["year_results"][2]["delivered_mwh"],
                                "additional_electric_mwh":m["year_results"][2]["additional_electric_mwh"]}
                               for m in o["models"]]}))
