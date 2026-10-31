"""C100: isolated synthetic indoor-pool air moisture + sensible ventilation ledger.
No manufacturer data, measured RH, fan power, humidifier power or real plant approval.
Pool water latent loss is NOT charged a second time to ventilation heating.
"""
from __future__ import annotations
import csv, gzip, hashlib, importlib.util, json, math, os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
C93=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
C93_SHA="0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923"
C88=REC/"AUTONOMOUS_RUN_20261030_1254_DCHR_C88_NATIVE_MATLAB_REPLAY"/"Warm45_Storage100_v2_MATLAB_NATIVE.csv"
C88_SHA="07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370"
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
P_KPA=101.325
INDOOR_T=29.0
INDOOR_RH=0.55
POOL_T=28.0
FLOW_M3_H=3000.0
DRY_AIR_DENSITY=1.18
CP_DRY_AIR=1.005
COVER=0.15
DEHUM_KWH_PER_KG=0.50
CONDENSER_HEAT_TO_AIR=0.50
OUTDOOR_RH=(0.40,0.70,0.90)
HRV_EFF=(0.0,0.50,0.80)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def guard():
    for root in (D,REC,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))

def sat_kpa(t):
    if not math.isfinite(t) or not -50<t<80:raise ValueError("BAD_TEMPERATURE")
    return 0.61094*math.exp(17.625*t/(t+243.04))

def humidity_ratio(t,rh):
    if not math.isfinite(rh) or not 0<=rh<=1:raise ValueError("BAD_RH")
    pv=rh*sat_kpa(t)
    if not 0<=pv<P_KPA:raise ValueError("BAD_VAPOR_PRESSURE")
    return 0.62198*pv/(P_KPA-pv)

def hour_balance(t_out,rh_out,evap_kg_h,hrv):
    if not all(map(math.isfinite,(t_out,rh_out,evap_kg_h,hrv))):
        raise ValueError("NONFINITE_INPUT")
    if evap_kg_h<0 or not 0<=hrv<=1:raise ValueError("BAD_LOAD_OR_HRV")
    w_in=humidity_ratio(INDOOR_T,INDOOR_RH)
    w_out=humidity_ratio(t_out,rh_out)
    mdry=FLOW_M3_H*DRY_AIR_DENSITY
    moisture_net=evap_kg_h+mdry*(w_out-w_in)
    dehum=max(0.0,moisture_net)
    humid=max(0.0,-moisture_net)
    # Fixed indoor RH requires humidification in cold/dry hours; energy is NOT modelled.
    moisture_residual=evap_kg_h+mdry*(w_out-w_in)-dehum+humid
    sensible_raw=max(0.0,mdry*CP_DRY_AIR*(INDOOR_T-t_out)/3_600_000.0)
    sensible_after=sensible_raw*(1-hrv)
    dehum_elec=dehum*DEHUM_KWH_PER_KG/1000.0
    condensate_latent=dehum*(2501.0-2.361*INDOOR_T)/3_600_000.0
    condenser_potential=CONDENSER_HEAT_TO_AIR*(condensate_latent+dehum_elec)
    condenser_credit=min(sensible_after,condenser_potential)
    external_air_heat=sensible_after-condenser_credit
    if abs(moisture_residual)>1e-8 or abs(sensible_after-condenser_credit-external_air_heat)>1e-12:
        raise RuntimeError("BALANCE_FAIL")
    return {"w_indoor":w_in,"w_outdoor":w_out,"evap_kg":evap_kg_h,
            "dehum_kg":dehum,"humidification_kg":humid,
            "moisture_residual_kg":moisture_residual,
            "vent_sensible_raw_MWh":sensible_raw,
            "vent_sensible_after_HRV_MWh":sensible_after,
            "dehum_electric_MWh":dehum_elec,
            "condensate_latent_MWh":condensate_latent,
            "condenser_air_credit_MWh":condenser_credit,
            "external_air_heat_MWh":external_air_heat}

def selftest():
    n=0
    def ck(v):
        nonlocal n
        assert v;n+=1
    ck(humidity_ratio(29,.55)>humidity_ratio(0,.7))
    ck(abs(humidity_ratio(29,.55)-.62198*(.55*sat_kpa(29))/(101.325-.55*sat_kpa(29)))<1e-14)
    a=hour_balance(0,.7,10,0)
    b=hour_balance(0,.7,10,.8)
    ck(a["external_air_heat_MWh"]>=b["external_air_heat_MWh"])
    ck(abs(a["dehum_kg"]-b["dehum_kg"])<1e-12)
    ck(a["moisture_residual_kg"]==0 or abs(a["moisture_residual_kg"])<1e-10)
    ck(hour_balance(29,.55,0,0)["external_air_heat_MWh"]==0)
    ck(hour_balance(-10,.4,0,0)["humidification_kg"]>0)
    ck(hour_balance(35,.9,0,0)["dehum_kg"]>0)
    ck(hour_balance(10,.5,20,0)["dehum_electric_MWh"]>=0)
    for vals in ((29,1.2,0,0),(29,.5,-1,0),(29,.5,1,1.2),(float("nan"),.5,1,0)):
        try:hour_balance(*vals)
        except ValueError:n+=1
        else:raise AssertionError("BAD_INPUT_ACCEPTED")
    print(f"C100 SELFTEST {n}/{n} PASS")
    return n

COLS=("scenario","time","Tout_C","RH_out_assumed","HRV_sensible_eff",
      "evap_kg","w_indoor","w_outdoor","dehum_kg","humidification_kg",
      "moisture_residual_kg","vent_sensible_raw_MWh","vent_sensible_after_HRV_MWh",
      "dehum_electric_MWh","condensate_latent_MWh","condenser_air_credit_MWh",
      "external_air_heat_MWh")

