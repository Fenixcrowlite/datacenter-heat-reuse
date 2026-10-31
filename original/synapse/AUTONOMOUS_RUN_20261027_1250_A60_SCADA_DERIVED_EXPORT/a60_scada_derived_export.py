"""A60: export EXISTING simulated SCADA trajectories to an analysis-ready schema.

Strictly DERIVED_SIMULATION. Never substitutes for measured calibration inputs.
Does not access hardware, the network, or change any upstream CSV.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import tempfile
from pathlib import Path

TARGET = ("time_s", "T_pool_C", "Q_DC_W", "Q_reject_W", "Q_pool_W",
          "Q_DH_W", "P_HP_W", "E_TES_J")
SIGNALS = TARGET[1:]
SCHEMAS = {
    "scada_v08": {
        "time_s": "cas_h", "T_pool_C": "T_pool_C", "Q_DC_W": "Q_DC_eff_W",
        "Q_reject_W": "Q_reject_physical_W", "Q_pool_W": "Q_pool_phys_W",
        "Q_DH_W": "Q_DH_W", "P_HP_W": "P_HP_W", "E_TES_J": "E_TES_J",
    },
    "scada_v09_matlab": {
        "time_s": "cas_h", "T_pool_C": "T_pool_C", "Q_DC_W": "Q_DC_W",
        "Q_reject_W": "Q_reject_W", "Q_pool_W": "Q_pool_W",
        "Q_DH_W": "Q_DH_W", "P_HP_W": "P_HP_W", "E_TES_J": "E_TES_J",
    },
}
# These are genuinely different physical measurements. Do not map pool temperature
# or simulated heat flows into A55's heat-capacity experiment by name similarity.
CALIBRATION_MISSING = (
    "timestamp_utc", "asset_id", "calibration_ref", "T_C", "Q_net_W",
    "P_cmd_W", "P_actual_W", "trip_state", "Q_residual_W", "Q_nominal_W",
)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def classify(headers: list[str]) -> str:
    if not headers or len(headers) != len(set(headers)):
        raise ValueError("DUPLICATE_OR_EMPTY_HEADERS")
    matches = [name for name, mapping in SCHEMAS.items()
               if set(mapping.values()).issubset(headers)]
    if len(matches) != 1:
        raise ValueError("UNKNOWN_OR_AMBIGUOUS_SCADA_SCHEMA")
    return matches[0]


def load(path: Path) -> tuple[str, list[dict[str, float]]]:
    if not path.is_file() or path.is_symlink():
        raise ValueError("INVALID_SOURCE")
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        schema = classify(reader.fieldnames or [])
        mapping = SCHEMAS[schema]
        data = []
        last_time = -1.0
        for record in reader:
            if None in record or any(v is None for v in record.values()):
                raise ValueError("MALFORMED_CSV")
            row = {}
            for target, source in mapping.items():
                try:
                    val = float(record[source])
                except (TypeError, ValueError) as exc:
                    raise ValueError("NON_NUMERIC_" + target) from exc
                if not math.isfinite(val):
                    raise ValueError("NONFINITE_" + target)
                row[target] = val * 3600.0 if target == "time_s" else val
            t = row["time_s"]
            if not math.isfinite(t) or t < 0 or t <= last_time:
                raise ValueError("NON_MONOTONIC_TIME")
            if data and t - last_time > 86400:
                raise ValueError("TIME_GAP_OVER_24H")
            last_time = t
            data.append(row)
    if len(data) < 3:
        raise ValueError("INSUFFICIENT_ROWS")
    return schema, data


def metrics(data: list[dict[str, float]]) -> dict:
    energies = {key: 0.0 for key in ("Q_DC_W", "Q_reject_W", "Q_pool_W",
                                     "Q_DH_W", "P_HP_W")}
    for left, right in zip(data, data[1:]):
        dt = right["time_s"] - left["time_s"]
        for key in energies:
            energies[key] += (left[key] + right[key]) * 0.5 * dt
    return {
        "samples": len(data),
        "duration_h": (data[-1]["time_s"] - data[0]["time_s"]) / 3600.0,
        "temperature_pool_min_C": min(row["T_pool_C"] for row in data),
        "temperature_pool_max_C": max(row["T_pool_C"] for row in data),
        "E_TES_delta_MWh": (data[-1]["E_TES_J"] - data[0]["E_TES_J"]) / 3.6e9,
        "integrated_MWh": {key: value / 3.6e9 for key, value in energies.items()},
        "integration": "trapezoidal; time from relative cas_h, not UTC",
    }


def export(source: Path, destination: Path) -> dict:
    source, destination = Path(source), Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("DESTINATION_EXISTS")
    if not destination.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    schema, rows = load(source)
    source_hash = sha(source)
    result = {
        "schema_version": "a60.1",
        "source_schema": schema,
        "source_kind": "derived_simulation",
        "source_csv_sha256": source_hash,
        "source_path": str(source.resolve()),
        "physical_release": False,
        "measurement_calibration_ready": False,
        "missing_for_A55": list(CALIBRATION_MISSING),
        "warning": "Simulation output only. Relative time, no calibration certificate, no measured compressor step response.",
        "metrics": metrics(rows),
    }
    temp = Path(tempfile.mkdtemp(prefix=".a60-staging-", dir=destination.parent))
    try:
        with (temp / "analysis_timeseries.csv").open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=TARGET, lineterminator="\n")
            writer.writeheader()
            for row in rows:
                writer.writerow({key: format(row[key], ".15g") for key in TARGET})
        result["analysis_csv_sha256"] = sha(temp / "analysis_timeseries.csv")
        (temp / "summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.rename(temp, destination)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(export(args.source, args.destination), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
