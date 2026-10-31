"""A63 regression and adversarial tests; synthetic fixtures only."""
import csv
from decimal import Decimal, getcontext
import json
from pathlib import Path
import tempfile
import unittest
from a63_offline_dashboard import build, read_one, sha, FIELDS

getcontext().prec = 34
C = Decimal("2084727000")
STEP = Decimal(900)


def fixture(folder: Path, gain_rows=91, temp_offset=0):
    folder.mkdir()
    path = folder / "analysis_with_signed_losses.csv"
    T = Decimal(16)
    ei = el = Decimal(0)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for i in range(672):
            q = Decimal(150000 + temp_offset)
            loss = Decimal(-5000 if i < gain_rows else 5000)
            net = q - loss
            T += net * STEP / C
            ei += q * STEP
            el += loss * STEP
            stored = C * (T - 16)
            w.writerow(dict(zip(FIELDS, map(str, [
                STEP * i, T, q, loss, net, ei, el, stored, Decimal(0)
            ]))))
    meta = {
        "schema_version": "a62.1", "source_kind": "derived_simulation",
        "physical_release": False, "calibration_ready": False,
        "records": 672, "step_seconds": 900.0,
        "pool_heat_capacity_J_per_K": float(C), "initial_T_C": 16,
        "source_schema": folder.name,
        "analysis_with_signed_losses_sha256": sha(path),
    }
    (folder / "summary.json").write_text(json.dumps(meta), encoding="utf-8")


class A63Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a62 = self.root / "A62"
        self.a62.mkdir()
        fixture(self.a62 / "OUTPUT_V08_SIGNED")
        fixture(self.a62 / "OUTPUT_V09_SIGNED", temp_offset=200)
        self.output = self.root / "A63"

    def refresh_sha(self, folder):
        meta = folder / "summary.json"
        obj = json.loads(meta.read_text(encoding="utf-8"))
        obj["analysis_with_signed_losses_sha256"] = sha(folder / "analysis_with_signed_losses.csv")
        meta.write_text(json.dumps(obj), encoding="utf-8")

    def mutate_csv(self, folder, find, replace):
        path = folder / "analysis_with_signed_losses.csv"
        text = path.read_text(encoding="utf-8")
        self.assertIn(find, text)
        path.write_text(text.replace(find, replace, 1), encoding="utf-8")
        self.refresh_sha(folder)

    def test_valid_synthetic_closure(self):
        m, data = read_one(self.a62 / "OUTPUT_V08_SIGNED")
        self.assertEqual(m["rows"], 672)
        self.assertEqual(m["negative_loss_rows"], 91)
        self.assertAlmostEqual(m["ambient_gain_MWh"], 91*5000*900/3.6e9)
        self.assertLess(abs(m["closure_J"]), .1)
        self.assertEqual(len(data["rows"]), 672)

    def test_generates_standalone_interactive_view(self):
        m = build(self.a62, self.output)
        self.assertEqual(set(m), {"v08", "v09"})
        html = (self.output / "dashboard.html").read_text(encoding="utf-8")
        for term in ("SIMULÁCIA", "SCADA v08", "MATLAB v09", "chart(", "pointermove", "application/json", "physical_release=false"):
            self.assertIn(term, html)
        for term in ("<script src=", "<link href=", "fetch(", "https://"):
            self.assertNotIn(term, html)
        self.assertTrue((self.output / "metrics.json").is_file())
        self.assertFalse(json.loads((self.output / "sources.json").read_text())["physical_release"])

    def test_no_overwrite(self):
        build(self.a62, self.output)
        with self.assertRaisesRegex(ValueError, "DESTINATION_EXISTS"):
            build(self.a62, self.output)

    def test_tampered_csv_hash(self):
        p = self.a62 / "OUTPUT_V08_SIGNED" / "analysis_with_signed_losses.csv"
        p.write_text(p.read_text()+"\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PROVENANCE_GATE"):
            build(self.a62, self.output)
        self.assertFalse(self.output.exists())

    def test_false_physical_claim(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        meta = folder / "summary.json"
        obj = json.loads(meta.read_text())
        obj["physical_release"] = True
        meta.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, "PROVENANCE_GATE"):
            build(self.a62, self.output)

    def test_wrong_source_kind(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        meta = folder / "summary.json"
        obj = json.loads(meta.read_text())
        obj["source_kind"] = "real_telemetry"
        meta.write_text(json.dumps(obj))
        with self.assertRaisesRegex(ValueError, "PROVENANCE_GATE"):
            build(self.a62, self.output)

    def test_bad_timebase_even_with_valid_sha(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        self.mutate_csv(folder, "900,", "901,")
        with self.assertRaisesRegex(ValueError, "INVALID_TIMEBASE"):
            build(self.a62, self.output)

    def test_bad_energy_even_with_valid_sha(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        self.mutate_csv(folder, "135000000", "136000000")
        with self.assertRaisesRegex(ValueError, "ENERGY_CLOSURE"):
            build(self.a62, self.output)

    def test_bad_signed_loss_even_with_valid_sha(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        self.mutate_csv(folder, "-5000", "-4000")
        with self.assertRaisesRegex(ValueError, "ENERGY_CLOSURE"):
            build(self.a62, self.output)

    def test_duplicate_header(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        self.mutate_csv(folder, "Q_pool_loss_W", "Q_pool_W")
        with self.assertRaisesRegex(ValueError, "INVALID_COLUMNS"):
            build(self.a62, self.output)

    def test_nonfinite_rejected(self):
        folder = self.a62 / "OUTPUT_V08_SIGNED"
        self.mutate_csv(folder, "150000", "NaN")
        with self.assertRaisesRegex(ValueError, "NONFINITE"):
            build(self.a62, self.output)


if __name__ == "__main__":
    unittest.main()
