"""A49 synthetic fault-injection and independent trace-ledger audit.
No hardware, GUI, MATLAB session, model mutation or network I/O.
"""
from __future__ import annotations
from decimal import Decimal, getcontext
from pathlib import Path
import copy, hashlib, json, math, random, sys

HERE = Path(__file__).resolve().parent
A45 = HERE.parent / "AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
sys.path.insert(0, str(A45))
import finite_trip_a45 as plant

getcontext().prec = 38
D = lambda x: Decimal(str(x))
DT = D(900)
HEAT_CAPACITY = D(8000000)
TES_CHARGE_EFF = D("0.93")
TES_DISCHARGE_EFF = D("0.91")
TES_MAX_J = D(900) * D(3600000)
STATE_NAMES = {"ACTIVE", "TRIP_PENDING", "TRIPPED", "RAMPING"}

class LedgerError(AssertionError):
    pass

def check(label, actual, expected, tolerance):
    if abs(actual - expected) > D(tolerance):
        raise LedgerError(f"{label}: actual={actual}, expected={expected}, tolerance={tolerance}")

def independent_audit(trace, *, sensor_lag_steps=0, heat_capacity_J_per_C=8e6,
                      compressor_tau_s=1800., reject_ramp_W=60000.):
    """Re-derive 5 energy/temperature equations and lag dynamics from output columns.
    Does not use the producer's residual columns or dispatch routines.
    """
    if not trace: raise LedgerError("EMPTY_TRACE")
    last_E, last_T, last_hp, last_cap = D(1620000000), D(30), D(0), D(330000)
    states = []
    max_err = D(0)
    first_trip = None
    for i, r in enumerate(trace):
        if r["k"] != i: raise LedgerError(f"INDEX {i}")
        if r["state"] not in STATE_NAMES: raise LedgerError(f"UNKNOWN_STATE {i}")
        states.append(r["state"])
        get = lambda name: D(r[name])
        E, T = get("E_start_J"), get("T_start_C")
        check(f"E continuity {i}", E, last_E, "0.001")
        check(f"T continuity {i}", T, last_T, "0.0000001")
        lag_index = max(0, i - sensor_lag_steps)
        check(f"sensor delay {i}", get("sensed_T_C"), D(trace[lag_index]["T_start_C"]), "0.0000001")
        nominal = get("nominal_cap_W")
        cap = min(nominal, last_cap + D(reject_ramp_W))
        check(f"reject ramp {i}", get("effective_cap_W"), cap, "0.000001")
        check(f"heat IT {i}", get("heat_it_W"), get("active_it_W") + get("residual_it_W"), "0.000001")
        check(f"IT ledger {i}", get("qit_W"),
              get("hx_W")+get("leak_W")+get("hp_source_W")+get("reject_W")+get("unhandled_W"), "0.000001")
        check(f"HP ledger {i}", get("hp_condenser_W"),
              get("hp_source_W")+get("hp_electric_W"), "0.000001")
        check(f"user ledger {i}", get("pool_dh_demand_W"),
              get("pool_dh_served_W")+get("pool_dh_unmet_W"), "0.000001")
        next_E = E + DT*(TES_CHARGE_EFF*get("tes_charge_W")
                    -get("tes_discharge_W")/TES_DISCHARGE_EFF-get("tes_loss_W"))
        check(f"TES ledger {i}", get("E_next_J"), max(D(0),min(TES_MAX_J,next_E)), "0.001")
        next_T = max(D(30), T+DT*(get("unhandled_W")-get("passive_W"))/D(heat_capacity_J_per_C))
        check(f"temperature ledger {i}", get("T_next_C"), next_T, "0.0000001")
        if not (D(0) <= get("reject_W") <= cap+D("0.000001")):
            raise LedgerError(f"REJECT_LIMIT {i}")
        if not (D(0) <= get("E_next_J") <= TES_MAX_J):
            raise LedgerError(f"TES_RANGE {i}")
        if get("active_it_W") < 0 or get("residual_it_W") < 0:
            raise LedgerError(f"NEGATIVE_HEAT {i}")
        if nominal <= 0 and not get("trip_trigger"):
            raise LedgerError(f"ZERO_CAP_NO_FAULT {i}")
        if compressor_tau_s == 0:
            hp_expected = get("hp_source_target_W")
        else:
            alpha = D(-math.expm1(-900.0/compressor_tau_s))
            hp_expected = last_hp + alpha*(get("hp_source_target_W")-last_hp)
        check(f"HP capacity lag {i}", get("hp_available_W"), hp_expected, "0.000001")
        if get("hp_source_W") > get("hp_available_W")+D("0.000001"):
            raise LedgerError(f"HP_SOURCE_LIMIT {i}")
        if r["state"] == "TRIPPED" and first_trip is None: first_trip=i
        last_E, last_T, last_hp, last_cap = get("E_next_J"), get("T_next_C"), get("hp_available_W"), cap
        max_err = max(max_err,abs(get("it_balance_W")),abs(get("hp_balance_W")),
                      abs(get("user_balance_W")))
    return {"samples":len(trace),"max_temperature_C":max(x["T_next_C"] for x in trace),
            "first_trip_index":first_trip, "tripped_steps":states.count("TRIPPED"),
            "pending_steps":states.count("TRIP_PENDING"),
            "max_reported_flow_residual_W":float(max_err)}

