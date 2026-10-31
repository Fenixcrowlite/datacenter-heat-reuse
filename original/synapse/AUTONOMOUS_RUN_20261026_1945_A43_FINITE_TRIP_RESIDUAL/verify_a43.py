"""A43 independent post-MATLAB artifact and numerical acceptance, no registry writes."""
import csv
import hashlib
import json
import math
import unittest
import zipfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
CASES=("both","main_only","backup_only","neither","CF_both","CF_backup_only","CF_neither")
LIMITS=(1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3)

class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=json.loads((HERE/"MATLAB_AUDIT_A43.json").read_text(encoding="utf8"))
        cls.s=json.loads((HERE/"SIMULINK_A43_RESULT.json").read_text(encoding="utf8"))
        cls.p=json.loads((HERE/"RESULTS_A43.json").read_text(encoding="utf8"))
    def test_matlab_numeric_audit(self):
        self.assertEqual(self.a["status"],"A43_MATLAB_INDEPENDENT_CSV_AUDIT_PASS")
        self.assertEqual(self.a["samples"],4704)
        self.assertLess(self.a["max_thermal_error_C"],1e-8)
        self.assertLess(self.a["max_scaled_balance_error"],1e-6)
        self.assertFalse(self.a["matlab_simulink_model_built"])
    def test_simulink_parity(self):
        self.assertEqual(self.s["status"],"A43_SIMULINK_EMCHART_CLOSED_LOOP_PARITY_PASS")
        self.assertEqual(self.s["samples"],4704)
        self.assertEqual(self.s["numeric_comparisons"],51744)
        self.assertEqual(set(self.s["scenarios"]),set(CASES))
        for label in CASES:
            v=self.s["scenarios"][label]
            self.assertEqual(v["samples"],672)
            self.assertEqual(v["parity"],"PASS")
            self.assertEqual(len(v["max_abs_differences"]),11)
            for diff,limit in zip(v["max_abs_differences"],LIMITS):
                self.assertLessEqual(diff,limit)
            self.assertAlmostEqual(v["max_temperature_C"],
                                   self.p["cases"][label]["max_temperature_C"],places=7)
    def test_simulink_model_zip(self):
        model=HERE/"DCHR_A43_Finite_Trip_Closed_Loop.slx"
        self.assertGreater(model.stat().st_size,30000)
        with zipfile.ZipFile(model) as z:
            self.assertIsNone(z.testzip())
            names=z.namelist()
            self.assertTrue(any("blockdiagram" in n.lower() for n in names))
            self.assertTrue(any("stateflow" in n.lower() for n in names))
    def test_actual_logs(self):
        self.assertIn("A43_SIMULINK_ALL_PASS 51744",
                      (HERE/"SIMULINK_STDOUT.txt").read_text(encoding="utf8"))
        self.assertIn("A43_MATLAB_ALL_PASS 4704",
                      (HERE/"MATLAB_STDOUT.txt").read_text(encoding="utf8"))
        self.assertEqual((HERE/"SIMULINK_STDERR.txt").stat().st_size,0)
        self.assertEqual((HERE/"MATLAB_STDERR.txt").stat().st_size,0)
    def test_synthetic_only(self):
        self.assertFalse(self.p["physical_release"])
        self.assertFalse(self.p["hardware_control"])
        self.assertFalse(self.s["physical_release"])
        self.assertFalse(self.s["graphical_stateflow_chart_built"])
        self.assertTrue(self.s["state_machine_implemented_in_EMChart"])
    def test_thermal_threshold(self):
        self.assertGreater(self.p["cases"]["neither"]["max_temperature_C"],42)
        self.assertGreater(self.p["cases"]["backup_only"]["max_temperature_C"],42)
        self.assertEqual(self.p["cases"]["both"]["exceed_42_steps"],0)
    def test_input_integrity(self):
        import finite_trip_a43 as f
        self.assertEqual(self.p["a42_source_sha256"],f.digest(f.A42/"coupled_a42.py"))
        self.assertEqual(self.p["input_sha256"],f.digest(f.base.SOURCE))

if __name__=="__main__":
    unittest.main(verbosity=2)
