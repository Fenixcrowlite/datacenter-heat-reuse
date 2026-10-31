"""Isolated D_ASSUMED thermal-hydraulic DH pilot for saved v04 results.

NOT an edited Simulink/Stateflow controller, field validation, or a PLC model.
Implicit two-volume heat balances and a quadratic design-pressure-loss proxy.
"""
from __future__ import annotations
import argparse, csv, json, math
from dataclasses import dataclass, asdict
from pathlib import Path
from live_bridge import JOBS, RUNTIME, safe_result

@dataclass(frozen=True)
class DesignAssumptions:
    cp_J_kgK: float = 4182.0
    rho_kg_m3: float = 997.0
    mass_supply_kg: float = 10000.0
    mass_return_kg: float = 10000.0
    ua_supply_W_K: float = 120.0
    ua_return_W_K: float = 80.0
    ambient_C: float = 15.0
    pump_head_nominal_Pa: float = 150000.0
    massflow_nominal_kg_s: float = 5.0
    pump_efficiency: float = .70

def step(ts, tr, heat_in_W, request_W, mdot, target_return_C, dt_s=900,
         a=DesignAssumptions()):
    values = (ts,tr,heat_in_W,request_W,mdot,target_return_C,dt_s,*asdict(a).values())
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in values):
        raise ValueError("All values must be finite")
    if heat_in_W < 0 or request_W < 0 or mdot < 0 or dt_s <= 0:
        raise ValueError("Power, requested load and flow must be nonnegative")
    if a.cp_J_kgK <= 0 or a.mass_supply_kg <= 0 or a.mass_return_kg <= 0 or a.rho_kg_m3 <= 0:
        raise ValueError("Invalid mass or specific heat")
    if a.pump_efficiency <= 0 or a.pump_efficiency > 1 or a.massflow_nominal_kg_s <= 0:
        raise ValueError("Invalid pump parameters")
    if a.ua_supply_W_K < 0 or a.ua_return_W_K < 0:
        raise ValueError("Negative thermal leakage")
    f = mdot * a.cp_J_kgK
    cs = a.mass_supply_kg*a.cp_J_kgK
    cr = a.mass_return_kg*a.cp_J_kgK
    ss=cs/dt_s+f+a.ua_supply_W_K
    rr=cr/dt_s+f+a.ua_return_W_K
    det=ss*rr-f*f
    rhs_s=cs/dt_s*ts+heat_in_W+a.ua_supply_W_K*a.ambient_C
    rhs_r0=cr/dt_s*tr+a.ua_return_W_K*a.ambient_C

    def fixed_load(q):
        rhs_r=rhs_r0-q
        return ( (rhs_s*rr+f*rhs_r)/det,
                 (ss*rhs_r+f*rhs_s)/det )

    ts0,tr0=fixed_load(0.0)
    if request_W == 0 or f == 0 or f*(ts0-target_return_C)<=0:
        tn,rn,load = ts0,tr0,0.0
        regime = "no_load"
    else:
        tsc,trc=fixed_load(request_W)
        if f*(tsc-target_return_C)>=request_W:
            tn,rn,load = tsc,trc,request_W
            regime = "load_capped"
        else:
            rn=(rhs_r0+f*target_return_C)/rr
            tn=(rhs_s+f*rn)/ss
            load=f*(tn-target_return_C)
            regime = "temperature_limited"
            if not (-1e-5 <= load <= request_W+1e-5):
                raise ValueError("Internal load regime conflict")

    qs=a.ua_supply_W_K*(tn-a.ambient_C)
    qr=a.ua_return_W_K*(rn-a.ambient_C)
    lhs=(cs*(tn-ts)+cr*(rn-tr))/dt_s
    residual=lhs+qs+qr+load-heat_in_W
    dp=a.pump_head_nominal_Pa*(mdot/a.massflow_nominal_kg_s)**2
    pump=dp*mdot/(a.rho_kg_m3*a.pump_efficiency)
    if not all(math.isfinite(v) for v in (tn,rn,load,residual,pump)):
        raise ValueError("Nonfinite dynamic result")
    if abs(residual)>1e-6 or load<-1e-6 or load>request_W+1e-6:
        raise ValueError("Energy equation or allocation violated")
    return {"T_supply_C":tn,"T_return_C":rn,"Q_load_W":max(0.0,load),
        "Q_pipe_loss_supply_W":qs,"Q_pipe_loss_return_W":qr,
        "P_pump_W":pump,"delta_pressure_Pa":dp,
        "energy_residual_W":residual,"load_regime":regime}