def run():
    guard();selftest()
    if sha(C93)!=C93_SHA or sha(C88)!=C88_SHA:raise RuntimeError("SOURCE_SHA_DRIFT")
    spec=importlib.util.spec_from_file_location("c93_for_c100",C93)
    c93=importlib.util.module_from_spec(spec);spec.loader.exec_module(c93)
    c91,c92,_,times=c93.load()
    with C88.open("r",encoding="utf-8-sig",newline="") as f:outdoor=list(csv.DictReader(f))
    if len(times)!=8760 or len(outdoor)!=8760:raise RuntimeError("NOT_8760")
    tout=[]
    for stamp,row in zip(times,outdoor):
        if datetime.strptime(row["Time"],"%d-%b-%Y %H:%M:%S")!=stamp:
            raise RuntimeError("TIMESTAMP_MISMATCH")
        tout.append(float(row["Tout_C"]))
    out=D/"C100_AIR_HOURLY.csv.gz";partial=D/"C100_AIR_HOURLY.partial.csv.gz"
    summary=D/"C100_AIR_SUMMARY.csv";meta=D/"C100_METADATA.json"
    if any(p.exists() for p in (out,partial,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
    summaries=[]
    with gzip.open(partial,"wt",encoding="utf-8",newline="",compresslevel=4) as f:
        w=csv.writer(f);w.writerow(COLS)
        for rh in OUTDOOR_RH:
            for hrv in HRV_EFF:
                guard()
                name=f"RHout{int(rh*100)}_HRV{int(hrv*100)}"
                totals=defaultdict(float)
                dry_hours=0;wet_hours=0
                for i,(stamp,tc) in enumerate(zip(times,tout)):
                    if i%720==0:guard()
                    _,evap=c93.loss_components(c91,c92,POOL_T,stamp.hour,INDOOR_RH,COVER)
                    h=hour_balance(tc,rh,evap,hrv)
                    dry_hours+=int(h["humidification_kg"]>1e-9)
                    wet_hours+=int(h["dehum_kg"]>1e-9)
                    for k in ("evap_kg","dehum_kg","humidification_kg",
                        "vent_sensible_raw_MWh","vent_sensible_after_HRV_MWh",
                        "dehum_electric_MWh","condensate_latent_MWh",
                        "condenser_air_credit_MWh","external_air_heat_MWh"):
                        totals[k]+=h[k]
                    w.writerow([name,stamp.isoformat(),f"{tc:.8f}",rh,hrv]+
                        [f"{h[k]:.12f}" for k in COLS[5:]])
                residual=totals["vent_sensible_after_HRV_MWh"]-totals["condenser_air_credit_MWh"]-totals["external_air_heat_MWh"]
                if abs(residual)>1e-8:raise RuntimeError("ANNUAL_AIR_BALANCE")
                summaries.append({"scenario":name,"RH_out_assumed":rh,"HRV_sensible_eff":hrv,
                    "hours":len(times),"humidification_hours":dry_hours,"dehum_hours":wet_hours,
                    **{k:round(v,9) for k,v in totals.items()},"air_balance_residual_MWh":residual})
    guard();os.replace(partial,out)
    with summary.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    metadata={"schema":"C100_POOL_AIR_HVAC_SIDECAR_V1","task_id":TASK,
        "synthetic":True,"measured_weather":False,"measured_outdoor_RH":False,
        "manufacturer_dehumidifier":False,"field_validated":False,
        "source_signoffs_added":0,"scenarios":len(summaries),
        "hourly_rows":len(summaries)*8760,
        "source_C93_sha256":C93_SHA,"source_C88_sha256":C88_SHA,
        "hourly_sha256":sha(out),"summary_sha256":sha(summary),
        "assumptions":{"pool_water_C":POOL_T,"indoor_air_C":INDOOR_T,
          "indoor_RH_controlled":INDOOR_RH,"outdoor_RH_assumed":OUTDOOR_RH,
          "flow_m3_h":FLOW_M3_H,"dry_air_density_kg_m3":DRY_AIR_DENSITY,
          "HRV_sensible_eff":HRV_EFF,"dehum_kWh_per_kg":DEHUM_KWH_PER_KG,
          "dehum_condenser_fraction_to_air":CONDENSER_HEAT_TO_AIR,
          "night_cover_evap_multiplier":COVER},
        "interpretation":"Air-side ledger is separate from C96 water heating; pool evaporation latent already charged to water. Condenser air heat credit is not credited to pool.",
        "excluded":["fan and filter electricity","cooling and free cooling",
          "humidifier energy and water treatment","supply/exhaust imbalance",
          "dynamic indoor humidity and temperature","actual HRV frost/condensation",
          "vendor dehumidifier performance","real pool source and source allocations"],
        "limits":["C88 outdoor temperature is synthetic, not measured.",
          "Outdoor RH held constant per scenario, not meteorological data.",
          "HRV is sensible-only; dehumidifier electricity is assumed.",
          "Humidification mass is reported but its energy is not included.",
          "These results cannot establish physical feasibility or total building energy."]}
    with meta.open("x",encoding="utf-8") as f:json.dump(metadata,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"scenarios":len(summaries),"rows":len(summaries)*8760,
      "summary_sha256":sha(summary),"hourly_sha256":sha(out),
      "anchors":[{"name":s["scenario"],"air_heat_MWh":round(s["external_air_heat_MWh"],2),
        "dehum_el_MWh":round(s["dehum_electric_MWh"],2),
        "humidification_kg":round(s["humidification_kg"],1)}
        for s in summaries if s["scenario"] in ("RHout40_HRV0","RHout70_HRV50","RHout90_HRV80")]},indent=2))
if __name__=="__main__":
    import sys
    if "--selftest" in sys.argv:selftest()
    else:run()
