"""Independent exponential loss-first TES/Stateflow numerical QA, v28.

No production MATLAB component or earlier Python physics kernel supplies
expected numeric values. The v24 reviewer supplies only its generic invalid-
case schema check; its transitive v22 physics import is never called here.
Synthetic reviewer tests are clearly distinct from executed Simulink evidence.
"""
from __future__ import annotations

import argparse
import copy
import csv
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import random
from xml.etree import ElementTree as ET
from zipfile import ZipFile

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
SCHEME = "exponential_loss_first"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def number(row, key):
    return float(row[key])


def near(a, b):
    return (math.isnan(a) and math.isnan(b)) or (
        math.isfinite(a) and math.isfinite(b) and abs(a-b) <= 1e-9 + 1e-11*abs(b))


def result(checks):
    return dict(checks=len(checks), passed=sum(c["passed"] for c in checks),
                failed=sum(not c["passed"] for c in checks), assertions=checks)


def mode_from_flows(row):
    for field, mode in [("Unmet_Heat_MW", 5), ("Gas_Heat_MW", 4),
                        ("Storage_Discharge_MW", 3), ("Storage_Charge_MW", 2),
                        ("HP_Direct_MW", 1)]:
        if number(row, field) > 0:
            return mode
    return 0


def fixed_cop_oracle(row, energy):
    """Closed-form source bound and exact passive attenuation, then port update.

    This solves the DECLARED operator-split dispatch. It is not the exact
    continuously charged/discharged reservoir solution, which is separate below.
    """
    dt, cap = number(row, "dt_h"), number(row, "storage_capacity_MWh")
    chlim, dislim = number(row, "charge_limit_MW"), number(row, "discharge_limit_MW")
    ec, ed = number(row, "eta_charge"), number(row, "eta_discharge")
    rate = number(row, "continuous_loss_rate_per_h")
    backup, hp_cap = number(row, "boiler_capacity_MW"), number(row, "hp_capacity_MW")
    source, demand = number(row, "Source_Heat_MW"), number(row, "Heat_Demand_MW")
    cold, hot = number(row, "Source_C")+273.15, number(row, "Sink_C")+273.15
    vals = [dt, cap, chlim, dislim, ec, ed, rate, backup, hp_cap, source, demand,
            cold, hot, energy]
    if not all(math.isfinite(v) for v in vals):
        raise ValueError("Nonfinite numeric domain")
    if (dt <= 0 or min(cap, chlim, dislim, rate, backup, hp_cap, source, demand) < 0
            or not 0 < ec <= 1 or not 0 < ed <= 1 or not 0 <= energy <= cap
            or not 0 < cold < hot or not math.isfinite(rate*dt)):
        raise ValueError("Invalid exponential fixed-COP/TES domain")
    if row.get("scheme", SCHEME) != SCHEME:
        raise ValueError("Wrong standing-loss scheme")
    if number(row, "part_load_penalty") != 0:
        raise ValueError("Independent v28 oracle intentionally requires zero part-load penalty")
    floor, ceiling = number(row, "cop_min"), number(row, "cop_max")
    if not math.isfinite(floor) or not math.isfinite(ceiling) or floor <= 1 or ceiling < floor:
        raise ValueError("Invalid COP limits")
    carnot = hot/(hot-cold)
    if row["backend"] == "lift_polynomial":
        lift = hot-cold
        coefficients = [number(row, name) for name in ("poly_c0", "poly_c1", "poly_c2")]
        if not all(math.isfinite(v) for v in coefficients):
            raise ValueError("Nonfinite polynomial coefficient")
        raw = coefficients[0]+coefficients[1]*lift+coefficients[2]*lift*lift
        if not math.isfinite(raw) or raw > carnot*(1+32*math.ulp(1.0)):
            raise ValueError("Polynomial invalid or exceeds reservoir Carnot bound")
    elif row["backend"] == "carnot":
        fraction = number(row, "carnot_efficiency")
        if not 0 < fraction <= 1:
            raise ValueError("Invalid Carnot fraction")
        raw = fraction*carnot
    else:
        raise ValueError("Unknown COP backend")
    cop = min(raw, ceiling)
    after = energy*math.exp(-rate*dt)
    room = min(chlim, max(0., cap-after)/(ec*dt))
    request = demand+room
    hp = 0.
    if source > 0 and hp_cap > 0 and request > 0 and cop >= floor:
        hp = min(request, hp_cap, source/(1-1/cop))
    direct = min(hp, demand)
    charge = max(hp-demand, 0.)
    discharge = min(max(demand-hp, 0.), dislim, after*ed/dt)
    deficit = max(demand-direct-discharge, 0.)
    gas = min(backup, deficit)
    unmet = max(deficit-gas, 0.)
    electricity = hp/cop if hp else 0.
    source_used = hp-electricity
    out = dict(zip(FIELDS, [request, hp, direct, electricity, source_used,
        cop if hp else math.nan, int(hp > 0), max(source-source_used, 0.), charge,
        discharge, energy, after, after+ec*charge*dt-discharge*dt/ed,
        energy-after, (1-ec)*charge*dt, (1/ed-1)*discharge*dt,
        gas, unmet, demand-unmet]))
    out["Mode"] = mode_from_flows(out)
    return out