def calculate(jobid, a=DesignAssumptions()):
    raw=safe_result(jobid)
    cfg=json.loads((JOBS/jobid/"config.json").read_text(encoding="utf-8-sig"))
    rows=raw["rows"]
    if len(rows)!=672 or raw["metadata"].get("status")!="VERIFIED_SIMULINK_NEW_RUN":
        raise ValueError("Invalid upstream MATLAB Simulink job")
    if not cfg.get("dh_enabled",True): enabled=False
    else: enabled=True
    off=float(cfg.get("dh_off_from_h",168))
    target=float(cfg.get("dh_return_C",45))
    mdot=float(cfg.get("dh_mass_flow_kg_s",5))
    request=float(cfg.get("dh_request_limit_kw",160))*1000
    if not (0.1<=mdot<=100 and 5<=target<=90 and 0<=request<=500_000 and 0<=off<=168):
        raise ValueError("Invalid recorded hydraulic setpoints")
    flow_start=mdot if enabled and off>0 else 0.0
    f0=flow_start*a.cp_J_kgK
    tr=target
    ts=target+max(0.0,float(rows[0]["Q_DH_W"]))/(f0 or 1e30)
    data=[]
    for i,row in enumerate(rows):
        time_h=float(row["cas_h"])
        if abs(time_h-i*.25)>1e-8:raise ValueError("Invalid source time grid")
        active=enabled and time_h<off
        q_in=float(row["Q_DH_W"])
        if not math.isfinite(q_in) or q_in<-1e-5:raise ValueError("Nonfinite or negative v04 DH power")
        if not active and q_in>1e-5:
            raise ValueError("Upstream v04 dispatch conflicts with DH shutdown")
        step_result=step(ts,tr,max(0.0,q_in),request if active else 0.0,
                         mdot if active else 0.0,target,a=a)
        ts,tr=step_result["T_supply_C"],step_result["T_return_C"]
        data.append({"interval_start_h":time_h,"interval_end_h":time_h+.25,
                     "Q_DH_source_W":q_in,"flow_kg_s":mdot if active else 0.0,
                     **step_result})
    return {"job_id":jobid,"source_model":"v04 completed MATLAB sim()",
            "provenance":"D_SYNTHETIC -> D_ASSUMED_DYNAMIC_DH_PILOT",
            "model":"two finite water masses, implicit coupled balance; no feedback to Stateflow",
            "assumptions":asdict(a),"configured":{
                "dh_return_target_C":target,"dh_mass_flow_kg_s":mdot,
                "dh_off_from_h":off,"dh_enabled":enabled,
                "dh_request_limit_kw":request/1000},
            "dt_s":900,"sample_count":len(data),
            "max_energy_residual_W":max(abs(row["energy_residual_W"]) for row in data),
            "total_Q_DH_source_MWh":sum(row["Q_DH_source_W"] for row in data)*900/3.6e9,
            "total_Q_load_MWh":sum(row["Q_load_W"] for row in data)*900/3.6e9,
            "pump_electric_MWh":sum(row["P_pump_W"] for row in data)*900/3.6e9,
            "rows":data}

def save(result):
    out=RUNTIME/"dh_pilot_v01"/result["job_id"]
    out.mkdir(parents=True,exist_ok=True)
    rows=result["rows"]
    with (out/"trajectory.csv").open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)
    summary={k:v for k,v in result.items() if k!="rows"}
    (out/"summary.json").write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding="utf-8")
    return out

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id",required=True)
    args=parser.parse_args()
    if len(args.job_id)!=32 or any(x not in "0123456789abcdef" for x in args.job_id):
        parser.error("job ID must be lowercase hex")
    result=calculate(args.job_id)
    path=save(result)
    print(json.dumps({"status":"PASS","folder":str(path),"rows":result["sample_count"],
      "max_energy_residual_W":result["max_energy_residual_W"],
      "source_MWh":result["total_Q_DH_source_MWh"],
      "load_MWh":result["total_Q_load_MWh"],"electric_pump_MWh":result["pump_electric_MWh"],
      "provenance":result["provenance"]},indent=2))
