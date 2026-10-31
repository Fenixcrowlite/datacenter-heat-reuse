import unittest
from tes_soc import (tes_step,load,baseline_replay,replay,EMAX,E0,DT,ETA_C,ETA_D)
class TESModelTests(unittest.TestCase):
 def test_empty_storage(self):
  r=tes_step(0,0,0);self.assertEqual(r["E_next_J"],0)
 def test_capacity_clips_charge(self):
  r=tes_step(EMAX,70000,0);self.assertAlmostEqual(r["charge_actual_W"],(.002*EMAX/86400)/ETA_C);self.assertAlmostEqual(r["E_next_J"],EMAX)
 def test_empty_capacity_blocks_discharge(self):
  with self.assertRaises(ValueError):tes_step(0,0,1000)
 def test_no_simultaneous(self):
  with self.assertRaises(ValueError):tes_step(E0,100,100)
 def test_exact_tes_energy(self):
  r=tes_step(E0,10000,0)
  loss=.002*E0/86400
  self.assertAlmostEqual(r["E_next_J"],E0+DT*(ETA_C*10000-loss),places=4)
 def test_over_capacity_rejected(self):
  with self.assertRaises(ValueError):tes_step(EMAX+100,0,0)
 def test_negative_rejected(self):
  with self.assertRaises(ValueError):tes_step(E0,-1,0)
 def test_original_v08_reproduced(self):
  raw,dispatch,src=load()
  self.assertEqual(len(raw),672)
  self.assertLess(baseline_replay(raw),1e-4)
 def test_both_off_saturation(self):
  raw,dispatch,src=load()
  trace=replay(raw,dispatch)
  self.assertEqual(len(trace),672)
  self.assertTrue(any(r["Q_charge_curtailed_W"]>1e-6 for r in trace))
  self.assertTrue(all(0<=r["TES_SOC_next"]<=1 for r in trace))
 def test_hp_dc_closure(self):
  raw,dispatch,src=load()
  trace=replay(raw,dispatch)
  self.assertLess(max(abs(x["DC_balance_residual_W"]) for x in trace),1e-5)
  self.assertLess(max(abs(x["HP_balance_residual_W"]) for x in trace),1e-5)
 def test_originals_not_mutated(self):
  raw,dispatch,src=load()
  self.assertEqual(float(raw[0]["cas_h"]),0)
  self.assertEqual(float(dispatch[-1]["cas_h"]),167.75)
if __name__=="__main__":unittest.main()