def config(**changes):
    values = dict(scheme=SCHEME, dt_h=.5, storage_capacity_MWh=10., charge_limit_MW=3.,
        discharge_limit_MW=2., eta_charge=.9, eta_discharge=.8,
        continuous_loss_rate_per_h=.01, boiler_capacity_MW=1., hp_capacity_MW=8.,
        carnot_efficiency=.45, cop_min=2.2, cop_max=7., part_load_penalty=0.,
        backend="lift_polynomial", poly_c0=4., poly_c1=0., poly_c2=0.,
        Source_C=35., Sink_C=70.)
    values.update(changes)
    return values


def generate_vectors():
    scenarios = [
        ("qa_mode_sequence_v28", 2., config(),
         [(0, 0), (2.25, 3), (3.75, 1), (0, 1), (0, 3), (0, 5), (3, 0), (0, 0)]),
        ("qa_full_store_v28", 10., config(dt_h=1., continuous_loss_rate_per_h=0.),
         [(10, 0), (3, 4), (0, 6)]),
        ("qa_zero_store_v28", 0., config(dt_h=.25, storage_capacity_MWh=0.),
         [(3, 4), (0, 1), (0, 3), (10, 0)]),
        ("qa_high_loss_v28", 10., config(dt_h=2., continuous_loss_rate_per_h=2.),
         [(0, 0), (3, 0), (0, 2)]),
        ("qa_charge_room_v28", 9.9, config(dt_h=.25, continuous_loss_rate_per_h=0.),
         [(30, 0), (30, 0), (0, 1)]),
        ("qa_discharge_emptying_v28", .5, config(dt_h=.5, continuous_loss_rate_per_h=0.,
         boiler_capacity_MW=0.), [(0, .8), (0, .8), (0, 0)]),
        ("qa_loss_underflow_v28", 10., config(dt_h=1., continuous_loss_rate_per_h=1000.),
         [(0, 0), (0, 2)]),
        ("qa_unity_efficiencies_v28", 4., config(eta_charge=1., eta_discharge=1.),
         [(3, 0), (0, 2)])]
    for dt in [2., 1., .5, .25]:
        label = str(dt).replace(".", "p")
        count = int(round(2./dt))
        scenarios.append(("qa_passive_dt_"+label, 10., config(dt_h=dt,
            continuous_loss_rate_per_h=.2, charge_limit_MW=0.), [(0, 0)]*count))
        scenarios.append(("qa_charge_dt_"+label, 2., config(dt_h=dt,
            continuous_loss_rate_per_h=.2, storage_capacity_MWh=100.), [(3, 0)]*count))
    rows = []
    for sid, energy, cfg, steps in scenarios:
        for step, (source, demand) in enumerate(steps, 1):
            row = dict(scenario_id=sid, step=step, **cfg,
                       Source_Heat_MW=source, Heat_Demand_MW=demand)
            out = fixed_cop_oracle(row, energy)
            row.update({"expected_"+key: value for key, value in out.items()})
            rows.append(row)
            energy = out["Storage_E_Next_MWh"]
    return rows


