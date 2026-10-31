"""Independent A43 acceptance: provenance, finite shutdown, energy and sensitivity."""
import csv
import json
import math
import unittest
from decimal import Decimal
from pathlib import Path
import finite_trip_a43 as a

D=lambda x: Decimal(str(x))
HERE=Path(__file__).resolve().parent

class A43Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=a.verified_inputs()
        cls.report=json.loads((HERE/"RESULTS_A43.json").read_text(encoding="utf8"))
    def test_source_immutability(self):
        self.assertEqual(len(self.rows),672)
        self.assertEqual(self.report["a42_source_sha256"],a.digest(a.A42/"coupled_a42.py"))
        self.assertEqual(self.report["input_sha256"],a.digest(a.base.SOURCE))
        self.assertFalse(self.report["physical_release"])
        self.assertFalse(self.report["hardware_control"])
        self.assertFalse(self.report["matlab_stateflow_executed"])
    def test_seven_saved_scenarios(self):
        self.assertEqual(len(self.report["cases"]),7)
        for label,info in self.report["cases"].items():
            p=HERE/("TRACE_A43_"+label+".csv")
            self.assertEqual(a.digest(p),info["sha256"])
            with p.open(encoding="utf8",newline="") as f:
                records=list(csv.DictReader(f))
            self.assertEqual(len(records),672)
            self.assertEqual([int(r["k"]) for r in records],list(range(672)))
    def test_two_intervals_before_trip(self):
        t=a.simulate(self.rows,"neither",trip_delay_steps=2)
        self.assertEqual([t[k]["state"] for k in (95,96,97,98)],
                         ["ACTIVE","TRIP_PENDING","TRIP_PENDING","TRIPPED"])
        self.assertGreater(t[96]["active_it_W"],0)
        self.assertGreater(t[97]["active_it_W"],0)
        self.assertEqual(t[98]["active_it_W"],0)
        self.assertGreater(t[98]["residual_it_W"],0)
    def test_residual_decay(self):
        t=a.simulate(self.rows,"neither")
        self.assertAlmostEqual(t[99]["residual_it_W"]/t[98]["residual_it_W"],
                               math.exp(-900/3600),places=10)
        self.assertGreater(t[98]["qit_W"],0)
        self.assertEqual(t[98]["qit_W"],t[98]["residual_it_W"])
    def test_finite_trip_changes_thermal_risk(self):
        ideal=a.base.replay(self.rows,"neither")
        delayed=a.simulate(self.rows,"neither")
        self.assertAlmostEqual(max(r["T_next_C"] for r in ideal),30)
        self.assertGreater(max(r["T_next_C"] for r in delayed),42)
        self.assertGreater(sum(r["unhandled_W"] for r in delayed),0)
    def test_reject_ramp_after_recovery(self):
        t=a.simulate(self.rows,"neither")
        self.assertEqual(t[383]["effective_cap_W"],0)
        self.assertEqual(t[384]["effective_cap_W"],60000)
        self.assertEqual(t[385]["effective_cap_W"],120000)
        self.assertLessEqual(max(r["reject_W"]-r["effective_cap_W"] for r in t),1e-7)
    def test_baseline_no_fault_parity(self):
        reference=a.base.replay(self.rows,"both")
        actual=a.simulate(self.rows,"both",trip_delay_steps=0,residual_fraction=0,
                          reject_ramp_W=1e9)
        for old,new in zip(reference,actual):
            self.assertAlmostEqual(old["T_next_C"],new["T_next_C"],places=7)
            self.assertAlmostEqual(old["E_next_J"],new["E_next_J"],delta=1e-4)
            self.assertAlmostEqual(old["qit_W"],new["qit_W"],places=6)
    def test_independent_decimal_balances_18816(self):
        count=0
        for label in self.report["cases"]:
            path=HERE/("TRACE_A43_"+label+".csv")
            with path.open(encoding="utf8",newline="") as f:
                for r in csv.DictReader(f):
                    it=D(r["qit_W"])-D(r["hx_W"])-D(r["leak_W"])-D(r["hp_source_W"])-D(r["reject_W"])-D(r["unhandled_W"])
                    hp=D(r["hp_condenser_W"])-D(r["hp_source_W"])-D(r["hp_electric_W"])
                    user=D(r["pool_dh_demand_W"])-D(r["pool_dh_served_W"])-D(r["pool_dh_unmet_W"])
                    tes=D(r["E_next_J"])-D(r["E_start_J"])-D("900")*(D(".93")*D(r["tes_charge_W"])-D(r["tes_discharge_W"])/D(".91")-D(r["tes_loss_W"]))
                    self.assertLess(abs(it),D(".000001"))
                    self.assertLess(abs(hp),D(".000001"))
                    self.assertLess(abs(user),D(".000001"))
                    self.assertLess(abs(tes),D(".001"))
                    self.assertGreaterEqual(D(r["active_it_W"]),0)
                    self.assertGreaterEqual(D(r["residual_it_W"]),0)
                    self.assertLessEqual(D(r["reject_W"]),D(r["effective_cap_W"])+D(".0000001"))
                    count+=4
        self.assertEqual(count,18816)
    def test_sensitivity_grid(self):
        self.assertEqual(len(self.report["sensitivity"]),12)
        low=self.report["sensitivity"]["delay0_residual0"]
        high=self.report["sensitivity"]["delay4_residual0.25"]
        self.assertGreater(high["max_temperature_C"],low["max_temperature_C"])
    def test_fail_closed_parameters(self):
        bad=({"trip_delay_steps":-1},{"trip_delay_steps":1.5},
             {"residual_fraction":.9},{"residual_tau_s":0},
             {"reject_ramp_W":0},{"sensor_lag_steps":-1},
             {"heat_capacity_J_per_C":0})
        for kwargs in bad:
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                a.simulate(self.rows,"neither",**kwargs)
    def test_no_hardware_calls(self):
        source=(HERE/"finite_trip_a43.py").read_text(encoding="utf8").lower()
        for banned in ("subprocess.","socket.","serial.","requests.","modbus","opcua","pymodbus"):
            self.assertNotIn(banned,source)

if __name__=="__main__":
    unittest.main(verbosity=2)
