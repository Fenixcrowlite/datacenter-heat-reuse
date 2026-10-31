"""Independent fixed-COP Stateflow acceptance oracle and trace audit, v22.

No production MATLAB code or earlier Python dispatch kernel is imported.
This oracle covers a fixed operating COP, loss-first TES dispatch assumption.
It is implementation QA, not equipment validation or paper replication.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
MODES = {0: "IDLE", 1: "HEAT_RECOVERY", 2: "STORAGE_CHARGE",
         3: "STORAGE_DISCHARGE", 4: "BACKUP", 5: "UNMET_DEMAND"}
FIELDS = ["HP_Request_MW", "HP_Heat_MW", "HP_Direct_MW", "HP_Electric_MW",
          "HP_Source_Used_MW", "COP", "HP_Available", "Source_Unused_MW",
          "Storage_Charge_MW", "Storage_Discharge_MW", "Storage_E_Start_MWh",
          "Storage_E_After_Loss_MWh", "Storage_E_Next_MWh",
          "Storage_Standing_Loss_MWh", "Storage_Charge_Loss_MWh",
          "Storage_Discharge_Loss_MWh", "Gas_Heat_MW", "Unmet_Heat_MW",
          "Supplied_Heat_MW"]


def number(r, key):
    return float(r[key])


def near(a, b):
    return (math.isnan(a) and math.isnan(b)) or (
        math.isfinite(a) and math.isfinite(b)
        and abs(a-b) <= 1e-9 + 1e-11*abs(b))


def mode_from_flows(r, tol=1e-10):
    for field, mode in [("Unmet_Heat_MW", 5), ("Gas_Heat_MW", 4),
                        ("Storage_Discharge_MW", 3), ("Storage_Charge_MW", 2),
                        ("HP_Heat_MW", 1)]:
        if number(r, field) > tol:
            return mode
    return 0


def fixed_cop_oracle(r, energy):
    """Closed-form source bound Qh <= Qsource/(1-1/C), COP C>1."""
    dt = number(r, "dt_h")
    cap = number(r, "storage_capacity_MWh")
    chlim, dislim = number(r, "charge_limit_MW"), number(r, "discharge_limit_MW")
    ec, ed = number(r, "eta_charge"), number(r, "eta_discharge")
    loss, backup = number(r, "loss_fraction_per_h"), number(r, "boiler_capacity_MW")
    hp_cap = number(r, "hp_capacity_MW")
    source, demand = number(r, "Source_Heat_MW"), number(r, "Heat_Demand_MW")
    cold, hot = number(r, "Source_C")+273.15, number(r, "Sink_C")+273.15
    vals = [dt, cap, chlim, dislim, ec, ed, loss, backup, hp_cap, source, demand, energy]
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("Nonfinite numeric domain")
    if (dt <= 0 or min(cap, chlim, dislim, loss, backup, hp_cap, source, demand) < 0
            or not 0 < ec <= 1 or not 0 < ed <= 1 or loss*dt > 1
            or not 0 <= energy <= cap or not 0 < cold < hot):
        raise ValueError("Invalid fixed-COP/TES physical domain")
    if number(r, "part_load_penalty") != 0:
        raise ValueError("Independent v22 oracle intentionally requires zero part-load penalty")
    carnot = hot/(hot-cold)
    if r["backend"] == "lift_polynomial":
        lift = hot-cold
        raw = (number(r, "poly_c0") + number(r, "poly_c1")*lift
               + number(r, "poly_c2")*lift*lift)
        if raw > carnot*(1+32*math.ulp(1.0)):
            raise ValueError("Polynomial exceeds reservoir Carnot bound")
    elif r["backend"] == "carnot":
        raw = number(r, "carnot_efficiency")*carnot
    else:
        raise ValueError("Unknown COP backend")
    cop = min(raw, number(r, "cop_max"))
    after = energy*(1-loss*dt)
    headroom = min(chlim, (cap-after)/(ec*dt))
    request = demand+headroom
    hp = 0.0
    if source > 0 and hp_cap > 0 and request > 0 and cop >= number(r, "cop_min"):
        if cop <= 1:
            raise ValueError("Operating fixed COP must exceed one")
        hp = min(request, hp_cap, source/(1-1/cop))
    direct = min(hp, demand)
    # Feasible headroom is included in the HP request, so all HP surplus is allocated.
    charge = max(hp-demand, 0.0)
    discharge = min(max(demand-hp, 0.0), dislim, after*ed/dt)
    deficit = max(demand-direct-discharge, 0.0)
    gas = min(backup, deficit)
    unmet = max(deficit-gas, 0.0)
    electricity = hp/cop if hp else 0.0
    source_used = hp-electricity
    result = dict(zip(FIELDS, [request, hp, direct, electricity, source_used,
        cop if hp else math.nan, int(hp > 0), max(source-source_used, 0.0),
        charge, discharge, energy, after, after+ec*charge*dt-discharge*dt/ed,
        energy-after, (1-ec)*charge*dt, (1/ed-1)*discharge*dt,
        gas, unmet, demand-unmet]))
    result["Mode"] = mode_from_flows(result)
    return result


def config(**changes):
    base = dict(dt_h=.5, storage_capacity_MWh=10., charge_limit_MW=3.,
        discharge_limit_MW=2., eta_charge=.9, eta_discharge=.8,
        loss_fraction_per_h=.01, boiler_capacity_MW=1., hp_capacity_MW=8.,
        carnot_efficiency=.45, cop_min=2.2, cop_max=7., part_load_penalty=0.,
        backend="lift_polynomial", poly_c0=4., poly_c1=0., poly_c2=0.,
        Source_C=35., Sink_C=70.)
    base.update(changes)
    return base


def generate_vectors():
    scenarios = [
        ("qa_mode_sequence", 2., config(),
         [(0, 0), (2.25, 3), (3.75, 1), (0, 1), (0, 3), (0, 5), (3, 0), (0, 0)]),
        ("qa_full_store", 10., config(dt_h=1., loss_fraction_per_h=0.),
         [(10, 0), (3, 4), (0, 6)]),
        ("qa_zero_store", 0., config(dt_h=.25, storage_capacity_MWh=0.),
         [(3, 4), (0, 1), (0, 3), (10, 0)]),
        ("qa_loss_boundary", 10., config(dt_h=2., loss_fraction_per_h=.5),
         [(0, 0), (3, 0), (0, 2)]),
        ("qa_hp_capacity", 0., config(storage_capacity_MWh=0., hp_capacity_MW=2.,
         boiler_capacity_MW=2.), [(30, 2), (30, 4), (30, 8)]),
        ("qa_charge_room", 9.9, config(dt_h=.25, loss_fraction_per_h=0.),
         [(30, 0), (30, 0), (0, 1)]),
        ("qa_discharge_emptying", .5, config(dt_h=.5, loss_fraction_per_h=0.,
         boiler_capacity_MW=0.), [(0, .8), (0, .8), (0, 0)])]
    rows = []
    for sid, energy, cfg, steps in scenarios:
        for step, (source, demand) in enumerate(steps, 1):
            row = dict(scenario_id=sid, step=step, **cfg,
                       Source_Heat_MW=source, Heat_Demand_MW=demand)
            out = fixed_cop_oracle(row, energy)
            row.update({"expected_"+k: v for k, v in out.items()})
            rows.append(row)
            energy = out["Storage_E_Next_MWh"]
    return rows


def verify_trace(rows, references):
    checks, failures, maximum = 0, [], 0.0

    def check(ok, key, name, residual=None):
        nonlocal checks, maximum
        checks += 1
        if residual is not None and math.isfinite(residual):
            maximum = max(maximum, abs(residual))
        if not ok:
            failures.append({"row": key, "check": name, "residual": residual})

    expected = {(r["scenario_id"], int(float(r["step"]))): r for r in references}
    seen, previous, modes = set(), {}, set()
    transitions = []
    for row in rows:
        raw_step = number(row, "step")
        key = (row["scenario_id"], int(raw_step))
        check(raw_step == key[1] and key[1] > 0, key, "defined_positive_integral_step")
        check(key not in seen, key, "unique_scenario_step")
        seen.add(key)
        try:
            dt = number(row, "dt_h")
            cap = number(row, "storage_capacity_MWh")
            check(math.isfinite(dt) and dt > 0 and math.isfinite(cap) and cap >= 0,
                  key, "dt_capacity_domain")
            values = {k: number(row, k) for k in FIELDS}
            raw_mode = number(row, "Mode")
            mode = int(raw_mode)
            modes.add(mode)
            check(raw_mode == mode and mode in MODES, key, "defined_integral_mode")
            check(mode == mode_from_flows(row), key, "mode_matches_actual_flows")
            for field in FIELDS:
                if field != "COP":
                    check(math.isfinite(values[field]) and values[field] >= -1e-10,
                          key, "finite_nonnegative_"+field)
            check(near(values["HP_Heat_MW"], values["HP_Electric_MW"]+
                       values["HP_Source_Used_MW"]), key, "hp_first_law")
            check(near(values["HP_Source_Used_MW"]+values["Source_Unused_MW"],
                       number(row, "Source_Heat_MW")), key, "source_port_accounting")
            check(values["HP_Available"] == int(values["HP_Heat_MW"] > 0),
                  key, "hp_availability_matches_flow")
            check(near(values["HP_Heat_MW"], values["HP_Direct_MW"]+
                       values["Storage_Charge_MW"]), key, "all_condenser_heat_allocated")
            demand = number(row, "Heat_Demand_MW")
            supplied = values["HP_Direct_MW"]+values["Storage_Discharge_MW"]+values["Gas_Heat_MW"]
            check(near(supplied+values["Unmet_Heat_MW"], demand), key, "demand_accounting")
            check(near(supplied, values["Supplied_Heat_MW"]), key, "useful_supply_accounting")
            ec, ed = number(row, "eta_charge"), number(row, "eta_discharge")
            loss = number(row, "loss_fraction_per_h")
            check(0 < ec <= 1 and 0 < ed <= 1 and 0 <= loss*dt <= 1,
                  key, "tes_efficiency_retention_domain")
            check(near(values["Storage_E_After_Loss_MWh"],
                  values["Storage_E_Start_MWh"]*(1-loss*dt)), key, "loss_first_tes_state")
            check(near(values["Storage_Standing_Loss_MWh"],
                  values["Storage_E_Start_MWh"]*loss*dt), key, "standing_loss_definition")
            check(near(values["Storage_Charge_Loss_MWh"],
                  (1-ec)*values["Storage_Charge_MW"]*dt), key, "charge_loss_definition")
            check(near(values["Storage_Discharge_Loss_MWh"],
                  (1/ed-1)*values["Storage_Discharge_MW"]*dt), key, "discharge_loss_definition")
            residual = ((values["HP_Source_Used_MW"]+values["HP_Electric_MW"]+
                values["Gas_Heat_MW"]-supplied)*dt+values["Storage_E_Start_MWh"]-
                values["Storage_E_Next_MWh"]-values["Storage_Standing_Loss_MWh"]-
                values["Storage_Charge_Loss_MWh"]-values["Storage_Discharge_Loss_MWh"])
            check(near(residual, 0.), key, "recomputed_system_first_law", residual)
            storage_residual = (values["Storage_E_Start_MWh"]+
                (values["Storage_Charge_MW"]-values["Storage_Discharge_MW"])*dt-
                values["Storage_E_Next_MWh"]-values["Storage_Standing_Loss_MWh"]-
                values["Storage_Charge_Loss_MWh"]-values["Storage_Discharge_Loss_MWh"])
            check(near(storage_residual, 0.), key, "recomputed_tes_port_first_law")
            if "System_Balance_Residual_MWh" in row:
                check(near(number(row, "System_Balance_Residual_MWh"), residual),
                      key, "reported_residual_agrees_with_recomputed")
            if "Time_h" in row:
                check(near(number(row, "Time_h"), (key[1]-1)*dt), key, "discrete_time_grid")
            check(0 <= values["Storage_E_Start_MWh"] <= cap+1e-9 and
                  -1e-9 <= values["Storage_E_Next_MWh"] <= cap+1e-9,
                  key, "tes_state_bounds")
            check(values["Storage_Charge_MW"] <= number(row, "charge_limit_MW")+1e-9 and
                  values["Storage_Discharge_MW"] <= number(row, "discharge_limit_MW")+1e-9,
                  key, "tes_power_limits")
            check(values["Storage_Charge_MW"]*values["Storage_Discharge_MW"] == 0,
                  key, "no_simultaneous_tes_flows")
            check(values["HP_Source_Used_MW"] <= number(row, "Source_Heat_MW")+1e-9 and
                  values["HP_Heat_MW"] <= number(row, "hp_capacity_MW")+1e-9 and
                  values["HP_Heat_MW"] <= values["HP_Request_MW"]+1e-9 and
                  values["Gas_Heat_MW"] <= number(row, "boiler_capacity_MW")+1e-9,
                  key, "hp_source_request_boiler_limits")
            if values["HP_Heat_MW"] > 0:
                cop = values["COP"]
                carnot = (number(row, "Sink_C")+273.15)/(number(row, "Sink_C")-number(row, "Source_C"))
                check(math.isfinite(cop) and number(row, "cop_min")-1e-9 <= cop <= carnot+1e-9,
                      key, "operating_cop_domain")
                check(near(cop*values["HP_Electric_MW"], values["HP_Heat_MW"]), key, "cop_definition")
            else:
                check(math.isnan(values["COP"]) and values["HP_Electric_MW"] == 0 and
                      values["HP_Source_Used_MW"] == 0 and values["HP_Available"] == 0,
                      key, "off_cop_undefined_zero_flows")
            sid = key[0]
            if sid in previous:
                old = previous[sid]
                check(key[1] == old[0]+1, key, "sequential_step_order")
                check(near(values["Storage_E_Start_MWh"], old[1]), key, "tes_memory_continuity")
                if old[2] != mode:
                    transitions.append([sid, old[0], old[2], key[1], mode])
            previous[sid] = (key[1], values["Storage_E_Next_MWh"], mode)
            if key in expected:
                ref = expected[key]
                for input_field in ref:
                    if input_field.startswith("expected_") or input_field in ("scenario_id", "step"):
                        continue
                    if input_field == "backend":
                        check(row[input_field] == ref[input_field], key, "oracle_input_backend")
                    else:
                        check(near(number(row, input_field), number(ref, input_field)),
                              key, "oracle_input_"+input_field)
                for field in FIELDS+["Mode"]:
                    wanted = number(ref, "expected_"+field)
                    actual = mode if field == "Mode" else values[field]
                    check(near(actual, wanted), key, "independent_oracle_"+field)
        except (KeyError, ValueError, ZeroDivisionError) as exc:
            check(False, key, "trace_schema_or_domain_"+str(exc))
    check(set(expected).issubset(seen), "ALL", "all_independent_qa_rows_present")
    check(modes == set(MODES), "ALL", "all_six_modes_executed")
    return dict(checks=checks, passed=checks-len(failures), failed=len(failures),
                failures=failures, max_abs_system_residual_MWh=maximum,
                intervals=len(rows), independent_qa_intervals=len(expected),
                modes_executed=sorted(modes), transitions=transitions)


def selftest():
    rows = generate_vectors()
    traces = [{**r, **{k[9:]: v for k, v in r.items() if k.startswith("expected_")}}
              for r in rows]
    report = verify_trace(traces, rows)
    assert report["failed"] == 0, report["failures"]
    # Hand-derived examples and a loss boundary are independent anchors.
    hand = config(storage_capacity_MWh=20., charge_limit_MW=4., discharge_limit_MW=3.)
    hand.update(Source_Heat_MW=3.75, Heat_Demand_MW=1.)
    h = fixed_cop_oracle(hand, 10.)
    assert near(h["Storage_E_Next_MWh"], 11.75) and near(h["Storage_Charge_Loss_MWh"], .2)
    hand.update(Source_Heat_MW=0., Heat_Demand_MW=4.)
    h = fixed_cop_oracle(hand, 10.)
    assert near(h["Storage_E_Next_MWh"], 8.075) and near(h["Storage_Discharge_Loss_MWh"], .375)
    # Deliberate trace corruptions demonstrate that QA rejects failures.
    rejected = []
    for field in ["Mode", "Storage_E_Next_MWh", "HP_Source_Used_MW", "Gas_Heat_MW"]:
        bad = [r.copy() for r in traces]
        bad[0][field] = number(bad[0], field)+.25
        assert verify_trace(bad, rows)["failed"] > 0, field
        rejected.append(field)
    rng = random.Random(22009)
    worst = 0.0
    for _ in range(500):
        c = config(dt_h=rng.choice([.05, .25, .5, 2.]),
            storage_capacity_MWh=rng.uniform(.1, 30), charge_limit_MW=rng.uniform(0, 8),
            discharge_limit_MW=rng.uniform(0, 8), eta_charge=rng.uniform(.3, 1),
            eta_discharge=rng.uniform(.3, 1), loss_fraction_per_h=rng.uniform(0, .2),
            boiler_capacity_MW=rng.uniform(0, 10), hp_capacity_MW=rng.uniform(0, 15))
        c.update(Source_Heat_MW=rng.uniform(0, 20), Heat_Demand_MW=rng.uniform(0, 30))
        energy = rng.uniform(0, c["storage_capacity_MWh"])
        x = fixed_cop_oracle(c, energy)
        residual = ((x["HP_Source_Used_MW"]+x["HP_Electric_MW"]+x["Gas_Heat_MW"]-
            x["Supplied_Heat_MW"])*c["dt_h"]+energy-x["Storage_E_Next_MWh"]-
            x["Storage_Standing_Loss_MWh"]-x["Storage_Charge_Loss_MWh"]-x["Storage_Discharge_Loss_MWh"])
        worst = max(worst, abs(residual))
        assert abs(residual) < 1e-10
        assert -1e-10 <= x["Storage_E_Next_MWh"] <= c["storage_capacity_MWh"]+1e-10
        y = fixed_cop_oracle({**c, "boiler_capacity_MW": c["boiler_capacity_MW"]+1}, energy)
        assert y["Unmet_Heat_MW"] <= x["Unmet_Heat_MW"]+1e-10
        z = fixed_cop_oracle({**c, "Source_Heat_MW": c["Source_Heat_MW"]+1}, energy)
        assert z["Unmet_Heat_MW"] <= x["Unmet_Heat_MW"]+1e-10
        assert z["Storage_E_Next_MWh"] >= x["Storage_E_Next_MWh"]-1e-10
    return dict(vector_intervals=len(rows), vector_scenarios=len({r["scenario_id"] for r in rows}),
                oracle_trace_checks=report["checks"], modes=report["modes_executed"],
                randomized_algebraic_cases=500, seed=22009,
                corruptions_rejected=rejected, max_abs_random_residual_MWh=worst)


def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-vectors", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--vectors", type=Path, default=HERE/"stateflow_qa_vectors_v22.csv")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = dict(version="0.22", primary_paper_replication=False, equipment_validation=False,
                  scope="Independent fixed-COP oracle and actual-trace numerical QA")
    if args.self_test:
        result["self_test"] = selftest()
    if args.generate_vectors:
        if args.vectors.exists():
            raise FileExistsError(args.vectors)
        rows = generate_vectors()
        with args.vectors.open("x", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        result["vectors_sha256"] = sha(args.vectors)
    if args.trace:
        result["trace_file"] = str(args.trace.resolve())
        result["trace_sha256"] = sha(args.trace)
        result["vectors_sha256"] = sha(args.vectors)
        result["trace_qa"] = verify_trace(read_csv(args.trace), read_csv(args.vectors))
    result["verifier_sha256"] = sha(Path(__file__))
    if args.report:
        with args.report.open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2, allow_nan=False)
            f.write("\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    if result.get("trace_qa", {}).get("failed", 0):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
