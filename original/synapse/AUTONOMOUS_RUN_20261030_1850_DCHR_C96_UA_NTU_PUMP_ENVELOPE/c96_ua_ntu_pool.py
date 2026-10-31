"""C96: synthetic counterflow UA/NTU + auxiliary pump electricity + pool dispatch.
NOT vendor COP, measured DC temperatures, or engineering signoff.
Only writes in this isolated recovery folder. All upstream inputs SHA-pinned.
"""
from __future__ import annotations
import csv, gzip, hashlib, importlib.util, json, math, os
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
UP=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
UP_SHA="0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923"
TASK="scc-2aab24704c2bd0"
CP=4.18   # kJ/(kg K), water-like assumed constant
COLD_IN_C=15.0
COLD_FLOW=2.0
MIN_SOURCE_OUT_C=12.0
HP_THERMAL_CAP=0.300
HP_ELECTRIC_CAP=0.075
HOT_DP_KPA=30.0
COLD_DP_KPA=40.0
PUMP_ETA=0.60
HOT_T=(35.0,38.0,50.0) # 35 baseline; 38-50 sensitivity, not measurements
HOT_FLOW=(0.5,2.0)
UA_KW_K=(2.0,10.0)
COP=(2.2,4.0) # explicit assumed COP, NOT a manufacturer curve
RH,COVER=0.55,0.15
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1048576),b""):h.update(b)
    return h.hexdigest()

def guard():
    for root in (D,REC,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))

def epsilon_counterflow(ntu,cr):
    if not math.isfinite(ntu) or not math.isfinite(cr) or ntu<0 or not 0<=cr<=1:
        raise ValueError("INVALID_NTU")
    if abs(cr-1.0)<1e-10:return ntu/(1.0+ntu)
    x=math.exp(-ntu*(1.0-cr))
    return (1.0-x)/(1.0-cr*x)

def hx_limit(q_rejected_mw,hot_c,hot_flow,ua_kw_k):
    v=(q_rejected_mw,hot_c,hot_flow,ua_kw_k)
    if not all(math.isfinite(x) for x in v) or q_rejected_mw<0 or hot_flow<=0 or ua_kw_k<=0 or hot_c<=COLD_IN_C or hot_c<MIN_SOURCE_OUT_C:
        raise ValueError("INVALID_HX_INPUT")
    ch=hot_flow*CP
    cc=COLD_FLOW*CP
    cmin=min(ch,cc)
    cmax=max(ch,cc)
    ntu=ua_kw_k/cmin
    eps=epsilon_counterflow(ntu,cmin/cmax)
    q_ntu_mw=eps*cmin*(hot_c-COLD_IN_C)/1000.0
    q_ret_mw=ch*(hot_c-MIN_SOURCE_OUT_C)/1000.0
    q_cap=max(0.0,min(q_rejected_mw,q_ntu_mw,q_ret_mw))
    return q_cap,eps,q_ntu_mw,ntu

def pump_power_mw(hot_flow):
    if not math.isfinite(hot_flow) or hot_flow<=0:raise ValueError("INVALID_FLOW")
    # DeltaP[Pa]*Vdot[m3/s]/eta, rho=1000 kg/m3, to MW
    return (HOT_DP_KPA*hot_flow+COLD_DP_KPA*COLD_FLOW)/(PUMP_ETA*1e6)

def scenario_grid():
    for t in HOT_T:
        for f in HOT_FLOW:
            for ua in UA_KW_K:
                for cop in COP:
                    yield (t,f,ua,cop,0.0)
    yield (35.0,0.5,2.0,2.2,0.05)
    yield (50.0,0.5,2.0,2.2,0.05)

