"""Publisher HTML check vectors for Varna source №20; not replication."""
import unittest,json,math
from pathlib import Path
class VarnaEquations(unittest.TestCase):
 def test_dc_airload_eq1(self):
  self.assertAlmostEqual(1.0*1.2*(35-20),18.0) # kJ/kg/K*kg/s*K = kW
 def test_fan_eq3_watt_not_kw(self):
  flow=1.2;dp=150;rho=1.2;eta=.6
  power_w=flow*dp/(rho*eta)
  self.assertAlmostEqual(power_w,250.)
  self.assertAlmostEqual(power_w/1000,.25)
 def test_vcc_energy_eq4_5(self):
  cold_kw=500;eer=2.5
  comp=cold_kw/eer;sink=cold_kw+comp
  self.assertEqual(comp,200)
  self.assertEqual(sink,700)
 def test_ideal_eer_eq6_kelvin(self):
  tl=288.15;th=318.15
  self.assertAlmostEqual(tl/(th-tl),9.605)
  self.assertGreater(tl/(th-tl),0)
 def test_case_ac_gate(self):
  def recover(active_cooling,q_waste): return q_waste if active_cooling else 0.
  self.assertEqual(recover(False,700),0)
  self.assertEqual(recover(True,700),700)
 def test_tcs_black_box_roundtrip(self):
  energy_charge_mwh=100
  self.assertEqual(energy_charge_mwh*.9,90)
  self.assertEqual(energy_charge_mwh*.75,75)
  self.assertAlmostEqual((90-75)/90,1/6)
 def test_annual_mean_vs_rounded(self):
  self.assertAlmostEqual(81162/8760,9.265068493150685)
  self.assertAlmostEqual(.03*81162,2434.86)
 def test_temperature_constraints(self):
  for tl,th in [(288.15,318.15),(300,310)]:
   eer=tl/(th-tl)
   self.assertGreater(eer,0)
  with self.assertRaises(ZeroDivisionError):_ = 300/(300-300)
if __name__=="__main__":
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(VarnaEquations)
 res=unittest.TestResult();suite.run(res)
 out={'source':20,'tests':res.testsRun,'status':'PASS' if res.wasSuccessful() else 'FAIL',
   'errors':[str(x) for _,x in res.errors],'failures':[str(x) for _,x in res.failures],
   'scope':'Publisher printed-equation unit sanity only; source replicability not established'}
 Path(__file__).with_name('varna_source_tests_v07.json').write_text(json.dumps(out,indent=2),encoding='utf8')
 print(json.dumps(out))
 if not res.wasSuccessful(): raise SystemExit(1)
