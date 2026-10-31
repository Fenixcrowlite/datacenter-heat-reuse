"""Independent conservation checks, separate from archived numerical fixtures."""
import math
import unittest
from heat_reuse.runner import run_model

class ConservationTests(unittest.TestCase):
    def test_pool_power_balances(self):
        result = run_model("pool-v04", steps=96)
        for r in result["rows"]:
            self.assertTrue(math.isfinite(r["T_bazen_C"]))
            self.assertGreaterEqual(r["E_TES_J"], 0)
            self.assertLessEqual(r["E_TES_J"], 900 * 3.6e6 + 1e-3)
            self.assertAlmostEqual(r["Q_pool_W"], r["Q_direct_W"] + r["Q_HP_pool_W"], delta=1e-6)
            self.assertAlmostEqual(r["Q_DH_delivered_W"], r["Q_HP_DH_W"] + r["Q_TES_dis_W"], delta=1e-6)
            self.assertAlmostEqual(r["Q_HP_pool_W"] + r["Q_HP_DH_W"] + r["Q_HP_TES_charge_W"],
                                   r["Q_HP_source_W"] + r["P_HP_comp_W"], delta=1e-6)
            self.assertAlmostEqual(r["Qdc_in_W"], r["Q_direct_W"] + r["Q_HP_source_W"] + r["Q_reject_W"], delta=1e-6)

    def test_disabled_pool_cannot_receive_heat(self):
        result = run_model("pool-v04", {"pool_enabled": False}, steps=48)
        for r in result["rows"]:
            self.assertEqual(r["Q_pool_req_W"], 0.0)
            self.assertEqual(r["Q_pool_W"], 0.0)

    def test_annual_heat_supply_balance(self):
        result = run_model("annual-v2", steps=48)
        for r in result["rows"]:
            self.assertAlmostEqual(r["Heat_Demand_MW"],
                r["HP_Heat_Used_MW"] - r["Storage_Charge_MW"]
                + r["Storage_Discharge_MW"] + r["Gas_Heat_MW"], delta=1e-8)
            self.assertGreaterEqual(r["Storage_E_end_MWh"], -1e-8)
            self.assertLessEqual(r["Storage_E_end_MWh"], result["config"]["storage_capacity_MWh"] + 1e-8)

if __name__ == "__main__":
    unittest.main()
