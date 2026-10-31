"""Independent acceptance tests for isolated A42, including Decimal balances."""
from __future__ import annotations
import csv
import json
import math
import unittest
from decimal import Decimal
from pathlib import Path
import coupled_a42 as m
import counterfactual_a42 as cf

HERE=Path(__file__).resolve().parent
D=lambda v:Decimal(str(v))

class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=m.load_inputs()
        cls.report=json.loads((HERE/"RESULTS_A42.json").read_text(encoding="utf8"))
        cls.counter=json.loads((HERE/"COUNTERFACTUAL_A42.json").read_text(encoding="utf8"))

    def test_input_provenance_and_no_source_mutation(self):
        self.assertEqual(len(self.inputs),672)
        self.assertEqual(self.report["a41_input_sha256"],m.sha(m.SOURCE))
        self.assertFalse(self.report["physical_release_allowed"])
        self.assertFalse(self.report["hardware_control"])

    def test_four_scenarios_672_each(self):
        self.assertEqual(set(self.report["cases"]),set(m.SCENARIOS))
        for scenario in m.SCENARIOS:
            path=HERE/f"TRACE_A42_{scenario}.csv"
            with path.open(encoding="utf8",newline="") as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),672)
            self.assertEqual(self.report["cases"][scenario]["trace_sha256"],m.sha(path))
            self.assertEqual([int(float(x["k"])) for x in rows],list(range(672)))

    def test_reject_and_source_caps(self):
        for s in m.SCENARIOS:
            for r in m.replay(self.inputs,s):
                self.assertLessEqual(r["reject_W"],r["cap_W"]+1e-7)
                self.assertLessEqual(r["hp_source_W"]+r["hx_W"]+r["leak_W"],r["qit_W"]+1e-7)
                self.assertLessEqual(r["hp_condenser_W"],r["hp_source_W"]+r["hp_electric_W"]+1e-7)
                self.assertGreaterEqual(r["pool_dh_unmet_W"],-1e-7)
                self.assertGreaterEqual(r["E_next_J"],-1e-5)
                self.assertLessEqual(r["E_next_J"],m.E_MAX+1e-5)

    def test_independent_decimal_energy_balances(self):
        count=0
        for s in m.SCENARIOS:
            for r in m.replay(self.inputs,s):
                it=D(r["qit_W"])-D(r["hx_W"])-D(r["leak_W"])-D(r["hp_source_W"])-D(r["reject_W"])-D(r["unhandled_W"])
                hp=D(r["hp_condenser_W"])-D(r["hp_source_W"])-D(r["hp_electric_W"])
                user=D(r["pool_dh_demand_W"])-D(r["pool_dh_served_W"])-D(r["pool_dh_unmet_W"])
                tes=D(r["E_next_J"])-D(r["E_start_J"])-D(m.DT)*(D(".93")*D(r["tes_charge_W"])-D(r["tes_discharge_W"])/D(".91")-D(r["tes_loss_W"]))
                self.assertLess(abs(it),D(".000001"))
                self.assertLess(abs(hp),D(".000001"))
                self.assertLess(abs(user),D(".000001"))
                self.assertLess(abs(tes),D(".001"))
                count+=4
        self.assertEqual(count,10752)

    def test_zero_capacity_interlock_independent_of_sensor_lag(self):
        for lag in (0,1,2,4):
            t=m.replay(self.inputs,"neither",sensor_lag_steps=lag)
            for r in t[96:384]:
                self.assertEqual(r["cap_W"],0)
                self.assertEqual(r["mode"],"TRIPPED")
                self.assertEqual(r["qit_W"],0)
                self.assertEqual(r["unhandled_W"],0)

    def test_restart_not_immediate(self):
        t=m.replay(self.inputs,"neither")
        self.assertEqual(t[384]["mode"],"TRIPPED")
        self.assertEqual(t[384]["qit_W"],0)
        self.assertEqual(t[385]["mode"],"RAMPING")
        self.assertEqual(t[385]["qit_W"],15000)

    def test_backup_switch_delay_and_temperature_trip(self):
        t=m.replay(self.inputs,"backup_only")
        self.assertEqual([t[k]["cap_W"] for k in (95,96,97,98)],[330000,0,0,150000])
        self.assertEqual([t[k]["mode"] for k in (96,97,98)],["TRIPPED","TRIPPED","TRIPPED"])
        self.assertGreaterEqual(max(r["T_next_C"] for r in t),42)

    def test_dynamic_cop_and_hp_source(self):
        r=self.inputs[0]
        a=m.dispatch(r,r["qdc"],m.E_INIT,30,330000)
        b=m.dispatch(r,r["qdc"],m.E_INIT,38,330000)
        self.assertGreater(b["cop_proxy"],a["cop_proxy"])
        self.assertGreater(a["hp_electric_W"],0)
        self.assertAlmostEqual(a["hp_source_W"]+a["hp_electric_W"],a["hp_condenser_W"],places=6)

    def test_tes_discharge_limited_by_energy(self):
        row=dict(self.inputs[0],qdis=500000,qpool=300000,qdh=0,qcharge=0)
        result=m.dispatch(row,0,0,30,0)
        self.assertEqual(result["tes_discharge_W"],0)
        self.assertEqual(result["E_next_J"],0)
        self.assertGreater(result["pool_dh_unmet_W"],0)

    def test_counterfactual_loads_and_shortfall(self):
        self.assertEqual(set(self.counter["cases"]),{"both","backup_only","neither"})
        self.assertEqual(self.counter["status"],"SYNTHETIC_COUNTERFACTUAL_NOT_MEASURED")
        rows=cf.counterfactual(self.inputs)
        self.assertEqual(rows[96]["qpool"]+rows[96]["qdh"],160000)
        self.assertEqual(self.inputs[96]["qpool"]+self.inputs[96]["qdh"],0)
        for s in ("both","backup_only","neither"):
            p=HERE/f"TRACE_A42_COUNTERFACTUAL_{s}.csv"
            self.assertEqual(m.sha(p),self.counter["cases"][s]["sha256"])
        self.assertEqual(self.counter["cases"]["both"]["fault_period_unmet_kWh"],0)
        self.assertGreater(self.counter["cases"]["neither"]["fault_period_unmet_kWh"],10000)
        self.assertGreater(self.counter["cases"]["backup_only"]["fault_period_unmet_kWh"],0)

    def test_counterfactual_conserves_energy(self):
        rows=cf.counterfactual(self.inputs)
        for s in ("both","backup_only","neither"):
            trace=m.replay(rows,s)
            for r in trace:
                self.assertLess(abs(r["it_balance_W"]),1e-6)
                self.assertLess(abs(r["hp_balance_W"]),1e-6)
                self.assertLess(abs(r["user_balance_W"]),1e-6)
                self.assertLess(abs(r["tes_balance_J"]),1e-3)

    def test_sensitivity_grid(self):
        sweep=self.report["sensor_capacity_sweep"]
        self.assertEqual(len(sweep),9)
        self.assertTrue(all(v["samples"]==672 for v in sweep.values()))

    def test_invalid_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            m.replay(self.inputs,"neither",sensor_lag_steps=-1)
        with self.assertRaises(ValueError):
            m.replay(self.inputs,"neither",heat_capacity_J_per_C=0)
        with self.assertRaises(ValueError):
            m.capacity("unapproved",100)
        with self.assertRaises(ValueError):
            m.dispatch(self.inputs[0],float("nan"),0,30,0)
        with self.assertRaises(ValueError):
            m.cop_proxy(float("nan"))

    def test_no_hardware_interface_in_source(self):
        src=(HERE/"coupled_a42.py").read_text(encoding="utf8")
        self.assertNotIn("subprocess.",src)
        self.assertNotIn("socket.",src)
        self.assertNotIn("serial.",src)
        self.assertNotIn("requests.",src)
        self.assertNotIn("modbus",src.lower())

if __name__=="__main__":
    unittest.main(verbosity=2)
