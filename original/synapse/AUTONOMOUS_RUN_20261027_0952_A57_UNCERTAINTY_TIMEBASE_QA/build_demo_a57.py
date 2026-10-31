"""Build immutable synthetic demonstration data and independent Decimal oracle."""
from __future__ import annotations
import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import a57_uncertainty_gate as gate

A55_DIR = gate.A56_DIR.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE"
sys.path.insert(0, str(A55_DIR))
from test_a55 import fixture

ROOT = Path(__file__).resolve().parent
DEMO = ROOT / "DEMO_SYNTHETIC"


def main():
    DEMO.mkdir(exist_ok=False)
    csv, meta, rows, provenance = fixture(DEMO)
    sensors = {
        name: {
            "abs_error_bound": bound, "relative_error_bound": 0.0,
            "calibration_ref": "SYNTHETIC-CAL-ONLY",
            "calibration_document_sha256": "0" * 64,
        }
        for name, bound in (("T_C", 0.0005), ("Q_net_W", 5.0),
                            ("P_cmd_W", 20.0), ("P_actual_W", 20.0))
    }
    bounds = {
        "asset_id": provenance["asset_id"], "source_kind": "synthetic_test",
        "source_csv_sha256": gate.sha(csv),
        "calibration_ref": provenance["sensor_calibration_record"],
        "timebase": "UTC",
        "time_sync": {
            "method": "synthetic_common_clock", "max_abs_clock_offset_s": 0.1,
            "clock_uncertainty_s": 0.05, "sample_timestamp_uncertainty_s": 0.05,
            "command_actuation_latency_bound_s": 0.2,
        },
        "sensors": sensors,
    }
    boundfile = DEMO / "uncertainty.json"
    boundfile.write_text(json.dumps(bounds, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result = gate.audit(csv, meta, boundfile)
    # Independent Decimal energy accounting for each 60-second interval.
    exact = Decimal("8000000")
    ledger = []
    for prev, now in zip(rows, rows[1:]):
        delta_t = Decimal(now["T_C"]) - Decimal(prev["T_C"])
        energy = Decimal(now["Q_net_W"]) * Decimal("60")
        residual = energy - exact * delta_t
        ledger.append(str(residual))
        assert abs(residual) <= Decimal("0.01"), residual
    assert result["capacity"]["lower_J_per_K"] <= 8e6 <= result["capacity"]["upper_J_per_K"]
    assert result["compressor_tau"]["lower_s"] <= 300 <= result["compressor_tau"]["upper_s"]
    assert result["physical_release"] is False
    (DEMO / "A57_RESULT_SYNTHETIC.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DEMO / "A57_DECIMAL_ORACLE.json").write_text(json.dumps({
        "source_kind": "synthetic_test", "intervals": len(ledger),
        "capacity_exact_J_per_K": "8000000", "energy_residual_max_abs_J":
            str(max(abs(Decimal(x)) for x in ledger)),
        "oracle_pass": True, "physical_release": False
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "capacity": result["capacity"],
                      "tau": result["compressor_tau"], "oracle_intervals": len(ledger),
                      "decimal_max_abs_J": max(abs(float(x)) for x in ledger)}))


if __name__ == "__main__":
    main()