def mutation_probes(trace):
    """Assert that the independent ledger rejects five representative corruptions."""
    probes = (
        ("IT_W", "hp_source_W", 1000),
        ("TES_J", "E_next_J", 1000000),
        ("TEMPERATURE_C", "T_next_C", 0.5),
        ("SENSOR_C", "sensed_T_C", 3),
        ("REJECT_W", "reject_W", 1000),
    )
    passed = []
    for label, key, amount in probes:
        altered = list(trace)
        altered[100] = dict(altered[100])
        altered[100][key] += amount
        try:
            independent_audit(altered)
        except LedgerError:
            passed.append(label)
        else:
            raise AssertionError(f"MUTATION_NOT_DETECTED {label}")
    return passed

def run():
    rows = plant.verified_inputs()
    cases = {}
    cf = plant.counter.counterfactual(rows)
    for name in ("both","main_only","backup_only","neither","CF_both","CF_backup_only","CF_neither"):
        source = cf if name.startswith("CF_") else rows
        scenario = name[3:] if name.startswith("CF_") else name
        trace = plant.simulate(source,scenario)
        cases[name] = independent_audit(trace)
    probes = mutation_probes(plant.simulate(rows[:120],"both"))
    # Deterministic variations of demand, sensor lag, trip latency and HP lag.
    rng = random.Random(490027)
    trials = []
    for trial in range(24):
        subset = [dict(r) for r in rows[:160]]
        for r in subset:
            r["qpool"] *= rng.uniform(.7,1.3)
            r["qdh"] *= rng.uniform(.7,1.3)
        scenario = ("both","main_only","backup_only","neither")[trial%4]
        lag = (0,1,2,4)[(trial//4)%4]
        trip_delay = (0,2,4)[trial%3]
        hp_tau = (0.,1800.,7200.)[trial%3]
        trace = plant.simulate(subset,scenario,sensor_lag_steps=lag,
            trip_delay_steps=trip_delay,compressor_tau_s=hp_tau)
        summary = independent_audit(trace,sensor_lag_steps=lag,compressor_tau_s=hp_tau)
        trials.append(dict(case=scenario,lag_steps=lag,trip_delay_steps=trip_delay,
            compressor_tau_s=hp_tau,**summary))
    # Specific zero-capacity interlock must remain independent of thermal sensor delay.
    zero_cap = {}
    for lag in (0,1,4):
        for delay in (0,2,4):
            trace=plant.simulate(rows[:120],"neither",sensor_lag_steps=lag,trip_delay_steps=delay)
            independent_audit(trace,sensor_lag_steps=lag)
            first=next(i for i,r in enumerate(trace) if r["state"]=="TRIPPED")
            if first != 96+delay:
                raise AssertionError(f"TRIP_LATENCY lag={lag} delay={delay} first={first}")
            zero_cap[f"lag{lag}_delay{delay}"]=first
    return {"status":"A49_INDEPENDENT_LEDGER_AND_FAULT_INJECTION_PASS",
            "synthetic_only":True,"physical_release":False,"matlab_a49_executed":False,
            "baseline":cases,"randomized_trials":trials,
            "mutation_probes_detected":probes,"zero_cap_trip_indices":zero_cap,
            "independent_equations":["IT","HP","USER","TES","TEMPERATURE","SENSOR_DELAY","REJECT_RAMP","HP_LAG"],
            "limitations":["No hardware or manufacturer validation",
                           "A49 Python-only; A48 Simulink remains validated only on seven baseline scenarios",
                           "Fault injection changes synthetic demand/parameters, not live equipment"]}
if __name__=="__main__":
    result=run()
    out=HERE/"A49_AUDIT_RESULT.json"
    if out.exists(): raise SystemExit("REFUSE_OVERWRITE_RESULT")
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print(json.dumps({"status":result["status"],"baseline_cases":len(result["baseline"]),
        "randomized_trials":len(result["randomized_trials"]),
        "mutation_probes":len(result["mutation_probes_detected"]),
        "zero_cap_checks":len(result["zero_cap_trip_indices"])},ensure_ascii=False))
