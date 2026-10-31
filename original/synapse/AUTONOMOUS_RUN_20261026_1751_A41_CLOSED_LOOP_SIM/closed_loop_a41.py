"""A41 synthetic, isolated CLOSED-LOOP reference. Not a hardware controller.
A40 mode uses live T and E feedback; A38 TES recurrence is recalculated every step.
Branch switching: two 900s samples of cold-standby delay in backup_only case.
Physical equipment ratings, shed behavior, and COP are unverified hypotheses.
"""
from __future__ import annotations
import csv, hashlib, importlib.util, json, math, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
A38=ROOT/"AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION"
A40=ROOT/"AUTONOMOUS_RUN_20261026_1650_A40_STATEFLOW_SUPERVISOR"
sys.path.insert(0,str(A38))
import integrated_a38 as a38
spec=importlib.util.spec_from_file_location("a40_oracle",A40/"verify_a40.py")
a40=importlib.util.module_from_spec(spec)
spec.loader.exec_module(a40)
DT=900.0
E_MAX=900*3.6e6
E_INITIAL=450*3.6e6
FAULT_INDEX=96
RECOVERY_INDEX=384
DELAY_STEPS=2
SCENARIOS=("both","main_only","backup_only","neither")
INPUT_COLUMNS=("cas_h","qdc","hx","leak","qcharge","qdis","qpool","qdh","pold","qsourceold","qrejectbase")

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def capacity(scenario,k):
    if k<FAULT_INDEX or k>=RECOVERY_INDEX or scenario=="both":
        return 330000.0
    if scenario=="main_only": return 180000.0
    if scenario=="neither": return 0.0
    if scenario=="backup_only": return 0.0 if k<FAULT_INDEX+DELAY_STEPS else 150000.0
    raise ValueError(scenario)

def inputs():
    raw,dispatch,tes,source=a38.checked_sources()
    rows=[]
    for r,d in zip(raw,dispatch):
        rows.append(dict(cas_h=float(r["cas_h"]),qdc=float(r["Q_DC_eff_W"]),
          hx=float(d["Q_HX_W"]),leak=float(r["Q_leak_W"]),
          qcharge=float(d["Q_HP_charge_W"]),qdis=float(d["Q_TES_discharge_W"]),
          qpool=float(d["Q_HP_pool_W"]),qdh=float(d["Q_HP_DH_W"]),
          pold=float(d["P_HP_proxy_W"]),qsourceold=float(d["Q_HP_source_W"]),
          qrejectbase=float(d["Q_reject_required_W"])))
    assert len(rows)==672
    return rows,source

def tes_dispatch(row,E):
    loss=.002*E/86400
    charge_room=max(0,(E_MAX-E+DT*(row["qdis"]/.91+loss))/(DT*.93))
    charge=min(row["qcharge"],charge_room)
    Enext=E+DT*(.93*charge-row["qdis"]/.91-loss)
    if not -1e-4<=Enext<=E_MAX+1e-4:
        raise AssertionError(("TES_OUT_OF_RANGE",Enext))
    Enext=max(0,min(E_MAX,Enext))
    condenser_old=row["qpool"]+row["qdh"]+row["qcharge"]
    condenser_new=condenser_old-(row["qcharge"]-charge)
    power_new=row["pold"]*condenser_new/condenser_old if condenser_old>1e-8 else 0.
    source_new=condenser_new-power_new
    required=row["qrejectbase"]+row["qsourceold"]-source_new
    if required < -1e-7: raise AssertionError("NEGATIVE_REJECT")
    required=max(0,required)
    tes_residual=Enext-E-DT*(.93*charge-row["qdis"]/.91-loss)
    return required,Enext,source_new,charge,tes_residual

def replay(rows,scenario):
    E,T,prev_shed,mode=E_INITIAL,30.,0.,0
    out=[]
    for k,row in enumerate(rows):
        cap=capacity(scenario,k)
        required,Enext,source,charge,tes_residual=tes_dispatch(row,E)
        mode=a40.step(mode,required,cap,T,E/E_MAX)
        ceiling=.4 if mode in (1,2) else 0.
        target=min(max(0,required-cap),ceiling*row["qdc"],required)
        shed=min(target,min(prev_shed,row["qdc"])+15000.) if ceiling else 0.
        rejected=min(required-shed,cap)
        unhandled=max(0,required-shed-rejected)
        passive=2000*max(0,T-30)
        Tnext=max(30.,T+DT*(unhandled-passive)/8e6)
        dc_res=row["qdc"]-shed-row["hx"]-source-row["leak"]-rejected-unhandled
        if abs(dc_res)>1e-5 or abs(tes_residual)>1e-4:
            raise AssertionError(("ENERGY_CLOSURE",k,dc_res,tes_residual))
        out.append(dict(k=k,cas_h=row["cas_h"],capacity_W=cap,mode=mode,
            shed_ceiling_fraction=ceiling,alarm=(1 if mode==3 else mode),
            required_W=required,qdc_W=row["qdc"],hx_W=row["hx"],leak_W=row["leak"],
            hp_source_W=source,charge_W=charge,
            T_start_C=T,T_next_C=Tnext,E_start_J=E,E_next_J=Enext,
            TES_SOC_start=E/E_MAX,TES_SOC_next=Enext/E_MAX,
            shed_W=shed,reject_W=rejected,unhandled_W=unhandled,passive_W=passive,
            dc_residual_W=dc_res,tes_residual_J=tes_residual))
        T,E,prev_shed=Tnext,Enext,shed
    return out

def write_csv(path,rows):
    with Path(path).open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader();w.writerows(rows)

def main():
    rows,source=inputs()
    write_csv(HERE/"INPUTS_A41.csv",rows)
    report=dict(status="SYNTHETIC_CLOSED_LOOP_PYTHON_REFERENCE",
      physical_release=False,matlab_simulink_executed=False,
      samples=672,dt_seconds=900,fault_index=FAULT_INDEX,recovery_index=RECOVERY_INDEX,
      backup_switch_delay_steps=DELAY_STEPS,source_a36_sha256=sha(source),
      a38_sha256=sha(A38/"integrated_a38.py"),a40_sha256=sha(A40/"verify_a40.py"),
      cases={})
    for scenario in SCENARIOS:
        trace=replay(rows,scenario)
        p=HERE/("TRACE_A41_"+scenario+".csv")
        write_csv(p,trace)
        report["cases"][scenario]=dict(max_T_C=max(r["T_next_C"] for r in trace),
          critical_steps=sum(r["mode"]==2 for r in trace),
          unhandled_kWh=sum(r["unhandled_W"] for r in trace)/4000,
          shed_kWh=sum(r["shed_W"] for r in trace)/4000,
          max_energy_residual_W=max(abs(r["dc_residual_W"]) for r in trace),
          trace_sha256=sha(p))
    (HERE/"PYTHON_RESULT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()