def selftest():
    n=0
    def check(v):
        nonlocal n
        assert v
        n+=1
    check(abs(epsilon_counterflow(1,1)-0.5)<1e-12)
    check(epsilon_counterflow(0,0.5)==0)
    check(0<epsilon_counterflow(1,0.5)<1)
    check(hx_limit(1,35,2,2)[0]<hx_limit(1,35,2,10)[0])
    check(hx_limit(1,35,0.5,10)[0]<hx_limit(1,35,2,10)[0])
    check(hx_limit(0,35,2,10)[0]==0)
    check(hx_limit(0.01,35,2,10)[0]<=0.01)
    check(pump_power_mw(2)>pump_power_mw(0.5))
    check(len(list(scenario_grid()))==26)
    for args in ((-1,35,2,10),(1,15,2,10),(1,35,0,10),(1,35,2,0),(1,float("nan"),2,10)):
        try:hx_limit(*args)
        except ValueError:n+=1
        else:raise AssertionError("BAD_INPUT_ACCEPTED")
    for args in ((-1,0.5),(1,1.5)):
        try:epsilon_counterflow(*args)
        except ValueError:n+=1
        else:raise AssertionError("BAD_NTU_ACCEPTED")
    print(f"C96 SELFTEST {n}/{n} PASS")
    return n

COLS=("scenario","time","hot_in_C","hot_flow_kg_s","UA_kW_K","COP_assumed","backup_cap_MW",
      "pool_start_C","pool_end_C","pool_loss_MW","hx_capacity_MW","hx_ntu_capacity_MW",
      "hx_extracted_MW","hot_out_C","cold_out_C","hp_heat_MW","hp_electric_MW",
      "pump_electric_MW","backup_MW","rejected_MW","epsilon","NTU")

def simulate(c93,c91,c92,rows,times,params,writer):
    hot,flow,ua,cop,backup_cap=params
    scenario="T%s_F%s_UA%s_COP%s_B%s"%params
    t=28.0;active=False;low=0;minimum=100.0
    totals=defaultdict(float)
    ch=flow*CP;cc=COLD_FLOW*CP
    for i,(stamp,row) in enumerate(zip(times,rows)):
        if i%720==0:guard()
        q,evap=c93.loss_components(c91,c92,t,stamp.hour,RH,COVER)
        if t<=c91.ON_C:active=True
        elif t>=c91.OFF_C:active=False
        request=max(0.0,q+(c91.OFF_C-t)*c91.CAP) if active else 0.0
        rejected=float(row["HX_rejected_MW"])
        cap,eps,q_ntu,ntu=hx_limit(rejected,hot,flow,ua)
        hp_cap=min(HP_THERMAL_CAP,HP_ELECTRIC_CAP*cop,cap*cop/(cop-1))
        hp=min(request,hp_cap)
        el=hp/cop
        recovered=hp-el
        hot_out=hot-1000.0*recovered/ch
        cold_out=COLD_IN_C+1000.0*recovered/cc
        pump=pump_power_mw(flow) if hp>0 else 0.0
        backup=min(backup_cap,max(0.0,(27.60-(t+(hp-q)/c91.CAP))*c91.CAP)) if active else 0.0
        t2=t+(hp+backup-q)/c91.CAP
        if recovered>cap+1e-10 or hot_out<MIN_SOURCE_OUT_C-1e-9 or cold_out>hot+1e-9 or hot_out<COLD_IN_C-1e-9:
            raise RuntimeError("HX_PHYSICS_VIOLATION")
        if abs(c91.CAP*(t2-t)-(hp+backup-q))>1e-10 or not 0<t2<45:
            raise RuntimeError("POOL_BALANCE_VIOLATION")
        totals["loss_MWh"]+=q
        totals["hp_heat_MWh"]+=hp
        totals["hp_electric_MWh"]+=el
        totals["hx_extracted_MWh"]+=recovered
        totals["pump_electric_MWh"]+=pump
        totals["backup_MWh"]+=backup
        totals["storage_MWh"]+=c91.CAP*(t2-t)
        totals["evap_kg"]+=evap
        low+=int(t2<27.5)
        minimum=min(minimum,t2)
        writer.writerow((scenario,stamp.isoformat(),hot,flow,ua,cop,backup_cap,
            f"{t:.12f}",f"{t2:.12f}",f"{q:.12f}",f"{cap:.12f}",f"{q_ntu:.12f}",
            f"{recovered:.12f}",f"{hot_out:.12f}",f"{cold_out:.12f}",f"{hp:.12f}",
            f"{el:.12f}",f"{pump:.12f}",f"{backup:.12f}",f"{rejected:.12f}",
            f"{eps:.12f}",f"{ntu:.12f}"))
        t=t2
    if abs(totals["storage_MWh"]-c91.CAP*(t-28.0))>1e-8:raise RuntimeError("ANNUAL_BALANCE")
    return dict(scenario=scenario,hot_in_C=hot,hot_flow_kg_s=flow,UA_kW_K=ua,
        COP_assumed=cop,backup_cap_MW=backup_cap,min_pool_C=minimum,
        final_pool_C=t,hours_below_27p5=low,**totals,
        total_electric_MWh=totals["hp_electric_MWh"]+totals["pump_electric_MWh"])

