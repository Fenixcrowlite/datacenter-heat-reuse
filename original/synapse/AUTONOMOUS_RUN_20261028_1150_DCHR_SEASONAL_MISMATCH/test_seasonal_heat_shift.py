import datetime as dt
import math
import tempfile
import unittest
from pathlib import Path
import seasonal_heat_shift as s

class StorageTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(s.ideal_store([(0,0)],0)[0]["saved_gas_heat_mwh"],0)
    def test_zero_capacity(self):
        self.assertEqual(s.ideal_store([(3,0),(0,2)],0)[0]["saved_gas_heat_mwh"],0)
    def test_shift(self):
        self.assertAlmostEqual(s.ideal_store([(3,0),(0,2)],10)[0]["saved_gas_heat_mwh"],2)
    def test_cap(self):
        self.assertAlmostEqual(s.ideal_store([(3,0),(0,2)],1)[0]["saved_gas_heat_mwh"],1)
    def test_no_double_count(self):
        y=s.ideal_store([(3,0),(0,2)],10)[0]
        self.assertAlmostEqual(y["charged_mwh"],3)
        self.assertAlmostEqual(y["final_soc_mwh"],1)
    def test_year_boundary(self):
        y=s.ideal_store([(0,2),(3,0)],10,3)
        self.assertEqual(y[0]["saved_gas_heat_mwh"],0)
        self.assertEqual(y[1]["saved_gas_heat_mwh"],2)
        self.assertEqual(y[2]["saved_gas_heat_mwh"],2)
    def test_overlapping_streams_rejected(self):
        with self.assertRaises(ValueError): s.ideal_store([(1,1)],10)
    def test_negative_rejected(self):
        with self.assertRaises(ValueError): s.ideal_store([(-1,0)],10)
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError): s.ideal_store([(float("nan"),0)],10)
    def test_bad_capacity(self):
        with self.assertRaises(ValueError): s.ideal_store([(0,1)],-1)
    def test_bad_cycles(self):
        with self.assertRaises(ValueError): s.ideal_store([(0,1)],1,0)
    def test_source_sha(self):
        with self.assertRaises(ValueError): s.load(s.SOURCE,"0"*64)
    def test_real_source(self):
        rows,sha=s.load()
        self.assertEqual(len(rows),8760)
        self.assertEqual(sha,s.EXPECTED_SHA)
        result=s.analyze(rows,sha)
        self.assertEqual(result["simultaneous_curtailment_gas_hours"],0)
        self.assertEqual(result["direct_same_hour_overlap_upper_bound_mwh"],0)
        self.assertGreater(result["curtailed_potential_mwh"],20000)
        self.assertGreater(result["gas_heat_mwh"],12000)
        self.assertLess(result["ideal_counterfactual_capacities_mwh"]["100"][1]["saved_gas_heat_mwh"],110)
        self.assertEqual(result["primary_source_signoffs"],0)
    def test_monotonic_capacity(self):
        y=[(2,0),(0,3),(4,0),(0,3)]
        values=[s.ideal_store(y,c)[0]["saved_gas_heat_mwh"] for c in (0,1,2,4,10)]
        self.assertEqual(values,sorted(values))
    def test_balance_rejection(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/"bad.csv"
            p.write_text("Time,"+",".join(s.FIELDS)+"\n"+"01-Jan-2026 00:00:00,"+"0,1,0,0,0,0\n",encoding="utf-8")
            with self.assertRaises(ValueError):s.load(p,None)

if __name__=="__main__":
    unittest.main(verbosity=2)
