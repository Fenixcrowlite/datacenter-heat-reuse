"""C92 source-informed sensitivity only; not a normative design signoff.
2023 ASHRAE Handbook HVAC Applications, Chapter 6, Indoor Swimming Pools:
https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx
Equation 2 coefficient 0.089 + 0.0782*V, p in kPa, Y in kJ/kg, V in m/s.
Activity factor baseline unoccupied 0.5; public/school 1.0.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, importlib.util, json, math
from pathlib import Path
D=Path(__file__).resolve().parent
C91=D.parent/"AUTONOMOUS_RUN_20261030_1553_DCHR_C91_POOL_DYNAMIC_THERMOSTAT"
spec=importlib.util.spec_from_file_location("c91",C91/"c91_pool_dynamic.py")
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SOURCE=m.C90
URL="https://handbook.ashrae.org/Handbooks/A23/SI/A23_Ch06/a23_ch06_si.aspx"
def guard():
    for root in (D,D.parent,D.parent.parent,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for f in m.FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))
def k_ashrae(tw,air_speed=0.1):
    Y=2501.0-2.361*tw
    if not (0.05<=air_speed<=0.15) or not (2000<Y<2600):raise ValueError("REFERENCE_RANGE")
    # kg/s/(m2 kPa) = (0.089+0.0782*V)/Y; multiply by 3600 to kg/h/(m2 kPa)
    return 3600.0*(0.089+0.0782*air_speed)/Y
def reference_losses(t,hour):
    covered=hour>=20 or hour<7
    occupied=9<=hour<20
    af=1.0 if occupied else 0.5
    dp=max(0,m.saturation(t)-0.55*m.saturation(29))
    evap=250*k_ashrae(t)*dp*af*(0.15 if covered else 1.0)
    latent=evap*(2501.0-2.361*t)/3600000.0
    makeup=evap*4.186*(t-12)/3600000.0
    conv=max(0,3*250*(t-29)/1e6)*(0.25 if covered else 1)
    rad=max(0,0.96*5.670374419e-8*250*((t+273.15)**4-(27+273.15)**4)/1e6)*(0.30 if covered else 1)
    ground=0.35*(250+140)*(t-18)/1e6
    return latent+makeup+conv+rad+ground
def selftest():
    assert 0.13<k_ashrae(28)<0.16
    assert abs(k_ashrae(28)-3600*(0.089+0.0782*0.1)/(2501-2.361*28))<1e-14
    assert k_ashrae(28)*1.0<0.12*1.5
    assert k_ashrae(28)*0.5<0.12
    assert reference_losses(28,12)<m.losses(28,12)
    assert reference_losses(28,2)<m.losses(28,2)
    try:k_ashrae(28,0.5)
    except ValueError:pass
    else:raise AssertionError("UNSUPPORTED_AIR_SPEED")
    print("C92 SELFTEST 7/7 PASS")
def simulate(rows,model,fraction):
    t=28.0;active=False; low=0; minimum=100; total_hp=0; total_source=0
    energy_residual=0
    for r in rows:
        hour=dt.datetime.fromisoformat(r["time"]).hour
        q=model(t,hour)
        if t<=m.ON_C:active=True
        elif t>=m.OFF_C:active=False
        need=max(0,q+(m.OFF_C-t)*m.CAP) if active else 0
        source=float(r["HX_rejected_MW"])
        hp=min(need,m.potential_hp(source,fraction))
        t2=t+(hp-q)/m.CAP
        if not 0<=t2<=45:raise RuntimeError("BAD_TEMPERATURE")
        energy_residual=max(energy_residual,abs(m.CAP*(t2-t)-(hp-q)))
        total_hp+=hp;total_source+=hp*(m.COP-1)/m.COP
        t=t2;minimum=min(minimum,t);low+=int(t<27.5)
    return {"min_temp_C":minimum,"hours_below_27p5":low,"HP_heat_MWh":total_hp,
            "HX_source_used_MWh":total_source,"final_temp_C":t,
            "max_abs_energy_residual_MWh":energy_residual}
def run():
    guard()
    if m.sha(SOURCE)!=m.C90_SHA:raise RuntimeError("C90_SOURCE_DRIFT")
    with SOURCE.open(encoding="utf-8",newline="") as f:
        rows=[r for r in csv.DictReader(f) if r["scenario"]=="covered_no_extra"]
    if len(rows)!=8760:raise RuntimeError("INPUT_HOURS")
    out={}
    for fraction in (0.10,0.25):
        for model_name,func in (("C91_assumed",m.losses),("ASHRAE2023_reference",reference_losses)):
            out[f"{model_name}_{int(fraction*100)}pct"]=simulate(rows,func,fraction)
    guard()
    result={"schema":"C92_ASHRAE_REFERENCE_SENSITIVITY_V1",
        "task_id":"scc-2aab24704c2bd0","reference_url":URL,
        "reference_year":2023,"reviewed_local_date":"2026-10-30",
        "source_input_sha256":m.C90_SHA,"source_C91_script_sha256":m.sha(C91/"c91_pool_dynamic.py"),
        "units":"kg/(m2 h kPa) for mass transfer coefficient",
        "reference_velocity_m_s":0.1,"reference_activity_unoccupied":0.5,
        "reference_activity_public_occupied":1.0,
        "C91_coefficient":0.12,"C91_multiplier_unoccupied":1.0,"C91_multiplier_occupied":1.5,
        "reference_coefficient_at_28C":k_ashrae(28),
        "reference_unoccupied_effective_at_28C":0.5*k_ashrae(28),
        "reference_public_occupied_effective_at_28C":k_ashrae(28),
        "C91_unoccupied_effective":0.12,"C91_occupied_effective":0.18,
        "cover_multiplier_still_assumed":0.15,
        "synthetic":True,"physical_field_validation":False,
        "source_signoffs_added":0,
        "notes":["ASHRAE equation and activity factors are source-informed, but actual facility classification and air speed are unmeasured.",
                 "Cover reduction 0.15, heat exchanger recoverability, COP, indoor humidity and ground coefficients remain assumed.",
                 "No claim of validated energy use or actual pool operating comfort."],
        "simulations":out}
    with (D/"C92_REFERENCE_COMPARISON.json").open("x",encoding="utf-8") as f:
        json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__":
    import sys
    if "--selftest" in sys.argv:selftest()
    else:run()
