"""C90 isolated 500 m3 pool-load and unused-HX-source counterfactual.
All coefficients are explicitly assumed, NOT sourced standards or field data.
Do not treat HX_Rejected_MW as a verified physically recoverable resource.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / "AUTONOMOUS_RUN_20261030_1254_DCHR_C88_NATIVE_MATLAB_REPLAY" / "Warm45_Storage100_v2_MATLAB_NATIVE.csv"
SOURCE_SHA = "07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370"
TASK = "scc-2aab24704c2bd0"
FLAGS = ("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
A_M2, V_M3 = 250.0, 500.0
TW, TA, TRAD, TG, TMAKE = 28.0, 29.0, 27.0, 18.0, 12.0
RHO_W, CP_W = 997.0, 4.186
CAPACITY_MWH_PER_K = V_M3 * RHO_W * CP_W / 3_600_000.0
COP, MAX_ELEC_MW, MAX_HEAT_MW = 4.0, 0.075, 0.30
K_EVAP = 0.12  # ASSUMED kg/(m2 h kPa), not an ASHRAE/VDI normative value
RHO_AIR, CP_AIR, FLOW_M3_H = 1.18, 1.005, 3000.0

SCENARIOS = {
    "covered_no_extra": (True, 0.0, 0.55),
    "covered_25pct": (True, 0.25, 0.55),
    "covered_50pct": (True, 0.50, 0.55),
    "covered_100pct": (True, 1.0, 0.55),
    "uncovered_50pct": (False, 0.50, 0.55),
    "covered_dry_air_50pct": (True, 0.50, 0.40),
}

def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024*1024), b""):
            h.update(block)
    return h.hexdigest()

def guard():
    for folder in (ROOT, ROOT.parent, ROOT.parent.parent, Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for flag in FLAGS:
            if (folder / flag).exists():
                raise RuntimeError("STOP_ACTIVE: " + str(folder / flag))

def saturation_kpa(temp_c):
    return 0.61094 * math.exp(17.625 * temp_c / (temp_c + 243.04))

def pool_losses(hour, rh, night_cover):
    covered = night_cover and (hour >= 20 or hour < 7)
    occupied = 9 <= hour < 20
    delta_p = max(0.0, saturation_kpa(TW) - rh*saturation_kpa(TA))
    evap_kg_h = A_M2*K_EVAP*delta_p*(1.5 if occupied else 1.0)*(0.15 if covered else 1.0)
    latent_mw = evap_kg_h*(2501.0 - 2.361*TW)/3_600_000.0
    makeup_mw = evap_kg_h*CP_W*(TW-TMAKE)/3_600_000.0
    conv_mw = max(0.0, 3.0*A_M2*(TW-TA)/1e6)*(0.25 if covered else 1.0)
    rad_mw = max(0.0, 0.96*5.670374419e-8*A_M2*((TW+273.15)**4-(TRAD+273.15)**4)/1e6)*(0.30 if covered else 1.0)
    ground_mw = 0.35*(A_M2 + 140.0)*(TW-TG)/1e6
    return (latent_mw+makeup_mw+conv_mw+rad_mw+ground_mw,
            {"evap_kg_h":evap_kg_h,"latent_mw":latent_mw,"makeup_mw":makeup_mw,
             "conv_mw":conv_mw,"rad_mw":rad_mw,"ground_mw":ground_mw})

def extra_heat(rejected_mw, recoverable_fraction):
    source_cap = max(0.0, rejected_mw)*recoverable_fraction
    heat = min(source_cap*COP/(COP-1.0), MAX_ELEC_MW*COP, MAX_HEAT_MW)
    return heat, heat/COP, heat*(COP-1.0)/COP

def selftest():
    assert abs(CAPACITY_MWH_PER_K-0.579633) < 0.001
    assert saturation_kpa(28) > saturation_kpa(20)
    a,_ = pool_losses(12,0.55,False)
    b,_ = pool_losses(22,0.55,True)
    c,_ = pool_losses(22,0.55,False)
    assert 0 < b < c and a > 0
    dry,_ = pool_losses(12,0.40,False)
    assert dry > a
    assert extra_heat(0.2,0.0)==(0.0,0.0,0.0)
    h,e,s = extra_heat(0.2,0.5)
    assert abs(h-e-s)<1e-12 and h <= MAX_HEAT_MW and e<=MAX_ELEC_MW
    assert extra_heat(0.2,1.0)[0] >= h
    print("SELFTEST 8/8 PASS")

def run():
    guard()
    if sha(SOURCE) != SOURCE_SHA:
        raise RuntimeError("PINNED_SOURCE_DRIFT")
    rows = list(csv.DictReader(SOURCE.open("r",encoding="utf-8-sig",newline="")))
    if len(rows) != 8760:
        raise RuntimeError("EXPECTED_8760_HOURS")
    timestamps = [dt.datetime.strptime(r["Time"],"%d-%b-%Y %H:%M:%S") for r in rows]
    if any((b-a)!=dt.timedelta(hours=1) for a,b in zip(timestamps,timestamps[1:])):
        raise RuntimeError("NON_CONTIGUOUS_HOURS")
    out = []
    totals = {}
    monthly = defaultdict(lambda: defaultdict(float))
    for name,(cover,fraction,rh) in SCENARIOS.items():
        t = defaultdict(float)
        hours_unmet = 0
        peak = 0.0
        for stamp,r in zip(timestamps,rows):
            q,parts = pool_losses(stamp.hour,rh,cover)
            rejected = float(r["HX_Rejected_MW"])
            heat,elec,source_used = extra_heat(rejected,fraction)
            delivered = min(q,heat)
            unmet = q-delivered
            air_vent = max(0.0,FLOW_M3_H*RHO_AIR*CP_AIR*(TA-float(r["Tout_C"]))/3_600_000.0)
            if min(q,rejected,heat,elec,source_used,unmet,air_vent) < -1e-12:
                raise RuntimeError("NEGATIVE_ENERGY")
            if abs(heat-elec-source_used)>1e-10 or source_used>max(0.0,rejected)*fraction+1e-10:
                raise RuntimeError("HEAT_SOURCE_BALANCE")
            if unmet>1e-9:
                hours_unmet+=1
            peak=max(peak,q)
            vals={"pool_load_MWh":q,"extra_HP_potential_MWh":heat,
                  "pool_delivered_MWh":delivered,"pool_unmet_MWh":unmet,
                  "HP_electric_if_fully_used_MWh":elec,
                  "HP_source_if_fully_used_MWh":source_used,
                  "air_ventilation_separate_MWh":air_vent,
                  "latent_MWh":parts["latent_mw"],
                  "makeup_MWh":parts["makeup_mw"]}
            for key,value in vals.items():
                t[key]+=value
                monthly[(name,stamp.strftime("%Y-%m"))][key]+=value
            out.append({"time":stamp.isoformat(),"scenario":name,"pool_load_MW":f"{q:.10f}",
                        "HX_rejected_MW":f"{rejected:.10f}","recoverable_fraction":fraction,
                        "potential_aux_HP_heat_MW":f"{heat:.10f}",
                        "delivered_to_pool_MW":f"{delivered:.10f}",
                        "unmet_pool_MW":f"{unmet:.10f}",
                        "air_ventilation_separate_MW":f"{air_vent:.10f}"})
        totals[name] = {**dict(t),"hours_unmet":hours_unmet,"peak_pool_MW":peak,
                        "fraction_source_assumed_recoverable":fraction,
                        "night_cover":cover,"relative_humidity":rh,
                        "pool_energy_coverage_fraction":1.0-t["pool_unmet_MWh"]/t["pool_load_MWh"],
                        "equiv_unheated_24h_temperature_drop_C":24*(t["pool_load_MWh"]/8760)/CAPACITY_MWH_PER_K}
    guard()
    result={"schema":"C90_POOL_500M3_COUNTERFACTUAL_V1","task_id":TASK,
            "input_C88_sha256":SOURCE_SHA,"input_hours":len(rows),
            "synthetic":True,"validated_physical_coefficients":False,
            "pool":{"length_m":25,"width_m":10,"depth_m":2,"volume_m3":V_M3,
                    "surface_m2":A_M2,"water_C":TW,"air_C":TA,
                    "heat_capacity_MWh_per_C":CAPACITY_MWH_PER_K},
            "assumptions":{"k_evap_kg_m2_h_kPa":K_EVAP,"occupancy_multiplier":1.5,
                           "cover_evap_multiplier":0.15,"RH_baseline":0.55,
                           "air_flow_m3_h":FLOW_M3_H,"air_ventilation_is_separate":True,
                           "COP_incremental":COP,"max_aux_HP_electric_MW":MAX_ELEC_MW,
                           "max_aux_HP_heat_MW":MAX_HEAT_MW,
                           "HX_Rejected_MW_is_counterfactual_not_proven_recoverable":True,
                           "no_shared_heat_allocation_or_existing_load_subtraction":True},
            "scenarios":totals,"limitations":["All psychrometric/transfer coefficients are illustrative, not source-validated.",
            "Ventilation air heating is calculated separately, not silently added to pool water demand.",
            "HX_Rejected_MW may be unrecoverable due to temperature, HX pinch, pumping and ownership.",
            "Potential HP electric/source totals assume full potential operation, not actual dispatch.",
            "Constant 28 C water thermostat; no dynamic temperature/control, pool occupancy measured data or standard signoff.",
            "Existing district heat allocation and incremental plant CAPEX/operating constraints unverified."]}
    with (ROOT/"C90_POOL_HOURLY.csv").open("x",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
    with (ROOT/"C90_POOL_MONTHLY.csv").open("x",encoding="utf-8",newline="") as f:
        keys=["scenario","month",*list(next(iter(monthly.values())).keys())]
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
        for (scenario,month),vals in sorted(monthly.items()):
            w.writerow({"scenario":scenario,"month":month,**vals})
    with (ROOT/"C90_POOL_SUMMARY.json").open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=False,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({k:{"pool_MWh":round(v["pool_load_MWh"],2),
                             "coverage_pct":round(v["pool_energy_coverage_fraction"]*100,2),
                             "hours_unmet":v["hours_unmet"],"peak_kW":round(v["peak_pool_MW"]*1000,2)}
                      for k,v in totals.items()},indent=2))

if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--selftest":
        selftest()
    else:
        run()
