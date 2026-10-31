"""Deterministic conservation and negative-path QA for synthetic v08 reference."""
import copy
import csv
import math
import unittest
from pathlib import Path
from redispatch import Caps, dispatch, apply_after

SOURCE = Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv")
def rows():
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

class RedispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = rows()
        cls.first = cls.rows[0]

    def test_full_real_baseline_672(self):
        self.assertEqual(len(self.rows), 672)
        for row in self.rows:
            o = dispatch(row)
            for key, original in (
                ("Q_pool_W", "Q_pool_phys_W"), ("Q_DH_W", "Q_DH_W"),
                ("Q_HP_source_W", "Q_HP_source_W"),
                ("Q_reject_required_W", "Q_reject_physical_W"),
                ("P_HP_proxy_W", "P_HP_W"),
                ("Q_TES_discharge_W", "Q_TES_discharge_W"),
            ):
                self.assertAlmostEqual(o[key], float(row[original]), places=5)

    def test_pool_off(self):
        for row in self.rows:
            o = dispatch(row, Caps(pool_W=0))
            self.assertAlmostEqual(o["Q_pool_W"], 0)
            self.assertAlmostEqual(o["Q_DH_W"], float(row["Q_DH_W"]), places=5)
            self.assertGreaterEqual(o["Q_reject_required_W"] + 1e-6, float(row["Q_reject_physical_W"]))

    def test_dh_off(self):
        for row in self.rows:
            o = dispatch(row, Caps(dh_W=0))
            self.assertAlmostEqual(o["Q_DH_W"], 0)
            self.assertAlmostEqual(o["Q_TES_discharge_W"], 0)
            self.assertAlmostEqual(o["Q_pool_W"], float(row["Q_pool_phys_W"]), places=5)

    def test_both_off(self):
        for row in self.rows:
            o = dispatch(row, Caps(pool_W=0, dh_W=0))
            self.assertAlmostEqual(o["Q_pool_W"], 0)
            self.assertAlmostEqual(o["Q_DH_W"], 0)
            self.assertGreaterEqual(o["Q_reject_required_W"], 0)

    def test_capped_power(self):
        for row in self.rows:
            o = dispatch(row, Caps(pool_W=40000, dh_W=25000))
            self.assertLessEqual(o["Q_pool_W"], 40000.00001)
            self.assertLessEqual(o["Q_DH_W"], 25000.00001)

    def test_reject_cap_unsafe(self):
        o = dispatch(self.first, Caps(pool_W=0, dh_W=0, reject_W=1000))
        self.assertEqual(o["status"], "UNSAFE_UNHANDLED_HEAT")
        self.assertGreater(o["Q_unhandled_W"], 0)
        self.assertAlmostEqual(o["Q_reject_actual_W"], 1000)

    def test_unknown_capacity_never_safe(self):
        o = dispatch(self.first, Caps(pool_W=0))
        self.assertEqual(o["status"], "REJECT_CAPACITY_UNKNOWN")

    def test_no_electrical_savings_claim(self):
        o = dispatch(self.first, Caps(pool_W=0))
        self.assertFalse(o["electric_savings_validated"])
        self.assertFalse(o["TES_state_validated"])
        self.assertLess(o["P_HP_proxy_W"], float(self.first["P_HP_W"]))

    def test_delayed_switch(self):
        r = self.rows[10]
        self.assertEqual(apply_after(r, Caps(pool_W=0), start_hour=24)["Q_pool_W"],
                         dispatch(r)["Q_pool_W"])
        r = self.rows[200]
        self.assertEqual(apply_after(r, Caps(pool_W=0), start_hour=24)["Q_pool_W"], 0)

    def test_inputs_immutable(self):
        r = copy.deepcopy(self.first)
        dispatch(r, Caps(pool_W=0, dh_W=0))
        self.assertEqual(r, self.first)

    def test_bad_nan(self):
        r = dict(self.first, Q_DC_eff_W="nan")
        with self.assertRaises(ValueError):
            dispatch(r)

    def test_bad_negative(self):
        r = dict(self.first, Q_HP_pool_W="-1")
        with self.assertRaises(ValueError):
            dispatch(r)

    def test_bad_baseline_energy(self):
        r = dict(self.first, Q_DC_eff_W="300000")
        with self.assertRaises(ValueError):
            dispatch(r)

    def test_bad_caps(self):
        for cap in [-1, math.inf, math.nan]:
            with self.assertRaises(ValueError):
                Caps(pool_W=cap)

    def test_bad_hour(self):
        with self.assertRaises(ValueError):
            apply_after(dict(self.first, cas_h="nan"), Caps(pool_W=0), 0)

    def test_conservation_for_all_rows_and_cases(self):
        for r in self.rows:
            for caps in (Caps(), Caps(pool_W=0), Caps(dh_W=0),
                         Caps(pool_W=0, dh_W=0),
                         Caps(pool_W=40000, dh_W=25000, reject_W=150000)):
                o = dispatch(r, caps)
                self.assertLess(max(abs(v) for v in o["residuals_W"].values()), 1e-5)
                self.assertGreaterEqual(o["Q_unhandled_W"], 0)
                self.assertGreaterEqual(o["P_HP_proxy_W"], 0)

    def test_hp_cop_consistency(self):
        for r in self.rows:
            o = dispatch(r, Caps(pool_W=0, dh_W=0))
            if o["P_HP_proxy_W"] > 1e-6:
                condenser = o["Q_HP_pool_W"] + o["Q_HP_DH_W"] + o["Q_HP_charge_W"]
                self.assertAlmostEqual(condenser / o["P_HP_proxy_W"],
                                       o["COP_baseline_effective"], places=7)

if __name__ == "__main__":
    unittest.main(verbosity=2)
