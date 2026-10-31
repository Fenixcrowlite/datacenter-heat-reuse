"""A42 isolated, synthetic IT/HP/TES/REJECT coupled heat-flow model.

Safety interlock is a *simulated ideal* zero-capacity shutdown, not a command
to physical IT equipment. Sensor lag affects thermal alarm, not the interlock.
No physical certification, measured COP map or hardware interfaces.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A41 = HERE.parent / "AUTONOMOUS_RUN_20261026_1751_A41_CLOSED_LOOP_SIM"
DT = 900.0
E_MAX = 900 * 3.6e6
E_INIT = 450 * 3.6e6
C_BASE = 8e6
RESTART_GOOD_SAMPLES = 2
RAMP_W = 15000.0
SCENARIOS = ("both", "main_only", "backup_only", "neither")
SOURCE = A41 / "INPUTS_A41.csv"

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load_inputs():
    manifest = json.loads((A41 / "SHA256_MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get(SOURCE.name) != sha(SOURCE):
        raise RuntimeError("UPSTREAM_A41_SHA_MISMATCH")
    with SOURCE.open(encoding="utf-8", newline="") as f:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(f)]
    if len(rows) != 672:
        raise ValueError("EXPECTED_672_SAMPLES")
    for k, row in enumerate(rows):
        if abs(row["cas_h"] - k / 4) > 1e-9:
            raise ValueError("TIME_GRID_MISMATCH")
        if any(not math.isfinite(v) or v < 0 for v in row.values()):
            raise ValueError("NONFINITE_OR_NEGATIVE_INPUT")
    return rows

def capacity(scenario, k, backup_delay_steps=2):
    if scenario not in SCENARIOS or backup_delay_steps < 0:
        raise ValueError("INVALID_SCENARIO")
    if k < 96 or k >= 384 or scenario == "both":
        return 330000.0
    if scenario == "main_only":
        return 180000.0
    if scenario == "backup_only":
        return 0.0 if k < 96 + backup_delay_steps else 150000.0
    return 0.0

def cop_proxy(temp_c):
    if not math.isfinite(temp_c):
        raise ValueError("INVALID_TEMPERATURE")
    # Synthetic lift proxy only; NOT a manufacturer's COP characteristic.
    return max(2.0, min(5.0, 3.5 + .04 * (temp_c - 30.0)))

def dispatch(row, qit, E, T, cap):
    """Conserve IT heat, HP source/electric/condenser heat, TES and user heat."""
    if any(not math.isfinite(x) for x in (qit, E, T, cap)):
        raise ValueError("NONFINITE_STATE")
    if not 0 <= qit <= row["qdc"] + 1e-7 or not 0 <= E <= E_MAX + 1e-4 or cap < 0:
        raise ValueError("INVALID_STATE")
    hx = min(row["hx"], qit)
    leak = min(row["leak"], max(0.0, qit - hx))
    it_available = max(0.0, qit - hx - leak)
    heat_demand = row["qpool"] + row["qdh"]
    loss = .002 * E / 86400.0
    dis_cap = max(0.0, (E - DT * loss) * .91 / DT)
    discharge = min(row["qdis"], heat_demand, dis_cap)
    charge_room = max(0.0, (E_MAX - E + DT * (discharge / .91 + loss)) / (DT * .93))
    charge_request = min(row["qcharge"], charge_room)
    need_hp = max(0.0, heat_demand - discharge)
    desired_cond = need_hp + charge_request
    cop = cop_proxy(T)
    source = min(it_available, desired_cond * (cop - 1.0) / cop)
    power = source / (cop - 1.0)
    condenser = source + power
    served_hp = min(need_hp, condenser)
    charge = min(charge_request, max(0.0, condenser - served_hp))
    served = discharge + served_hp
    unmet = max(0.0, heat_demand - served)
    E_next = E + DT * (.93 * charge - discharge / .91 - loss)
    if not -1e-4 <= E_next <= E_MAX + 1e-4:
        raise AssertionError("TES_LIMIT")
    E_next = max(0.0, min(E_MAX, E_next))
    required = max(0.0, qit - hx - leak - source)
    rejected = min(required, cap)
    unhandled = max(0.0, required - rejected)
    return dict(qit_W=qit, hx_W=hx, leak_W=leak, hp_source_W=source,
        hp_electric_W=power, hp_condenser_W=condenser, cop_proxy=cop,
        pool_dh_demand_W=heat_demand, pool_dh_served_W=served,
        pool_dh_unmet_W=unmet, tes_charge_W=charge, tes_discharge_W=discharge,
        tes_loss_W=loss, E_next_J=E_next, required_reject_W=required,
        reject_W=rejected, unhandled_W=unhandled,
        it_balance_W=qit-hx-leak-source-rejected-unhandled,
        hp_balance_W=condenser-source-power,
        user_balance_W=heat_demand-served-unmet,
        tes_balance_J=E_next-E-DT*(.93*charge-discharge/.91-loss))

def replay(rows, scenario, sensor_lag_steps=0, heat_capacity_J_per_C=C_BASE,
           backup_delay_steps=2):
    if sensor_lag_steps < 0 or not isinstance(sensor_lag_steps, int):
        raise ValueError("INVALID_SENSOR_LAG")
    if heat_capacity_J_per_C <= 0 or not math.isfinite(heat_capacity_J_per_C):
        raise ValueError("INVALID_HEAT_CAPACITY")
    E, T, mode, previous_shed, previous_it, good = E_INIT, 30.0, "ACTIVE", 0.0, 0.0, 0
    starts = []
    trace = []
    for k, row in enumerate(rows):
        starts.append(T)
        sensed_T = starts[max(0, k - sensor_lag_steps)]
        cap = capacity(scenario, k, backup_delay_steps)
        # Direct capacity-zero interlock is intentionally independent of sensor lag.
        if cap == 0 or sensed_T >= 42.0:
            mode, good, qit = "TRIPPED", 0, 0.0
        elif mode == "TRIPPED":
            good = good + 1 if sensed_T < 36.0 else 0
            if good >= RESTART_GOOD_SAMPLES:
                mode, qit = "RAMPING", min(row["qdc"], RAMP_W)
            else:
                qit = 0.0
        elif mode == "RAMPING":
            qit = min(row["qdc"], previous_it + RAMP_W)
            if qit >= row["qdc"] - 1e-8:
                mode = "ACTIVE"
        else:
            nominal = dispatch(row, row["qdc"], E, T, cap)
            excess = max(0.0, nominal["required_reject_W"] - cap)
            target_shed = min(.4 * row["qdc"], excess)
            shed = min(target_shed, previous_shed + RAMP_W)
            qit = row["qdc"] - shed
        flows = dispatch(row, qit, E, T, cap)
        passive = 2000.0 * max(0.0, T - 30.0)
        T_next = max(30.0, T + DT * (flows["unhandled_W"] - passive) / heat_capacity_J_per_C)
        record = dict(k=k, t_h=k/4, scenario=scenario, mode=mode, cap_W=cap,
            T_start_C=T, sensed_T_C=sensed_T, T_next_C=T_next,
            E_start_J=E, TES_SOC_next=flows["E_next_J"]/E_MAX,
            qdc_nominal_W=row["qdc"], shed_W=row["qdc"]-qit,
            passive_W=passive, **flows)
        for name in ("it_balance_W", "hp_balance_W", "user_balance_W"):
            if abs(record[name]) > 1e-6:
                raise AssertionError(("BALANCE", k, name, record[name]))
        if abs(record["tes_balance_J"]) > 1e-3:
            raise AssertionError(("TES_BALANCE", k, record["tes_balance_J"]))
        if record["reject_W"] > cap + 1e-7:
            raise AssertionError("REJECT_CAPACITY")
        if cap == 0 and (record["qit_W"] != 0 or record["unhandled_W"] != 0):
            raise AssertionError("ZERO_CAPACITY_INTERLOCK")
        trace.append(record)
        E, T = flows["E_next_J"], T_next
        previous_shed, previous_it = row["qdc"]-qit, qit
    return trace

def summarize(trace):
    return dict(samples=len(trace),
        max_T_C=max(x["T_next_C"] for x in trace),
        trip_steps=sum(x["mode"]=="TRIPPED" for x in trace),
        unhandled_kWh=sum(x["unhandled_W"] for x in trace)/4000,
        unmet_user_kWh=sum(x["pool_dh_unmet_W"] for x in trace)/4000,
        hp_electric_kWh=sum(x["hp_electric_W"] for x in trace)/4000,
        IT_generated_kWh=sum(x["qit_W"] for x in trace)/4000,
        max_it_balance_W=max(abs(x["it_balance_W"]) for x in trace),
        max_hp_balance_W=max(abs(x["hp_balance_W"]) for x in trace),
        max_tes_balance_J=max(abs(x["tes_balance_J"]) for x in trace))

def write_csv(path, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def main():
    rows=load_inputs()
    cases={}
    for scenario in SCENARIOS:
        trace=replay(rows,scenario)
        p=HERE / ("TRACE_A42_"+scenario+".csv")
        write_csv(p,trace)
        cases[scenario]=dict(**summarize(trace),trace_sha256=sha(p))
    sensitivity={}
    for lag in (0,1,2):
        for c in (8e6,16e6,32e6):
            t=replay(rows,"backup_only",sensor_lag_steps=lag,heat_capacity_J_per_C=c)
            sensitivity[f"lag{lag}_C{int(c)}"]=summarize(t)
    report=dict(status="SYNTHETIC_COUPLED_FAILSAFE_REFERENCE_VERIFIED_BY_PYTHON_ONLY",
        physical_release_allowed=False,hardware_control=False,
        a41_input_sha256=sha(SOURCE),samples=672,dt_seconds=900,
        assumptions=["synthetic demand and REJECT A/B ratings","ideal immediate zero-capacity IT trip",
          "2-step restart qualification and 15 kW/sample ramp are hypothetical",
          "HP COP is a synthetic temperature proxy, not measured",
          "HP condenser serves users first, then TES charging",
          "unmet heating demand tracked explicitly; no pump/fan/electrical grid model",
          "sensor lag applies to alarm, not independent zero-capacity interlock"],
        cases=cases,sensor_capacity_sweep=sensitivity)
    (HERE/"RESULTS_A42.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="sensor_capacity_sweep"},indent=2))

if __name__=="__main__":
    main()
