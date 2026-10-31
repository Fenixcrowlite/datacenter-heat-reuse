"""A56: independent, fail-closed adversarial quality gate for A55 telemetry.

Synthetic-only acceptance tests. This is not an instrument calibration, vendor
performance map, safe operating envelope, or physical release authorization.
A55 is imported read-only from its immutable prior run directory.
"""
from __future__ import annotations

import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A55_DIR = HERE.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE"
A55_FILE = A55_DIR / "a55_calibration_gate.py"
EXPECTED_A55_SHA256 = "e65e2ec1e2e7927023637c0bd8f430dcfb1045346666220ede8ecb7ed0e5be91"

if str(A55_DIR) not in sys.path:
    sys.path.insert(0, str(A55_DIR))
import a55_calibration_gate as a55


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fit_capacity(pairs: list[tuple[float, float]]) -> float:
    denom = sum(dt * dt for dt, _ in pairs)
    if denom <= 0:
        raise ValueError("A56_CAPACITY_ZERO_EXCITATION")
    return sum(dt * energy for dt, energy in pairs) / denom


def audit(csv_path: Path, metadata_path: Path) -> dict:
    if _sha(A55_FILE) != EXPECTED_A55_SHA256:
        raise ValueError("A56_A55_SOURCE_CHANGED")
    rows, meta = a55.load_telemetry(csv_path, metadata_path)
    usable: list[tuple[float, float]] = []
    tau_candidates: list[float] = []
    significant_energy = 0
    weak_temperature = 0
    compressor_checked = 0

    for prev, now in zip(rows, rows[1:]):
        dt_s = (now["_t"] - prev["_t"]).total_seconds()
        dT_K = now["T_C"] - prev["T_C"]
        energy_J = now["Q_net_W"] * dt_s
        if abs(energy_J) >= 1000:
            significant_energy += 1
            # A55 silently drops small |dT|, including sign-inconsistent
            # intervals. A56 must reject a reversal, however small.
            if dT_K * energy_J < -1e-9:
                raise ValueError("A56_SUBRESOLUTION_ENERGY_SIGN_REVERSAL")
            if abs(dT_K) < 0.01:
                weak_temperature += 1
            else:
                usable.append((dT_K, energy_J))
        elif abs(dT_K) >= 0.01:
            raise ValueError("A56_TEMPERATURE_WITHOUT_NET_ENERGY")

        if abs(now["P_cmd_W"] - prev["P_cmd_W"]) > 1e-6:
            continue  # unknown intra-interval command transition
        cmd = now["P_cmd_W"]
        initial = prev["P_actual_W"] - cmd
        if abs(initial) < 1000:
            continue
        compressor_checked += 1
        final = now["P_actual_W"] - cmd
        ratio = final / initial
        if not (0 < ratio < 1):
            raise ValueError("A56_COMPRESSOR_NONCONTRACTIVE_STEP")
        tau_candidates.append(-dt_s / math.log(ratio))

    if significant_energy < 12 or len(usable) < 12:
        raise ValueError("A56_INSUFFICIENT_ENERGY_EXCITATION")
    if len(usable) / significant_energy < 0.8:
        raise ValueError("A56_TEMPERATURE_RESOLUTION_INSUFFICIENT")
    if compressor_checked < 4:
        raise ValueError("A56_INSUFFICIENT_COMPRESSOR_EXCITATION")

    mid = len(usable) // 2
    c_first = _fit_capacity(usable[:mid])
    c_second = _fit_capacity(usable[mid:])
    drift = abs(c_first - c_second) / max(abs(c_first), abs(c_second))
    if drift > 0.10:
        raise ValueError("A56_CAPACITY_HOLDOUT_DRIFT")

    # Independent cross-validation, not a confidence interval.
    baseline = a55.calibrate(csv_path, metadata_path)
    if baseline["physical_release"] or baseline["safe_operating_limits_certified"]:
        raise ValueError("A56_UNEXPECTED_RELEASE_FLAG")
    return {
        "status": "SYNTHETIC_QA_ONLY" if meta["source_kind"] == "synthetic_test"
                  else "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA",
        "source_kind": meta["source_kind"],
        "asset_id": meta["asset_id"],
        "source_csv_sha256": _sha(csv_path),
        "metadata_sha256": _sha(metadata_path),
        "a55_source_sha256": _sha(A55_FILE),
        "intervals": len(rows) - 1,
        "energy_intervals_significant": significant_energy,
        "energy_intervals_usable": len(usable),
        "weak_temperature_intervals": weak_temperature,
        "compressor_intervals_checked": compressor_checked,
        "compressor_tau_median_s": statistics.median(tau_candidates),
        "capacity_holdout_first_J_per_K": c_first,
        "capacity_holdout_second_J_per_K": c_second,
        "capacity_holdout_relative_drift": drift,
        "a55_capacity_J_per_K": baseline["capacity"]["value_J_per_K"],
        "a55_compressor_tau_s": baseline["compressor_tau"]["median_s"],
        "a55_residual_fraction": baseline["residual_fraction"]["median_fraction"],
        "physical_release": False,
        "safe_operating_limits_certified": False,
        "measurement_uncertainty_verified": False,
        "note": "This stricter first-order gate rejects noncontractive compressor responses. It is an assumed model class, not a general equipment safety criterion.",
    }


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.csv, args.metadata), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
