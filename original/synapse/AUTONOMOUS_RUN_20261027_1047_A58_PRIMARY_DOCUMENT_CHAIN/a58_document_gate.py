"""A58: independently bind A57's claimed calibration hashes to actual local documents.
This validates file integrity and internal consistency, NOT issuer authenticity or safety.
No network, device control, or writes in audit().
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
A57_DIR = HERE.parent / "AUTONOMOUS_RUN_20261027_0952_A57_UNCERTAINTY_TIMEBASE_QA"
A57_FILE = A57_DIR / "a57_uncertainty_gate.py"
EXPECTED_A57_SHA = "309fdf0ab614a0c2f858cde0066cafae5d3f9039fab2eeab85b080d30e19ec1f"
# SHA is populated from a verified on-host digest during setup, not assumed from history.
if str(A57_DIR) not in sys.path:
    sys.path.insert(0, str(A57_DIR))
import a57_uncertainty_gate as a57

SENSORS = {"T_C": "degC", "Q_net_W": "W", "P_cmd_W": "W", "P_actual_W": "W"}
REQUIRED_KINDS = {"calibration", "vendor_map", "time_sync"}
HEX = set("0123456789abcdef")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique(pairs):
    out = {}
    for key, val in pairs:
        if key in out:
            raise ValueError("A58_DUPLICATE_JSON_KEY")
        out[key] = val
    return out


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)
    if not isinstance(data, dict):
        raise ValueError("A58_NOT_OBJECT")
    return data


def digest(value) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(x not in HEX for x in value):
        raise ValueError("A58_INVALID_SHA")
    return value


def number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("A58_BAD_NUMBER_" + name)
    n = float(value)
    if not math.isfinite(n) or n < 0:
        raise ValueError("A58_BAD_NUMBER_" + name)
    return n


def stamp(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("A58_BAD_TIMESTAMP")
    try:
        t = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError("A58_BAD_TIMESTAMP") from e
    if t.tzinfo is None or t.utcoffset().total_seconds() != 0:
        raise ValueError("A58_NOT_UTC")
    return t


def doc_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative.startswith("docs/") or "\\" in relative:
        raise ValueError("A58_BAD_DOCUMENT_PATH")
    parts = Path(relative).parts
    if ".." in parts or "." in parts or len(parts) != 2:
        raise ValueError("A58_PATH_TRAVERSAL")
    p = root / relative
    if p.is_symlink() or (root / "docs").is_symlink() or not p.is_file():
        raise ValueError("A58_MISSING_OR_SYMLINK_DOCUMENT")
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError("A58_PATH_ESCAPE")
    if not 0 < p.stat().st_size <= 8_000_000:
        raise ValueError("A58_BAD_DOCUMENT_SIZE")
    return p


def audit(root: Path) -> dict:
    root = Path(root)
    if not root.is_dir():
        raise ValueError("A58_BUNDLE_MISSING")
    if sha(A57_FILE) != EXPECTED_A57_SHA:
        raise ValueError("A58_UPSTREAM_A57_CHANGED")
    csv_path, meta_path = root / "telemetry.csv", root / "metadata.json"
    uncertainty_path, manifest_path = root / "uncertainty.json", root / "document_manifest.json"
    baseline = a57.audit(csv_path, meta_path, uncertainty_path)
    meta, uncertainty, manifest = (load_json(p) for p in (meta_path, uncertainty_path, manifest_path))
    if manifest.get("schema_version") != "a58.1":
        raise ValueError("A58_SCHEMA_VERSION")
    if manifest.get("asset_id") != meta["asset_id"] or manifest.get("source_kind") != meta["source_kind"]:
        raise ValueError("A58_ASSET_SOURCE_MISMATCH")
    for key, path in (("telemetry_sha256", csv_path), ("metadata_sha256", meta_path),
                      ("uncertainty_sha256", uncertainty_path)):
        if digest(manifest.get(key)) != sha(path):
            raise ValueError("A58_INPUT_HASH_MISMATCH_" + key)
    if manifest.get("physical_release") is not False or manifest.get("independent_issuer_authentication") is not False:
        raise ValueError("A58_UNAUTHORIZED_RELEASE")
    with csv_path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    start, end = stamp(rows[0]["timestamp_utc"]), stamp(rows[-1]["timestamp_utc"])
    docs = manifest.get("documents")
    if not isinstance(docs, list) or len(docs) != 6:
        raise ValueError("A58_DOCUMENT_COUNT")
    seen_ids, seen_sensors, kinds = set(), set(), []
    for doc in docs:
        if not isinstance(doc, dict):
            raise ValueError("A58_BAD_DOCUMENT")
        identifier = doc.get("id")
        if not isinstance(identifier, str) or not identifier.strip() or identifier in seen_ids:
            raise ValueError("A58_DUPLICATE_OR_EMPTY_DOCUMENT_ID")
        seen_ids.add(identifier)
        kind = doc.get("kind")
        if kind not in REQUIRED_KINDS:
            raise ValueError("A58_UNKNOWN_DOCUMENT_KIND")
        kinds.append(kind)
        if doc.get("asset_id") != meta["asset_id"]:
            raise ValueError("A58_DOCUMENT_ASSET_MISMATCH")
        if not isinstance(doc.get("issuer"), str) or len(doc["issuer"].strip()) < 3:
            raise ValueError("A58_MISSING_ISSUER")
        p = doc_file(root, doc.get("file"))
        if digest(doc.get("sha256")) != sha(p):
            raise ValueError("A58_DOCUMENT_HASH_MISMATCH")
        issued, expires = stamp(doc.get("issued_utc")), stamp(doc.get("valid_until_utc"))
        if issued > start or expires < end or expires <= issued:
            raise ValueError("A58_DOCUMENT_OUTSIDE_MEASUREMENT_WINDOW")
        if kind == "calibration":
            sensor = doc.get("sensor")
            if sensor not in SENSORS or sensor in seen_sensors:
                raise ValueError("A58_DUPLICATE_OR_UNKNOWN_SENSOR")
            seen_sensors.add(sensor)
            spec = uncertainty["sensors"][sensor]
            if doc.get("unit") != SENSORS[sensor]:
                raise ValueError("A58_UNIT_MISMATCH")
            if doc.get("calibration_ref") != meta["sensor_calibration_record"]:
                raise ValueError("A58_CALIBRATION_REF_MISMATCH")
            if spec["calibration_document_sha256"] != sha(p):
                raise ValueError("A58_UNBOUND_A57_CERTIFICATE_HASH")
            for k in ("abs_error_bound", "relative_error_bound"):
                if number(doc.get(k), k) != number(spec[k], k):
                    raise ValueError("A58_ERROR_BOUND_CONFLICT")
        elif kind == "time_sync":
            if doc.get("method") != uncertainty["time_sync"]["method"]:
                raise ValueError("A58_TIME_SYNC_METHOD_CONFLICT")
            for key in a57.SYNC_FIELDS:
                if number(doc.get(key), key) != number(uncertainty["time_sync"][key], key):
                    raise ValueError("A58_TIME_SYNC_BOUND_CONFLICT")
            if meta["source_kind"] == "real_telemetry" and doc.get("method") == "synthetic_common_clock":
                raise ValueError("A58_SYNTHETIC_CLOCK_ON_REAL_DATA")
        else:
            if doc.get("temperature_unit") != "degC" or doc.get("power_unit") != "W":
                raise ValueError("A58_VENDOR_UNIT_CONFLICT")
            tmin = number(doc.get("min_T_C"), "min_T_C")
            tmax = number(doc.get("max_T_C"), "max_T_C")
            pmax = number(doc.get("max_P_W"), "max_P_W")
            if not tmin < tmax or pmax <= 0:
                raise ValueError("A58_VENDOR_RANGE_INVALID")
            if any(not tmin <= float(row["T_C"]) <= tmax or
                   abs(float(row["P_actual_W"])) > pmax for row in rows):
                raise ValueError("A58_TELEMETRY_OUTSIDE_DECLARED_VENDOR_RANGE")
    if seen_sensors != set(SENSORS) or kinds.count("time_sync") != 1 or kinds.count("vendor_map") != 1:
        raise ValueError("A58_INCOMPLETE_DOCUMENT_CHAIN")
    return {
        "status": ("SYNTHETIC_DOCUMENT_CHAIN_TEST_ONLY" if meta["source_kind"] == "synthetic_test"
                   else "DOCUMENT_HASHES_MATCH_ISSUER_AUTHENTICITY_UNVERIFIED"),
        "asset_id": meta["asset_id"], "source_kind": meta["source_kind"],
        "document_count": len(docs), "document_sha256": {d["id"]: d["sha256"] for d in docs},
        "manifest_sha256": sha(manifest_path), "A57_source_sha256": sha(A57_FILE),
        "a57_status": baseline["status"], "independent_issuer_authentication": False,
        "physical_release": False, "safe_operating_limits_certified": False,
        "limitations": "SHA checks prove file consistency only; issuer identity, traceable calibration and equipment applicability require independent verification."
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python a58_document_gate.py BUNDLE_DIR")
    print(json.dumps(audit(Path(sys.argv[1])), ensure_ascii=False, indent=2, sort_keys=True))
