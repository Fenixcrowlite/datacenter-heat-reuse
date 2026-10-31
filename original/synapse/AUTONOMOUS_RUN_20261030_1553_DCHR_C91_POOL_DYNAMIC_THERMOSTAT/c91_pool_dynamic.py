"""C91: isolated 500 m3 pool dynamic thermostat, counterfactual heat-source scenarios.
Inputs are synthetic C90 values; source recoverability and transfer coefficients UNVALIDATED.
No shared MATLAB, SCADA, GUI, worktree, or external system writes.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent.parent
C90=ROOT.parent/"AUTONOMOUS_RUN_20261030_1452_DCHR_C90_POOL_COUNTERFACTUAL"/"C90_POOL_HOURLY.csv"
C90_SHA="0a5e674d316e1d4e223861f1e728ff095a84485b0a4b99da6e38b67af81be8e7"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
CAP=500.0*997.0*4.186/3600000.0  # MWh per kelvin
COP=4.0
ON_C=27.85
OFF_C=28.05
INITIAL_C=28.0
SCENARIOS={"no_recovery":(0.0,0.0),"fraction_10pct":(0.10,0.0),
           "fraction_10pct_backup50kW":(0.10,0.05),"fraction_25pct":(0.25,0.0),"fraction_25pct_backup50kW":(0.25,0.05),
           "fraction_50pct":(0.50,0.0)}

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1048576),b""): h.update(b)
    return h.hexdigest()

def guard():
    for d in (ROOT,ROOT.parent,BASE,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for flag in FLAGS:
            if (d/flag).exists(): raise RuntimeError("STOP_ACTIVE "+str(d/flag))

def saturation(t):
    return 0.61094*math.exp(17.625*t/(t+243.04))

def losses(t, hour, rh=0.55, night_cover=True):
    covered=night_cover and (hour>=20 or hour<7)
    occupied=9<=hour<20
    evap=250.0*0.12*max(0.0,saturation(t)-rh*saturation(29.0))*(1.5 if occupied else 1.0)*(0.15 if covered else 1.0)
    latent=evap*(2501.0-2.361*t)/3600000.0
    makeup=evap*4.186*(t-12.0)/3600000.0
    conv=max(0.0,3.0*250.0*(t-29.0)/1e6)*(0.25 if covered else 1.0)
    rad=max(0.0,0.96*5.670374419e-8*250.0*((t+273.15)**4-(27.0+273.15)**4)/1e6)*(0.30 if covered else 1.0)
    ground=0.35*(250.0+140.0)*(t-18.0)/1e6
    return latent+makeup+conv+rad+ground

def potential_hp(source, fraction):
    if not math.isfinite(source) or source < 0: raise ValueError("INVALID_HX_SOURCE")
    if not 0<=fraction<=1: raise ValueError("INVALID_FRACTION")
    return min(source*fraction*COP/(COP-1),0.075*COP,0.30)

def simulate_hour(temp, active, source, fraction, backup_cap, hour):
    if not math.isfinite(temp) or not 0<=temp<=45: raise ValueError("INVALID_POOL_TEMPERATURE")
    q=losses(temp,hour)
    if temp<=ON_C: active=True
    elif temp>=OFF_C: active=False
    request=max(0.0, q+(OFF_C-temp)*CAP) if active else 0.0
    hp=min(request,potential_hp(source,fraction))
    backup=min(backup_cap,max(0.0,(27.60-(temp+(hp-q)/CAP))*CAP)) if active else 0.0
    next_temp=temp+(hp+backup-q)/CAP
    if not math.isfinite(next_temp) or not 0<=next_temp<=45: raise ValueError("UNPHYSICAL_NEXT_TEMPERATURE")
    return next_temp,active,q,hp,backup,request

def selftest():
    assert 0.579<CAP<0.581
    assert 0 < losses(28,12) < 0.1
    assert losses(28,12)>losses(28,22)
    assert losses(29,12)>losses(27,12)
    assert potential_hp(0.2,0)==0
    assert potential_hp(0.2,0.5)<=0.3
    assert potential_hp(0.2,0.5)>potential_hp(0.2,0.1)
    nxt,active,q,hp,backup,req=simulate_hour(27.7,False,0.2,0.25,0.05,12)
    assert active and hp>=0 and backup>=0 and abs((nxt-27.7)*CAP-(hp+backup-q))<1e-12
    nxt,active,q,hp,backup,req=simulate_hour(28.1,True,0.2,0.25,0.05,12)
    assert not active and hp==backup==0
    try: potential_hp(-1,0.2)
    except ValueError: pass
    else: raise AssertionError("NEGATIVE_SOURCE_ACCEPTED")
    nxt,active,q,hp,backup,req=simulate_hour(27.4,True,0.0,0.1,0.05,12)
    assert backup>0 and hp==0 and nxt>27.4-q/CAP
    print("C91 SELFTEST 11/11 PASS")

def run():
    guard()
    if sha(C90)!=C90_SHA: raise RuntimeError("C90_PIN_MISMATCH")
    with C90.open("r",encoding="utf-8-sig",newline="") as f:
        data=[r for r in csv.DictReader(f) if r["scenario"]=="covered_no_extra"]
    if len(data)!=8760: raise RuntimeError("BAD_HOURLY_COUNT")
    times=[dt.datetime.fromisoformat(r["time"]) for r in data]
    if any(b-a!=dt.timedelta(hours=1) for a,b in zip(times,times[1:])): raise RuntimeError("NON_CONTIGUOUS")
    if times[0]!=dt.datetime(2026,1,1) or times[-1]!=dt.datetime(2026,12,31,23): raise RuntimeError("WRONG_YEAR")
    for i in (0,12,1000,4000,8759):
        if abs(losses(28,times[i].hour)-float(data[i]["pool_load_MW"]))>1e-9:
            raise RuntimeError("C90_BASELINE_MISMATCH")
    hourly=[]; monthly=defaultdict(lambda:defaultdict(float)); summary={}
    for scenario,(fraction,backup_cap) in SCENARIOS.items():
        t=INITIAL_C; active=False; low=0; comfort_degree_hours=0.0
        peak_drop=0.0; totals=defaultdict(float); min_temp=50; max_temp=-50
        for stamp,row in zip(times,data):
            source=float(row["HX_rejected_MW"])
            t0=t
            t,active,q,hp,backup,request=simulate_hour(t,active,source,fraction,backup_cap,stamp.hour)
            electric=hp/COP; extracted=hp-electric
            if extracted>source*fraction+1e-10 or hp>0.3+1e-10 or backup>backup_cap+1e-10:
                raise RuntimeError("SOURCE_OR_CAP_VIOLATION")
            if abs(CAP*(t-t0)-(hp+backup-q))>1e-11: raise RuntimeError("ENERGY_BALANCE")
            min_temp=min(min_temp,t);max_temp=max(max_temp,t)
            low+=int(t<27.5)
            comfort_degree_hours+=max(0,27.5-t)
            vals={"pool_loss_MWh":q,"HP_heat_MWh":hp,"HP_electric_MWh":electric,
                  "HX_extracted_MWh":extracted,"backup_MWh":backup,
                  "net_storage_change_MWh":CAP*(t-t0)}
            for k,v in vals.items():
                totals[k]+=v;monthly[(scenario,stamp.strftime("%Y-%m"))][k]+=v
            hourly.append({"time":stamp.isoformat(),"scenario":scenario,
                           "temp_start_C":f"{t0:.10f}","temp_end_C":f"{t:.10f}",
                           "thermostat_on":int(active),"pool_loss_MW":f"{q:.10f}",
                           "HP_heat_MW":f"{hp:.10f}","HP_electric_MW":f"{electric:.10f}",
                           "HX_extracted_MW":f"{extracted:.10f}","backup_MW":f"{backup:.10f}",
                           "source_HX_rejected_MW":f"{source:.10f}"})
        summary[scenario]={"fraction_assumed":fraction,"backup_cap_MW":backup_cap,
                           "min_temp_C":min_temp,"max_temp_C":max_temp,"final_temp_C":t,
                           "hours_below_27p5_C":low,"degree_hours_below_27p5_C":comfort_degree_hours,
                           **dict(totals)}
        if abs(totals["net_storage_change_MWh"]-CAP*(t-INITIAL_C))>1e-8:
            raise RuntimeError("YEAR_STORAGE_BALANCE")
    guard()
    with (ROOT/"C91_DYNAMIC_HOURLY.csv").open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(hourly[0]));w.writeheader();w.writerows(hourly)
    with (ROOT/"C91_DYNAMIC_MONTHLY.csv").open("x",encoding="utf-8",newline="") as f:
        keys=["scenario","month","pool_loss_MWh","HP_heat_MWh","HP_electric_MWh",
              "HX_extracted_MWh","backup_MWh","net_storage_change_MWh"]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for (s,m),v in sorted(monthly.items()):w.writerow({"scenario":s,"month":m,**v})
    output={"schema":"C91_POOL_DYNAMIC_THERMOSTAT_V1","task_id":"scc-2aab24704c2bd0",
            "source_C90_sha256":C90_SHA,"synthetic":True,"physical_validation":False,
            "heat_capacity_MWh_per_C":CAP,"initial_C":INITIAL_C,"thermostat_on_below_C":ON_C,
            "thermostat_off_above_C":OFF_C,"step_h":1,"assumed_COP":COP,
            "source_recoverability_not_verified":True,"scenarios":summary,
            "limitations":["Illustrative heat transfer coefficients inherited from C90.",
                           "Source heat is a hypothetical share of HX_Rejected_MW, not a plant dispatch.",
                           "No temperature pinch, measured COP, pool occupancy, ventilation coupling or tariff.",
                           "Explicit Euler 1-hour thermostat; no water stratification or mixing dynamics."]}
    with (ROOT/"C91_DYNAMIC_SUMMARY.json").open("x",encoding="utf-8") as f:
        json.dump(output,f,ensure_ascii=False,sort_keys=True,indent=2);f.write("\n")
    print(json.dumps({k:{"min_C":round(v["min_temp_C"],3),"hours_below_27p5":v["hours_below_27p5_C"],
                         "HP_MWh":round(v["HP_heat_MWh"],2),"backup_MWh":round(v["backup_MWh"],2)}
                      for k,v in summary.items()},indent=2))
if __name__=="__main__":
    if "--selftest" in sys.argv: selftest()
    else: run()
