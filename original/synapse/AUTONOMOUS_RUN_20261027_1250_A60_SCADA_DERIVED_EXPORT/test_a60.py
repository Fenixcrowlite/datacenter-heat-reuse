"""Deterministic A60 tests. No external files, network or device required."""
import csv
import json
import tempfile
import unittest
from pathlib import Path

from a60_scada_derived_export import SCHEMAS, classify, export, load, metrics, sha


class A60Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "input.csv"
        self.dest = self.root / "output"

    def make(self, schema="scada_v08", times=(0, .25, .5), *, overrides=None):
        mapping = SCHEMAS[schema]
        values = {
            "time_s": 0, "T_pool_C": 20, "Q_DC_W": 200000,
            "Q_reject_W": 100000, "Q_pool_W": 150000,
            "Q_DH_W": 100000, "P_HP_W": 50000, "E_TES_J": 1e9,
        }
        values.update(overrides or {})
        with self.source.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(mapping.values()))
            writer.writeheader()
            for time in times:
                row = dict(values)
                row["time_s"] = time
                writer.writerow({source: row[target] for target, source in mapping.items()})

    def test_v08_export_real_transform(self):
        self.make()
        result = export(self.source, self.dest)
        self.assertEqual(result["source_schema"], "scada_v08")
        self.assertEqual(result["source_kind"], "derived_simulation")
        self.assertFalse(result["physical_release"])
        self.assertFalse(result["measurement_calibration_ready"])
        self.assertEqual(len(result["missing_for_A55"]), 10)
        self.assertAlmostEqual(result["metrics"]["duration_h"], .5)
        self.assertAlmostEqual(result["metrics"]["integrated_MWh"]["Q_DC_W"], .1)
        self.assertEqual(result["analysis_csv_sha256"], sha(self.dest / "analysis_timeseries.csv"))
        self.assertEqual(result["source_csv_sha256"], sha(self.source))
        self.assertEqual(json.loads((self.dest / "summary.json").read_text())["schema_version"], "a60.1")

    def test_v09_export(self):
        self.make("scada_v09_matlab")
        self.assertEqual(export(self.source, self.dest)["source_schema"], "scada_v09_matlab")

    def test_unknown_schema_rejected(self):
        self.source.write_text("time,T\n0,1\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "UNKNOWN"):
            load(self.source)

    def test_duplicate_header_rejected(self):
        self.source.write_text("cas_h,cas_h\n0,1\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            load(self.source)

    def test_nonmonotonic_time_rejected(self):
        self.make(times=(0, .5, .5))
        with self.assertRaisesRegex(ValueError, "NON_MONOTONIC"):
            load(self.source)

    def test_negative_time_rejected(self):
        self.make(times=(-1, 0, 1))
        with self.assertRaisesRegex(ValueError, "NON_MONOTONIC"):
            load(self.source)

    def test_time_gap_rejected(self):
        self.make(times=(0, 25, 26))
        with self.assertRaisesRegex(ValueError, "TIME_GAP"):
            load(self.source)

    def test_nonfinite_rejected(self):
        self.make(overrides={"Q_DC_W": "nan"})
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            load(self.source)

    def test_bad_number_rejected(self):
        self.make(overrides={"Q_DC_W": "oops"})
        with self.assertRaisesRegex(ValueError, "NON_NUMERIC"):
            load(self.source)

    def test_insufficient_rows_rejected(self):
        self.make(times=(0, .25))
        with self.assertRaisesRegex(ValueError, "INSUFFICIENT"):
            load(self.source)

    def test_existing_destination_preserved(self):
        self.make()
        self.dest.mkdir()
        (self.dest / "important.txt").write_text("keep")
        with self.assertRaisesRegex(ValueError, "DESTINATION_EXISTS"):
            export(self.source, self.dest)
        self.assertEqual((self.dest / "important.txt").read_text(), "keep")

    def test_missing_input(self):
        with self.assertRaisesRegex(ValueError, "INVALID_SOURCE"):
            load(self.source)

    def test_metric_tes_delta(self):
        self.make()
        _, rows = load(self.source)
        rows[-1]["E_TES_J"] += 3.6e9
        self.assertAlmostEqual(metrics(rows)["E_TES_delta_MWh"], 1)

    def test_bad_csv_row(self):
        self.make()
        with self.source.open("a", encoding="utf-8") as f:
            f.write("1,2\n")
        with self.assertRaisesRegex(ValueError, "MALFORMED"):
            load(self.source)

    def test_schema_contract(self):
        self.assertEqual(len(SCHEMAS), 2)
        for mapping in SCHEMAS.values():
            self.assertEqual(set(mapping), {"time_s", "T_pool_C", "Q_DC_W",
                                            "Q_reject_W", "Q_pool_W", "Q_DH_W",
                                            "P_HP_W", "E_TES_J"})
        self.assertEqual(classify(list(SCHEMAS["scada_v08"].values())), "scada_v08")


if __name__ == "__main__":
    unittest.main()
