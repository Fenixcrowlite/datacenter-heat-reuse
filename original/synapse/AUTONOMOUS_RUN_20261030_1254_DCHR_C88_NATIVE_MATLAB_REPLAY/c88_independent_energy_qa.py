"""Independent annual thermodynamic/energy checks of C88 native MATLAB CSV.

This is synthetic scenario QA, NOT validation against measured field data,
Stateflow parity, or approval of physical assumptions.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCC = HERE.parents[1]
PROJECT = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
CSV = HERE / "Warm45_Storage100_v2_MATLAB_NATIVE.csv"
REPORT = HERE / "C40_NATIVE_EXPORT_RESULT.json"
PARITY = HERE / "C40_NATIVE_PARITY_RESULT.json"
FLAGS = ("STOP", "STOP.txt", "STOP.flag", "PAUSE", "PAUSE.txt", "PAUSE.flag", ".STOP", ".PAUSE")
NUMERIC = ("Heat_Demand_MW", "Gas_Heat_MW", "HP_Heat_Used_MW", "Storage_Charge_MW",
           "Storage_Discharge_MW", "Source_Heat_Available_MW", "HX_Heat_to_HP_MW",
           "HX_Rejected_MW", "HP_Electric_MW", "HP_Source_Used_MW", "Storage_E_MWh",
           "HP_Heat_MW", "Curtailed_HP_Heat_MW", "COP")
checks = []
MAX_TOL = 2e-8
CAP = 100.0
ETA_C = 0.95
ETA_D = 0.95
LOSS = 1e-4

def require(cond, label):
    if not cond:
        raise AssertionError(label)
    checks.append(label)

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1048576), b""):
            h.update(b)
    return h.hexdigest()

def stop_gate():
    for root in (SCC, SCC / "recovery", PROJECT, HERE):
        for flag in FLAGS:
            if (root / flag).exists():
                raise RuntimeError("STOP_OR_PAUSE_ACTIVE " + str(root / flag))

def main():
    stop_gate()
    require(CSV.is_file() and REPORT.is_file() and PARITY.is_file(), "native_csv_report_parity_exist")
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    parity = json.loads(PARITY.read_text(encoding="utf-8"))
    require(report["synthetic_data"] is True and report["stateflow_v85_parity"] is False and report["physical_validation"] is False, "synthetic_disclaimer")
    require(parity["candidate_sha256"] == sha(CSV) and parity["hours"] == 8760 and parity["numeric_comparisons"] == 192720, "native_parity_receipt")
    require(parity["max_absolute_error"] < 2e-8, "matlab_python_numeric_parity")
    with CSV.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        require(len(reader.fieldnames) == 23 and reader.fieldnames[0] == "Time", "schema_23_columns")
        rows = list(reader)
    require(len(rows) == 8760, "8760_hourly_rows")
    totals = {"gas_MWh": 0.0, "hp_electric_MWh": 0.0, "heat_demand_MWh": 0.0}
    errors = {"heat_balance": 0.0, "hx_balance": 0.0, "hp_source_balance": 0.0, "storage_recurrence": 0.0}
    prev_t = None
    prev_e = None
    prev_ch = None
    prev_dis = None
    for i, row in enumerate(rows):
        t = dt.datetime.strptime(row["Time"], "%d-%b-%Y %H:%M:%S")
        if prev_t is not None and t - prev_t != dt.timedelta(hours=1):
            raise AssertionError(f"NON_HOURLY_TIME at {i}")
        prev_t = t
        v = {k: float(row[k]) for k in NUMERIC}
        if not all(math.isfinite(x) for x in v.values()):
            raise AssertionError(f"NONFINITE at {i}")
        gas, hp, charge, discharge, demand = (v["Gas_Heat_MW"], v["HP_Heat_Used_MW"],
                                                v["Storage_Charge_MW"], v["Storage_Discharge_MW"],
                                                v["Heat_Demand_MW"])
        if min(gas, hp, charge, discharge, demand, v["HP_Electric_MW"], v["Curtailed_HP_Heat_MW"]) < -1e-9:
            raise AssertionError(f"NEGATIVE_FLOW at {i}")
        if charge > 5.0 + 1e-9 or discharge > 5.0 + 1e-9 or charge * discharge > 1e-9:
            raise AssertionError(f"STORAGE_POWER_CONTRACT at {i}")
        e = v["Storage_E_MWh"]
        if not (-1e-9 <= e <= CAP + 1e-9):
            raise AssertionError(f"STORAGE_CAPACITY at {i}")
        if v["COP"] <= 0 or hp > v["HP_Heat_MW"] + 1e-8:
            raise AssertionError(f"HP_CONTRACT at {i}")
        heat_balance = abs(gas + hp - charge + discharge - demand)
        hx_balance = abs(v["Source_Heat_Available_MW"] - v["HX_Heat_to_HP_MW"] - v["HX_Rejected_MW"])
        source_balance = abs(hp - v["HP_Electric_MW"] - v["HP_Source_Used_MW"])
        errors["heat_balance"] = max(errors["heat_balance"], heat_balance)
        errors["hx_balance"] = max(errors["hx_balance"], hx_balance)
        errors["hp_source_balance"] = max(errors["hp_source_balance"], source_balance)
        if prev_e is not None:
            expected_e = max(0.0, prev_e * (1.0 - LOSS))
            expected_e = expected_e + ETA_C * prev_ch - prev_dis / ETA_D
            storage_err = abs(e - expected_e)
            errors["storage_recurrence"] = max(errors["storage_recurrence"], storage_err)
        prev_e, prev_ch, prev_dis = e, charge, discharge
        totals["gas_MWh"] += gas
        totals["hp_electric_MWh"] += v["HP_Electric_MW"]
        totals["heat_demand_MWh"] += demand
    require(all(e <= MAX_TOL for e in errors.values()), "four_independent_energy_balances")
    require(abs(totals["gas_MWh"] - report["gas_MWh"]) < 1e-6, "gas_annual_oracle")
    require(abs(totals["hp_electric_MWh"] - report["hp_electric_MWh"]) < 1e-6, "electric_annual_oracle")
    require(prev_t == dt.datetime(2026, 12, 31, 23), "annual_time_coverage")
    require(rows[0]["Time"] == "01-Jan-2026 00:00:00", "deterministic_start")
    # Deliberate tamper in-memory, confirming the heat-balance equation is not vacuous.
    x = rows[0]
    tampered = float(x["Gas_Heat_MW"]) + 0.1 + float(x["HP_Heat_Used_MW"]) - float(x["Storage_Charge_MW"]) + float(x["Storage_Discharge_MW"]) - float(x["Heat_Demand_MW"])
    require(abs(tampered) > 0.09, "negative_heat_balance_test")
    stop_gate()
    require(True, "final_stop_pause_gate")
    out = {"status": "PASS", "checks": len(checks), "passed": checks,
           "scenario": "Warm45_Storage100", "source": "native MATLAB R2026a CSV, synthetic input seed=42",
           "hours": len(rows), "numeric_parity_comparisons": parity["numeric_comparisons"],
           "max_matlab_python_delta": parity["max_absolute_error"],
           "max_energy_balance_residual_MW": errors, "totals_MWh": totals,
           "native_csv_sha256": sha(CSV),
           "limitations": "No Stateflow parity, measured weather, source-signoff, economic calibration or independent field validation."}
    with (HERE / "C88_INDEPENDENT_ENERGY_QA.json").open("x", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps(out, ensure_ascii=False))

if __name__ == "__main__":
    main()
