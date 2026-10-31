"""Critical unit discrepancy regression for Varna article, sec.3.1.1."""
import unittest,json
from pathlib import Path
class UnitGate(unittest.TestCase):
 def test_published_gas_unit_mismatch(self):
  volume_reported_m3=9122; gas_kwh_m3=10.7; heat_mwh=97522
  gas_energy_mwh=volume_reported_m3*gas_kwh_m3/1000
  self.assertAlmostEqual(gas_energy_mwh,97.6054)
  self.assertGreater(heat_mwh/gas_energy_mwh,900)
 def test_inferred_volume_thousands(self):
  actual_m3=97522*1000/10.7
  self.assertGreater(actual_m3,9_000_000)
  self.assertLess(actual_m3,9_300_000)
 def test_9122_thousand_cubic_m_is_consistent_to_1pct(self):
  energy_mwh=9122*1000*10.7/1000
  self.assertLess(abs(energy_mwh-97522)/97522,.01)
 def test_thermal_demand_not_equal_fuel_energy(self):
  self.assertNotEqual(81162,97522)
  self.assertTrue(0<81162/97522<1)
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(UnitGate)
 res=unittest.TestResult();suite.run(res)
 out={'source':20,'unit_gate_tests':res.testsRun,'status':'PASS' if res.wasSuccessful() else 'FAIL',
  'failures':[x for _,x in res.failures], 'errors':[x for _,x in res.errors],
  'meaning':'Found about thousandfold natural-gas unit mismatch in printed article; author clarification pending'}
 Path(__file__).with_name('varna_unit_sanity_v07.json').write_text(json.dumps(out,indent=2),encoding='utf8')
 print(json.dumps(out))
 if not res.wasSuccessful():raise SystemExit(1)