def verify_trace(rows, references, supplemental=None):
    checks, maximum = [], 0.
    def check(name, ok, key="ALL"):
        checks.append(dict(row=key, name=name, passed=bool(ok)))
    expected = {(r["scenario_id"], int(number(r, "step"))): r for r in references}
    supplemental_expected = {}
    for source in supplemental or []:
        supplemental_row = {name: value for name, value in source.items()
                            if not name.startswith("expected_") and name != "loss_fraction_per_h"}
        supplemental_row["continuous_loss_rate_per_h"] = source["loss_fraction_per_h"]
        supplemental_row["scheme"] = SCHEME
        supplemental_row["scenario_id"] = "legacy_input_"+source["scenario_id"]
        supplemental_expected[(supplemental_row["scenario_id"], int(number(source, "step")))] = supplemental_row
    seen, previous, modes, transitions = set(), {}, set(), []
    oracle_intervals = 0
    for row in rows:
        key = (row["scenario_id"], int(number(row, "step")))
        try:
            check("positive_integral_unique_step", number(row, "step") == key[1] and
                  key[1] > 0 and key not in seen, key)
            seen.add(key)
            check("row_has_independently_saved_input_reference", key in expected or key in supplemental_expected, key)
            ref = expected.get(key, supplemental_expected.get(key))
            if ref is None:
                raise ValueError("Unrecognized scenario input metadata")
            for name, value in ref.items():
                if name.startswith("expected_") or name in ("scenario_id", "step"):
                    continue
                check("independent_input_"+name,
                      row[name] == value if name in ("backend", "scheme") else
                      near(number(row, name), float(value)), key)
            if key in expected:
                oracle_intervals += 1
                energy = number(ref, "expected_Storage_E_Start_MWh")
                oracle = fixed_cop_oracle(ref, energy)
                for field in FIELDS+["Mode"]:
                    check("stored_vector_rederived_"+field,
                          near(number(ref, "expected_"+field), oracle[field]), key)
                    check("actual_independent_oracle_"+field,
                          near(number(row, field), oracle[field]), key)
            dt, cap = number(row, "dt_h"), number(row, "storage_capacity_MWh")
            ec, ed = number(row, "eta_charge"), number(row, "eta_discharge")
            rate = number(row, "continuous_loss_rate_per_h")
            values = {name: number(row, name) for name in FIELDS}
            mode = int(number(row, "Mode"))
            modes.add(mode)
            check("defined_mode_matching_flows", number(row, "Mode") == mode and
                  mode in MODES and mode == mode_from_flows(row), key)
            for field in FIELDS:
                if field != "COP":
                    check("finite_nonnegative_"+field,
                          math.isfinite(values[field]) and values[field] >= -1e-10, key)
            check("source_heat_accounted", near(values["HP_Source_Used_MW"]+
                  values["Source_Unused_MW"], number(row, "Source_Heat_MW")), key)
            check("hp_first_law", near(values["HP_Heat_MW"], values["HP_Source_Used_MW"]+
                  values["HP_Electric_MW"]), key)
            check("all_condenser_heat_allocated", near(values["HP_Heat_MW"],
                  values["HP_Direct_MW"]+values["Storage_Charge_MW"]), key)
            supplied = values["HP_Direct_MW"]+values["Storage_Discharge_MW"]+values["Gas_Heat_MW"]
            check("demand_and_useful_supply_accounting", near(supplied, values["Supplied_Heat_MW"])
                  and near(supplied+values["Unmet_Heat_MW"], number(row, "Heat_Demand_MW")), key)
            start, after, end = (values["Storage_E_"+name+"_MWh"] for name in
                                  ("Start", "After_Loss", "Next"))
            check("exact_passive_exponential_attenuation", near(after, start*math.exp(-rate*dt)), key)
            check("standing_loss_from_start_state", near(values["Storage_Standing_Loss_MWh"], start-after), key)
            check("charge_conversion_loss", near(values["Storage_Charge_Loss_MWh"],
                  (1-ec)*values["Storage_Charge_MW"]*dt), key)
            check("discharge_conversion_loss", near(values["Storage_Discharge_Loss_MWh"],
                  (1/ed-1)*values["Storage_Discharge_MW"]*dt), key)
            losses = sum(values[name] for name in ("Storage_Standing_Loss_MWh",
                "Storage_Charge_Loss_MWh", "Storage_Discharge_Loss_MWh"))
            tres = start+(values["Storage_Charge_MW"]-values["Storage_Discharge_MW"])*dt-end-losses
            sres = start+(values["HP_Source_Used_MW"]+values["HP_Electric_MW"]+
                values["Gas_Heat_MW"]-supplied)*dt-end-losses
            maximum = max(maximum, abs(sres))
            check("recomputed_TES_first_law", near(tres, 0.), key)
            check("recomputed_system_first_law", near(sres, 0.), key)
            if "System_Balance_Residual_MWh" in row:
                check("reported_residual_matches_recomputed", near(
                      number(row, "System_Balance_Residual_MWh"), sres), key)
            check("SOC_start_after_next_bounds", all(-1e-9 <= e <= cap+1e-9 for e in (start, after, end)), key)
            check("TES_power_limits_and_exclusivity", values["Storage_Charge_MW"] <=
                  number(row, "charge_limit_MW")+1e-9 and values["Storage_Discharge_MW"] <=
                  number(row, "discharge_limit_MW")+1e-9 and
                  values["Storage_Charge_MW"]*values["Storage_Discharge_MW"] == 0, key)
            check("source_HP_request_boiler_limits", values["HP_Source_Used_MW"] <=
                  number(row, "Source_Heat_MW")+1e-9 and values["HP_Heat_MW"] <=
                  number(row, "hp_capacity_MW")+1e-9 and values["HP_Heat_MW"] <=
                  values["HP_Request_MW"]+1e-9 and values["Gas_Heat_MW"] <=
                  number(row, "boiler_capacity_MW")+1e-9, key)
            if values["HP_Heat_MW"] > 0:
                carnot = (number(row, "Sink_C")+273.15)/(number(row, "Sink_C")-number(row, "Source_C"))
                check("operating_COP_and_availability", math.isfinite(values["COP"]) and
                      number(row, "cop_min") <= values["COP"] <= carnot+1e-9 and
                      near(values["COP"]*values["HP_Electric_MW"], values["HP_Heat_MW"])
                      and values["HP_Available"] == 1, key)
            else:
                check("off_COP_undefined_and_zero_flows", math.isnan(values["COP"]) and
                      values["HP_Electric_MW"] == values["HP_Source_Used_MW"] ==
                      values["HP_Available"] == 0, key)
            if "Time_h" in row:
                check("physical_sample_times", near(number(row, "Time_h"), (key[1]-1)*dt), key)
            sid = key[0]
            if sid in previous:
                old = previous[sid]
                check("sequential_step_and_memory_continuity", key[1] == old[0]+1 and near(start, old[1]), key)
                if old[2] != mode:
                    transitions.append([sid, old[0], old[2], key[1], mode])
            else:
                check("scenario_starts_on_step_one", key[1] == 1, key)
            previous[sid] = (key[1], end, mode)
        except (KeyError, ValueError, OverflowError, ZeroDivisionError) as exc:
            check("trace_schema_or_domain_"+str(exc), False, key)
    check("all_fixed_COP_reference_rows_present", set(expected).issubset(seen))
    check("all_supplemental_reference_rows_present", set(supplemental_expected).issubset(seen))
    check("only_recognized_reference_inputs_executed", seen.issubset(set(expected)|set(supplemental_expected)))
    check("all_six_modes_executed", modes == set(MODES))
    output = result(checks)
    output.update(intervals=len(rows), independently_predicted_fixed_COP_intervals=oracle_intervals,
                  supplemental_physical_contract_intervals=len(rows)-oracle_intervals,
                  supplemental_limit="Nonzero part-load HP outputs are not independently predicted by this fixed-COP reviewer.",
                  scenarios=len(previous), modes_executed=sorted(modes),
                  transitions=transitions, max_abs_system_residual_MWh=maximum)
    return output


