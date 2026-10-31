"""Independent A55 regression: all telemetry in tests is synthetic and isolated."""
import csv
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import a55_calibration_gate as g


def fixture(root, source_kind="synthetic_test"):
    root = Path(root)
    path = root / "telemetry.csv"
    meta = root / "metadata.json"
    t = datetime(2026, 10, 27, tzinfo=timezone.utc)
    rows = []
    p = 0.0
    temperature = 30.0
    for i in range(65):
        cmd = 100000.0 if i < 35 else 0.0
        if i:
            p = cmd + (p - cmd) * math.exp(-60.0 / 300.0)
            temperature += 2000.0 * 60.0 / 8e6
        rows.append(dict(timestamp_utc=(t + timedelta(seconds=60*i)).isoformat(),
                         asset_id="TEST-LOOP-NOT-REAL",
                         calibration_ref="SYNTHETIC-CAL-ONLY",
                         T_C=f"{temperature:.10f}", Q_net_W="2000",
                         P_cmd_W=f"{cmd:.10f}", P_actual_W=f"{p:.10f}",
                         trip_state="TRIPPED" if i >= 50 else "RUN",
                         Q_residual_W="12000", Q_nominal_W="100000"))
    write_rows(path, rows)
    m = dict(asset_id="TEST-LOOP-NOT-REAL", source_kind=source_kind,
             sensor_calibration_record="SYNTHETIC-CAL-ONLY",
             original_csv_sha256=g.sha(path),
             provenance_notes="Generated for unit tests; not real telemetry")
    meta.write_text(json.dumps(m), encoding="utf-8")
    return path, meta, rows, m


def write_rows(path, rows):
    with Path(path).open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=g.FIELDS)
        w.writeheader()
        w.writerows(rows)


def rewrite(path, meta, rows, m):
    write_rows(path, rows)
    m["original_csv_sha256"] = g.sha(path)
    meta.write_text(json.dumps(m), encoding="utf-8")


class A55Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path, self.meta, self.rows, self.m = fixture(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_synthetic_recovers_three_parameters(self):
        r = g.calibrate(self.path, self.meta)
        self.assertEqual(r["status"], "SYNTHETIC_TEST_ONLY")
        self.assertAlmostEqual(r["capacity"]["value_J_per_K"], 8e6, delta=1)
        self.assertAlmostEqual(r["compressor_tau"]["median_s"], 300, delta=0.01)
        self.assertAlmostEqual(r["residual_fraction"]["median_fraction"], .12, places=10)
        self.assertFalse(r["physical_release"])

    def test_a54_provenance_not_promoted(self):
        r = g.audit_a54()
        self.assertEqual(r["A54_parameter_provenance"][0], "D")
        self.assertEqual(len(r["water_only_equivalent_m3"]), 3)
        self.assertFalse(r["source_class_promoted"])
        self.assertFalse(r["safe_operating_limits_certified"])

    def test_source_tampering_rejected(self):
        self.path.write_text(self.path.read_text() + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            g.calibrate(self.path, self.meta)

    def test_missing_provenance_rejected(self):
        self.m.pop("sensor_calibration_record")
        self.meta.write_text(json.dumps(self.m), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_PROVENANCE"):
            g.calibrate(self.path, self.meta)

    def test_nonmonotonic_timestamps_rejected(self):
        self.rows[8]["timestamp_utc"] = self.rows[7]["timestamp_utc"]
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC"):
            g.calibrate(self.path, self.meta)

    def test_real_claim_does_not_certify(self):
        self.m["source_kind"] = "real_telemetry"
        self.meta.write_text(json.dumps(self.m), encoding="utf-8")
        r = g.calibrate(self.path, self.meta)
        self.assertEqual(r["status"], "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA")
        self.assertFalse(r["independent_sensor_calibration_verified"])
        self.assertFalse(r["physical_release"])

    def test_wrong_energy_sign_rejected(self):
        self.rows[8]["Q_net_W"] = "-2000"
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "INCONSISTENT_ENERGY_SIGN"):
            g.calibrate(self.path, self.meta)

    def test_residual_drift_rejected(self):
        self.rows[54]["Q_residual_W"] = "70000"
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "RESIDUAL_NOT_CONSTANT"):
            g.calibrate(self.path, self.meta)

    def test_no_compressor_excitation_rejected(self):
        for r in self.rows:
            r["P_cmd_W"] = "100000"
            r["P_actual_W"] = "100000"
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "COMPRESSOR_TAU_NOT_IDENTIFIABLE"):
            g.calibrate(self.path, self.meta)

    def test_calibration_record_mismatch_rejected(self):
        self.rows[2]["calibration_ref"] = "UNKNOWN"
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "CALIBRATION_RECORD_MISMATCH"):
            g.calibrate(self.path, self.meta)

    def test_nonfinite_measurement_rejected(self):
        self.rows[5]["T_C"] = "NaN"
        rewrite(self.path, self.meta, self.rows, self.m)
        with self.assertRaisesRegex(ValueError, "NONFINITE_T_C"):
            g.calibrate(self.path, self.meta)

    def test_insufficient_samples_rejected(self):
        rewrite(self.path, self.meta, self.rows[:9], self.m)
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT_SAMPLES"):
            g.calibrate(self.path, self.meta)


if __name__ == "__main__":
    unittest.main(verbosity=2)
