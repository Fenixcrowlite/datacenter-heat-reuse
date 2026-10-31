"""Independent regression tests for A69 offline telemetry review."""
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from a69_telemetry_review import digest, energy_kwh, load, review, summary

ROOT = Path(__file__).resolve().parent
FIXTURE = ROOT / "FIXTURE"


class A69Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)
        self.source = self.home / "source"
        shutil.copytree(FIXTURE, self.source)

    def data(self):
        return load(self.source)

    def read_csv(self):
        with (self.source / "telemetry.csv").open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader), reader.fieldnames

    def write_csv(self, rows, fields=None):
        fields = fields or list(rows[0])
        with (self.source / "telemetry.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        self.rehash()

    def rehash(self):
        meta_path = self.source / "metadata.json"
        prov_path = self.source / "provenance.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        meta["original_csv_sha256"] = digest(self.source / "telemetry.csv")
        meta_path.write_text(json.dumps(meta) + "\n", encoding="utf-8")
        prov["normalized_csv_sha256"] = digest(self.source / "telemetry.csv")
        prov["metadata_sha256"] = digest(meta_path)
        prov_path.write_text(json.dumps(prov) + "\n", encoding="utf-8")

    def test_01_fixture_integrity_and_identity(self):
        rows, meta, prov, hashes = self.data()
        self.assertEqual(len(rows), 30)
        self.assertEqual(meta["asset_id"], "TEST-LOOP-NOT-REAL")
        self.assertEqual(prov["source_kind"], "synthetic_test")
        self.assertEqual(hashes["telemetry.csv"], digest(self.source / "telemetry.csv"))

    def test_02_independent_constant_net_energy(self):
        rows, *_ = self.data()
        self.assertAlmostEqual(float(energy_kwh(rows, "Q_net_W")), 2000 * 29 * 60 / 3600000, places=12)

    def test_03_independent_command_energy(self):
        rows, *_ = self.data()
        self.assertAlmostEqual(float(energy_kwh(rows, "P_cmd_W")), 100000 * 29 * 60 / 3600000, places=12)

    def test_04_summary_has_observed_not_extrapolated_duration(self):
        report = summary(*self.data())
        self.assertAlmostEqual(report["observed_hours"], 29 / 60)
        self.assertEqual(report["median_step_s"], 60)
        self.assertFalse(report["physical_release"])

    def test_05_tampered_csv_is_rejected(self):
        p = self.source / "telemetry.csv"
        p.write_bytes(p.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH"):
            self.data()

    def test_06_tampered_metadata_is_rejected(self):
        p = self.source / "metadata.json"
        p.write_bytes(p.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "SOURCE_SHA_MISMATCH"):
            self.data()

    def test_07_source_kind_conflict(self):
        p = self.source / "provenance.json"
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["source_kind"] = "real_telemetry"
        p.write_text(json.dumps(obj), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_KIND_CONFLICT"):
            self.data()

    def test_08_nonfinite_value_rejected(self):
        rows, fields = self.read_csv()
        rows[3]["Q_net_W"] = "NaN"
        self.write_csv(rows, fields)
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            self.data()

    def test_09_negative_actuator_power_rejected(self):
        rows, fields = self.read_csv()
        rows[3]["P_actual_W"] = "-1"
        self.write_csv(rows, fields)
        with self.assertRaisesRegex(ValueError, "NEGATIVE_POWER"):
            self.data()

    def test_10_time_reversal_rejected(self):
        rows, fields = self.read_csv()
        rows[2]["timestamp_utc"] = rows[1]["timestamp_utc"]
        self.write_csv(rows, fields)
        with self.assertRaisesRegex(ValueError, "TIMEBASE_INVALID"):
            self.data()

    def test_11_irregular_sample_gap_warning(self):
        rows, fields = self.read_csv()
        rows[10]["timestamp_utc"] = "2026-10-27T00:10:45+00:00"
        self.write_csv(rows, fields)
        self.assertIn("IRREGULAR_SAMPLE_GAPS_REVIEW", summary(*self.data())["warnings"])

    def test_12_trip_state_transition(self):
        baseline = summary(*self.data())
        rows, fields = self.read_csv()
        rows[7]["trip_state"] = "TRIPPED"
        rows[8]["trip_state"] = "TRIPPED"
        self.write_csv(rows, fields)
        report = summary(*self.data())
        self.assertEqual((report["trip_rows"] - baseline["trip_rows"],
                          report["trip_starts"] - baseline["trip_starts"]), (2, 1))

    def test_13_generates_self_contained_html(self):
        target = self.home / "report"
        result = review(self.source, target)
        page = (target / "review.html").read_text(encoding="utf-8")
        self.assertIn("<svg", page)
        self.assertIn("SYNTETICKÉ", page)
        self.assertNotIn("<script", page.lower())
        self.assertNotIn("http://", page)
        self.assertNotIn("https://", page)
        self.assertEqual(result["rows"], 30)
        receipt = json.loads((target / "source_receipt.json").read_text(encoding="utf-8"))
        for filename, sha in receipt["output_sha256"].items():
            self.assertEqual(sha, digest(target / filename))

    def test_14_no_overwrite(self):
        target = self.home / "report"
        review(self.source, target)
        with self.assertRaisesRegex(ValueError, "DESTINATION_EXISTS"):
            review(self.source, target)

    def test_15_deterministic_report(self):
        a, b = self.home / "a", self.home / "b"
        review(self.source, a)
        review(self.source, b)
        for filename in ("review.html", "summary.json", "source_receipt.json"):
            self.assertEqual(digest(a / filename), digest(b / filename))

    def test_16_html_injection_escaped(self):
        p = self.source / "metadata.json"
        obj = json.loads(p.read_text(encoding="utf-8"))
        obj["provenance_notes"] = '<img src=x onerror=alert(1)>'
        p.write_text(json.dumps(obj), encoding="utf-8")
        prov_path = self.source / "provenance.json"
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        prov["metadata_sha256"] = digest(p)
        prov_path.write_text(json.dumps(prov), encoding="utf-8")
        target = self.home / "escaped"
        review(self.source, target)
        page = (target / "review.html").read_text(encoding="utf-8")
        self.assertNotIn('<img src=x', page)
        self.assertIn("&lt;img", page)

    def test_17_real_label_never_releases(self):
        meta_path, prov_path = self.source / "metadata.json", self.source / "provenance.json"
        meta, prov = json.loads(meta_path.read_text()), json.loads(prov_path.read_text())
        meta["source_kind"] = prov["source_kind"] = "real_telemetry"
        meta_path.write_text(json.dumps(meta), encoding="utf-8")
        prov["metadata_sha256"] = digest(meta_path)
        prov_path.write_text(json.dumps(prov), encoding="utf-8")
        target = self.home / "real_label"
        report = review(self.source, target)
        self.assertFalse(report["physical_release"])
        self.assertIn("NEOVERENÝ FYZICKÝ PÔVOD", (target / "review.html").read_text(encoding="utf-8"))

    def test_18_fail_closed_without_partial_output(self):
        rows, fields = self.read_csv()
        rows[0]["T_C"] = "Infinity"
        self.write_csv(rows, fields)
        target = self.home / "failed"
        with self.assertRaises(ValueError):
            review(self.source, target)
        self.assertFalse(target.exists())

    def test_19_symlink_input_rejected(self):
        link = self.home / "alias.csv"
        try:
            link.symlink_to(self.source / "telemetry.csv")
        except (OSError, NotImplementedError):
            self.skipTest("symlink privilege unavailable on Windows")
        (self.source / "telemetry.csv").unlink()
        link.rename(self.source / "telemetry.csv")
        with self.assertRaisesRegex(ValueError, "INVALID_INPUT_FILE"):
            self.data()


if __name__ == "__main__":
    unittest.main(verbosity=2)