def exact_constant_input(initial, rate, horizon, internal_power):
    """Integrating-factor solution E'=q-lambda E; q is signed internal MW."""
    if rate == 0:
        return initial+internal_power*horizon
    return initial*math.exp(-rate*horizon)+internal_power*(-math.expm1(-rate*horizon))/rate


def closed_form_split(initial, rate, horizon, internal_power, dt, scheme):
    intervals = int(round(horizon/dt))
    if intervals <= 0 or not near(intervals*dt, horizon):
        raise ValueError("Horizon not positive integral number of physical intervals")
    if scheme == SCHEME:
        retention = math.exp(-rate*dt)
        sum_weights = intervals if rate == 0 else (-math.expm1(-rate*horizon))/(-math.expm1(-rate*dt))
    elif scheme == "linear_loss_first":
        if rate*dt > 1:
            raise ValueError("Linear interval loss exceeds state")
        retention = 1-rate*dt
        sum_weights = intervals if rate == 0 else (1-retention**intervals)/(1-retention)
    elif scheme == "exact_continuous":
        return exact_constant_input(initial, rate, horizon, internal_power)
    else:
        raise ValueError("Unknown split scheme: "+scheme)
    return initial*retention**intervals+internal_power*dt*sum_weights


def verify_experiments(rows, evidence_directory=None):
    checks, groups = [], {}
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    seen = set()
    actual_trace_hashes = {}
    actual_trace_intervals = 0
    for row in rows:
        prefix = row["scenario_id"]+":"+row["scheme"]+":"+row["dt_h"]+":"
        try:
            dt, rate, horizon, initial, q = [number(row, name) for name in
                ("dt_h", "lambda_per_h", "horizon_h", "initial_MWh", "charge_internal_MW")]
            check(prefix+"finite_nonnegative_physical_experiment_inputs", all(math.isfinite(v) for v in
                  (dt, rate, horizon, initial, q)) and dt > 0 and horizon > 0 and min(rate, initial, q) >= 0)
            signature = (row["scenario_id"], row["scheme"], dt)
            check(prefix+"unique_experiment", signature not in seen)
            seen.add(signature)
            wanted = closed_form_split(initial, rate, horizon, q, dt, row["scheme"])
            exact = exact_constant_input(initial, rate, horizon, q)
            check(prefix+"actual_terminal_matches_independent_geometric_solution", near(number(row, "terminal_MWh"), wanted))
            check(prefix+"reported_continuous_reference_matches_integrating_factor_solution", near(number(row, "exact_continuous_MWh"), exact))
            if "abs_error_MWh" in row:
                check(prefix+"reported_absolute_error", near(number(row, "abs_error_MWh"), abs(wanted-exact)))
            if evidence_directory is not None:
                path = (evidence_directory/row["trace_file"]).resolve()
                check(prefix+"trace_is_local_to_evidence_directory", path.parent == evidence_directory.resolve())
                if path.parent != evidence_directory.resolve():
                    raise ValueError("Trace path outside experiment evidence directory")
                samples = read_csv(path)
                actual_trace_hashes[path.name] = sha(path)
                intervals = int(round(horizon/dt))
                check(prefix+"actual_sample_count_is_horizon_over_dt", len(samples) == intervals)
                if "intervals" in row:
                    check(prefix+"reported_interval_count", number(row, "intervals") == intervals)
                start = initial
                for index, sample in enumerate(samples):
                    label = prefix+"sample_"+str(index)+":"
                    numbers = [number(sample, name) for name in ("Time_h", "Mode", "Charge_MW",
                        "Discharge_MW", "After_MWh", "Next_MWh", "Standing_Loss_MWh", "Residual_MWh")]
                    check(label+"all_actual_ports_finite", all(math.isfinite(v) for v in numbers))
                    time, mode, charge, discharge, after, end, standing, residual = numbers
                    retention = math.exp(-rate*dt) if row["scheme"] == SCHEME else 1-rate*dt
                    check(label+"actual_physical_sample_grid", near(time, index*dt))
                    check(label+"constant_port_charge_and_no_discharge", near(charge, q) and discharge == 0)
                    check(label+"mode_semantics", mode == (2 if q > 0 else 0))
                    check(label+"standing_retention_from_previous_actual_state", near(after, start*retention))
                    check(label+"state_update_from_actual_ports", near(end, after+charge*dt))
                    check(label+"standing_loss_from_actual_states", near(standing, start-after))
                    actual_residual = start+(charge-discharge)*dt-end-standing
                    check(label+"recomputed_actual_first_law", near(actual_residual, 0.))
                    check(label+"reported_first_law_matches_actual", near(residual, actual_residual))
                    check(label+"actual_SOC_and_loss_nonnegative", min(after, end, standing) >= -1e-9)
                    start = end
                actual_trace_intervals += len(samples)
                check(prefix+"reported_terminal_is_last_actual_next_port", bool(samples) and
                      near(number(row, "terminal_MWh"), number(samples[-1], "Next_MWh")))
            groups.setdefault((row["scenario_id"], row["scheme"], rate, horizon, initial, q), []).append(row)
        except (ValueError, OverflowError, ZeroDivisionError, KeyError, OSError) as exc:
            check(prefix+"schema_domain_"+str(exc), False)
    for key, group in groups.items():
        sid, scheme, rate, horizon, initial, q = key
        ordered = sorted(group, key=lambda r: number(r, "dt_h"), reverse=True)
        if scheme == SCHEME and q == 0:
            check(sid+":passive_exponential_semigroup", all(near(number(r, "terminal_MWh"),
                  initial*math.exp(-rate*horizon)) for r in ordered))
        elif len(ordered) > 1 and rate > 0 and q > 0 and scheme == SCHEME:
            errors = [number(r, "terminal_MWh")-number(r, "exact_continuous_MWh") for r in ordered]
            check(sid+":end_of_interval_charging_overestimates_continuous_charge", all(e > 0 for e in errors))
            check(sid+":charge_split_error_decreases_on_refinement", all(a > b for a, b in zip(errors, errors[1:])))
        elif len(ordered) > 1 and rate > 0 and q == 0 and scheme == "linear_loss_first":
            errors = [number(r, "exact_continuous_MWh")-number(r, "terminal_MWh") for r in ordered]
            check(sid+":legacy_linear_underestimates_passive_energy", all(e > 0 for e in errors))
            check(sid+":legacy_passive_error_decreases_on_refinement", all(a > b for a, b in zip(errors, errors[1:])))
    check("nonempty_actual_experiment_evidence", bool(rows))
    output = result(checks)
    output.update(actual_trace_intervals=actual_trace_intervals, actual_trace_sha256=actual_trace_hashes,
                  trace_series_verified=evidence_directory is not None)
    return output


