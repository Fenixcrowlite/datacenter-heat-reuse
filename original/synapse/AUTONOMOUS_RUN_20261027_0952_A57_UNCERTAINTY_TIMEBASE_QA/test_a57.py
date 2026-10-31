"""A57 regression and adversarial tests; synthetic data, no real calibration."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import a57_uncertainty_gate as gate

A55_DIR = gate.A56_DIR.parent / "AUTONOMOUS_RUN_20261027_0749_A55_PARAMETER_PROVENANCE_GATE"
if str(A55_DIR) not in sys.path:
    sys.path.insert(0, str(A55_DIR))
from test_a55 import fixture, rewrite


class A57Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.csv, self.meta, self.rows, self.metadata = fixture(self.tmp.name)
        self.bounds = Path(self.tmp.name) / "uncertainty.json"
        sensors = {}
        for name, abs_err in (("T_C", .0005), ("Q_net_W", 5),
                              ("P_cmd_W", 20), ("P_actual_W", 20)):
            sensors[name] = {
                "abs_error_bound": abs_err, "relative_error_bound": 0,
                "calibration_ref": "SYNTHETIC-CAL-ONLY",
                "calibration_document_sha256": "0" * 64,
            }
        self.doc = {
            "asset_id": "TEST-LOOP-NOT-REAL", "source_kind": "synthetic_test",
            "source_csv_sha256": gate.sha(self.csv),
            "calibration_ref": "SYNTHETIC-CAL-ONLY", "timebase": "UTC",
            "time_sync": {
                "method": "synthetic_common_clock", "max_abs_clock_offset_s": .1,
                "clock_uncertainty_s": .05,
                "sample_timestamp_uncertainty_s": .05,
                "command_actuation_latency_bound_s": .2,
            },
            "sensors": sensors,
        }
        self.save()

    def tearDown(self):
        self.tmp.cleanup()

    def save(self):
        self.bounds.write_text(json.dumps(self.doc, sort_keys=True), encoding="utf-8")

    def run_audit(self):
        return gate.audit(self.csv, self.meta, self.bounds)

    def test_synthetic_baseline_bounds_cover_known_parameters(self):
        r = self.run_audit()
        self.assertEqual(r["status"], "SYNTHETIC_QA_ONLY")
        self.assertGreaterEqual(r["capacity"]["usable_intervals"], 12)
        self.assertGreaterEqual(r["compressor_tau"]["usable_intervals"], 4)
        self.assertLess(r["capacity"]["lower_J_per_K"], 8e6)
        self.assertGreater(r["capacity"]["upper_J_per_K"], 8e6)
        self.assertLess(r["compressor_tau"]["lower_s"], 300)
        self.assertGreater(r["compressor_tau"]["upper_s"], 300)
        self.assertFalse(r["physical_release"])
        self.assertFalse(r["independent_calibration_verified"])

    def test_deterministic_output(self):
        self.assertEqual(self.run_audit(), self.run_audit())

    def test_mismatched_csv_hash_rejected(self):
        self.doc["source_csv_sha256"] = "f" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "SOURCE_HASH_MISMATCH"):
            self.run_audit()

    def test_mismatched_asset_rejected(self):
        self.doc["asset_id"] = "WRONG-ASSET"
        self.save()
        with self.assertRaisesRegex(ValueError, "ASSET_OR_SOURCE_KIND_MISMATCH"):
            self.run_audit()

    def test_source_kind_mismatch_rejected(self):
        self.doc["source_kind"] = "real_telemetry"
        self.save()
        with self.assertRaisesRegex(ValueError, "ASSET_OR_SOURCE_KIND_MISMATCH"):
            self.run_audit()

    def test_sensor_calibration_mismatch_rejected(self):
        self.doc["sensors"]["T_C"]["calibration_ref"] = "OTHER"
        self.save()
        with self.assertRaisesRegex(ValueError, "SENSOR_CALIBRATION_MISMATCH"):
            self.run_audit()

    def test_missing_sensor_rejected(self):
        del self.doc["sensors"]["Q_net_W"]
        self.save()
        with self.assertRaisesRegex(ValueError, "MISSING_SENSOR_BOUNDS"):
            self.run_audit()

    def test_nonfinite_uncertainty_rejected(self):
        self.doc["sensors"]["T_C"]["abs_error_bound"] = float("nan")
        self.save()
        with self.assertRaisesRegex(ValueError, "INVALID_T_C_ABS"):
            self.run_audit()

    def test_negative_uncertainty_rejected(self):
        self.doc["sensors"]["Q_net_W"]["abs_error_bound"] = -1
        self.save()
        with self.assertRaisesRegex(ValueError, "INVALID_Q_net_W_ABS"):
            self.run_audit()

    def test_bad_certificate_hash_rejected(self):
        self.doc["sensors"]["P_actual_W"]["calibration_document_sha256"] = "not-a-sha"
        self.save()
        with self.assertRaisesRegex(ValueError, "INVALID_CALIBRATION_DOCUMENT_HASH"):
            self.run_audit()

    def test_unidentifiable_temperature_with_large_uncertainty(self):
        self.doc["sensors"]["T_C"]["abs_error_bound"] = .02
        self.save()
        with self.assertRaisesRegex(ValueError, "CAPACITY_UNCERTAINTY_UNIDENTIFIABLE"):
            self.run_audit()

    def test_unidentifiable_tau_with_large_power_uncertainty(self):
        self.doc["sensors"]["P_actual_W"]["abs_error_bound"] = 90000
        self.save()
        with self.assertRaisesRegex(ValueError, "COMPRESSOR_UNCERTAINTY_UNIDENTIFIABLE"):
            self.run_audit()

    def test_large_time_jitter_rejected(self):
        self.doc["time_sync"]["sample_timestamp_uncertainty_s"] = 10
        self.save()
        with self.assertRaisesRegex(ValueError, "TIMEBASE_INTERVAL_UNCERTAIN"):
            self.run_audit()

    def test_command_alignment_ambiguity_rejected(self):
        self.doc["time_sync"]["max_abs_clock_offset_s"] = 20
        self.save()
        with self.assertRaisesRegex(ValueError, "TIMEBASE_COMMAND_AMBIGUOUS"):
            self.run_audit()

    def test_timebase_not_utc_rejected(self):
        self.doc["timebase"] = "local"
        self.save()
        with self.assertRaisesRegex(ValueError, "TIMEBASE_NOT_UTC"):
            self.run_audit()

    def test_duplicate_json_keys_rejected(self):
        self.bounds.write_text('{"asset_id":"a","asset_id":"b"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_JSON_KEY"):
            self.run_audit()

    def test_unauthorized_release_claim_rejected(self):
        self.doc["physical_release"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "UNAUTHORIZED_RELEASE_CLAIM"):
            self.run_audit()

    def test_real_label_still_unverified(self):
        self.metadata["source_kind"] = "real_telemetry"
        self.meta.write_text(json.dumps(self.metadata), encoding="utf-8")
        self.doc["source_kind"] = "real_telemetry"
        for sensor in self.doc["sensors"].values():
            sensor["calibration_document_sha256"] = "1" * 64
        self.save()
        r = self.run_audit()
        self.assertEqual(r["status"], "MEASURED_CANDIDATE_REQUIRES_INDEPENDENT_QA")
        self.assertFalse(r["physical_release"])
        self.assertFalse(r["safe_operating_limits_certified"])

    def test_real_placeholder_certificate_rejected(self):
        self.metadata["source_kind"] = "real_telemetry"
        self.meta.write_text(json.dumps(self.metadata), encoding="utf-8")
        self.doc["source_kind"] = "real_telemetry"
        self.save()
        with self.assertRaisesRegex(ValueError, "PLACEHOLDER_CERTIFICATE_REAL_SENSOR"):
            self.run_audit()

    def test_real_zero_uncertainty_rejected(self):
        self.metadata["source_kind"] = "real_telemetry"
        self.meta.write_text(json.dumps(self.metadata), encoding="utf-8")
        self.doc["source_kind"] = "real_telemetry"
        for sensor in self.doc["sensors"].values():
            sensor["calibration_document_sha256"] = "1" * 64
        self.doc["sensors"]["T_C"]["abs_error_bound"] = 0
        self.save()
        with self.assertRaisesRegex(ValueError, "ZERO_UNCERTAINTY_REAL_SENSOR"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
