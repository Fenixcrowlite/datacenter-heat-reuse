"""C98: bounded synthetic UA feasibility boundary using immutable C96 engine.
No field validation, no edits to production/shared simulation.
"""
from __future__ import annotations
import csv, hashlib, importlib.util, json, math, time
from pathlib import Path

D=Path(__file__).resolve().parent
REC=D.parent
SCC=REC.parent
UP=REC/"AUTONOMOUS_RUN_20261030_1850_DCHR_C96_UA_NTU_PUMP_ENVELOPE"/"c96_ua_ntu_pool.py"
UP_SHA="c084e706fc79c635856df6ba6223c1fed1cb9b8c7c72c5aba0e67ae38b8700d9"
TASK="scc-2aab24704c2bd0"
FLAGS=("STOP","STOP.txt","STOP.flag","PAUSE","PAUSE.txt","PAUSE.flag",".STOP",".PAUSE")
CASES=[
    (35.,0.5,15.,2.2),
    (35.,0.5,25.,2.2),
    (35.,0.5,32.,2.2),
    (35.,2.0,32.,2.2),
    (38.,0.5,32.,2.2),
    (50.,0.5,32.,2.2),
    (35.,0.5,15.,4.0),
    (38.,0.5,25.,4.0),
]
UA_GRID=(0.0001,0.02,0.1,0.5,1.0,2.0,10.0,100.0)
ITERATIONS=9

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()

