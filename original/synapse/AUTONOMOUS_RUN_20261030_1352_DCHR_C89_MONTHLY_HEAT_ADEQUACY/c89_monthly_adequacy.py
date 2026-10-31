"""C89: independent monthly dispatch/adequacy report from C88 native MATLAB synthetic CSV.
No model changes, field validation, electricity-price claims or source signoffs.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PROJECT = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
SOURCE = ROOT / "recovery" / "AUTONOMOUS_RUN_20261030_1254_DCHR_C88_NATIVE_MATLAB_REPLAY" / "Warm45_Storage100_v2_MATLAB_NATIVE.csv"
SOURCE_SHA = "07d1d7f19d92ce34d5b3e5a44a2131234a4a2e7991e21f018b197137ed0eb370"
FLAGS = ("STOP", "PAUSE", "STOP.flag", "PAUSE.flag", "STOP.txt", "PAUSE.txt", ".STOP", ".PAUSE")
METRICS = ("Heat_Demand_MW", "Gas_Heat_MW", "HP_Heat_Used_MW", "HP_Electric_MW",
           "HP_Heat_MW", "Source_Heat_Available_MW", "HP_Source_Used_MW",
           "Storage_Charge_MW", "Storage_Discharge_MW", "Storage_E_MWh", "COP")
MONTHS = ("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def guard():
    for root in (ROOT, ROOT / "recovery", PROJECT, HERE):
        for flag in FLAGS:
            if (root / flag).exists():
                raise RuntimeError("STOP_PAUSE_PRESENT " + str(root / flag))

def require(ok, msg):
    if not ok:
        raise AssertionError(msg)

def parse(text):
    reader = csv.DictReader(io.StringIO(text))
    require(reader.fieldnames is not None and len(reader.fieldnames) == 23, "schema")
    require(all(k in reader.fieldnames for k in METRICS), "required_columns")
    out = []
    previous = None
    for i, row in enumerate(reader):
        t = dt.datetime.strptime(row["Time"], "%d-%b-%Y %H:%M:%S")
        if previous is not None:
            require(t - previous == dt.timedelta(hours=1), f"hourly_continuity_{i}")
        previous = t
        v = {k: float(row[k]) for k in METRICS}
        require(all(math.isfinite(x) for x in v.values()), f"nonfinite_{i}")
        require(all(v[k] >= -1e-8 for k in METRICS if k != "COP"), f"negative_flow_{i}")
        require(v["COP"] > 0 and v["Heat_Demand_MW"] > 0, f"positive_cop_demand_{i}")
        require(abs(v["Gas_Heat_MW"] + v["HP_Heat_Used_MW"] -
                    v["Storage_Charge_MW"] + v["Storage_Discharge_MW"] -
                    v["Heat_Demand_MW"]) < 2e-8, f"balance_{i}")
        out.append((t, v))
    return out

def summarize(rows):
    require(bool(rows), "nonempty")
    sums = {k: sum(v[k] for _, v in rows) for k in METRICS}
    demand = sums["Heat_Demand_MW"]
    gas = sums["Gas_Heat_MW"]
    require(demand > 0 and -1e-7 <= gas <= demand + 1e-7, "gas_fraction_contract")
    peak_t, peak = max(rows, key=lambda item: item[1]["Gas_Heat_MW"])
    return {
        "hours": len(rows),
        "demand_MWh": round(demand, 6),
        "gas_heat_MWh": round(gas, 6),
        "hp_electric_MWh": round(sums["HP_Electric_MW"], 6),
        "hp_heat_used_MWh": round(sums["HP_Heat_Used_MW"], 6),
        "source_heat_available_MWh": round(sums["Source_Heat_Available_MW"], 6),
        "hp_source_used_MWh": round(sums["HP_Source_Used_MW"], 6),
        "storage_charge_MWh": round(sums["Storage_Charge_MW"], 6),
        "storage_discharge_MWh": round(sums["Storage_Discharge_MW"], 6),
        "gas_fraction_of_heat_demand_pct": round(100 * gas / demand, 3),
        "non_gas_fraction_of_heat_demand_pct": round(100 * (demand - gas) / demand, 3),
        "hours_gas_needed": sum(v["Gas_Heat_MW"] > 1e-7 for _, v in rows),
        "hours_storage_active": sum(v["Storage_Charge_MW"] > 1e-7 or v["Storage_Discharge_MW"] > 1e-7 for _, v in rows),
        "max_gas_MW": round(peak["Gas_Heat_MW"], 6),
        "max_gas_time": peak_t.isoformat(),
        "cop_min": round(min(v["COP"] for _, v in rows), 4),
        "cop_max": round(max(v["COP"] for _, v in rows), 4),
        "cop_median": round(statistics.median(v["COP"] for _, v in rows), 4)
    }

def make_report(rows):
    require(len(rows) == 8760, "annual_length")
    require(rows[0][0] == dt.datetime(2026, 1, 1) and rows[-1][0] == dt.datetime(2026, 12, 31, 23), "annual_coverage")
    months = []
    for month in range(1, 13):
        subset = [(t, v) for t, v in rows if t.month == month]
        require(bool(subset), "missing_month")
        months.append({"month": f"2026-{month:02d}", **summarize(subset)})
    annual = summarize(rows)
    for k in ("demand_MWh", "gas_heat_MWh", "hp_electric_MWh", "hp_heat_used_MWh"):
        require(abs(sum(m[k] for m in months) - annual[k]) < 1e-4, "monthly_reconciliation_" + k)
    require(abs(annual["gas_heat_MWh"] - 10542.548227789) < 0.001, "native_gas_oracle")
    require(abs(annual["hp_electric_MWh"] - 7969.875645451) < 0.001, "native_electric_oracle")
    return {"schema": "C89_MONTHLY_ADEQUACY_V1", "synthetic": True,
            "source_sha256": SOURCE_SHA, "stateflow_v85_parity": False,
            "physical_field_validation": False, "primary_sources_signed": 0,
            "interpretation": "Non-gas heat share is demand minus gas; not the DC-only share and not a carbon or cost estimate.",
            "annual": annual, "months": months}

def selftest():
    t = dt.datetime(2026, 1, 1)
    v = {k: 0.0 for k in METRICS}
    v.update(Heat_Demand_MW=10.0, Gas_Heat_MW=3.0, HP_Heat_Used_MW=7.0,
             HP_Electric_MW=2.0, COP=3.5)
    assert summarize([(t, v)])["non_gas_fraction_of_heat_demand_pct"] == 70.0
    assert summarize([(t, v)])["hours_gas_needed"] == 1
    bad = dict(v, Gas_Heat_MW=4.0)
    header = ["Time"] + list(METRICS) + [f"other{i}" for i in range(11)]
    def make_line(x):
        return ",".join([t.strftime("%d-%b-%Y %H:%M:%S")] + [str(x[k]) for k in METRICS] + ["0"] * 11)
    try:
        parse(",".join(header) + "\n" + make_line(bad) + "\n")
        raise AssertionError("tamper_not_detected")
    except AssertionError as exc:
        assert "balance" in str(exc)
    try:
        parse(",".join(header) + "\n" + make_line(v) + "\n" + make_line(v) + "\n")
        raise AssertionError("duplicate_time_not_detected")
    except AssertionError as exc:
        assert "hourly_continuity" in str(exc)
    return 4

def main():
    import sys
    if "--selftest" in sys.argv:
        print("C89_SELFTEST_PASS", selftest())
        return
    guard()
    require(SOURCE.exists() and sha(SOURCE) == SOURCE_SHA, "source_sha_gate")
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = parse(f.read())
    report = make_report(rows)
    outputs = [HERE / "C89_MONTHLY_ADEQUACY.json", HERE / "C89_MONTHLY_ADEQUACY.csv", HERE / "C89_FINDINGS.md"]
    require(not any(p.exists() for p in outputs), "output_exists")
    guard()
    outputs[0].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    keys = ["month","hours","demand_MWh","gas_heat_MWh","hp_electric_MWh","gas_fraction_of_heat_demand_pct","non_gas_fraction_of_heat_demand_pct","hours_gas_needed","hours_storage_active","max_gas_MW","cop_min","cop_max"]
    with outputs[1].open("x", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(report["months"])
    a = report["annual"]
    worst = max(report["months"], key=lambda m: m["gas_fraction_of_heat_demand_pct"])
    lines = ["# C89 | Synthetic annual heat adequacy and monthly dispatch",
             "", "Native MATLAB R2026a C88 dataset; 8760 synthetic hours, seed 42. Not field-validated.",
             f"Input SHA256: `{SOURCE_SHA}`", "",
             f"Annual demand: {a['demand_MWh']:.1f} MWh; gas backup: {a['gas_heat_MWh']:.1f} MWh.",
             f"Non-gas share of heat demand: {a['non_gas_fraction_of_heat_demand_pct']:.2f}%; gas share: {a['gas_fraction_of_heat_demand_pct']:.2f}%.",
             f"Gas required in {a['hours_gas_needed']} of {a['hours']} hours; maximum gas: {a['max_gas_MW']:.2f} MW at {a['max_gas_time']}.",
             f"Worst gas-share month: {worst['month']} ({worst['gas_fraction_of_heat_demand_pct']:.2f}%).",
             f"Storage active in {a['hours_storage_active']} hours. HP electricity: {a['hp_electric_MWh']:.1f} MWh.",
             "", "## Interpretation and gates",
             "Non-gas fraction is NOT solely recovered data-center heat: heat-pump electricity and storage are included in the system.",
             "The scenario still requires gas backup. It cannot establish actual pool-heating adequacy without a separate pool-load profile.",
             "No Stateflow v85 parity, measured thermal data, prices, emissions, standards or primary-source signoffs verified.",
             "Next: reconcile a standard 500 m3 pool load, temperature/loss assumptions and heat-pump electricity with cited field data.",
             ""]
    outputs[2].write_text("\n".join(lines), encoding="utf-8")
    guard()
    print(json.dumps({"status": "PASS", "selftest": selftest(), "hours": len(rows),
        "annual": a, "worst_month": worst["month"],
        "outputs": {p.name: sha(p) for p in outputs}}, ensure_ascii=False))

if __name__ == "__main__":
    main()
