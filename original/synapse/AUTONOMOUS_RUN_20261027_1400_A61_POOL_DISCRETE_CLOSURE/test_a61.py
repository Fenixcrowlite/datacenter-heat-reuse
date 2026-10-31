"""Isolated adversarial tests for A61; all inputs are disposable synthetic fixtures."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from a61_pool_discrete_closure import C_POOL_J_PER_K, audit


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestA61(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.raw = self.root / "raw.csv"
        self.derived = self.root / "derived"
        self.derived.mkdir()
        self.schema = "scada_v08"
        self.q_name = "Q_pool_phys_W"
        self.loss_name = "Q_pool_loss_W"
        self.make_fixture()

    def make_fixture(self, q=1000.0, loss=200.0):
        T = 16.0
        raw_rows, derived_rows = [], []
        for i in range(3):
            T += 900.0 * (q - loss) / C_POOL_J_PER_K
            raw_rows.append({"cas_h": format(i / 4, ".17g"), "T_pool_C": format(T, ".17g"),
                             self.q_name: str(q), self.loss_name: str(loss)})
            derived_rows.append({"time_s": str(i * 900), "T_pool_C": format(T, ".17g"),
                                 "Q_pool_W": str(q)})
        with self.raw.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=raw_rows[0].keys()); w.writeheader(); w.writerows(raw_rows)
        self.csv = self.derived / "analysis_timeseries.csv"
        with self.csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=derived_rows[0].keys()); w.writeheader(); w.writerows(derived_rows)
        self.meta = self.derived / "summary.json"
        self.summary = {
            "schema_version": "a60.1", "source_kind": "derived_simulation",
            "source_schema": self.schema, "source_path": str(self.raw.resolve()),
            "source_csv_sha256": digest(self.raw), "analysis_csv_sha256": digest(self.csv),
            "physical_release": False, "measurement_calibration_ready": False,
            "metrics": {"integrated_MWh": {"Q_pool_W": q * 1800.0 / 3.6e9}},
        }
        self.save()

    def save(self):
        self.meta.write_text(json.dumps(self.summary), encoding="utf-8")

    def assert_rejected(self, code):
        with self.assertRaisesRegex(ValueError, code):
            audit(self.raw, self.derived)

    def test_v08_valid(self):
        a = audit(self.raw, self.derived)
        self.assertEqual(a["samples"], 3)
        self.assertLess(a["max_abs_step_residual_W"], 0.001)
        self.assertAlmostEqual(a["E_pool_signed_losses_MWh"], 200*2700/3.6e9)

    def test_v09_valid(self):
        self.q_name, self.loss_name, self.schema = "Q_pool_W", "Q_pool_losses_W", "scada_v09_matlab"
        self.make_fixture()
        self.assertEqual(audit(self.raw, self.derived)["source_schema"], self.schema)

    def test_negative_loss_is_heat_gain(self):
        self.make_fixture(q=1000, loss=-100)
        a = audit(self.raw, self.derived)
        self.assertEqual(a["negative_loss_samples"], 3)
        self.assertGreater(a["environmental_gain_MWh_from_negative_losses"], 0)

    def test_physical_release_is_forbidden(self):
        self.summary["physical_release"] = True; self.save()
        self.assert_rejected("UNAUTHORIZED_PHYSICAL_RELEASE")

    def test_real_source_kind_is_not_inferred(self):
        self.summary["source_kind"] = "real_telemetry"; self.save()
        self.assert_rejected("NOT_A60_DERIVED_SIMULATION")

    def test_raw_tamper_hash(self):
        self.raw.write_text(self.raw.read_text() + "\n", encoding="utf-8")
        self.assert_rejected("SOURCE_SHA_MISMATCH")

    def test_derived_tamper_hash(self):
        self.csv.write_text(self.csv.read_text() + "\n", encoding="utf-8")
        self.assert_rejected("DERIVED_SHA_MISMATCH")

    def test_source_path_mismatch(self):
        self.summary["source_path"] = str(self.root / "another.csv"); self.save()
        self.assert_rejected("SOURCE_PATH_MISMATCH")

    def test_unknown_schema(self):
        self.summary["source_schema"] = "random"; self.save()
        self.assert_rejected("UNSUPPORTED_SOURCE_SCHEMA")

    def test_wrong_initial_temperature(self):
        with self.assertRaisesRegex(ValueError, "POOL_FIRST_LAW_RESIDUAL"):
            audit(self.raw, self.derived, initial_T_C=17)

    def test_loss_tamper_with_valid_sha(self):
        lines = self.raw.read_text().splitlines()
        lines[1] = lines[1].replace(",200.0", ",400.0")
        self.raw.write_text("\n".join(lines)+"\n", encoding="utf-8")
        self.summary["source_csv_sha256"] = digest(self.raw); self.save()
        self.assert_rejected("POOL_FIRST_LAW_RESIDUAL")

    def test_time_tamper_with_valid_sha(self):
        text = self.csv.read_text().replace("900,","901,")
        self.csv.write_text(text, encoding="utf-8")
        self.summary["analysis_csv_sha256"] = digest(self.csv); self.save()
        self.assert_rejected("TIME_GRID_MISMATCH")

    def test_source_mapping_tamper_with_valid_sha(self):
        text = self.csv.read_text().replace(",1000.0", ",900.0")
        self.csv.write_text(text, encoding="utf-8")
        self.summary["analysis_csv_sha256"] = digest(self.csv); self.save()
        self.assert_rejected("A60_SOURCE_MAPPING_MISMATCH")

    def test_missing_loss_column(self):
        self.raw.write_text(self.raw.read_text().replace(self.loss_name, "lost_column"), encoding="utf-8")
        self.summary["source_csv_sha256"] = digest(self.raw); self.save()
        self.assert_rejected("INVALID_CSV_SCHEMA")

    def test_nonfinite_temperature(self):
        lines = self.raw.read_text().splitlines()
        fields = lines[1].split(",")
        fields[1] = "nan"
        lines[1] = ",".join(fields)
        self.raw.write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.summary["source_csv_sha256"] = digest(self.raw); self.save()
        # First data row contains 16.000... in all standard fixtures.
        self.assert_rejected("NONFINITE_T_pool_C")

    def test_a60_integral_mismatch(self):
        self.summary["metrics"]["integrated_MWh"]["Q_pool_W"] += 0.1
        self.save()
        self.assert_rejected("A60_TRAPEZOID_MISMATCH")


if __name__ == "__main__":
    unittest.main()