def prop(element, name, default=""):
    if element is None:
        return default
    return element.findtext("P[@Name='"+name+"']", default=default)


def verify_structure(model):
    """Read generated archive, never invoke MATLAB; full gate/feedback provenance."""
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    with ZipFile(model) as archive:
        system = ET.fromstring(archive.read("simulink/systems/system_root.xml"))
        charts = [ET.fromstring(archive.read(member)) for member in archive.namelist()
                  if member.startswith("simulink/stateflow/chart_") and member.endswith(".xml")]
    blocks = {b.get("Name"): b for b in system.findall("Block")}
    edges = {(prop(line, "Src"), p.text) for line in system.findall("Line")
             for p in line.iter("P") if p.get("Name") == "Dst"}
    def edge(source, target, port=1):
        return (blocks[source].get("SID")+"#out:1", blocks[target].get("SID")+"#in:"+str(port)) in edges
    for source, target, port in [
        ("Scenario_Input", "Verified_HP_Component", 1),
        ("Verified_HP_Component", "Thermal_Dispatch", 1),
        ("TES_Energy_Memory", "Verified_HP_Component", 2),
        ("TES_Energy_Memory", "Thermal_Dispatch", 2),
        ("TES_and_Boiler_Parameters", "Verified_HP_Component", 3),
        ("TES_and_Boiler_Parameters", "Thermal_Dispatch", 3),
        ("HP_Parameters", "Verified_HP_Component", 4),
        ("Integration_Step", "Verified_HP_Component", 5),
        ("Integration_Step", "Runtime_Contract_Gate", 5),
        ("Thermal_Dispatch", "Runtime_Contract_Gate", 1),
        ("Verified_HP_Component", "Runtime_Contract_Gate", 2),
        ("TES_Energy_Memory", "Runtime_Contract_Gate", 3),
        ("TES_and_Boiler_Parameters", "Runtime_Contract_Gate", 4),
        ("Runtime_Contract_Gate", "Next_TES_Energy", 1),
        ("Runtime_Contract_Gate", "Dispatch_Trace", 1),
        ("Next_TES_Energy", "TES_Energy_Memory", 1),
        ("Verified_HP_Component", "HP_Trace", 1),
        ("TES_Energy_Memory", "Energy_Start_Trace", 1)]:
        check(source+"_to_"+target+"_port_"+str(port), edge(source, target, port))
    check("no_unchecked_chart_bypass", {dst for src, dst in edges if src ==
          blocks["Thermal_Dispatch"].get("SID")+"#out:1"} ==
          {blocks["Runtime_Contract_Gate"].get("SID")+"#in:1"})
    check("UnitDelay_stores_next_energy_index_8", blocks["TES_Energy_Memory"].get("BlockType") ==
          "UnitDelay" and prop(blocks["Next_TES_Energy"], "Indices") == "8")
    check("initial_energy_configurable", prop(blocks["TES_Energy_Memory"], "InitialCondition") == "dchr_E0_v28")
    check("physical_clock_constant", prop(blocks["Integration_Step"], "Value") == "dchr_dt_v28")
    check("input_interpolation_disabled", prop(blocks["Scenario_Input"], "Interpolate") == "off")
    dispatch = [c for c in charts if prop(c, "name") == "Thermal_Dispatch"]
    check("single_actual_operational_chart", len(dispatch) == 1)
    if len(dispatch) != 1:
        return result(checks)
    chart = dispatch[0]
    check("common_discrete_sample_time", prop(chart, "updateMethod") == "DISCRETE" and
          prop(chart, "sampleTime") == prop(blocks["TES_Energy_Memory"], "SampleTime") ==
          prop(blocks["Scenario_Input"], "SampleTime") == "dchr_dt_v28")
    children = chart.find("Children")
    states = [s for s in children.findall("state") if prop(s, "type") == "OR_STATE"]
    state_modes = {}
    for state in states:
        label = prop(state, "labelString")
        name = label.splitlines()[0]
        if name in MODES.values():
            mode = next(m for m in MODES if MODES[m] == name)
            state_modes[state.get("SSID")] = mode
            check(name+"_entry_during_execute_allocator", label ==
                  name+"\nen,du:\ny=stateflow_allocate_v28("+str(mode)+",u,E,p);")
    check("six_required_actual_states", len(states) == len(state_modes) == 6)
    transitions = children.findall("transition")
    actual, initial, default = set(), set(), []
    for t in transitions:
        src, dst = prop(t.find("src"), "SSID"), prop(t.find("dst"), "SSID")
        guard = prop(t, "labelString")
        if dst in state_modes:
            check("destination_guard_"+t.get("SSID"), guard ==
                  "[stateflow_choose_mode_v28(u,E,p)=="+str(state_modes[dst])+"]")
            if src in state_modes:
                actual.add((state_modes[src], state_modes[dst]))
            else:
                initial.add((src, state_modes[dst]))
        elif not src:
            default.append((dst, guard))
    check("all_30_guarded_mode_changes", actual == {(a, b) for a in MODES for b in MODES if a != b})
    check("six_guarded_startup_choices", len(initial) == 6 and {m for _, m in initial} == set(MODES)
          and len({s for s, _ in initial}) == 1)
    check("one_default_into_initial_junction", len(default) == 1 and default[0][1] == "" and
          {default[0][0]} == {s for s, _ in initial} and len(transitions) == 37)
    for helper in ("stateflow_choose_mode_v28", "stateflow_allocate_v28", "stateflow_contract_gate_v28"):
        scripts = [prop(e, "script") for c in charts for e in c.iter("eml")
                   if helper in prop(e, "script").partition("\n")[0]]
        source = (model.parent/(helper+".m")).read_text(encoding="utf-8")
        check("embedded_"+helper+"_equals_reviewed_source", len(scripts) == 1 and scripts[0] == source)
    hp = [c for c in charts if prop(c, "name") == "Verified_HP_Component"]
    check("single_host_HP_adapter", len(hp) == 1)
    check("versioned_host_HP_adapter_receives_clock", len(hp) == 1 and any(
          "u=dchr_stateflow_hp_v28(x,E,p,h,model_dt);" in prop(e, "script") and
          "coder.extrinsic('dchr_stateflow_hp_v28');" in prop(e, "script") for e in hp[0].iter("eml")))
    return result(checks)


