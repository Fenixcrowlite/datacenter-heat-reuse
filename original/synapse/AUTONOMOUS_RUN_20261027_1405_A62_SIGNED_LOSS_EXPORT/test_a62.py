"""A62 isolated functional and adversarial regression tests."""
import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from a62_signed_loss_export import export, C_POOL_J_PER_K


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestA62(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.raw = self.root / "source.csv"
        self.a60 = self.root / "a60"
        self.a60.mkdir()
        self.dst = self.root / "a62"
        self.schema = "scada_v08"
        self.qkey, self.lkey = "Q_pool_phys_W", "Q_pool_loss_W"
        self.fixture()

    def fixture(self, loss=-100.0):
        T = 16.0
        original, derived = [], []
        for i in range(3):
            T += 900 * (1000 - loss) / C_POOL_J_PER_K
            original.append({"cas_h": str(i/4), "T_pool_C": format(T, ".17g"),
                             self.qkey: "1000", self.lkey: str(loss)})
            derived.append({"time_s": str(i*900), "T_pool_C": format(T, ".17g"),
                            "Q_pool_W": "1000", "Q_DC_W": "3000"})
        with self.raw.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=original[0].keys()); w.writeheader(); w.writerows(original)
        self.a60csv = self.a60 / "analysis_timeseries.csv"
        with self.a60csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=derived[0].keys()); w.writeheader(); w.writerows(derived)
        self.summary = {
            "schema_version": "a60.1", "source_kind": "derived_simulation",
            "physical_release": False, "measurement_calibration_ready": False,
            "source_schema": self.schema, "source_path": str(self.raw.resolve()),
            "source_csv_sha256": sha(self.raw), "analysis_csv_sha256": sha(self.a60csv),
            "metrics": {"integrated_MWh": {"Q_pool_W": 1000*1800/3.6e9}},
        }
        self.save()

    def save(self):
        (self.a60 / "summary.json").write_text(json.dumps(self.summary), encoding="utf-8")

    def reject(self, message):
        with self.assertRaisesRegex(ValueError, message):
            export(self.raw, self.a60, self.dst)

    def test_v08_export(self):
        meta = export(self.raw, self.a60, self.dst)
        self.assertEqual(meta["records"], 3)
        self.assertEqual(meta["source_kind"], "derived_simulation")
        self.assertFalse(meta["physical_release"])
        self.assertEqual(meta["a61_validation"]["negative_loss_samples"], 3)

    def test_v09_export(self):
        self.schema = "scada_v09_matlab"
        self.qkey, self.lkey = "Q_pool_W", "Q_pool_losses_W"
        self.fixture()
        self.assertEqual(export(self.raw, self.a60, self.dst)["source_schema"], self.schema)

    def test_signed_loss_and_original_columns(self):
        export(self.raw, self.a60, self.dst)
        with (self.dst / "analysis_with_signed_losses.csv").open() as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["Q_DC_W"], "3000")
        self.assertEqual(float(rows[0]["Q_pool_loss_W"]), -100)
        self.assertEqual(float(rows[0]["Q_pool_net_W"]), 1100)
        self.assertAlmostEqual(float(rows[-1]["E_pool_input_cum_J"]), 2700000)

    def test_discrete_stored_energy_matches_input_less_signed_loss(self):
        export(self.raw, self.a60, self.dst)
        with (self.dst / "analysis_with_signed_losses.csv").open() as f:
            last = list(csv.DictReader(f))[-1]
        self.assertAlmostEqual(float(last["E_pool_input_cum_J"]) -
                               float(last["E_pool_signed_loss_cum_J"]),
                               float(last["E_pool_stored_cum_J"]), delta=0.01)

    def test_no_overwrite(self):
        export(self.raw, self.a60, self.dst)
        self.reject("DESTINATION_EXISTS")

    def test_missing_parent(self):
        with self.assertRaisesRegex(ValueError, "DESTINATION_PARENT_MISSING"):
            export(self.raw, self.a60, self.root / "missing" / "new")

    def test_tampered_source_hash(self):
        self.raw.write_text(self.raw.read_text() + "\n", encoding="utf-8")
        self.reject("SOURCE_SHA_MISMATCH")

    def test_tampered_a60_hash(self):
        self.a60csv.write_text(self.a60csv.read_text() + "\n", encoding="utf-8")
        self.reject("DERIVED_SHA_MISMATCH")

    def test_no_fake_physical_release(self):
        self.summary["physical_release"] = True
        self.save()
        self.reject("UNAUTHORIZED_PHYSICAL_RELEASE")

    def test_no_fake_real_telemetry(self):
        self.summary["source_kind"] = "real_telemetry"
        self.save()
        self.reject("NOT_A60_DERIVED_SIMULATION")

    def test_loss_corruption_rejected_even_with_updated_sha(self):
        text = self.raw.read_text().replace(",-100.0", ",400.0")
        self.raw.write_text(text, encoding="utf-8")
        self.summary["source_csv_sha256"] = sha(self.raw)
        self.save()
        self.reject("POOL_FIRST_LAW_RESIDUAL")

    def test_output_hash_matches(self):
        meta = export(self.raw, self.a60, self.dst)
        self.assertEqual(sha(self.dst / "analysis_with_signed_losses.csv"),
                         meta["analysis_with_signed_losses_sha256"])


if __name__ == "__main__":
    unittest.main()
