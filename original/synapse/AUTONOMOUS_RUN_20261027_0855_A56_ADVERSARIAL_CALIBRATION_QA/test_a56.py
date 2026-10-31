"""A56 adversarial tests: intentionally corrupt synthetic A55 fixtures."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

import a56_quality_gate as gate
from test_a55 import fixture, rewrite
import a55_calibration_gate as a55


class A56Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv, self.meta, self.rows, self.metadata = fixture(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        rewrite(self.csv, self.meta, self.rows, self.metadata)

    def test_baseline_synthetic_passes_without_release(self):
        result = gate.audit(self.csv, self.meta)
        self.assertEqual(result["status"], "SYNTHETIC_QA_ONLY")
        self.assertAlmostEqual(result["a55_capacity_J_per_K"], 8e6, delta=1)
        self.assertAlmostEqual(result["a55_compressor_tau_s"], 300, delta=.01)
        self.assertAlmostEqual(result["a55_residual_fraction"], .12, places=9)
        self.assertLess(result["capacity_holdout_relative_drift"], 1e-6)
        self.assertFalse(result["physical_release"])

    def test_compressor_spike_a55_accepts_a56_rejects(self):
        self.rows[10]["P_actual_W"] = str(float(self.rows[10]["P_actual_W"]) * 1.8)
        self.save()
        self.assertFalse(a55.calibrate(self.csv, self.meta)["physical_release"])
        with self.assertRaisesRegex(ValueError, "A56_COMPRESSOR_NONCONTRACTIVE_STEP"):
            gate.audit(self.csv, self.meta)

    def test_subresolution_sign_reversal_a55_accepts_a56_rejects(self):
        self.rows[12]["T_C"] = str(float(self.rows[11]["T_C"]) - 0.005)
        self.save()
        self.assertFalse(a55.calibrate(self.csv, self.meta)["physical_release"])
        with self.assertRaisesRegex(ValueError, "A56_SUBRESOLUTION_ENERGY_SIGN_REVERSAL"):
            gate.audit(self.csv, self.meta)

    def test_capacity_drift_a55_accepts_a56_rejects(self):
        for row in self.rows[36:]:
            row["Q_net_W"] = "2400"
        self.save()
        self.assertFalse(a55.calibrate(self.csv, self.meta)["physical_release"])
        with self.assertRaisesRegex(ValueError, "A56_CAPACITY_HOLDOUT_DRIFT"):
            gate.audit(self.csv, self.meta)

    def test_zero_energy_temperature_rise_rejected(self):
        self.rows[16]["Q_net_W"] = "0"
        self.save()
        with self.assertRaisesRegex(ValueError, "A56_TEMPERATURE_WITHOUT_NET_ENERGY"):
            gate.audit(self.csv, self.meta)

    def test_hash_tampering_rejected(self):
        self.csv.write_text(self.csv.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            gate.audit(self.csv, self.meta)

    def test_missing_calibration_record_rejected(self):
        self.metadata.pop("sensor_calibration_record")
        self.meta.write_text(json.dumps(self.metadata), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_PROVENANCE"):
            gate.audit(self.csv, self.meta)

    def test_real_claim_is_never_certified(self):
        self.metadata["source_kind"] = "real_telemetry"
        self.meta.write_text(json.dumps(self.metadata), encoding="utf-8")
        result = gate.audit(self.csv, self.meta)
        self.assertEqual(result["status"], "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA")
        self.assertFalse(result["physical_release"])
        self.assertFalse(result["measurement_uncertainty_verified"])

    def test_no_compressor_excitation_rejected(self):
        for row in self.rows:
            row["P_cmd_W"] = "100000"
            row["P_actual_W"] = "100000"
        self.save()
        with self.assertRaisesRegex(ValueError, "A56_INSUFFICIENT_COMPRESSOR_EXCITATION"):
            gate.audit(self.csv, self.meta)

    def test_nonmonotonic_timestamp_rejected(self):
        self.rows[8]["timestamp_utc"] = self.rows[7]["timestamp_utc"]
        self.save()
        with self.assertRaisesRegex(ValueError, "NONMONOTONIC"):
            gate.audit(self.csv, self.meta)

    def test_a55_source_is_immutable(self):
        self.assertEqual(gate._sha(gate.A55_FILE), gate.EXPECTED_A55_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
