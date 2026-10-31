"""Independent regression gates for A54 parameter sensitivity."""
import unittest,sys,json
from pathlib import Path
D=Path(__file__).resolve().parent
sys.path.insert(0,str(D))
import a54_uncertainty as a
class A54Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads((D/"A54_UNCERTAINTY_RESULTS.json").read_text(encoding="utf-8"))
 def test_full_matrix(self):
  self.assertEqual(len(self.report["cases"]),144)
  self.assertEqual(self.report["baseline_A52_anchors_checked"],18)
 def test_unique_parameters(self):
  cases=self.report["cases"]
  self.assertEqual(len({(x["scenario"],x["sensor_lag_steps"],x["trip_delay_steps"],x["heat_capacity_J_per_C"],x["residual_fraction"],x["compressor_tau_s"]) for x in cases}),144)
 def test_no_safety_claim(self):
  self.assertTrue(self.report["not_a_certified_safety_envelope"])
  self.assertFalse(self.report["physical_release"])
 def test_energy_ledger(self):
  self.assertLess(max(x["max_flow_residual_W"] for x in self.report["cases"]),1e-6)
 def test_finite_metrics(self):
  import math
  self.assertTrue(all(math.isfinite(x["max_temperature_C"]) and math.isfinite(x["unhandled_heat_kWh"]) for x in self.report["cases"]))
 def test_trip_exists(self):
  self.assertTrue(all(isinstance(x["first_trip_index"],int) for x in self.report["cases"]))
 def test_baseline_anchor_replay(self):
  from a49_independent_audit import independent_audit
  rows=a.plant.verified_inputs()[:240]
  t=a.plant.simulate(rows,"neither",sensor_lag_steps=0,trip_delay_steps=4)
  self.assertEqual(independent_audit(t)["first_trip_index"],100)
 def test_source_hash(self):
  self.assertEqual(self.report["source_A52_sha256"],a.sha(a.A52/"SENSITIVITY_A52.json"))
if __name__=="__main__":unittest.main()

