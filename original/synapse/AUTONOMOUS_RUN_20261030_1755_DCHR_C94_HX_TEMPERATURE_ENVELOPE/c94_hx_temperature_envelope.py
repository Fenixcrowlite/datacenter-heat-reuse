"""C94 synthetic source-temperature/flow feasibility envelope, task-local and read-only upstream.
NOT a measured heat-exchanger design, manufacturer COP curve, or physical validation.
"""
from __future__ import annotations
import csv, datetime as dt, hashlib, importlib.util, json, math
from collections import defaultdict
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
C93=REC/"AUTONOMOUS_RUN_20261030_1649_DCHR_C93_POOL_UNCERTAINTY_SWEEP"/"c93_uncertainty_sweep.py"
C93_SHA="0686860f25ac42735bdecf9b896278e093177dc8062426f7cd232d232e48d923"
SOURCE_T=(18.0,25.0,35.0)  # hypothetical deg C
FLOW=(0.5,2.0,8.0)         # hypothetical kg/s
BACKUP=(0.0,0.05)         # MW
CP_KJ_KGK=4.18
SOURCE_MIN_C=12.0
EVAP_APPROACH_K=8.0
SOURCE_PINCH_K=2.0
SINK_C=38.0
ETA_CARNOT=0.35
COP_MIN,COP_MAX=2.0,6.0
ELECTRIC_CAP_MW=0.075
HP_HEAT_CAP_MW=0.30
RH,COVER=0.55,0.15
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def guard():
    for root in (D,REC,REC.parent,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for name in FLAGS:
            if (root/name).exists():raise RuntimeError("STOP_ACTIVE "+str(root/name))
def load():
    if sha(C93)!=C93_SHA:raise RuntimeError("C93_SOURCE_DRIFT")
    spec=importlib.util.spec_from_file_location("c93_c94",C93)
    c93=importlib.util.module_from_spec(spec);spec.loader.exec_module(c93)
    c91,c92,rows,times=c93.load()
    return c93,c91,c92,rows,times
def envelope(q_rejected,source_c,flow):
    if not all(math.isfinite(x) for x in (q_rejected,source_c,flow)):
        raise ValueError("NONFINITE_INPUT")
    if q_rejected<0 or flow<=0 or not (SOURCE_MIN_C<=source_c<45):
        raise ValueError("INVALID_SOURCE")
    evap_c=source_c-EVAP_APPROACH_K
    lift=SINK_C-evap_c
    if lift<=0:raise ValueError("INVALID_LIFT")
    cop=max(COP_MIN,min(COP_MAX,ETA_CARNOT*(SINK_C+273.15)/lift))
    max_drop=max(0.0,min(EVAP_APPROACH_K-SOURCE_PINCH_K,source_c-SOURCE_MIN_C))
    q_flow=flow*CP_KJ_KGK*max_drop/1000.0
    q_src_cap=min(q_rejected,q_flow)
    q_hp_cap=min(HP_HEAT_CAP_MW,ELECTRIC_CAP_MW*cop,q_src_cap*cop/(cop-1.0))
    return cop,q_src_cap,q_hp_cap,max_drop
def selftest():
    checks=0
    def ok(b):
        nonlocal checks
        assert b
        checks+=1
    a=envelope(1,18,0.5);b=envelope(1,18,8)
    ok(a[1]<b[1]);ok(a[2]<b[2])
    ok(envelope(1,18,2)[0]<envelope(1,25,2)[0])
    ok(envelope(0,25,2)[2]==0)
    ok(envelope(1,12,2)[2]==0)
    ok(envelope(1,35,8)[2]<=HP_HEAT_CAP_MW)
    ok(envelope(1,35,8)[2]/envelope(1,35,8)[0]<=ELECTRIC_CAP_MW)
    ok(envelope(1,18,2)[3]<=EVAP_APPROACH_K-SOURCE_PINCH_K)
    for x in ((-1,25,2),(1,25,0),(1,float("nan"),2),(1,50,2)):
        try:envelope(*x)
        except ValueError:checks+=1
        else:raise AssertionError("BAD_INPUT_ACCEPTED")
    print(f"C94 SELFTEST {checks}/{checks} PASS")
def simulate(c93,c91,c92,rows,times,source_c,flow,backup_cap,writer):
    t,active=28.0,False
    totals=defaultdict(float);minimum=99.0;low=0;max_balance=0.0
    for stamp,row in zip(times,rows):
        q,evap=c93.loss_components(c91,c92,t,stamp.hour,RH,COVER)
        if t<=c91.ON_C:active=True
        elif t>=c91.OFF_C:active=False
        request=max(0.0,q+(c91.OFF_C-t)*c91.CAP) if active else 0.0
        rejected=float(row["HX_rejected_MW"])
        cop,q_src_cap,hp_cap,max_drop=envelope(rejected,source_c,flow)
        hp=min(request,hp_cap)
        electric=hp/cop
        extracted=hp-electric
        source_out=source_c-extracted*1000.0/(flow*CP_KJ_KGK)
        if extracted>q_src_cap+1e-11 or source_out<max(SOURCE_MIN_C,source_c-max_drop)-1e-9:
            raise RuntimeError("HX_PINCH_OR_FLOW_VIOLATION")
        backup=min(backup_cap,max(0.0,(27.60-(t+(hp-q)/c91.CAP))*c91.CAP)) if active else 0.0
        t2=t+(hp+backup-q)/c91.CAP
        if not 0<=t2<=45:raise RuntimeError("POOL_TEMPERATURE_RANGE")
        balance=abs(c91.CAP*(t2-t)-(hp+backup-q))
        if balance>1e-10:raise RuntimeError("POOL_ENERGY_BALANCE")
        max_balance=max(max_balance,balance)
        vals=dict(loss_MWh=q,hp_heat_MWh=hp,hp_electric_MWh=electric,
                  hx_extracted_MWh=extracted,backup_MWh=backup,storage_MWh=c91.CAP*(t2-t))
        for k,v in vals.items():totals[k]+=v
        writer.writerow(dict(time=stamp.isoformat(),source_C=source_c,flow_kg_s=flow,
                             backup_cap_MW=backup_cap,pool_start_C=f"{t:.12f}",
                             pool_end_C=f"{t2:.12f}",loss_MW=f"{q:.12f}",
                             hp_heat_MW=f"{hp:.12f}",hp_electric_MW=f"{electric:.12f}",
                             hx_extracted_MW=f"{extracted:.12f}",backup_MW=f"{backup:.12f}",
                             source_rejected_MW=f"{rejected:.12f}",source_out_C=f"{source_out:.12f}",
                             source_cap_MW=f"{q_src_cap:.12f}",COP=f"{cop:.12f}"))
        minimum=min(minimum,t2);low+=int(t2<27.5);t=t2
    if abs(totals["storage_MWh"]-c91.CAP*(t-28.0))>1e-8:raise RuntimeError("YEAR_BALANCE")
    return dict(source_C=source_c,flow_kg_s=flow,backup_cap_MW=backup_cap,
                min_pool_C=minimum,final_pool_C=t,hours_below_27p5=low,
                max_energy_residual_MWh=max_balance,**totals)
def run():
    guard()
    c93,c91,c92,rows,times=load()
    selftest()
    if len(rows)!=8760 or len(times)!=8760:raise RuntimeError("NOT_8760")
    hourly=D/"C94_HOURLY.csv";summary_path=D/"C94_SUMMARY.csv"
    if hourly.exists() or summary_path.exists() or (D/"C94_METADATA.json").exists():
        raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    keys=("time","source_C","flow_kg_s","backup_cap_MW","pool_start_C","pool_end_C",
          "loss_MW","hp_heat_MW","hp_electric_MW","hx_extracted_MW","backup_MW",
          "source_rejected_MW","source_out_C","source_cap_MW","COP")
    summary=[]
    with hourly.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader()
        for source in SOURCE_T:
            for flow in FLOW:
                for backup in BACKUP:
                    summary.append(simulate(c93,c91,c92,rows,times,source,flow,backup,writer))
    with summary_path.open("x",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    meta={"schema":"C94_SYNTHETIC_HX_TEMPERATURE_ENVELOPE_V1",
          "task_id":"scc-2aab24704c2bd0","synthetic":True,"measured":False,
          "primary_source_signoffs_added":0,"scenarios":len(summary),
          "hourly_rows":len(summary)*len(rows),
          "assumptions":{"source_inlet_C":SOURCE_T,"source_flow_kg_s":FLOW,
            "source_min_outlet_C":SOURCE_MIN_C,"source_evaporator_approach_K":EVAP_APPROACH_K,
            "pinch_at_source_outlet_K":SOURCE_PINCH_K,"sink_condenser_C":SINK_C,
            "carnot_efficiency_assumed":ETA_CARNOT,"COP_clamp":[COP_MIN,COP_MAX],
            "HP_electric_cap_MW":ELECTRIC_CAP_MW,"HP_thermal_cap_MW":HP_HEAT_CAP_MW,
            "relative_humidity":RH,"cover_multiplier":COVER,
            "backup_capacity_MW":BACKUP},
          "upstream_C93_script_sha256":C93_SHA,
          "upstream_C90_data_sha256":c91.C90_SHA,
          "hourly_sha256":sha(hourly),"summary_sha256":sha(summary_path),
          "limitations":["Temperature/flow are scenario assumptions, not DC measurements.",
            "COP uses bounded Carnot-efficiency proxy, not vendor performance map.",
            "Source heat cap is synthetic HX_rejected_MW and assumed flow cooling envelope.",
            "No exchanger UA/LMTD, fouling, pressure drop, or real source return measurements.",
            "Only water loop modeled; air ventilation/dehumidification excluded.",
            "Do not treat this as actual heat recoverability or ASHRAE signoff."]}
    (D/"C94_METADATA.json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"scenarios":len(summary),"hourly_rows":len(summary)*8760,
        "hourly_sha256":meta["hourly_sha256"],
        "summary":[{"source_C":s["source_C"],"flow_kg_s":s["flow_kg_s"],
                    "backup_MW":s["backup_cap_MW"],"low_h":s["hours_below_27p5"],
                    "min_C":round(s["min_pool_C"],3),"hp_MWh":round(s["hp_heat_MWh"],2),
                    "backup_MWh":round(s["backup_MWh"],2)} for s in summary]},indent=2))
if __name__=="__main__":
    import sys
    if "--selftest" in sys.argv:selftest()
    else:run()
