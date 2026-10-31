import copy
import csv
import json
import math
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import a59_scada_ingest as mod

A55 = Path(__file__).resolve().parent.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE"
sys.path.insert(0, str(A55))
import a55_calibration_gate as a55


def fixture(root: Path):
    raw = root / "scada_export.csv"
    cfg_path = root / "mapping.json"
    config = {
        "schema_version": "a59.1", "source_kind": "synthetic_test",
        "asset_id": "TEST-LOOP-NOT-REAL", "calibration_ref": "SYNTHETIC-CAL-ONLY",
        "provenance_notes": "Explicitly synthetic fixture, not real SCADA data",
        "columns": {
            "timestamp_utc": "Time", "asset_id": "Equipment",
            "calibration_ref": "Calibration", "T_C": "Temperature_K",
            "Q_net_W": "Heat_kW", "P_cmd_W": "Command_kW",
            "P_actual_W": "Actual_kW", "trip_state": "Trip",
            "Q_residual_W": "Residual_kW", "Q_nominal_W": "Nominal_kW",
        },
        "units": {"T_C": "K", "Q_net_W": "kW", "P_cmd_W": "kW",
                  "P_actual_W": "kW", "Q_residual_W": "kW", "Q_nominal_W": "kW"},
    }
    rows = []
    for i in range(30):
        rows.append({
            "Time": (datetime(2026, 10, 27, tzinfo=timezone.utc) + timedelta(seconds=60*i)).isoformat(),
            "Equipment": config["asset_id"], "Calibration": config["calibration_ref"],
            "Temperature_K": f"{303.15 + .015*i:.9f}", "Heat_kW": "2",
            "Command_kW": "100", "Actual_kW": f"{100*(1-math.exp(-i*60/300)):.12f}",
            "Trip": "TRIPPED" if i >= 24 else "RUN",
            "Residual_kW": "12", "Nominal_kW": "100",
        })
    with raw.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    cfg_path.write_text(json.dumps(config), encoding="utf-8")
    return raw, cfg_path, rows, config


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw, self.mapping, self.rows, self.config = fixture(self.root)
        self.out = self.root / "normalized"

    def remap(self, **changes):
        cfg = copy.deepcopy(self.config)
        cfg.update(changes)
        self.mapping.write_text(json.dumps(cfg), encoding="utf-8")

    def rewrite_rows(self, rows):
        with self.raw.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    def rejects(self, code):
        with self.assertRaisesRegex(ValueError, code):
            mod.ingest(self.raw, self.mapping, self.out)
        self.assertFalse(self.out.exists(), "Failed import must not leave a partial bundle")

    def test_full_pipeline_a55_calibration(self):
        proof = mod.ingest(self.raw, self.mapping, self.out)
        rows, meta = a55.load_telemetry(self.out / "telemetry.csv", self.out / "metadata.json")
        result = a55.calibrate(self.out / "telemetry.csv", self.out / "metadata.json")
        self.assertEqual(len(rows), 30)
        self.assertEqual(proof["source_kind"], "synthetic_test")
        self.assertFalse(proof["physical_release"])
        self.assertAlmostEqual(result["capacity"]["value_J_per_K"], 8e6, delta=1)
        self.assertAlmostEqual(result["compressor_tau"]["median_s"], 300, delta=.01)
        self.assertAlmostEqual(result["residual_fraction"]["median_fraction"], .12)
        self.assertEqual(meta["original_csv_sha256"], mod.digest(self.out / "telemetry.csv"))
        self.assertEqual(proof["raw_csv_sha256"], mod.digest(self.raw))
        self.assertEqual(proof["mapping_sha256"], mod.digest(self.mapping))

    def test_deterministic_normalization(self):
        mod.ingest(self.raw, self.mapping, self.out)
        first = mod.digest(self.out / "telemetry.csv")
        mod.ingest(self.raw, self.mapping, self.root / "second")
        self.assertEqual(first, mod.digest(self.root / "second" / "telemetry.csv"))

    def test_output_collision(self):
        self.out.mkdir()
        with self.assertRaisesRegex(ValueError, "DESTINATION_EXISTS"):
            mod.ingest(self.raw, self.mapping, self.out)
        self.assertEqual(list(self.out.iterdir()), [])

    def test_unknown_unit(self):
        cfg = copy.deepcopy(self.config)
        cfg["units"]["T_C"] = "F"
        self.remap(**cfg)
        self.rejects("INVALID_UNIT")

    def test_missing_mapping(self):
        cfg = copy.deepcopy(self.config)
        del cfg["columns"]["Q_net_W"]
        self.remap(**cfg)
        self.rejects("ALL_SOURCE_COLUMNS_REQUIRED")

    def test_duplicate_source_mapping(self):
        cfg = copy.deepcopy(self.config)
        cfg["columns"]["P_actual_W"] = cfg["columns"]["P_cmd_W"]
        self.remap(**cfg)
        self.rejects("DUPLICATE_SOURCE_MAPPING")

    def test_duplicate_json_key(self):
        self.mapping.write_text(self.mapping.read_text()[:-1] + ', "asset_id": "FAKE"}')
        self.rejects("DUPLICATE_JSON_KEY")

    def test_missing_channel_in_csv(self):
        rows = [{k: v for k, v in r.items() if k != "Residual_kW"} for r in self.rows]
        self.rewrite_rows(rows)
        self.rejects("MISSING_CSV_COLUMNS")

    def test_mixed_asset(self):
        rows = copy.deepcopy(self.rows)
        rows[8]["Equipment"] = "OTHER"
        self.rewrite_rows(rows)
        self.rejects("ASSET_ID_MISMATCH")

    def test_calibration_mismatch(self):
        rows = copy.deepcopy(self.rows)
        rows[5]["Calibration"] = "OTHER"
        self.rewrite_rows(rows)
        self.rejects("CALIBRATION_REF_MISMATCH")

    def test_non_utc(self):
        rows = copy.deepcopy(self.rows)
        rows[4]["Time"] = "2026-10-27T00:04:00+01:00"
        self.rewrite_rows(rows)
        self.rejects("UTC_REQUIRED")

    def test_nonmonotonic(self):
        rows = copy.deepcopy(self.rows)
        rows[4]["Time"] = rows[3]["Time"]
        self.rewrite_rows(rows)
        self.rejects("TIMESTAMP_GAP_OR_ORDER")

    def test_nan(self):
        rows = copy.deepcopy(self.rows)
        rows[10]["Heat_kW"] = "NaN"
        self.rewrite_rows(rows)
        self.rejects("NONFINITE")

    def test_negative_power(self):
        rows = copy.deepcopy(self.rows)
        rows[7]["Actual_kW"] = "-2"
        self.rewrite_rows(rows)
        self.rejects("NEGATIVE_POWER")

    def test_no_inferred_channel(self):
        rows = copy.deepcopy(self.rows)
        for row in rows:
            row["Heat_kW"] = ""
        self.rewrite_rows(rows)
        self.rejects("NON_NUMERIC")

    def test_minimum_rows(self):
        self.rewrite_rows(self.rows[:10])
        self.rejects("INSUFFICIENT_ROWS")

    def test_invalid_trip(self):
        rows = copy.deepcopy(self.rows)
        rows[2]["Trip"] = "UNKNOWN"
        self.rewrite_rows(rows)
        self.rejects("INVALID_TRIP_STATE")


if __name__ == "__main__":
    unittest.main()
