"""Build deliberately synthetic A58 document bundle; no real vendor/calibration claims."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from a58_document_gate import A57_DIR, SENSORS, sha


def write_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def build(root: Path) -> Path:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(exist_ok=True)
    src = A57_DIR / "DEMO_SYNTHETIC"
    for name in ("telemetry.csv", "metadata.json"):
        shutil.copyfile(src / name, root / name)
    uncertainty = json.loads((src / "uncertainty.json").read_text(encoding="utf-8"))
    asset = uncertainty["asset_id"]
    common = {
        "asset_id": asset, "issuer": "Synthetic QA fixture generator",
        "issued_utc": "2026-10-01T00:00:00Z",
        "valid_until_utc": "2027-10-27T00:00:00Z",
    }
    docs = []
    for sensor, unit in SENSORS.items():
        filename = "cal_" + sensor + ".txt"
        p = root / "docs" / filename
        p.write_text("SYNTHETIC TEST ONLY. NOT A REAL CALIBRATION CERTIFICATE.\n"
                     + "Sensor: " + sensor + "\n", encoding="utf-8")
        h = sha(p)
        uncertainty["sensors"][sensor]["calibration_document_sha256"] = h
        docs.append({
            **common, "id": "QA-CAL-" + sensor, "kind": "calibration",
            "file": "docs/" + filename, "sha256": h, "sensor": sensor,
            "unit": unit, "calibration_ref": uncertainty["calibration_ref"],
            "abs_error_bound": uncertainty["sensors"][sensor]["abs_error_bound"],
            "relative_error_bound": uncertainty["sensors"][sensor]["relative_error_bound"],
        })
    sync_file = root / "docs" / "time_sync.txt"
    sync_file.write_text("SYNTHETIC TEST ONLY. NOT A REAL CLOCK SYNC LOG.\n", encoding="utf-8")
    docs.append({**common, "id": "QA-TIME", "kind": "time_sync",
                 "file": "docs/time_sync.txt", "sha256": sha(sync_file),
                 **uncertainty["time_sync"]})
    vendor_file = root / "docs" / "vendor_map.txt"
    vendor_file.write_text("SYNTHETIC TEST ONLY. NOT A VENDOR PERFORMANCE MAP.\n", encoding="utf-8")
    docs.append({**common, "id": "QA-VENDOR", "kind": "vendor_map",
                 "file": "docs/vendor_map.txt", "sha256": sha(vendor_file),
                 "temperature_unit": "degC", "power_unit": "W",
                 "min_T_C": 0, "max_T_C": 100, "max_P_W": 150000})
    write_json(root / "uncertainty.json", uncertainty)
    write_json(root / "document_manifest.json", {
        "schema_version": "a58.1", "asset_id": asset,
        "source_kind": "synthetic_test", "physical_release": False,
        "independent_issuer_authentication": False,
        "telemetry_sha256": sha(root / "telemetry.csv"),
        "metadata_sha256": sha(root / "metadata.json"),
        "uncertainty_sha256": sha(root / "uncertainty.json"),
        "documents": docs
    })
    return root


if __name__ == "__main__":
    build(Path(__file__).resolve().parent / "DEMO_SYNTHETIC")
    print("Synthetic-only A58 fixture created")
