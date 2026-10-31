"""A58 regression tests, including adversarial document forgery attempts."""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path
from build_demo_a58 import build
from a58_document_gate import audit, sha


def save(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")


class DocumentChainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = build(Path(self.temp.name) / "bundle")
        self.manifest_path = self.root / "document_manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def commit(self):
        save(self.manifest_path, self.manifest)

    def reject(self, code):
        self.commit()
        with self.assertRaisesRegex(ValueError, code):
            audit(self.root)

    def test_01_valid_synthetic_bundle_never_releases(self):
        result = audit(self.root)
        self.assertEqual(result["document_count"], 6)
        self.assertEqual(result["status"], "SYNTHETIC_DOCUMENT_CHAIN_TEST_ONLY")
        self.assertFalse(result["physical_release"])
        self.assertFalse(result["independent_issuer_authentication"])

    def test_02_modified_document_bytes(self):
        with (self.root / "docs/cal_T_C.txt").open("a", encoding="utf-8") as f:
            f.write("TAMPER")
        self.reject("A58_DOCUMENT_HASH_MISMATCH")

    def test_03_forged_matching_manifest_hash_but_a57_not_updated(self):
        p = self.root / "docs/cal_T_C.txt"
        p.write_text("SYNTHETIC FORGED CERTIFICATE", encoding="utf-8")
        self.manifest["documents"][0]["sha256"] = sha(p)
        self.reject("A58_UNBOUND_A57_CERTIFICATE_HASH")

    def test_04_manifest_source_hash_drift(self):
        self.manifest["telemetry_sha256"] = "0" * 64
        self.reject("A58_INPUT_HASH_MISMATCH")

    def test_05_path_traversal(self):
        self.manifest["documents"][0]["file"] = "docs/../metadata.json"
        self.reject("A58_PATH_TRAVERSAL")

    def test_06_absolute_path(self):
        self.manifest["documents"][0]["file"] = "C:/private/cert.txt"
        self.reject("A58_BAD_DOCUMENT_PATH")

    def test_07_missing_document(self):
        (self.root / "docs/cal_T_C.txt").unlink()
        self.reject("A58_MISSING_OR_SYMLINK_DOCUMENT")

    def test_08_duplicate_document_id(self):
        self.manifest["documents"][1]["id"] = self.manifest["documents"][0]["id"]
        self.reject("A58_DUPLICATE_OR_EMPTY_DOCUMENT_ID")

    def test_09_missing_calibration_document(self):
        self.manifest["documents"].pop()
        self.reject("A58_DOCUMENT_COUNT")

    def test_10_wrong_sensor_unit(self):
        self.manifest["documents"][0]["unit"] = "K"
        self.reject("A58_UNIT_MISMATCH")

    def test_11_changed_calibration_reference(self):
        self.manifest["documents"][0]["calibration_ref"] = "OTHER"
        self.reject("A58_CALIBRATION_REF_MISMATCH")

    def test_12_expired_calibration(self):
        self.manifest["documents"][0]["valid_until_utc"] = "2026-10-26T00:00:00Z"
        self.reject("A58_DOCUMENT_OUTSIDE_MEASUREMENT_WINDOW")

    def test_13_issued_after_measurements(self):
        self.manifest["documents"][0]["issued_utc"] = "2026-10-28T00:00:00Z"
        self.reject("A58_DOCUMENT_OUTSIDE_MEASUREMENT_WINDOW")

    def test_14_wrong_asset(self):
        self.manifest["documents"][0]["asset_id"] = "SOME-OTHER-LOOP"
        self.reject("A58_DOCUMENT_ASSET_MISMATCH")

    def test_15_vendor_operating_range_violated(self):
        self.manifest["documents"][-1]["max_T_C"] = 30.2
        self.reject("A58_TELEMETRY_OUTSIDE_DECLARED_VENDOR_RANGE")

    def test_16_vendor_units_wrong(self):
        self.manifest["documents"][-1]["power_unit"] = "kW"
        self.reject("A58_VENDOR_UNIT_CONFLICT")

    def test_17_clock_method_disagrees(self):
        self.manifest["documents"][-2]["method"] = "ntp"
        self.reject("A58_TIME_SYNC_METHOD_CONFLICT")

    def test_18_clock_error_bounds_disagree(self):
        self.manifest["documents"][-2]["clock_uncertainty_s"] = 0.3
        self.reject("A58_TIME_SYNC_BOUND_CONFLICT")

    def test_19_unauthorized_release(self):
        self.manifest["physical_release"] = True
        self.reject("A58_UNAUTHORIZED_RELEASE")

    def test_20_claimed_independent_issuer_auth(self):
        self.manifest["independent_issuer_authentication"] = True
        self.reject("A58_UNAUTHORIZED_RELEASE")

    def test_21_duplicate_json_key(self):
        s = self.manifest_path.read_text(encoding="utf-8")
        self.manifest_path.write_text(s.replace('"schema_version":', '"schema_version": "fake", "schema_version":', 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "A58_DUPLICATE_JSON_KEY"):
            audit(self.root)

    def test_22_fake_real_source(self):
        self.manifest["source_kind"] = "real_telemetry"
        self.reject("A58_ASSET_SOURCE_MISMATCH")

    def test_23_invalid_numeric_nan(self):
        self.manifest["documents"][-1]["max_P_W"] = float("nan")
        self.reject("A58_BAD_NUMBER_max_P_W")

    def test_24_mismatched_sensor_error_bound(self):
        self.manifest["documents"][0]["abs_error_bound"] = 99
        self.reject("A58_ERROR_BOUND_CONFLICT")

    def test_25_missing_issuer(self):
        self.manifest["documents"][0]["issuer"] = ""
        self.reject("A58_MISSING_ISSUER")


if __name__ == "__main__":
    unittest.main()