def verify_integrity(summary_path, model, vectors, spec, trace, experiments):
    """Tie reported acceptance counts and reviewed sources to immutable run files."""
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    directory = summary_path.parent
    checks, hashes = [], {}
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    check("acceptance_version_is_v28", summary.get("version") == "0.28")
    check("actual_simulink_and_stateflow_execution_declared", summary.get("simulink_executed") is True and
          summary.get("stateflow_executed") is True)
    check("no_unjustified_validation_or_codegen_claim", summary.get("primary_paper_replication") is False and
          summary.get("equipment_validation") is False and summary.get("standalone_codegen") is False)
    check("reported_all_acceptance_checks_pass", summary.get("failed") == 0 and
          summary.get("passed") == summary.get("checks") and summary.get("checks", 0) > 0)
    for filename, counts in [("stateflow_assertions_v28.csv", summary),
                             ("storage_experiment_assertions_v28.csv", summary.get("loss_experiments", {}))]:
        path = directory/filename
        assertions = read_csv(path)
        passed = sum(str(r.get("passed", "")).lower() in ("1", "true") for r in assertions)
        check(filename+"_reported_counts_match_saved_assertions", len(assertions) == counts.get("checks") and
              passed == counts.get("passed") and len(assertions)-passed == counts.get("failed") == 0)
        check(filename+"_assertion_names_unique", len({r.get("name") for r in assertions}) == len(assertions))
        hashes[filename] = sha(path)
    if trace is not None:
        rows = read_csv(trace)
        check("actual_trace_count_matches_acceptance_summary", len(rows) == summary.get("intervals") and
              len({r["scenario_id"] for r in rows}) == summary.get("scenarios"))
        check("actual_trace_modes_match_acceptance_summary", sorted({int(number(r, "Mode")) for r in rows}) ==
              summary.get("modes_observed") == list(MODES))
    if experiments is not None:
        rows = read_csv(experiments)
        check("actual_experiments_count_matches_acceptance_summary", len(rows) ==
              summary.get("loss_experiments", {}).get("cases"))
        check("actual_timestep_design_matches_acceptance_summary", sorted({number(r, "dt_h") for r in rows}) ==
              sorted(summary.get("loss_experiments", {}).get("dt_values_h", [])))
    snapshot = directory/"source_snapshot"
    source_files = list((HERE.parent/"matlab"/"simulink").glob("*v28.m"))
    source_files += list((HERE.parent/"matlab"/"+dchr").glob("*v28.m"))
    source_files += list((HERE.parent/"matlab"/"+dchr"/"+components").glob("*v28.m"))
    source_files += [vectors, spec, HERE/"dispatch_reference_vectors_v18.csv"]
    for source in source_files:
        copied = snapshot/source.name
        check("source_snapshot_matches_reviewed_"+source.name, copied.is_file() and sha(copied) == sha(source))
        if copied.is_file():
            hashes["source_snapshot/"+source.name] = sha(copied)
    old_model = HERE.parent/"matlab"/"simulink"/"DCHR_Dispatch_Stateflow_v24.slx"
    check("preserved_v24_model_hash_unchanged", sha(old_model) ==
          "1f1c826f0f61d04bea58c2ab39d607268ac273bad9564e69bec89e361c461389")
    hashes["preserved_model_v24"] = sha(old_model)
    hashes["new_model_v28"] = sha(model) if model is not None else None
    output = result(checks)
    output["evidence_sha256"] = hashes
    return output


