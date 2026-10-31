"""N-1 envelope regression and independent CSV cross-check."""
import csv
import hashlib
import json
import unittest
from decimal import Decimal as D
from pathlib import Path
from reject_envelope import HERE,A36,MODEL,capacity_from_model,evaluate

class EnvelopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=json.loads((HERE/"RESULTS_N1.json").read_text(encoding="utf8"))

    def test_source_declares_synthetic(self):
        self.assertIn("scenarove hodnoty",MODEL.read_text(encoding="utf-8-sig"))

    def test_source_caps(self):
        self.assertEqual(capacity_from_model(),(180000,150000))

    def test_source_hash(self):
        self.assertEqual(hashlib.sha256(MODEL.read_bytes()).hexdigest(),
                         self.result["source_v07_sha256"])

    def test_four_availabilities(self):
        for s,cases in self.result["scenarios"].items():
            self.assertEqual(set(cases),{"both_available","main_only",
                                        "backup_only","neither_available"})

    def test_n1_ordering(self):
        for s,c in self.result["scenarios"].items():
            a=[c[k]["unhandled_kWh"] for k in (
                "both_available","main_only","backup_only","neither_available")]
            self.assertEqual(a,sorted(a))

    def test_both_off_numbers(self):
        x=self.result["scenarios"]["both_off"]
        self.assertEqual(x["both_available"]["unsafe_intervals"],0)
        self.assertEqual(x["main_only"]["unsafe_intervals"],171)
        self.assertEqual(x["backup_only"]["unsafe_intervals"],358)
        self.assertEqual(x["neither_available"]["unsafe_intervals"],576)

    def test_decimal_crosscheck_backup(self):
        with (A36/"scenario_both_off.csv").open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        energy=sum(max(D(0),D(r["Q_reject_required_W"])-D(150000)) for r in rows)*D("0.25")/D(1000)
        actual=self.result["scenarios"]["both_off"]["backup_only"]["unhandled_kWh"]
        self.assertLess(abs(energy-D(str(actual))),D("0.000001"))

    def test_csv_24_records(self):
        with (HERE/"N1_ENVELOPE.csv").open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),24)

    def test_reject_limit_monotonic(self):
        for cap in (0,150000,180000,330000):
            values=evaluate([0,100000,180000,210000],cap)
            self.assertGreaterEqual(values["unhandled_kWh"],0)
            self.assertEqual(values["max_required_kW"],210)

    def test_release_false(self):
        self.assertFalse(self.result["physical_release_allowed"])
        self.assertEqual(self.result["IT_shedding_and_TES_dynamics"],"NOT RECOMPUTED")

if __name__=="__main__":
    unittest.main(verbosity=2)
