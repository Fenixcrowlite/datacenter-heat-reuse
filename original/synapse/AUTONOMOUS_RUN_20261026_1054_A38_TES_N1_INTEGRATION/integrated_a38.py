"""A38: isolated synthetic TES + REJECT N-1 + IT thermal coupled reference.
Does NOT actuate hardware, run MATLAB, alter SCADA, or certify Stateflow.
Frozen HP COP and 1:1 IT shedding -> rejected-heat reduction are hypotheses.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A36 = ROOT / "AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"
A37 = ROOT / "AUTONOMOUS_RUN_20261026_1025_A37_DCHR_IT_THERMAL_PROTECTION"
A37B = ROOT / "AUTONOMOUS_RUN_20261026_1037_A37B_DCHR_TES_SOC_REDIRECT"
sys.path.insert(0, str(A37))
sys.path.insert(0, str(A37B))
import tes_soc
import thermal_n1
import run_a37

FIELDS = [
    "cas_h", "capacity_W", "Q_DC_eff_W", "Q_HX_W", "Q_HP_source_W",
    "Q_leak_W", "Q_reject_required_W", "Q_reject_actual_W",
    "Q_unhandled_W", "Q_IT_shed_W", "Q_DC_after_shed_W",
    "T_IT_start_C", "T_IT_next_C", "passive_W", "alarm_next",
    "E_TES_start_J", "E_TES_next_J", "TES_SOC_next",
    "Q_TES_charge_actual_W", "Q_TES_charge_curtailed_W",
    "P_HP_proxy_W", "TES_residual_J", "DC_residual_W", "HP_residual_W",
]
LIMITS = {
    "physical_release_allowed": False,
    "matlab_stateflow_executed": False,
    "hardware_control": False,
    "real_equipment_certified": False,
    "assumptions": [
        "synthetic v08 demand; v04 TES parameters; v07 IT thermal recurrence",
        "HP COP proxy fixed by baseline interval, not a part-load curve",
        "IT shed reduces only REJECT demand 1:1; other heat branches frozen",
        "TES corrected without feedback from IT shedding or equipment dynamics",
        "hypothetical REJECT 180/150 kW and hypothetical 40%/15kW shedding",
        "no controller response delay, pump/fan power, pool or district dynamics",
    ],
}

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_manifest(folder: Path, filename: str) -> None:
    manifest = json.loads((folder / "SHA256_MANIFEST.json").read_text(encoding="utf8"))
    expected = manifest.get(filename)
    if not isinstance(expected, str) or sha(folder / filename) != expected:
        raise RuntimeError("UPSTREAM_SHA_MISMATCH: " + str(folder / filename))

def checked_sources():
    check_manifest(A37, "thermal_n1.py")
    check_manifest(A37B, "tes_soc.py")
    raw, dispatch, source_csv = tes_soc.load()  # checks v04, v08, A36 source SHA
    legacy, _, source_a37 = run_a37.read_inputs()  # checks v07 and A36 provenance
    if source_csv.resolve() != source_a37.resolve():
        raise RuntimeError("UPSTREAM_A36_MISMATCH")
    if len(raw) != 672 or len(dispatch) != 672 or len(legacy) != 672:
        raise RuntimeError("EXPECTED_672")
    if tes_soc.baseline_replay(raw) > 1e-4:
        raise RuntimeError("BASELINE_TES_NOT_REPRODUCED")
    tes = tes_soc.replay(raw, dispatch)
    if len(tes) != 672:
        raise RuntimeError("TES_REPLAY_LENGTH")
    for i, (r, d, t) in enumerate(zip(raw, dispatch, tes)):
        expected_h = i * 0.25
        if any(abs(float(x["cas_h"]) - expected_h) > 1e-8 for x in (r, d, t)):
            raise RuntimeError("TIMESTAMP_MISMATCH")
        if float(d["Q_unhandled_W"]) > 1e-7:
            raise RuntimeError("PREEXISTING_UNHANDLED_NOT_SUPPORTED")
    return raw, dispatch, tes, source_csv

def replay_case(raw, dispatch, tes, capacity_W, policy, fault_hour=24.0):
    temperature = thermal_n1.T_FLOOR_C
    previous_shed = 0.0
    result = []
    for r, d, t in zip(raw, dispatch, tes):
        hour = float(r["cas_h"])
        qdc = float(r["Q_DC_eff_W"])
        hx = float(d["Q_HX_W"])
        hp = float(t["Q_HP_source_corrected_W"])
        leak = float(r["Q_leak_W"])
        raw_required = float(t["Q_reject_corrected_W"])
        if not math.isfinite(raw_required) or raw_required < -1e-7:
            raise ValueError("INVALID_CORRECTED_REJECT")
        required = max(0.0, raw_required)  # clamp only floating-point roundoff
        if any(not math.isfinite(x) or x < -1e-8 for x in (qdc, hx, hp, leak, required)):
            raise ValueError("NONFINITE_OR_NEGATIVE_INPUT")
        active = hour >= fault_hour
        cap = capacity_W if active else thermal_n1.CAPACITIES["both"]
        effective_policy = policy if active else thermal_n1.POLICIES["no_shed"]
        # Clamping previous shed is required if DC output drops between intervals.
        # Ramp applies only to increasing shedding, as in A37.
        previous_shed = min(previous_shed, qdc)
        x = thermal_n1.advance(required, qdc, cap, temperature,
                               previous_shed, effective_policy)
        residual = qdc - x["shed_W"] - hx - hp - leak - x["reject_actual_W"] - x["unhandled_W"]
        hp_residual = float(t["HP_balance_residual_W"])
        tes_residual = float(t["TES_balance_residual_J"])
        if abs(residual) > 1e-5 or abs(hp_residual) > 1e-5 or abs(tes_residual) > 1e-4:
            raise AssertionError("COUPLED_ENERGY_CLOSURE")
        row = {
            "cas_h": hour, "capacity_W": cap, "Q_DC_eff_W": qdc,
            "Q_HX_W": hx, "Q_HP_source_W": hp, "Q_leak_W": leak,
            "Q_reject_required_W": required, "Q_reject_actual_W": x["reject_actual_W"],
            "Q_unhandled_W": x["unhandled_W"], "Q_IT_shed_W": x["shed_W"],
            "Q_DC_after_shed_W": x["Q_DC_after_shed_W"],
            "T_IT_start_C": temperature, "T_IT_next_C": x["T_IT_next_C"],
            "passive_W": x["passive_W"], "alarm_next": x["alarm_next"],
            "E_TES_start_J": float(t["E_TES_start_J"]),
            "E_TES_next_J": float(t["E_TES_next_J"]),
            "TES_SOC_next": float(t["TES_SOC_next"]),
            "Q_TES_charge_actual_W": float(t["Q_charge_actual_W"]),
            "Q_TES_charge_curtailed_W": float(t["Q_charge_curtailed_W"]),
            "P_HP_proxy_W": float(t["P_HP_corrected_W"]),
            "TES_residual_J": tes_residual,
            "DC_residual_W": residual, "HP_residual_W": hp_residual,
        }
        result.append(row)
        temperature = x["T_IT_next_C"]
        previous_shed = x["shed_W"]
    return result

def calculate():
    raw, dispatch, tes, source_csv = checked_sources()
    cases = {}
    for label, capacity in thermal_n1.CAPACITIES.items():
        for policy_name, policy in thermal_n1.POLICIES.items():
            key = label + "/" + policy_name
            cases[key] = replay_case(raw, dispatch, tes, capacity, policy)
    return raw, dispatch, tes, source_csv, cases

def summarize(cases):
    report = {}
    for key, rows in cases.items():
        after = [r for r in rows if r["cas_h"] >= 24]
        alarms = [r for r in rows if r["alarm_next"]]
        report[key] = {
            "samples": len(rows),
            "max_T_IT_C": max(r["T_IT_next_C"] for r in rows),
            "first_alarm_h": alarms[0]["cas_h"] if alarms else None,
            "alarm_intervals": len(alarms),
            "unhandled_kWh": sum(r["Q_unhandled_W"] for r in after) / 4000,
            "shed_kWh": sum(r["Q_IT_shed_W"] for r in after) / 4000,
            "max_DC_residual_W": max(abs(r["DC_residual_W"]) for r in rows),
        }
    return report

def main():
    raw, dispatch, tes, source_csv, cases = calculate()
    output = {
        "status": "SYNTHETIC_INTEGRATED_REFERENCE_ONLY",
        **LIMITS,
        "samples": len(raw), "interval_seconds": 900, "fault_hour": 24.0,
        "upstream": {
            "v08_sha256": sha(tes_soc.V08),
            "v04_sha256": sha(tes_soc.V04),
            "v07_sha256": sha(run_a37.V07),
            "a36_csv_sha256": sha(source_csv),
            "a37_thermal_py_sha256": sha(A37 / "thermal_n1.py"),
            "a37b_tes_py_sha256": sha(A37B / "tes_soc.py"),
            "a37b_tes_trace_sha256": sha(A37B / "TES_SOC_TRACE.csv"),
        },
        "TES_clipped_intervals": sum(t["Q_charge_curtailed_W"] > 1e-6 for t in tes),
        "cases": summarize(cases),
    }
    for key, rows in cases.items():
        path = HERE / ("trace_" + key.replace("/", "_") + ".csv")
        with path.open("w", encoding="utf8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        output["cases"][key]["trace"] = path.name
        output["cases"][key]["sha256"] = sha(path)
    path = HERE / "RESULTS_A38.json"
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": output["status"], "samples": len(raw),
                      "cases": len(cases), "TES_clipped_intervals": output["TES_clipped_intervals"],
                      "cases_summary": {k: {m: v[m] for m in ("max_T_IT_C", "unhandled_kWh", "alarm_intervals")}
                                        for k, v in output["cases"].items()}}, indent=2))
if __name__ == "__main__":
    main()