def selftest():
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    refs = generate_vectors()
    traces = [{**r, **{k[9:]: v for k, v in r.items() if k.startswith("expected_")}} for r in refs]
    check("synthetic_exp_vectors_verify", verify_trace(traces, refs)["failed"] == 0)
    for field in ("Mode", "HP_Source_Used_MW", "Storage_E_After_Loss_MWh",
                  "Storage_E_Next_MWh", "Storage_Standing_Loss_MWh", "Gas_Heat_MW"):
        broken = copy.deepcopy(traces)
        broken[0][field] = number(broken[0], field)+.2
        check("reject_synthetic_corruption_"+field, verify_trace(broken, refs)["failed"] > 0)
    check("reject_missing_actual_interval", verify_trace(traces[:-1], refs)["failed"] > 0)
    check("reject_duplicate_actual_interval", verify_trace(traces+traces[:1], refs)["failed"] > 0)
    # Supply a separately recognized supplemental interval, then delete only
    # that interval. Keeping every fixed-COP vector must not mask missing
    # supplemental evidence. These rows are synthetic reviewer fixtures.
    supplemental_source = {**refs[0], "scenario_id": "synthetic_supplemental",
                           "loss_fraction_per_h": refs[0]["continuous_loss_rate_per_h"]}
    supplemental_trace = {**traces[0], "scenario_id": "legacy_input_synthetic_supplemental"}
    check("synthetic_complete_supplemental_evidence_verifies", verify_trace(
        traces+[supplemental_trace], refs, [supplemental_source])["failed"] == 0)
    check("reject_missing_supplemental_interval", verify_trace(
        traces, refs, [supplemental_source])["failed"] > 0)
    hand = config(storage_capacity_MWh=20., charge_limit_MW=4., discharge_limit_MW=3.,
                  Source_Heat_MW=3.75, Heat_Demand_MW=1.)
    out = fixed_cop_oracle(hand, 10.)
    check("independent_hand_charge_state", near(out["Storage_E_Next_MWh"], 10*math.exp(-.005)+1.8))
    check("independent_hand_charge_loss", near(out["Storage_Charge_Loss_MWh"], .2))
    out = fixed_cop_oracle({**hand, "Source_Heat_MW": 0., "Heat_Demand_MW": 4.}, 10.)
    check("independent_hand_backup_discharge_state", near(out["Storage_E_Next_MWh"], 10*math.exp(-.005)-1.875)
          and out["Mode"] == 4 and out["Storage_Discharge_MW"] == 3 and out["Gas_Heat_MW"] == 1)
    check("passive_semigroup_hand", near(10*math.exp(-.2*2), 10*math.exp(-.2)**2))
    check("legacy_partition_discrepancy_hand", near(10*(1-.2*2), 6.) and near(10*(1-.2)**2, 6.4))
    check("zero_rate_continuous_limit", exact_constant_input(2., 0., 2., 2.7) == 7.4)
    errors = [closed_form_split(2., .2, 2., 2.7, dt, SCHEME)-exact_constant_input(2., .2, 2., 2.7)
              for dt in (2., 1., .5, .25)]
    check("charging_split_overestimate_refines", all(e > 0 for e in errors) and
          all(a > b for a, b in zip(errors, errors[1:])))
    # Independent hand scenario, with file I/O mocked rather than synthetic
    # files being mistaken for actual model traces. Each accepted/corrupt test
    # exercises the same per-sample reviewer used on real evidence later.
    from unittest.mock import patch
    synthetic_row = dict(scenario_id="synthetic_passive", scheme=SCHEME, dt_h="1",
        lambda_per_h="0.2", horizon_h="2", initial_MWh="10", charge_internal_MW="0",
        terminal_MWh=str(10*math.exp(-.4)), exact_continuous_MWh=str(10*math.exp(-.4)),
        trace_file="synthetic_only.csv", intervals="2")
    synthetic_samples = []
    state = 10.
    for index in range(2):
        end = 10*math.exp(-.2*(index+1))
        synthetic_samples.append(dict(Time_h=index, Mode=0, Charge_MW=0, Discharge_MW=0,
                                      After_MWh=end, Next_MWh=end, Standing_Loss_MWh=state-end, Residual_MWh=0))
        state = end
    def review_fixture(samples, rows):
        with patch(__name__+".read_csv", return_value=samples), patch(__name__+".sha", return_value="synthetic_only"):
            return verify_experiments(rows, HERE)
    check("synthetic_experiment_series_verifies", review_fixture(synthetic_samples, [synthetic_row])["failed"] == 0)
    for field in ("Time_h", "Mode", "Charge_MW", "Discharge_MW", "After_MWh", "Next_MWh", "Standing_Loss_MWh", "Residual_MWh"):
        broken = copy.deepcopy(synthetic_samples)
        broken[0][field] += .25
        check("reject_synthetic_experiment_series_"+field, review_fixture(broken, [synthetic_row])["failed"] > 0)
    check("reject_missing_experiment_series_interval", review_fixture(synthetic_samples[:-1], [synthetic_row])["failed"] > 0)
    wrong_terminal = {**synthetic_row, "terminal_MWh": "0"}
    check("reject_experiment_terminal_csv_corruption", review_fixture(synthetic_samples, [wrong_terminal])["failed"] > 0)
    rng = random.Random(28009)
    worst = 0.
    for index in range(500):
        cfg = config(dt_h=rng.choice([.05, .25, .5, 2.]), storage_capacity_MWh=rng.uniform(.1, 30),
            charge_limit_MW=rng.uniform(0, 8), discharge_limit_MW=rng.uniform(0, 8),
            eta_charge=rng.uniform(.3, 1), eta_discharge=rng.uniform(.3, 1),
            continuous_loss_rate_per_h=rng.uniform(0, 5), boiler_capacity_MW=rng.uniform(0, 10),
            hp_capacity_MW=rng.uniform(0, 15), Source_Heat_MW=rng.uniform(0, 20), Heat_Demand_MW=rng.uniform(0, 30))
        energy = rng.uniform(0, cfg["storage_capacity_MWh"])
        out = fixed_cop_oracle(cfg, energy)
        residual = (energy+(out["HP_Source_Used_MW"]+out["HP_Electric_MW"]+out["Gas_Heat_MW"]-
                    out["Supplied_Heat_MW"])*cfg["dt_h"]-out["Storage_E_Next_MWh"]-
                    sum(out[name] for name in ("Storage_Standing_Loss_MWh", "Storage_Charge_Loss_MWh", "Storage_Discharge_Loss_MWh")))
        worst = max(worst, abs(residual))
        check("random_first_law_SOC_"+str(index), abs(residual) < 1e-10 and
              -1e-10 <= out["Storage_E_Next_MWh"] <= cfg["storage_capacity_MWh"]+1e-10)
        less_rate = fixed_cop_oracle({**cfg, "continuous_loss_rate_per_h": 0.}, energy)
        check("random_increased_loss_cannot_improve_unmet_"+str(index),
              out["Unmet_Heat_MW"]+1e-10 >= less_rate["Unmet_Heat_MW"])
    output = result(checks)
    output.update(synthetic_only=True, randomized_algebraic_cases=500, seed=28009,
                  vector_intervals=len(refs), vector_scenarios=len({r["scenario_id"] for r in refs}),
                  max_abs_random_residual_MWh=worst)
    return output


