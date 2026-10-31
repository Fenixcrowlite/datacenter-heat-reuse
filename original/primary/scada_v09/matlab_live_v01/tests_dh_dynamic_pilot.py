"""Independent equations / guard tests for isolated v04-derived DH pilot."""
import math, sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dh_dynamic_pilot import step, calculate, DesignAssumptions

JOB="ca74c32211a44b6d9e83cd61d96cf59f"

class DynamicHeatingTests(unittest.TestCase):
    def test_equilibrium_at_ambient(self):
        a=DesignAssumptions()
        row=step(15,15,0,0,2,38,a=a)
        self.assertAlmostEqual(row["T_supply_C"],15,places=10)
        self.assertAlmostEqual(row["T_return_C"],15,places=10)
        self.assertEqual(row["Q_load_W"],0)

    def test_exact_two_node_energy_independent(self):
        a=DesignAssumptions()
        ts,tr=41.7,37.2
        q=85_000.
        stepv=step(ts,tr,q,60_000.,2.,38.,a=a)
        lhs=(a.mass_supply_kg*a.cp_J_kgK*(stepv["T_supply_C"]-ts)+
             a.mass_return_kg*a.cp_J_kgK*(stepv["T_return_C"]-tr))/900
        rhs=(q-stepv["Q_load_W"]-a.ua_supply_W_K*(stepv["T_supply_C"]-a.ambient_C)
             -a.ua_return_W_K*(stepv["T_return_C"]-a.ambient_C))
        self.assertLess(abs(lhs-rhs),1e-6)
        self.assertGreaterEqual(stepv["Q_load_W"],0)
        self.assertLessEqual(stepv["Q_load_W"],60_000)

    def test_no_flow_no_pump_and_no_load(self):
        r=step(45,37,0,90_000.,0,38)
        self.assertEqual(r["Q_load_W"],0)
        self.assertEqual(r["P_pump_W"],0)
        self.assertEqual(r["delta_pressure_Pa"],0)
        self.assertLess(r["T_supply_C"],45)

    def test_design_flow_and_pump_electricity(self):
        a=DesignAssumptions()
        r=step(48,38,80_000,100_000,5,38,a=a)
        self.assertAlmostEqual(r["delta_pressure_Pa"],a.pump_head_nominal_Pa)
        expected=a.pump_head_nominal_Pa*5/(a.rho_kg_m3*a.pump_efficiency)
        self.assertAlmostEqual(r["P_pump_W"],expected)

    def test_reject_invalid_parameters(self):
        for heat, demand, flow in ((float("nan"),0,1),(-1,0,1),(1,-1,1),(1,0,-2)):
            with self.subTest(heat=heat,demand=demand,flow=flow):
                with self.assertRaises(ValueError):
                    step(40,35,heat,demand,flow,38)

    def test_real_saved_v04_source_time_and_off(self):
        result=calculate(JOB)
        self.assertEqual(result["sample_count"],672)
        self.assertLess(result["max_energy_residual_W"],1e-6)
        rows=result["rows"]
        self.assertAlmostEqual(rows[-1]["interval_end_h"],168)
        self.assertAlmostEqual(result["total_Q_DH_source_MWh"],7.615207628813911,places=9)
        for row in rows:
            self.assertGreaterEqual(row["Q_load_W"],0)
            self.assertTrue(math.isfinite(row["T_supply_C"]))
            self.assertTrue(math.isfinite(row["T_return_C"]))
        for row in rows:
            if row["interval_start_h"]>=96:
                self.assertEqual(row["flow_kg_s"],0)
                self.assertEqual(row["P_pump_W"],0)
                self.assertEqual(row["Q_load_W"],0)
                self.assertAlmostEqual(row["Q_DH_source_W"],0)

if __name__=="__main__":unittest.main()