def guard():
    for root in (D,REC,SCC,Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")):
        for f in FLAGS:
            if (root/f).exists():raise RuntimeError("STOP_ACTIVE "+str(root/f))

class Sink:
    def writerow(self,row):pass

def load_engine():
    if sha(UP)!=UP_SHA:raise RuntimeError("C96_SOURCE_DRIFT")
    spec=importlib.util.spec_from_file_location("c96_for_c98",UP)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    if sha(m.UP)!=m.UP_SHA:raise RuntimeError("C93_SOURCE_DRIFT")
    spec93=importlib.util.spec_from_file_location("c93_for_c98",m.UP)
    c93=importlib.util.module_from_spec(spec93);spec93.loader.exec_module(c93)
    c91,c92,rows,times=c93.load()
    if len(rows)!=8760 or len(times)!=8760:raise RuntimeError("EXPECTED_8760")
    return m,c93,c91,c92,rows,times

def run():
    guard()
    output=D/"C98_SWEEP.csv"
    summary=D/"C98_THRESHOLDS.json"
    if output.exists() or summary.exists():raise RuntimeError("OUTPUT_EXISTS")
    t0=time.monotonic()
    m,c93,c91,c92,rows,times=load_engine()
    assert m.epsilon_counterflow(0,0.5)==0
    assert m.hx_limit(0.5,35,0.5,0.1)[0]<m.hx_limit(0.5,35,0.5,2)[0]
    cache={}
    measurements=[]
    def evaluate(case,ua):
        key=tuple(case)+(round(float(ua),10),)
        if key in cache:return cache[key]
        hot,flow,cold,cop=case
        m.COLD_IN_C=cold
        if cold>=hot:raise ValueError("COLD_GE_HOT")
        res=m.simulate(c93,c91,c92,rows,times,(hot,flow,float(ua),cop,0.0),Sink())
        result={"hot_in_C":hot,"hot_flow_kg_s":flow,"cold_in_C":cold,"COP_assumed":cop,
                "UA_kW_K":float(ua),"min_pool_C":res["min_pool_C"],
                "hours_below_27p5":res["hours_below_27p5"],
                "hp_heat_MWh":res["hp_heat_MWh"],"hx_extracted_MWh":res["hx_extracted_MWh"],
                "hp_electric_MWh":res["hp_electric_MWh"],"pump_electric_MWh":res["pump_electric_MWh"],
                "energy_residual_MWh":res["hp_heat_MWh"]+res["backup_MWh"]-res["loss_MWh"]-res["storage_MWh"],
                "feasible":res["hours_below_27p5"]==0 and res["min_pool_C"]>=27.5}
        if abs(result["energy_residual_MWh"])>1e-7:raise RuntimeError("ENERGY_BALANCE")
        measurements.append(result)
        cache[key]=result
        return result
    boundaries=[]
    for case in CASES:
        guard()
        scans=[evaluate(case,ua) for ua in UA_GRID]
        # Strictly require monotone feasibility across coarse UA sweep.
        feasibility=[x["feasible"] for x in scans]
        if any(a and not b for a,b in zip(feasibility,feasibility[1:])):
            raise RuntimeError("NONMONOTONIC_FEASIBILITY "+str(case))
        passing=[x for x in scans if x["feasible"]]
        failing=[x for x in scans if not x["feasible"]]
        record={"case":{"hot_in_C":case[0],"hot_flow_kg_s":case[1],
                        "cold_in_C":case[2],"COP_assumed":case[3]},
                "UA_upper_tested_kW_K":max(UA_GRID),
                "coarse_monotone":True,"max_UA_min_pool_C":scans[-1]["min_pool_C"],
                "max_UA_hours_below":scans[-1]["hours_below_27p5"]}
        if not passing:
            record.update(status="NO_FEASIBLE_UA_IN_GRID",bracket_fail_kW_K=None,bracket_pass_kW_K=None)
        else:
            high=min(x["UA_kW_K"] for x in passing)
            low=max((x["UA_kW_K"] for x in failing if x["UA_kW_K"]<high),default=None)
            if low is None:
                record.update(status="PASS_AT_GRID_FLOOR",bracket_fail_kW_K=None,bracket_pass_kW_K=high)
            else:
                for _ in range(ITERATIONS):
                    mid=math.sqrt(low*high)
                    if evaluate(case,mid)["feasible"]:high=mid
                    else:low=mid
                if evaluate(case,low)["feasible"] or not evaluate(case,high)["feasible"]:
                    raise RuntimeError("INVALID_BOUNDARY")
                record.update(status="BRACKETED",bracket_fail_kW_K=low,bracket_pass_kW_K=high,
                              bracket_ratio=high/low)
        boundaries.append(record)
    guard()
    with output.open("x",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(measurements[0]));w.writeheader();w.writerows(measurements)
    result={"schema":"C98_SYNTHETIC_UA_FEASIBILITY_V1","task_id":TASK,
            "upstream_C96_sha256":UP_SHA,"synthetic":True,"field_validated":False,
            "source_signoffs_added":0,"vendor_COP":False,
            "criterion":"Every hour pool temperature >= 27.5 C, zero backup, 8760 synthetic hours",
            "model_notes":["C96 constant assumed COP; changing cold-loop inlet does not change COP.",
                           "UA is a synthetic effective conductance, no fouling or manufacturer curve.",
                           "No pool ventilation/dehumidification, no source flow/temperature measurements.",
                           "Feasibility may not be monotone between untested points; coarse scan checked only.",
                           "A no-feasible-UA result is bounded by tested grid and other assumed caps."],
            "cases":len(CASES),"unique_simulations":len(measurements),
            "hour_steps":len(measurements)*8760,"UA_grid":UA_GRID,
            "bisection_iterations":ITERATIONS,"elapsed_s":round(time.monotonic()-t0,3),
            "sweep_sha256":sha(output),"boundaries":boundaries}
    with summary.open("x",encoding="utf-8") as f:json.dump(result,f,indent=2,sort_keys=True);f.write("\n")
    print(json.dumps({"cases":len(CASES),"simulations":len(measurements),
       "hour_steps":len(measurements)*8760,"elapsed_s":result["elapsed_s"],
       "status_counts":{k:sum(x["status"]==k for x in boundaries) for k in ("BRACKETED","PASS_AT_GRID_FLOOR","NO_FEASIBLE_UA_IN_GRID")},
       "sweep_sha256":result["sweep_sha256"],"boundaries":boundaries},indent=2))
if __name__=="__main__":run()