def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generate-vectors", action="store_true")
    parser.add_argument("--vectors", type=Path, default=HERE/"stateflow_qa_vectors_v28.csv")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--supplemental-vectors", type=Path, default=HERE/"dispatch_reference_vectors_v18.csv")
    parser.add_argument("--experiments", type=Path)
    parser.add_argument("--model", type=Path)
    parser.add_argument("--summary", type=Path)
    parser.add_argument("--spec", type=Path, default=HERE/"stateflow_domain_cases_v28.json")
    parser.add_argument("--rejections", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    output = dict(version="0.28", timestamp_utc=datetime.now(timezone.utc).isoformat(),
        scheme=SCHEME, rate_semantics="continuous inverse-hour decay coefficient, not hourly fraction",
        primary_paper_replication=False, equipment_validation=False, verifier_sha256=sha(__file__))
    if args.generate_vectors:
        vectors = generate_vectors()
        with args.vectors.open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(vectors[0]))
            writer.writeheader()
            writer.writerows(vectors)
        output["vectors_sha256"] = sha(args.vectors)
    if args.self_test:
        output["self_test"] = selftest()
        from verify_stateflow_runtime_v24 import self_test as rejection_self_test
        output["generic_rejection_schema_self_test"] = rejection_self_test(
            json.loads(args.spec.read_text(encoding="utf-8")))
        output["generic_rejection_schema_self_test"]["synthetic_only"] = True
    if args.trace:
        output["trace_qa"] = verify_trace(read_csv(args.trace), read_csv(args.vectors),
                                         read_csv(args.supplemental_vectors))
        output["trace_sha256"], output["vectors_sha256"] = sha(args.trace), sha(args.vectors)
        output["supplemental_input_metadata_sha256"] = sha(args.supplemental_vectors)
    if args.experiments:
        output["experiments_qa"] = verify_experiments(read_csv(args.experiments), args.experiments.parent)
        output["experiments_sha256"] = sha(args.experiments)
    if args.model:
        output["structure"] = verify_structure(args.model)
        output["model_sha256"] = sha(args.model)
        output["reviewed_source_sha256"] = {p.name: sha(p) for p in args.model.parent.glob("*v28.m")}
    if args.rejections:
        # Pure evidence-schema logic has no TES equations or Stateflow execution.
        from verify_stateflow_runtime_v24 import verify_rejections
        output["runtime_rejections"] = verify_rejections(json.loads(args.spec.read_text(encoding="utf-8")),
                                                         json.loads(args.rejections.read_text(encoding="utf-8")))
        output["reused_generic_rejection_verifier"] = "audit/verify_stateflow_runtime_v24.py:verify_rejections only"
        output["reused_generic_rejection_verifier_sha256"] = sha(HERE/"verify_stateflow_runtime_v24.py")
        output["rejections_sha256"], output["domain_spec_sha256"] = sha(args.rejections), sha(args.spec)
    if args.summary:
        output["acceptance_integrity"] = verify_integrity(args.summary, args.model, args.vectors,
                                                         args.spec, args.trace, args.experiments)
        output["acceptance_summary_sha256"] = sha(args.summary)
    output["failed"] = sum(v.get("failed", 0) for v in output.values() if isinstance(v, dict))
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: ({q: w for q, w in v.items() if q != "assertions"} if isinstance(v, dict) else v)
                      for k, v in output.items()}, indent=2, allow_nan=False))
    raise SystemExit(bool(output["failed"]))


if __name__ == "__main__":
    main()
