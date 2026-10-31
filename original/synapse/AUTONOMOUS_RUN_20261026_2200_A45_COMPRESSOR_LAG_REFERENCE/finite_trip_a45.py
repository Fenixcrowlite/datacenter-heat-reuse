"""A43 synthetic finite-trip-latency IT heat-reuse reference. No hardware I/O.

Trip delay, residual decay and REJECT recovery ramp are hypotheses, not
certified protective behavior. Reuses immutable A42 dispatch and A41 inputs.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
A42=HERE.parent/"AUTONOMOUS_RUN_20261026_1850_A42_COUPLED_FAILSAFE"
sys.path.insert(0,str(A42))
import coupled_a42 as base
import counterfactual_a42 as counter
from compressor_a45 import step_capacity, dispatch_limited
DT=base.DT
STATES=("ACTIVE","TRIP_PENDING","TRIPPED","RAMPING")
DEFAULT_TRIP_STEPS=2
DEFAULT_RESIDUAL_FRACTION=.12
DEFAULT_TAU_S=3600.0
DEFAULT_REJECT_RAMP_W=60000.0

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def verified_inputs():
    manifest=json.loads((A42/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
    if manifest["coupled_a42.py"]!=digest(A42/"coupled_a42.py"):
        raise RuntimeError("A42_SOURCE_CHANGED")
    return base.load_inputs()

def simulate(rows,scenario,*,trip_delay_steps=DEFAULT_TRIP_STEPS,
             residual_fraction=DEFAULT_RESIDUAL_FRACTION,
             residual_tau_s=DEFAULT_TAU_S,
             reject_ramp_W=DEFAULT_REJECT_RAMP_W,
             sensor_lag_steps=0,heat_capacity_J_per_C=base.C_BASE,
             compressor_tau_s=1800.0):
    if not isinstance(trip_delay_steps,int) or trip_delay_steps<0 or trip_delay_steps>12:
        raise ValueError("INVALID_TRIP_DELAY")
    if not (math.isfinite(residual_fraction) and 0<=residual_fraction<=.5):
        raise ValueError("INVALID_RESIDUAL_FRACTION")
    if not (math.isfinite(residual_tau_s) and residual_tau_s>0):
        raise ValueError("INVALID_RESIDUAL_TAU")
    if not (math.isfinite(reject_ramp_W) and reject_ramp_W>0):
        raise ValueError("INVALID_REJECT_RAMP")
    if not isinstance(sensor_lag_steps,int) or sensor_lag_steps<0:
        raise ValueError("INVALID_SENSOR_LAG")
    if not math.isfinite(heat_capacity_J_per_C) or heat_capacity_J_per_C<=0:
        raise ValueError("INVALID_HEAT_CAPACITY")
    if not math.isfinite(compressor_tau_s) or compressor_tau_s<0:
        raise ValueError("INVALID_COMPRESSOR_TAU")
    hp_available_W=0.0
    E,T=base.E_INIT,30.0
    state="ACTIVE"
    previous_active=0.0
    previous_shed=0.0
    pending=0
    good=0
    residual=0.0
    last_trip=False
    effective_cap=330000.0
    temps=[]
    trace=[]
    for k,row in enumerate(rows):
        temps.append(T)
        sensed=temps[max(0,k-sensor_lag_steps)]
        nominal_cap=base.capacity(scenario,k)
        effective_cap=min(nominal_cap,effective_cap+reject_ramp_W)
        fault=(nominal_cap<=0 or sensed>=42.0)
        if state in ("ACTIVE","RAMPING") and fault:
            state="TRIP_PENDING"
            pending=0
        if state=="TRIP_PENDING" and not fault and sensed<36:
            state="ACTIVE"
            pending=0
        if state=="TRIP_PENDING":
            if pending<trip_delay_steps:
                active=row["qdc"]
                pending+=1
            else:
                state="TRIPPED"
                active=0.0
                good=0
        elif state=="TRIPPED":
            active=0.0
            good=good+1 if nominal_cap>0 and sensed<36 else 0
            if good>=base.RESTART_GOOD_SAMPLES:
                state="RAMPING"
                active=min(row["qdc"],base.RAMP_W)
        elif state=="RAMPING":
            active=min(row["qdc"],previous_active+base.RAMP_W)
            if active>=row["qdc"]-1e-8:
                state="ACTIVE"
        else:
            nominal=base.dispatch(row,row["qdc"],E,T,effective_cap)
            deficit=max(0.0,nominal["required_reject_W"]-effective_cap)
            target=min(.4*row["qdc"],deficit)
            shed=min(target,previous_shed+base.RAMP_W)
            active=row["qdc"]-shed
        just_tripped=state=="TRIPPED" and not last_trip
        if just_tripped:
            residual=residual_fraction*previous_active
        elif residual>0:
            residual*=math.exp(-DT/residual_tau_s)
        # Residual is physical heat, not useful IT compute. Keep total <= nominal
        # because A42 dispatch validates its physical heat-source domain.
        active=min(active,max(0.0,row["qdc"]-residual))
        qheat=active+residual
        hp_target_W=base.dispatch(row,qheat,E,T,effective_cap)['hp_source_W']
        hp_available_W=step_capacity(hp_available_W,hp_target_W,DT,compressor_tau_s)
        flow=dispatch_limited(row,qheat,E,T,effective_cap,hp_available_W)
        passive=2000.0*max(0.0,T-30.0)
        Tnext=max(30.0,T+DT*(flow["unhandled_W"]-passive)/heat_capacity_J_per_C)
        rec=dict(k=k,t_h=k/4,scenario=scenario,state=state,
            nominal_cap_W=nominal_cap,effective_cap_W=effective_cap,
            active_it_W=active,residual_it_W=residual,heat_it_W=qheat,
            pending_steps=pending,trip_trigger=int(fault),
            T_start_C=T,sensed_T_C=sensed,T_next_C=Tnext,
            E_start_J=E,passive_W=passive,hp_available_W=hp_available_W,**flow)
        assert abs(rec["it_balance_W"])<1e-6
        assert abs(rec["hp_balance_W"])<1e-6
        assert abs(rec["user_balance_W"])<1e-6
        assert abs(rec["tes_balance_J"])<1e-3
        assert 0<=rec["reject_W"]<=effective_cap+1e-7
        assert rec["active_it_W"]>=0 and rec["residual_it_W"]>=0
        assert rec["qit_W"]==rec["heat_it_W"]
        trace.append(rec)
        E,T=flow["E_next_J"],Tnext
        previous_active=active
        previous_shed=row["qdc"]-active
        last_trip=(state=="TRIPPED")
    return trace

def summarize(trace):
    return dict(samples=len(trace),
        max_temperature_C=max(x["T_next_C"] for x in trace),
        exceed_42_steps=sum(x["T_next_C"]>=42 for x in trace),
        pending_steps=sum(x["state"]=="TRIP_PENDING" for x in trace),
        tripped_steps=sum(x["state"]=="TRIPPED" for x in trace),
        residual_heat_kWh=sum(x["residual_it_W"] for x in trace)/4000,
        unhandled_kWh=sum(x["unhandled_W"] for x in trace)/4000,
        unmet_heat_kWh=sum(x["pool_dh_unmet_W"] for x in trace)/4000,
        max_balance_W=max(abs(x["it_balance_W"]) for x in trace))

def write_csv(path,rows):
    with Path(path).open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

def main():
    rows=verified_inputs()
    cases={}
    for scenario in base.SCENARIOS:
        t=simulate(rows,scenario)
        name="TRACE_A45_"+scenario+".csv"
        write_csv(HERE/name,t)
        cases[scenario]=dict(**summarize(t),sha256=digest(HERE/name))
    synthetic=counter.counterfactual(rows)
    for scenario in ("both","backup_only","neither"):
        t=simulate(synthetic,scenario)
        name="TRACE_A45_CF_"+scenario+".csv"
        write_csv(HERE/name,t)
        cases["CF_"+scenario]=dict(**summarize(t),sha256=digest(HERE/name))
    sweep={}
    for delay in (0,1,2,4):
        for fraction in (0,.12,.25):
            t=simulate(rows,"neither",trip_delay_steps=delay,residual_fraction=fraction)
            sweep[f"delay{delay}_residual{fraction}"]=summarize(t)
    report=dict(status="A45_SYNTHETIC_COMPRESSOR_LAG_REFERENCE",physical_release=False,
        hardware_control=False,matlab_stateflow_executed=False,
        a42_source_sha256=digest(A42/"coupled_a42.py"),
        input_sha256=digest(base.SOURCE),cases=cases,sensitivity=sweep,
        assumptions=["trip latency is hypothetical, 2 x 900 seconds",
          "post-trip heat starts at 12 percent of last active IT power and decays with tau=3600s",
          "REJECT recovery limited to 60kW per 900s; fault shutdown instantaneous",
          "A45 HP evaporator source capacity has a synthetic first-order lag; no compressor coastdown storage",
          "no hardware commands, no physical safety certification"])
    (HERE/"RESULTS_A45.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print(json.dumps({"status":report["status"],"cases":cases,
        "sweep":sweep},indent=2,ensure_ascii=False))

if __name__=="__main__":
    main()
