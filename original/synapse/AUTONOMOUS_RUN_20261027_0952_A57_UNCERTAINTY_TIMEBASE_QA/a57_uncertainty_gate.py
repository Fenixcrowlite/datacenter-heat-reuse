"""A57: conservative measurement-error and timebase gate over A55+A56.
Read-only inputs; synthetic QA only. Not a statistical confidence interval or
a safety certification. Supplied uncertainty bounds are NOT independently verified.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
A56_DIR = HERE.parent / "AUTONOMOUS_RUN_20261027_0855_A56_ADVERSARIAL_CALIBRATION_QA"
A56_FILE = A56_DIR / "a56_quality_gate.py"
EXPECTED_A56_SHA = "0834471ae3505906167192769da7ba5baf9cabd2baac55352fb480f607e4358c"
if str(A56_DIR) not in sys.path:
    sys.path.insert(0, str(A56_DIR))
import a56_quality_gate as a56
a55 = a56.a55

SENSORS = ("T_C", "Q_net_W", "P_cmd_W", "P_actual_W")
SYNC_FIELDS = ("max_abs_clock_offset_s", "clock_uncertainty_s",
               "sample_timestamp_uncertainty_s", "command_actuation_latency_bound_s")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("A57_DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def nonnegative(value, field, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("A57_INVALID_" + field)
    v = float(value)
    if not math.isfinite(v) or v < 0 or (positive and v == 0):
        raise ValueError("A57_INVALID_" + field)
    return v


def load_bounds(path: Path, rows: list[dict], meta: dict, csv_path: Path) -> dict:
    if not path.is_file():
        raise ValueError("A57_MISSING_UNCERTAINTY_RECORD")
    doc = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(doc, dict):
        raise ValueError("A57_INVALID_UNCERTAINTY_SCHEMA")
    if doc.get("asset_id") != meta["asset_id"] or doc.get("source_kind") != meta["source_kind"]:
        raise ValueError("A57_ASSET_OR_SOURCE_KIND_MISMATCH")
    if doc.get("source_csv_sha256") != sha(csv_path):
        raise ValueError("A57_UNCERTAINTY_SOURCE_HASH_MISMATCH")
    if doc.get("calibration_ref") != meta["sensor_calibration_record"]:
        raise ValueError("A57_CALIBRATION_REF_MISMATCH")
    if doc.get("timebase") != "UTC":
        raise ValueError("A57_TIMEBASE_NOT_UTC")
    if doc.get("physical_release") is True or doc.get("certified_safe_limits") is True:
        raise ValueError("A57_UNAUTHORIZED_RELEASE_CLAIM")
    sync = doc.get("time_sync")
    if not isinstance(sync, dict) or sync.get("method") not in ("synthetic_common_clock", "ptp", "ntp", "gps", "instrument_common_clock"):
        raise ValueError("A57_MISSING_TIME_SYNC_METHOD")
    for field in SYNC_FIELDS:
        nonnegative(sync.get(field), field)
    sensors = doc.get("sensors")
    if not isinstance(sensors, dict) or not all(x in sensors for x in SENSORS):
        raise ValueError("A57_MISSING_SENSOR_BOUNDS")
    for name in SENSORS:
        spec = sensors[name]
        if not isinstance(spec, dict):
            raise ValueError("A57_INVALID_SENSOR_RECORD")
        a = nonnegative(spec.get("abs_error_bound"), name + "_ABS")
        r = nonnegative(spec.get("relative_error_bound"), name + "_REL")
        if r > 1:
            raise ValueError("A57_RELATIVE_BOUND_GT_ONE")
        if meta["source_kind"] == "real_telemetry" and a == 0 and r == 0:
            raise ValueError("A57_ZERO_UNCERTAINTY_REAL_SENSOR")
        digest = spec.get("calibration_document_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise ValueError("A57_INVALID_CALIBRATION_DOCUMENT_HASH")
        if meta["source_kind"] == "real_telemetry" and digest == "0" * 64:
            raise ValueError("A57_PLACEHOLDER_CERTIFICATE_REAL_SENSOR")
        if spec.get("calibration_ref") != meta["sensor_calibration_record"]:
            raise ValueError("A57_SENSOR_CALIBRATION_MISMATCH")
    dt_min = min((now["_t"] - prev["_t"]).total_seconds() for prev, now in zip(rows, rows[1:]))
    u_dt = 2 * (sync["clock_uncertainty_s"] + sync["sample_timestamp_uncertainty_s"])
    if u_dt >= dt_min * .1:
        raise ValueError("A57_TIMEBASE_INTERVAL_UNCERTAIN")
    cross = sum(sync[k] for k in SYNC_FIELDS)
    if cross >= dt_min * .25:
        raise ValueError("A57_TIMEBASE_COMMAND_AMBIGUOUS")
    return doc


def err(spec: dict, value: float) -> float:
    return spec["abs_error_bound"] + spec["relative_error_bound"] * abs(value)


def audit(csv_path: Path, metadata_path: Path, bounds_path: Path) -> dict:
    if sha(A56_FILE) != EXPECTED_A56_SHA:
        raise ValueError("A57_A56_SOURCE_CHANGED")
    baseline = a56.audit(csv_path, metadata_path)
    rows, meta = a55.load_telemetry(csv_path, metadata_path)
    doc = load_bounds(bounds_path, rows, meta, csv_path)
    specs, sync = doc["sensors"], doc["time_sync"]
    u_dt = 2 * (sync["clock_uncertainty_s"] + sync["sample_timestamp_uncertainty_s"])
    capacity_bounds = []
    tau_bounds = []
    weak_capacity = weak_tau = 0
    for prev, now in zip(rows, rows[1:]):
        dt = (now["_t"] - prev["_t"]).total_seconds()
        dtemp = now["T_C"] - prev["T_C"]
        energy = now["Q_net_W"] * dt
        u_t = err(specs["T_C"], prev["T_C"]) + err(specs["T_C"], now["T_C"])
        u_q = err(specs["Q_net_W"], now["Q_net_W"])
        u_energy = u_q * dt + (abs(now["Q_net_W"]) + u_q) * u_dt
        if abs(energy) >= 1000:
            sign = 1 if energy > 0 else -1
            e_min, e_max = abs(energy) - u_energy, abs(energy) + u_energy
            t_min, t_max = sign * dtemp - u_t, sign * dtemp + u_t
            if e_min <= 0 or t_min <= 0:
                weak_capacity += 1
            else:
                capacity_bounds.append((e_min / t_max, e_max / t_min))
        if abs(now["P_cmd_W"] - prev["P_cmd_W"]) > 1e-6:
            continue
        cmd = now["P_cmd_W"]
        initial = prev["P_actual_W"] - cmd
        final = now["P_actual_W"] - cmd
        if abs(initial) < 1000:
            continue
        u_cmd = err(specs["P_cmd_W"], cmd)
        u_initial = err(specs["P_actual_W"], prev["P_actual_W"]) + u_cmd
        u_final = err(specs["P_actual_W"], now["P_actual_W"]) + u_cmd
        if abs(initial) <= u_initial or abs(final) <= u_final:
            weak_tau += 1
            continue
        r_min = (abs(final) - u_final) / (abs(initial) + u_initial)
        r_max = (abs(final) + u_final) / (abs(initial) - u_initial)
        if not (0 < r_min <= r_max < 1):
            weak_tau += 1
            continue
        tau_bounds.append(((dt - u_dt) / (-math.log(r_min)),
                           (dt + u_dt) / (-math.log(r_max))))
    if len(capacity_bounds) < 12:
        raise ValueError("A57_CAPACITY_UNCERTAINTY_UNIDENTIFIABLE")
    if len(tau_bounds) < 4:
        raise ValueError("A57_COMPRESSOR_UNCERTAINTY_UNIDENTIFIABLE")
    cap = baseline["a55_capacity_J_per_K"]
    tau = baseline["a55_compressor_tau_s"]
    # Envelope spans ALL usable intervals; not a statistical CI.
    cap_lo, cap_hi = min(x[0] for x in capacity_bounds), max(x[1] for x in capacity_bounds)
    tau_lo, tau_hi = min(x[0] for x in tau_bounds), max(x[1] for x in tau_bounds)
    if not (cap_lo <= cap <= cap_hi and tau_lo <= tau <= tau_hi):
        raise ValueError("A57_BASELINE_OUTSIDE_ERROR_ENVELOPE")
    return {
        "status": "SYNTHETIC_QA_ONLY" if meta["source_kind"] == "synthetic_test" else "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA",
        "asset_id": meta["asset_id"], "source_kind": meta["source_kind"],
        "csv_sha256": sha(csv_path), "metadata_sha256": sha(metadata_path),
        "uncertainty_sha256": sha(bounds_path), "a56_sha256": sha(A56_FILE),
        "timebase": "UTC", "time_sync_method": sync["method"],
        "interval_time_error_bound_s": u_dt,
        "capacity": {"baseline_J_per_K": cap, "lower_J_per_K": cap_lo,
                     "upper_J_per_K": cap_hi, "usable_intervals": len(capacity_bounds),
                     "uncertain_intervals": weak_capacity},
        "compressor_tau": {"baseline_s": tau, "lower_s": tau_lo,
                           "upper_s": tau_hi, "usable_intervals": len(tau_bounds),
                           "uncertain_intervals": weak_tau},
        "error_model": "conservative supplied absolute/relative worst-case bounds; independent per-sample bound; NOT confidence intervals",
        "independent_calibration_verified": False, "safe_operating_limits_certified": False,
        "physical_release": False,
    }
