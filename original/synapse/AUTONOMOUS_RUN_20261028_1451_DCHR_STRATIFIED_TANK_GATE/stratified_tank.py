"""Finite-volume stratified water tank gate on SYNTHETIC DataCenter baseline.
Independent counterfactual, NOT an incremental savings claim.
Fixed equal-volume layers; charge = top injection/bottom extraction;
discharge = bottom return injection/top extraction. Upwind advection
uses CFL<=0.5, explicit ambient loss and interlayer mixing.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, math
from dataclasses import dataclass, asdict, replace
from pathlib import Path

SOURCE=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\best_scenario_v2_timeseries.csv")
SOURCE_SHA="8125719923bae97901f37cf0f5354df77b46544df0477f863172255748873f25"
COLS=("COP","Temperature_Lift_K","DH_Supply_C","DC_Total_MW",
      "Source_Heat_Available_MW","HP_Source_Used_MW","HP_Electric_MW",
      "Curtailed_HP_Heat_MW","Gas_Heat_MW")
CP=4180.0
RHO=1000.0
EPS=1e-9

@dataclass(frozen=True)
class Config:
    volume_m3:float=10000.0
    layers:int=8
    charge_temp_c:float=80.0
    return_temp_c:float=35.0
    initial_temp_c:float=35.0
    ambient_c:float=15.0
    hx_approach_k:float=3.0
    ua_kw_per_k:float=10.0
    mixing_kw_per_k:float=0.5
    charge_mw:float=3.0
    discharge_mw:float=3.0
    extra_hp_electric_mw:float=1.5
    site_electric_cap_mw:float=12.0
    hp_total_electric_cap_mw:float=2.5
    substeps:int=8

def validate(c):
    vals=asdict(c)
    if not all(math.isfinite(x) for x in vals.values()): raise ValueError("nonfinite")
    if c.layers<2 or c.substeps<2 or c.volume_m3<=0:raise ValueError("geometry")
    if c.charge_temp_c<=c.return_temp_c or c.initial_temp_c>c.charge_temp_c:raise ValueError("temperature")
    if min(c.hx_approach_k,c.ua_kw_per_k,c.mixing_kw_per_k,c.charge_mw,
           c.discharge_mw,c.extra_hp_electric_mw,c.site_electric_cap_mw,
           c.hp_total_electric_cap_mw)<0:raise ValueError("negative")
    if c.substeps<2:raise ValueError("substeps")

def load(path=SOURCE,expected_sha=SOURCE_SHA,expected_rows=8760):
    raw=Path(path).read_bytes()
    sha=hashlib.sha256(raw).hexdigest()
    if expected_sha is not None and sha!=expected_sha:raise ValueError("source SHA mismatch")
    rows=[];prev=None
    for i,row in enumerate(csv.DictReader(raw.decode("utf-8-sig").splitlines()),2):
        try:
            t=dt.datetime.strptime(row["Time"],"%d-%b-%Y %H:%M:%S")
            v={k:float(row[k]) for k in COLS}
        except (ValueError,KeyError,TypeError) as exc:raise ValueError(f"row {i}") from exc
        if prev is not None and t-prev!=dt.timedelta(hours=1):raise ValueError(f"timestamp {i}")
        if not all(math.isfinite(x) for x in v.values()):raise ValueError(f"nonfinite row {i}")
        if any(v[k]<0 for k in COLS if k!="DH_Supply_C") or v["COP"]<=1.01 or v["Temperature_Lift_K"]<=0:
            raise ValueError(f"invalid source row {i}")
        rows.append(v);prev=t
    if expected_rows is not None and len(rows)!=expected_rows:raise ValueError("row count")
    return rows,sha

def energy(temps,c):
    return c.volume_m3*RHO*CP/(3.6e9*c.layers)*math.fsum(temps)

def hourly(temps,row,c):
    """One-hour step. Return (new temperatures, physical energy ledger)."""
    validate(c)
    if len(temps)!=c.layers or not all(math.isfinite(x) for x in temps):raise ValueError("profile")
    t=list(temps); cell=c.volume_m3*RHO*CP/(3.6e9*c.layers)
    before=energy(t,c)
    base_cop=row["COP"]
    lift=max(0.,c.charge_temp_c+c.hx_approach_k-row["DH_Supply_C"])
    cop=base_cop*row["Temperature_Lift_K"]/(row["Temperature_Lift_K"]+lift)
    source_headroom=max(0.,row["Source_Heat_Available_MW"]-row["HP_Source_Used_MW"])
    elec_headroom=min(c.extra_hp_electric_mw,
                      max(0.,c.site_electric_cap_mw-row["DC_Total_MW"]),
                      max(0.,c.hp_total_electric_cap_mw-row["HP_Electric_MW"]))
    charge_budget=0.
    if cop>1.01:
        charge_budget=max(0.,min(c.charge_mw,
              max(0.,row["Curtailed_HP_Heat_MW"])*min(1.,cop/base_cop),
              elec_headroom*cop,source_headroom/(1.-1./cop)))
    gas=max(0.,row["Gas_Heat_MW"])
    discharge_budget=min(gas,c.discharge_mw)
    qin=qout=loss=0.
    max_residual=0.
    dt_h=1./c.substeps
    threshold=row["DH_Supply_C"]+c.hx_approach_k
    for _ in range(c.substeps):
        start=energy(t,c)
        # Charge from hot inlet at top; extract same water mass at bottom.
        q_c=0.
        if charge_budget-qin>EPS and c.charge_temp_c>t[-1]+EPS:
            q_c=min(charge_budget-qin,c.charge_mw*dt_h,
                    0.5*cell*(c.charge_temp_c-t[-1]))
            alpha=q_c/(cell*(c.charge_temp_c-t[-1]))
            old=t[:]
            for i in range(c.layers):
                t[i]=old[i]+alpha*((c.charge_temp_c if i==0 else old[i-1])-old[i])
            qin+=q_c
        # Discharge: hot outlet to DH, return enters bottom. Reject below supply gate.
        q_d=0.
        if discharge_budget-qout>EPS and t[0]>max(threshold,c.return_temp_c)+EPS:
            diff=t[0]-c.return_temp_c
            alpha_max=0.5
            if t[0]>t[1]+EPS:
                alpha_max=min(alpha_max,max(0.,(t[0]-threshold)/(t[0]-t[1])))
            q_d=min(discharge_budget-qout,c.discharge_mw*dt_h,
                    alpha_max*cell*diff)
            if q_d>EPS:
                alpha=q_d/(cell*diff)
                old=t[:]
                for i in range(c.layers):
                    t[i]=old[i]+alpha*((old[i+1] if i<c.layers-1 else c.return_temp_c)-old[i])
                qout+=q_d
        # Ambient UA and vertical interlayer conduction. Both explicitly energy accounted.
        qloss=0.
        for i in range(c.layers):
            q=max(0.,c.ua_kw_per_k/c.layers/1000.*(t[i]-c.ambient_c)*dt_h)
            t[i]-=q/cell; qloss+=q
        old=t[:]
        for i in range(c.layers-1):
            q=c.mixing_kw_per_k/1000.*(old[i]-old[i+1])*dt_h
            t[i]-=q/cell; t[i+1]+=q/cell
        loss+=qloss
        residual=energy(t,c)-start-q_c+q_d+qloss
        max_residual=max(max_residual,abs(residual))
        if abs(residual)>1e-7:raise AssertionError(f"energy conservation {residual}")
    if qin>charge_budget+1e-7 or qout>discharge_budget+1e-7:raise AssertionError("hourly power")
    if any(x>c.charge_temp_c+1e-7 for x in t):raise AssertionError("hot inlet bound")
    if any(not math.isfinite(x) for x in t):raise AssertionError("nonfinite state")
    final=energy(t,c)
    if abs(final-before-qin+qout+loss)>1e-6:raise AssertionError("hour balance")
    return t,{"charge_mwh":qin,"delivered_mwh":qout,"loss_mwh":loss,
        "added_electric_mwh":qin/cop if cop>1.01 else 0.,
        "source_heat_mwh":qin*(1.-1./cop) if cop>1.01 else 0.,
        "remaining_gas_heat_mwh":gas-qout,
        "max_substep_residual_mwh":max_residual,
        "temperature_gate_blocked":int(gas>0 and temps[0]<threshold),
        "effective_cop":cop,"initial_energy_mwh":before,"final_energy_mwh":final}

def simulate(rows,c,years=3):
    validate(c)
    if not rows or years<1:raise ValueError("empty")
    t=[c.initial_temp_c]*c.layers
    yearly=[]
    for y in range(years):
        initial=energy(t,c)
        totals={k:0. for k in ("charge_mwh","delivered_mwh","loss_mwh",
                               "added_electric_mwh","source_heat_mwh","remaining_gas_heat_mwh")}
        blocked=0;maxres=0.
        for row in rows:
            t,z=hourly(t,row,c)
            for k in totals:totals[k]+=z[k]
            blocked+=z["temperature_gate_blocked"]
            maxres=max(maxres,z["max_substep_residual_mwh"])
        final=energy(t,c)
        residual=final-initial-totals["charge_mwh"]+totals["delivered_mwh"]+totals["loss_mwh"]
        if abs(residual)>1e-5:raise AssertionError(f"year balance {residual}")
        yearly.append({"year":y+1,"initial_energy_mwh":initial,"final_energy_mwh":final,
            "balance_residual_mwh":residual,"max_substep_residual_mwh":maxres,
            "temperature_blocked_hours":blocked,"top_c":t[0],"bottom_c":t[-1],
            **totals})
    return {"config":asdict(c),"yearly":yearly,"final_profile_c":t,
        "classification":"SYNTHETIC_STRATIFIED_COUNTERFACTUAL_NOT_INCREMENTAL_SAVINGS"}

def geometry_ua_kw_per_k(volume_m3,height_m=10.,u_w_m2_k=0.15):
    """Equivalent cylinder side+top+bottom area times assumed U (W/m2/K)."""
    if not all(math.isfinite(x) for x in (volume_m3,height_m,u_w_m2_k)) or volume_m3<=0 or height_m<=0 or u_w_m2_k<0:
        raise ValueError("invalid insulation geometry")
    radius=math.sqrt(volume_m3/(math.pi*height_m))
    area=2.*math.pi*radius*height_m+2.*math.pi*radius*radius
    return area*u_w_m2_k/1000.

def run():
    rows,sha=load()
    configs=[
        Config(volume_m3=10000,charge_temp_c=72,ua_kw_per_k=geometry_ua_kw_per_k(10000)),
        Config(volume_m3=10000,charge_temp_c=80,ua_kw_per_k=geometry_ua_kw_per_k(10000)),
        Config(volume_m3=305485.8,charge_temp_c=72,ua_kw_per_k=geometry_ua_kw_per_k(305485.8)),
        Config(volume_m3=305485.8,charge_temp_c=80,ua_kw_per_k=geometry_ua_kw_per_k(305485.8)),
        Config(volume_m3=10000,charge_temp_c=80,ua_kw_per_k=0.,mixing_kw_per_k=0.),
    ]
    cases=[simulate(rows,c) for c in configs]
    out={"source_sha256":sha,"source_rows":len(rows),"synthetic_not_metered":True,
         "baseline_existing_storage_mwh":100,"primary_source_signoffs":0,
         "case_results":cases,"assumed_insulation_u_w_m2_k":0.15,"equivalent_cylinder_height_m":10.,"assumptions":[
          "Finite-volume fixed-volume equal-mass layers; 8 substeps/h; upwind advection CFL<=0.5.",
          "Charge at fixed hot-inlet temperature, bottom extraction; discharge at top, return injected at bottom.",
          "Return 35 C, ambient 15 C, U=0.15 W/m2/K, cylinder height 10 m and mixing are assumed, NOT measured.",
          "The same synthetic baseline already includes a 100 MWh storage; no incremental gas savings are claimed.",
          "COP lift adjustment is heuristic, not an OEM map. Site/HP electric caps are assumed.",
          "No pressure drop, hydraulic pump power, variable density, freezing, or validated vessel geometry.",
          "Layer temperature gate is conservative per substep, but no heat-exchanger dynamic response.",
          "3 repetitions of one synthetic year; no metered validation, no MATLAB/Simulink integration, 0/31 sources signed."
         ]}
    dest=Path(__file__).with_name("STRATIFIED_TANK_RESULTS.json")
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"source_rows":len(rows),"cases":[{"volume_m3":v["config"]["volume_m3"],
        "charge_c":v["config"]["charge_temp_c"],"ua_kw_k":v["config"]["ua_kw_per_k"],
        "year3_delivered_mwh":round(v["yearly"][2]["delivered_mwh"],3),
        "year3_added_electric_mwh":round(v["yearly"][2]["added_electric_mwh"],3),
        "top_c":round(v["yearly"][2]["top_c"],3),
        "year3_energy_residual_mwh":v["yearly"][2]["balance_residual_mwh"]}
        for v in cases]}))
if __name__=="__main__":run()
