"""A55: fail-closed physical-parameter provenance and telemetry identification.
Never treat A54 stress ranges or synthetic tests as equipment measurements.
Only stdlib; no GUI, hardware writes, external requests, or model edits.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
A54 = HERE.parent / "AUTONOMOUS_RUN_20261027_0648_A54_PARAMETER_UNCERTAINTY" / "A54_UNCERTAINTY_RESULTS.json"
ROOT = Path.home() / "OneDrive" / "Projects" / "DataCenter_Heat_Reuse"
REGISTRY = ROOT / "sources" / "parameter_registry.yaml"

FIELDS = ("timestamp_utc", "asset_id", "calibration_ref", "T_C", "Q_net_W",
          "P_cmd_W", "P_actual_W", "trip_state", "Q_residual_W", "Q_nominal_W")
REQUIRED_METADATA = ("asset_id", "source_kind", "sensor_calibration_record",
                     "original_csv_sha256", "provenance_notes")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    x = (len(ys) - 1) * p
    lo = int(x)
    return ys[lo] + (ys[min(lo + 1, len(ys) - 1)] - ys[lo]) * (x - lo)


def finite_number(value: str, name: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"NON_NUMERIC_{name}") from exc
    if not math.isfinite(n):
        raise ValueError(f"NONFINITE_{name}")
    return n


def parse_utc(value: str) -> datetime:
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if t.tzinfo is None or t.utcoffset().total_seconds() != 0:
        raise ValueError("TIMESTAMP_NOT_UTC")
    return t


def load_telemetry(csv_path: Path, metadata_path: Path) -> tuple[list[dict], dict]:
    if not csv_path.is_file() or not metadata_path.is_file():
        raise ValueError("MISSING_TELEMETRY_OR_PROVENANCE")
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not all(meta.get(key) for key in REQUIRED_METADATA):
        raise ValueError("INCOMPLETE_PROVENANCE")
    if meta["original_csv_sha256"].lower() != sha(csv_path):
        raise ValueError("SOURCE_HASH_MISMATCH")
    if meta["source_kind"] not in ("real_telemetry", "synthetic_test"):
        raise ValueError("UNKNOWN_SOURCE_KIND")
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not set(FIELDS).issubset(set(reader.fieldnames or [])):
            raise ValueError("MISSING_REQUIRED_COLUMNS")
        rows = list(reader)
    if len(rows) < 20:
        raise ValueError("INSUFFICIENT_SAMPLES")
    prev = None
    for r in rows:
        if r["asset_id"] != meta["asset_id"] or not r["calibration_ref"]:
            raise ValueError("ASSET_OR_CALIBRATION_MISMATCH")
        if r["calibration_ref"] != meta["sensor_calibration_record"]:
            raise ValueError("CALIBRATION_RECORD_MISMATCH")
        t = parse_utc(r["timestamp_utc"])
        if prev is not None:
            dt = (t - prev).total_seconds()
            if not 0 < dt <= 3600:
                raise ValueError("NONMONOTONIC_OR_GAPPED_TIMESTAMPS")
        prev = t
        r["_t"] = t
        for k in ("T_C", "Q_net_W", "P_cmd_W", "P_actual_W",
                  "Q_residual_W", "Q_nominal_W"):
            r[k] = finite_number(r[k], k)
        if r["trip_state"] not in ("RUN", "TRIPPED"):
            raise ValueError("INVALID_TRIP_STATE")
    return rows, meta


def estimate_capacity(rows: list[dict]) -> dict:
    # Energy balance: Q_net_avg * dt = C_eff * (T_i - T_(i-1)).
    pairs = []
    for prev, now in zip(rows, rows[1:]):
        dt = (now["_t"] - prev["_t"]).total_seconds()
        dT = now["T_C"] - prev["T_C"]
        energy = now["Q_net_W"] * dt
        if abs(dT) >= 0.01 and abs(energy) >= 1000:
            if dT * energy <= 0:
                raise ValueError("INCONSISTENT_ENERGY_SIGN")
            pairs.append((dT, energy))
    if len(pairs) < 12:
        raise ValueError("CAPACITY_NOT_IDENTIFIABLE")
    c = sum(x * y for x, y in pairs) / sum(x * x for x, _ in pairs)
    per_interval = [y / x for x, y in pairs]
    if not 1e3 < c < 1e12:
        raise ValueError("IMPLAUSIBLE_CAPACITY")
    relative_error = sum(abs(y - c * x) for x, y in pairs) / sum(abs(y) for _, y in pairs)
    if relative_error > 0.15:
        raise ValueError("CAPACITY_MODEL_MISMATCH")
    return {"value_J_per_K": c, "empirical_p10_J_per_K": quantile(per_interval, 0.1),
            "empirical_p90_J_per_K": quantile(per_interval, 0.9),
            "intervals": len(pairs), "relative_energy_fit_error": relative_error}


def estimate_compressor_tau(rows: list[dict]) -> dict:
    # Exact zero-order-hold first-order lag: r=exp(-dt/tau).
    candidates = []
    for prev, now in zip(rows, rows[1:]):
        cmd = now["P_cmd_W"]
        if abs(cmd - prev["P_cmd_W"]) > 1e-6:
            continue  # command changed during interval; timestamp alignment unknown
        initial = prev["P_actual_W"] - cmd
        final = now["P_actual_W"] - cmd
        if abs(initial) < 1000:
            continue
        ratio = final / initial
        if 0 < ratio < 1:
            dt = (now["_t"] - prev["_t"]).total_seconds()
            candidates.append(-dt / math.log(ratio))
    if len(candidates) < 4:
        raise ValueError("COMPRESSOR_TAU_NOT_IDENTIFIABLE")
    med = statistics.median(candidates)
    if (quantile(candidates, 0.9) - quantile(candidates, 0.1)) / med > 0.35:
        raise ValueError("COMPRESSOR_NONFIRSTORDER_OR_NOISY")
    return {"median_s": med, "empirical_p10_s": quantile(candidates, 0.1),
            "empirical_p90_s": quantile(candidates, 0.9),
            "intervals": len(candidates)}


def estimate_residual_fraction(rows: list[dict]) -> dict:
    fractions = [r["Q_residual_W"] / r["Q_nominal_W"] for r in rows
                 if r["trip_state"] == "TRIPPED" and r["Q_nominal_W"] > 0]
    if len(fractions) < 5:
        raise ValueError("RESIDUAL_NOT_IDENTIFIABLE")
    if any(not 0 <= x <= 1 for x in fractions):
        raise ValueError("RESIDUAL_OUT_OF_RANGE")
    med = statistics.median(fractions)
    if max(fractions) - min(fractions) > 0.2 * max(med, 0.01):
        raise ValueError("RESIDUAL_NOT_CONSTANT")
    return {"median_fraction": med, "empirical_p10": quantile(fractions, 0.1),
            "empirical_p90": quantile(fractions, 0.9), "intervals": len(fractions)}


def calibrate(csv_path: Path, metadata_path: Path) -> dict:
    rows, meta = load_telemetry(csv_path, metadata_path)
    return {
        "status": "SYNTHETIC_TEST_ONLY" if meta["source_kind"] == "synthetic_test"
                  else "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA",
        "source_kind": meta["source_kind"], "asset_id": meta["asset_id"],
        "source_csv_sha256": sha(csv_path), "metadata_sha256": sha(metadata_path),
        "capacity": estimate_capacity(rows),
        "compressor_tau": estimate_compressor_tau(rows),
        "residual_fraction": estimate_residual_fraction(rows),
        "safe_operating_limits_certified": False,
        "independent_sensor_calibration_verified": False,
        "physical_release": False,
    }


def audit_a54() -> dict:
    a54 = json.loads(A54.read_text(encoding="utf-8"))
    if a54["cases_checked"] != 144 or not a54["not_a_certified_safety_envelope"]:
        raise ValueError("A54_SOURCE_INTEGRITY_OR_STATUS")
    if "class: D" not in REGISTRY.read_text(encoding="utf-8"):
        raise ValueError("PARAMETER_CLASSIFICATION_MISSING")
    caps = a54["parameter_values"]["heat_capacity_J_per_C"]
    # Water-only equivalence at ~20 C; this is NOT an inferred physical loop volume.
    rho_kg_m3, cp_J_kg_K = 998.0, 4182.0
    return {
        "status": "A55_PROVENANCE_GATE_IMPLEMENTED_PHYSICAL_CALIBRATION_BLOCKED",
        "A54_sha256": sha(A54), "parameter_registry_sha256": sha(REGISTRY),
        "A54_parameter_provenance": "D: engineering stress-test assumptions",
        "A54_ranges": {
            "heat_capacity_J_per_K": caps,
            "residual_fraction": a54["parameter_values"]["residual_fraction"],
            "compressor_tau_s": a54["parameter_values"]["compressor_tau_s"]},
        "water_only_equivalent_m3": [round(x / (rho_kg_m3 * cp_J_kg_K), 4) for x in caps],
        "water_equivalence_assumption": "rho=998 kg/m3, cp=4182 J/(kg K), ~20 C; excludes metal, glycol and spatial effects",
        "required_primary_evidence": [
            "selected equipment/loop asset ID and sensor calibration records",
            "time-aligned UTC inlet/outlet temperatures, measured flow and heat balance",
            "compressor command and measured thermal response during identified steps",
            "measured post-trip heat flow and nominal heat flow over a documented window",
            "vendor performance map, operating envelope and sensor uncertainty"],
        "telemetry_schema": list(FIELDS),
        "measurements_supplied": False,
        "source_class_promoted": False,
        "safe_operating_limits_certified": False,
        "physical_release": False,
        "next_step": "Obtain asset-specific calibrated telemetry and vendor datasheet; run calibrate() then independent review; only then re-run Stateflow uncertainty grid."
    }


def main() -> None:
    report = audit_a54()
    out = HERE / "A55_PROVENANCE_AUDIT.json"
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if out.exists() and out.read_text(encoding="utf-8") != rendered:
        raise RuntimeError("A55_AUDIT_IMMUTABLE_CONFLICT")
    if not out.exists():
        out.write_text(rendered, encoding="utf-8")
    print(json.dumps({"status": report["status"],
                      "A54_sha256": report["A54_sha256"],
                      "water_only_equivalent_m3": report["water_only_equivalent_m3"]}))


if __name__ == "__main__":
    main()