def run():
    guard()
    selftest()
    if sha(UP)!=UP_SHA:raise RuntimeError("C93_SOURCE_DRIFT")
    spec=importlib.util.spec_from_file_location("c93_for_c96",UP)
    c93=importlib.util.module_from_spec(spec);spec.loader.exec_module(c93)
    c91,c92,rows,times=c93.load()
    if len(rows)!=8760 or len(times)!=8760:raise RuntimeError("EXPECTED_8760")
    out=D/"C96_HOURLY.csv.gz";temp=D/"C96_HOURLY.partial.csv.gz"
    summary=D/"C96_SUMMARY.csv";meta=D/"C96_METADATA.json"
    if any(p.exists() for p in (out,temp,summary,meta)):raise RuntimeError("OUTPUT_EXISTS")
    results=[]
    with gzip.open(temp,"xt",encoding="utf-8",newline="",compresslevel=4) as f:
        w=csv.writer(f);w.writerow(COLS)
        for params in scenario_grid():
            results.append(simulate(c93,c91,c92,rows,times,params,w))
    guard()
    os.replace(temp,out)
    with summary.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    m={"schema":"C96_UA_NTU_PUMP_POOL_V1","task_id":TASK,"synthetic":True,
       "field_validated":False,"vendor_COP":False,"primary_source_signoffs_added":0,
       "scenarios":len(results),"hourly_rows":len(results)*8760,
       "upstream_C93_sha256":UP_SHA,"upstream_C90_sha256":c91.C90_SHA,
       "hourly_sha256":sha(out),"summary_sha256":sha(summary),
       "assumptions":{"source_inlet_C":HOT_T,"source_flow_kg_s":HOT_FLOW,
        "UA_kW_per_K":UA_KW_K,"COP_assumed":COP,"cold_inlet_C":COLD_IN_C,
        "cold_flow_kg_s":COLD_FLOW,"source_return_min_C":MIN_SOURCE_OUT_C,
        "source_pressure_drop_kPa":HOT_DP_KPA,"cold_pressure_drop_kPa":COLD_DP_KPA,
        "pump_efficiency":PUMP_ETA,"pool_RH":RH,"cover_multiplier":COVER,
        "HP_thermal_cap_MW":HP_THERMAL_CAP,"HP_electric_cap_MW":HP_ELECTRIC_CAP},
       "limitations":["Synthetic source heat availability and fixed inlet temperatures.",
        "UA, flows, pressure drop, pump efficiency and COP are scenario assumptions.",
        "No measured exchanger, no vendor COP map, no fouling or pressure-drop curves.",
        "Pumps counted only when HP dispatches; constant assumed differential pressure.",
        "Pool water only: ventilation/dehumidification excluded.",
        "Do not interpret numerical balance as physical validation."]}
    with meta.open("x",encoding="utf-8") as f:json.dump(m,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"scenarios":len(results),"rows":len(results)*8760,
      "hourly_sha256":m["hourly_sha256"],"summary_sha256":m["summary_sha256"],
      "anchors":[{"scenario":s["scenario"],"min_C":round(s["min_pool_C"],3),
         "low_hours":s["hours_below_27p5"],"hp_MWh":round(s["hp_heat_MWh"],2),
         "backup_MWh":round(s["backup_MWh"],2),"pump_MWh":round(s["pump_electric_MWh"],2)}
         for s in results if (s["hot_in_C"],s["hot_flow_kg_s"],s["UA_kW_K"],s["COP_assumed"]) in
             ((35.0,0.5,2.0,2.2),(50.0,2.0,10.0,4.0))]},indent=2))
if __name__=="__main__":
    import sys
    if "--selftest" in sys.argv:selftest()
    else:run()
