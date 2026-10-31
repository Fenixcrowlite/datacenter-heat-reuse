"""A61: independent discrete first-law audit of A60-derived SCADA simulation.

READ ONLY: original v08/v09 CSV and A60 outputs. Never declares physical
calibration, real telemetry, or industrial safety acceptance.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

C_POOL_J_PER_K = 997.0 * 500.0 * 4182.0
INITIAL_T_C = 16.0
STEP_S = 900.0
SOURCE = {
    "scada_v08": ("Q_pool_phys_W", "Q_pool_loss_W"),
    "scada_v09_matlab": ("Q_pool_W", "Q_pool_losses_W"),
}
DERIVED_FIELDS = ("time_s", "T_pool_C", "Q_pool_W")


def sha(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def records(path: Path, required: tuple[str, ...]) -> list[dict]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("INVALID_INPUT_FILE")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, strict=True)
        heads = reader.fieldnames or []
        if len(heads) != len(set(heads)) or not set(required).issubset(heads):
            raise ValueError("INVALID_CSV_SCHEMA")
        rows = list(reader)
    if len(rows) < 3 or any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError("INVALID_CSV_ROWS")
    return rows


def number(row: dict, key: str) -> float:
    try:
        value = float(row[key])
    except (ValueError, TypeError, KeyError) as e:
        raise ValueError("INVALID_NUMBER_" + key) from e
    if not math.isfinite(value):
        raise ValueError("NONFINITE_" + key)
    return value


def audit(raw: Path, derived_dir: Path, *, initial_T_C: float = INITIAL_T_C,
          step_s: float = STEP_S, tolerance_W: float = 0.001) -> dict:
    raw, derived_dir = Path(raw), Path(derived_dir)
    summary_path = derived_dir / "summary.json"
    analysis_path = derived_dir / "analysis_timeseries.csv"
    if not math.isfinite(initial_T_C) or not math.isfinite(step_s) or step_s <= 0:
        raise ValueError("INVALID_PHYSICAL_ASSUMPTIONS")
    if not summary_path.is_file() or summary_path.is_symlink():
        raise ValueError("INVALID_SUMMARY")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("schema_version") != "a60.1" or summary.get("source_kind") != "derived_simulation":
        raise ValueError("NOT_A60_DERIVED_SIMULATION")
    if summary.get("physical_release") is not False or summary.get("measurement_calibration_ready") is not False:
        raise ValueError("UNAUTHORIZED_PHYSICAL_RELEASE")
    schema = summary.get("source_schema")
    if schema not in SOURCE:
        raise ValueError("UNSUPPORTED_SOURCE_SCHEMA")
    if raw.resolve() != Path(summary.get("source_path", "")).resolve():
        raise ValueError("SOURCE_PATH_MISMATCH")
    if sha(raw) != summary.get("source_csv_sha256"):
        raise ValueError("SOURCE_SHA_MISMATCH")
    if sha(analysis_path) != summary.get("analysis_csv_sha256"):
        raise ValueError("DERIVED_SHA_MISMATCH")
    q_name, loss_name = SOURCE[schema]
    src = records(raw, ("cas_h", "T_pool_C", q_name, loss_name))
    dst = records(analysis_path, DERIVED_FIELDS)
    if len(src) != len(dst):
        raise ValueError("ROW_COUNT_MISMATCH")

    previous_T = initial_T_C
    energy_in_J = energy_signed_loss_J = 0.0
    negative_loss_count = 0
    negative_loss_energy_J = 0.0
    max_abs_residual_W = 0.0
    last_time = None
    previous_Q = None
    trapezoid_J = 0.0
    for i, (a, b) in enumerate(zip(src, dst)):
        t = number(a, "cas_h") * 3600.0
        td = number(b, "time_s")
        if abs(t - td) > 1e-5 or abs(t - i * step_s) > 1e-5:
            raise ValueError("TIME_GRID_MISMATCH")
        if last_time is not None and abs(t - last_time - step_s) > 1e-5:
            raise ValueError("TIME_STEP_MISMATCH")
        T = number(a, "T_pool_C")
        q = number(a, q_name)
        loss = number(a, loss_name)
        if abs(T - number(b, "T_pool_C")) > 1e-6 or abs(q - number(b, "Q_pool_W")) > 0.001:
            raise ValueError("A60_SOURCE_MAPPING_MISMATCH")
        residual_W = C_POOL_J_PER_K * (T - previous_T) / step_s - (q - loss)
        max_abs_residual_W = max(max_abs_residual_W, abs(residual_W))
        if abs(residual_W) > tolerance_W:
            raise ValueError("POOL_FIRST_LAW_RESIDUAL_AT_" + str(i))
        energy_in_J += q * step_s
        energy_signed_loss_J += loss * step_s
        if loss < 0:
            negative_loss_count += 1
            negative_loss_energy_J += loss * step_s
        if previous_Q is not None:
            trapezoid_J += (previous_Q + q) * 0.5 * step_s
        previous_Q, previous_T, last_time = q, T, t
    stored_J = C_POOL_J_PER_K * (previous_T - initial_T_C)
    closure_J = energy_in_J - energy_signed_loss_J - stored_J
    if abs(closure_J) > max(1.0, tolerance_W * len(src) * step_s):
        raise ValueError("INTEGRATED_FIRST_LAW_MISMATCH")
    a60_trap_MWh = summary["metrics"]["integrated_MWh"]["Q_pool_W"]
    if abs(trapezoid_J / 3.6e9 - a60_trap_MWh) > 1e-8:
        raise ValueError("A60_TRAPEZOID_MISMATCH")
    return {
        "source_schema": schema, "source_kind": "derived_simulation",
        "physical_release": False, "calibration_ready": False,
        "samples": len(src), "time_span_h": last_time / 3600.0,
        "discrete_steps_h": len(src) * step_s / 3600.0,
        "initial_T_C": initial_T_C, "final_T_C": previous_T,
        "pool_volume_m3_assumed_from_v04": 500,
        "rho_kg_m3_assumed_from_v04": 997,
        "cp_J_kg_K_assumed_from_v04": 4182,
        "E_pool_input_discrete_MWh": energy_in_J / 3.6e9,
        "E_pool_signed_losses_MWh": energy_signed_loss_J / 3.6e9,
        "E_pool_stored_MWh": stored_J / 3.6e9,
        "integrated_closure_J": closure_J,
        "max_abs_step_residual_W": max_abs_residual_W,
        "negative_loss_samples": negative_loss_count,
        "environmental_gain_MWh_from_negative_losses": -negative_loss_energy_J / 3.6e9,
        "A60_trapezoid_MWh": a60_trap_MWh,
        "A60_trapezoid_minus_discrete_kWh": (trapezoid_J - energy_in_J) / 3.6e6,
        "note": "Negative signed losses are heat gains, not proof of a first-law violation. A60 trapezoid covers 167.75 h of timestamp span; discrete state updates cover 672 x 900 s = 168 h.",
        "source_sha256": sha(raw), "analysis_sha256": sha(analysis_path),
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("raw_v08", type=Path)
    p.add_argument("derived_v08", type=Path)
    p.add_argument("raw_v09", type=Path)
    p.add_argument("derived_v09", type=Path)
    p.add_argument("report_json", type=Path)
    args = p.parse_args()
    if args.report_json.exists() or args.report_json.is_symlink():
        raise ValueError("REPORT_ALREADY_EXISTS")
    a = audit(args.raw_v08, args.derived_v08)
    b = audit(args.raw_v09, args.derived_v09)
    if a["source_schema"] != "scada_v08" or b["source_schema"] != "scada_v09_matlab":
        raise ValueError("WRONG_VERSION_ORDER")
    result = {"schema_version": "a61.1", "v08": a, "v09": b,
              "status": "VERIFIED_SYNTHETIC_DISCRETE_CLOSURE",
              "physical_release": False,
              "physical_validation": "BLOCKED_NO_REAL_MEASUREMENTS"}
    args.report_json.write_text(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"v08_max_residual_W": a["max_abs_step_residual_W"],
                      "v09_max_residual_W": b["max_abs_step_residual_W"],
                      "negative_loss_samples": [a["negative_loss_samples"], b["negative_loss_samples"]],
                      "a60_trap_bias_kWh": [a["A60_trapezoid_minus_discrete_kWh"], b["A60_trapezoid_minus_discrete_kWh"]]}))


if __name__ == "__main__":
    main()
