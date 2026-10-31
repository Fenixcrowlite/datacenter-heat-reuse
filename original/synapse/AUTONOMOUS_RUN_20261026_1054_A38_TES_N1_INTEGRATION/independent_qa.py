"""A38 independent Decimal energy and thermal replay; never imports integrated_a38."""
import csv
import hashlib
import json
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec = 36
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
A36 = ROOT / "AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE"
A37B = ROOT / "AUTONOMOUS_RUN_20261026_1037_A37B_DCHR_TES_SOC_REDIRECT"
V08 = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
D = lambda x: Decimal(str(x))
ZERO = D(0)
DT = D(900)
CAP = {"both": D(330000), "main_only": D(180000),
       "backup_only": D(150000), "neither": ZERO}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def near(actual, expected, tolerance="0.00001"):
    if abs(D(actual) - D(expected)) > D(tolerance):
        raise AssertionError("DECIMAL_MISMATCH " + str(actual) + " vs " + str(expected))

def read_csv(path):
    with path.open(encoding="utf8", newline="") as f:
        return list(csv.DictReader(f))

def main():
    report = json.loads((HERE / "RESULTS_A38.json").read_text(encoding="utf8"))
    if report["physical_release_allowed"] or report["matlab_stateflow_executed"]:
        raise AssertionError("RELEASE_GATE")
    assert sha(V08) == report["upstream"]["v08_sha256"]
    src = A36 / "scenario_both_off.csv"
    assert sha(src) == report["upstream"]["a36_csv_sha256"]
    tesfile = A37B / "TES_SOC_TRACE.csv"
    assert sha(tesfile) == report["upstream"]["a37b_tes_trace_sha256"]
    raw = read_csv(V08)
    dispatch = read_csv(src)
    tes = read_csv(tesfile)
    assert len(raw) == len(dispatch) == len(tes) == 672
    checks = 0
    case_stats = {}
    for key, summary in report["cases"].items():
        label, policy = key.split("/")
        path = HERE / summary["trace"]
        assert sha(path) == summary["sha256"]
        rows = read_csv(path)
        assert len(rows) == 672
        T = D(30)
        previous_shed = ZERO
        previous_E = None
        n_alarm = 0
        shed_energy = ZERO
        unhandled_energy = ZERO
        for index, (row, original, d, ts) in enumerate(zip(rows, raw, dispatch, tes)):
            hour = D(index) / 4
            near(row["cas_h"], hour, "0.00000001")
            near(original["cas_h"], hour, "0.00000001")
            near(d["cas_h"], hour, "0.00000001")
            near(ts["cas_h"], hour, "0.00000001")
            qdc = D(original["Q_DC_eff_W"])
            hx = D(d["Q_HX_W"])
            hp = D(ts["Q_HP_source_corrected_W"])
            leak = D(original["Q_leak_W"])
            required = max(ZERO, D(ts["Q_reject_corrected_W"]))
            capacity = CAP[label] if hour >= 24 else CAP["both"]
            near(row["capacity_W"], capacity)
            near(row["Q_DC_eff_W"], qdc)
            near(row["Q_HX_W"], hx)
            near(row["Q_HP_source_W"], hp)
            near(row["Q_leak_W"], leak)
            near(row["Q_reject_required_W"], required)
            previous_shed = min(previous_shed, qdc)
            if hour < 24 or policy == "no_shed":
                shed = ZERO
            else:
                target = min(max(ZERO, required - capacity), D("0.4") * qdc, required)
                shed = min(target, previous_shed + D(15000)) if policy == "ramp15k_40pct" else target
            actual = min(required - shed, capacity)
            unhandled = max(ZERO, required - shed - actual)
            near(row["Q_IT_shed_W"], shed)
            near(row["Q_reject_actual_W"], actual)
            near(row["Q_unhandled_W"], unhandled)
            near(row["Q_DC_after_shed_W"], qdc - shed)
            near(qdc - shed, hx + hp + leak + actual + unhandled)
            passive = max(ZERO, D(2000) * (T - 30))
            Tnext = max(D(30), T + DT * (unhandled - passive) / D(8000000))
            near(row["T_IT_start_C"], T, "0.000001")
            near(row["T_IT_next_C"], Tnext, "0.000001")
            near(row["passive_W"], passive, "0.00001")
            alarm = int(Tnext >= 42)
            assert int(row["alarm_next"]) == alarm
            n_alarm += alarm
            E = D(ts["E_TES_start_J"])
            E_next = D(ts["E_TES_next_J"])
            if previous_E is not None:
                near(E, previous_E, "0.0001")
            charge = D(ts["Q_charge_actual_W"])
            discharge = D(ts["Q_TES_discharge_W"])
            loss = D("0.002") * E / D(86400)
            expected_E = E + DT * (D(".93") * charge - discharge / D(".91") - loss)
            near(E_next, expected_E, "0.0001")
            near(row["E_TES_start_J"], E, "0.0001")
            near(row["E_TES_next_J"], E_next, "0.0001")
            near(row["TES_SOC_next"], E_next / (D(900) * D(3600000)), "0.00000001")
            assert ZERO <= E_next <= D(900) * D(3600000) + D("0.0001")
            near(row["Q_TES_charge_actual_W"], charge)
            near(row["Q_TES_charge_curtailed_W"], ts["Q_charge_curtailed_W"])
            near(row["P_HP_proxy_W"], ts["P_HP_corrected_W"])
            near(row["DC_residual_W"], ZERO)
            near(row["HP_residual_W"], ZERO)
            near(row["TES_residual_J"], ZERO, "0.0001")
            if hour >= 24:
                shed_energy += shed / D(4000)
                unhandled_energy += unhandled / D(4000)
            T = Tnext
            previous_shed = shed
            previous_E = E_next
            checks += 28
        near(summary["max_T_IT_C"], max(D(x["T_IT_next_C"]) for x in rows), "0.000001")
        near(summary["shed_kWh"], shed_energy, "0.000001")
        near(summary["unhandled_kWh"], unhandled_energy, "0.000001")
        assert n_alarm == summary["alarm_intervals"]
        case_stats[key] = {"alarms": n_alarm, "max_temperature_C": str(max(D(x["T_IT_next_C"]) for x in rows))}
    output = {
        "status": "PASS",
        "rows": 672 * len(report["cases"]),
        "cases": len(report["cases"]),
        "decimal_invariant_checks": checks,
        "provenance": "SHA-checked A36, A37B and v08; independent Decimal recurrence",
        "release": "BLOCKED_SYNTHETIC_NOT_MATLAB_STATEFLOW",
        "case_stats": case_stats,
    }
    (HERE / "INDEPENDENT_QA.json").write_text(json.dumps(output, indent=2) + "\n", encoding="utf8")
    print(json.dumps({"status": output["status"], "rows": output["rows"],
                      "decimal_invariant_checks": checks}, indent=2))
if __name__ == "__main__":
    main()
