import math
import unittest

import compressor_a45 as hp
import finite_trip_a45 as a45

class CompressorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = a45.verified_inputs()
    def test_step_zero_tau(self):
        self.assertEqual(hp.step_capacity(0, 100000, 900, 0), 100000)
    def test_first_order_exact(self):
        self.assertAlmostEqual(hp.step_capacity(0, 100000, 900, 900), 100000*(1-math.exp(-1)))
    def test_decay(self):
        self.assertLess(hp.step_capacity(100000, 0, 900, 900), 100000)
    def test_invalid_tau(self):
        with self.assertRaises(ValueError): hp.step_capacity(0, 1000, 900, -1)
    def test_invalid_nan(self):
        with self.assertRaises(ValueError): hp.step_capacity(0, math.nan, 900, 900)
    def test_invalid_hp_cap(self):
        with self.assertRaises(ValueError):
            hp.dispatch_limited(self.rows[0], 0, hp.base.E_INIT, 30, 330000, -1)
    def test_zero_tau_parity_with_a43(self):
        from finite_trip_a45 import base
        from pathlib import Path
        import sys
        a43_path = Path(__file__).resolve().parent.parent/"AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL"
        sys.path.insert(0,str(a43_path))
        import finite_trip_a43 as a43
        for scenario in ("both","backup_only","neither"):
            new = a45.simulate(self.rows[:115],scenario,compressor_tau_s=0)
            old = a43.simulate(self.rows[:115],scenario)
            for n,o in zip(new,old):
                for key in ("T_next_C","E_next_J","hp_source_W","hp_electric_W","unhandled_W"):
                    self.assertAlmostEqual(n[key],o[key],delta=1e-5)
    def test_lag_lowers_first_step_hp_source(self):
        slow = a45.simulate(self.rows[:8],"both",compressor_tau_s=7200)
        instant = a45.simulate(self.rows[:8],"both",compressor_tau_s=0)
        self.assertLess(slow[0]["hp_source_W"],instant[0]["hp_source_W"])
    def test_hp_capacity_bound(self):
        trace=a45.simulate(self.rows[:115],"backup_only",compressor_tau_s=1800)
        self.assertTrue(all(r["hp_source_W"]<=r["hp_available_W"]+1e-8 for r in trace))
    def test_balance(self):
        for scenario in hp.base.SCENARIOS:
            for r in a45.simulate(self.rows,scenario):
                self.assertLess(abs(r["it_balance_W"]),1e-6)
                self.assertLess(abs(r["hp_balance_W"]),1e-6)
                self.assertLess(abs(r["user_balance_W"]),1e-6)
                self.assertLess(abs(r["tes_balance_J"]),1e-3)
    def test_energy_no_creation(self):
        for r in a45.simulate(self.rows[:100],"both"):
            self.assertAlmostEqual(r["hp_condenser_W"],r["hp_source_W"]+r["hp_electric_W"],delta=1e-7)
    def test_compressor_tau_validation(self):
        with self.assertRaises(ValueError):a45.simulate(self.rows[:1],"both",compressor_tau_s=-2)

if __name__=="__main__": unittest.main()
