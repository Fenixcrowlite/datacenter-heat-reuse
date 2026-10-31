"""A59: deterministic, fail-closed SCADA CSV -> A55 telemetry import.

Does not infer unmeasured channels, manufacture certificates or authorize hardware.
No network/device access. Writes only to a new, caller-selected output directory.
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
from datetime import datetime
from pathlib import Path

FIELDS = ("timestamp_utc", "asset_id", "calibration_ref", "T_C", "Q_net_W",
          "P_cmd_W", "P_actual_W", "trip_state", "Q_residual_W", "Q_nominal_W")
NUMERIC = ("T_C", "Q_net_W", "P_cmd_W", "P_actual_W", "Q_residual_W", "Q_nominal_W")
POWER = set(NUMERIC) - {"T_C"}
CONVERSIONS = {"degC": (1., 0.), "K": (1., -273.15),
               "W": (1., 0.), "kW": (1000., 0.), "MW": (1000000., 0.)}


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def utc(text: str):
    if not isinstance(text, str):
        raise ValueError("INVALID_UTC")
    try:
        stamp = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_UTC") from exc
    if stamp.tzinfo is None or stamp.utcoffset().total_seconds() != 0:
        raise ValueError("UTC_REQUIRED")
    return stamp


def configuration(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(obj, dict) or obj.get("schema_version") != "a59.1":
        raise ValueError("INVALID_MAPPING_VERSION")
    if obj.get("source_kind") not in ("real_telemetry", "synthetic_test"):
        raise ValueError("SOURCE_KIND_MUST_BE_EXPLICIT")
    for field in ("asset_id", "calibration_ref", "provenance_notes"):
        if not isinstance(obj.get(field), str) or not obj[field].strip():
            raise ValueError("MISSING_" + field)
    columns = obj.get("columns")
    units = obj.get("units")
    if not isinstance(columns, dict) or set(columns) != set(FIELDS):
        raise ValueError("ALL_SOURCE_COLUMNS_REQUIRED")
    if any(not isinstance(v, str) or not v.strip() for v in columns.values()):
        raise ValueError("INVALID_COLUMN_NAME")
    if len(set(columns.values())) != len(FIELDS):
        raise ValueError("DUPLICATE_SOURCE_MAPPING")
    if not isinstance(units, dict) or set(units) != set(NUMERIC):
        raise ValueError("ALL_UNITS_REQUIRED")
    for key, unit in units.items():
        if unit not in (("degC", "K") if key == "T_C" else ("W", "kW", "MW")):
            raise ValueError("INVALID_UNIT_" + key)
    return obj


def normalize(raw: Path, cfg: dict):
    with raw.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)):
            raise ValueError("DUPLICATE_CSV_HEADERS")
        if not set(cfg["columns"].values()).issubset(headers):
            raise ValueError("MISSING_CSV_COLUMNS")
        previous = None
        rows = []
        for row in reader:
            if None in row or any(value is None for value in row.values()):
                raise ValueError("MALFORMED_CSV_ROW")
            converted = {}
            for target, source in cfg["columns"].items():
                value = row[source].strip()
                if target in NUMERIC:
                    try:
                        n = float(value)
                    except ValueError as exc:
                        raise ValueError("NON_NUMERIC_" + target) from exc
                    if not math.isfinite(n):
                        raise ValueError("NONFINITE_" + target)
                    factor, offset = CONVERSIONS[cfg["units"][target]]
                    n = n * factor + offset
                    if not math.isfinite(n):
                        raise ValueError("CONVERSION_OVERFLOW")
                    if target in POWER and target != "Q_net_W" and n < 0:
                        raise ValueError("NEGATIVE_POWER_" + target)
                    converted[target] = format(n, ".15g")
                else:
                    converted[target] = value
            if converted["asset_id"] != cfg["asset_id"]:
                raise ValueError("ASSET_ID_MISMATCH")
            if converted["calibration_ref"] != cfg["calibration_ref"]:
                raise ValueError("CALIBRATION_REF_MISMATCH")
            if converted["trip_state"] not in ("RUN", "TRIPPED"):
                raise ValueError("INVALID_TRIP_STATE")
            stamp = utc(converted["timestamp_utc"])
            if previous is not None and not 0 < (stamp - previous).total_seconds() <= 3600:
                raise ValueError("TIMESTAMP_GAP_OR_ORDER")
            previous = stamp
            rows.append(converted)
    if len(rows) < 20:
        raise ValueError("INSUFFICIENT_ROWS")
    return rows


def ingest(raw: Path, mapping: Path, destination: Path) -> dict:
    raw, mapping, destination = Path(raw), Path(mapping), Path(destination)
    if not raw.is_file() or not mapping.is_file():
        raise ValueError("MISSING_INPUT")
    if raw.is_symlink() or mapping.is_symlink():
        raise ValueError("SYMLINK_INPUT")
    if destination.exists() or destination.is_symlink():
        raise ValueError("DESTINATION_EXISTS")
    if not destination.parent.is_dir():
        raise ValueError("DESTINATION_PARENT_MISSING")
    cfg = configuration(mapping)
    rows = normalize(raw, cfg)
    source_sha, map_sha = digest(raw), digest(mapping)
    temp = Path(tempfile.mkdtemp(prefix=".a59-staging-", dir=destination.parent))
    try:
        csv_path = temp / "telemetry.csv"
        with csv_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        normalized_sha = digest(csv_path)
        metadata = {
            "asset_id": cfg["asset_id"], "source_kind": cfg["source_kind"],
            "sensor_calibration_record": cfg["calibration_ref"],
            "original_csv_sha256": normalized_sha,
            "provenance_notes": cfg["provenance_notes"],
        }
        (temp / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        provenance = {
            "schema_version": "a59.1", "source_kind": cfg["source_kind"],
            "raw_csv_path": str(raw.resolve()), "raw_csv_sha256": source_sha,
            "mapping_path": str(mapping.resolve()), "mapping_sha256": map_sha,
            "normalized_csv_sha256": normalized_sha,
            "metadata_sha256": digest(temp / "metadata.json"),
            "rows": len(rows), "physical_release": False,
            "sensor_certificates_verified": False, "time_sync_verified": False,
            "vendor_map_verified": False,
            "next_gate": "Supply real uncertainty.json and authenticated docs for A57/A58; do not synthesize them.",
        }
        (temp / "provenance.json").write_text(json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.rename(temp, destination)
        return provenance
    finally:
        if temp.exists():
            shutil.rmtree(temp)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw_csv", type=Path)
    parser.add_argument("mapping_json", type=Path)
    parser.add_argument("new_output_directory", type=Path)
    args = parser.parse_args()
    print(json.dumps(ingest(args.raw_csv, args.mapping_json, args.new_output_directory), indent=2))


if __name__ == "__main__":
    main()
