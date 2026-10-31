"""Independent analytical preflight. This is NOT a validated numerical replica of any paper.
Run: python audit/analytical_preflight_v06.py
All powers are MW, energy MWh, dt h, temperatures deg C unless noted.
"""
from __future__ import annotations
import math
import unittest
from pathlib import Path
import json

def assert_physical(condition, message):
    if not condition:
        raise ValueError(message)

def heat_pump(q_evap_available_mw: float, heat_capacity_mw: float, cop: float):
    assert_physical(all(math.isfinite(x) for x in (q_evap_available_mw, heat_capacity_mw, cop)), "nonfinite input")
    assert_physical(q_evap_available_mw >= 0 and heat_capacity_mw >= 0 and cop > 1, "nonphysical input")
    q_hot = min(heat_capacity_mw, q_evap_available_mw * cop / (cop - 1))
    p_el = q_hot / cop
    q_evap = q_hot - p_el
    return q_hot, p_el, q_evap

def heat_exchanger(q_hot_cap_mw_per_k: float, q_cold_cap_mw_per_k: float, th_in_c: float, tc_in_c: float, effectiveness: float):
    assert_physical(q_hot_cap_mw_per_k > 0 and q_cold_cap_mw_per_k > 0, "invalid capacity flow")
    assert_physical(0 <= effectiveness <= 1, "invalid epsilon")
    q = effectiveness * min(q_hot_cap_mw_per_k, q_cold_cap_mw_per_k) * max(0, th_in_c - tc_in_c)
    return q, th_in_c-q/q_hot_cap_mw_per_k, tc_in_c+q/q_cold_cap_mw_per_k

def dh_input_from_sold(sold_mwh: float, loss_fraction: float):
    assert_physical(sold_mwh >= 0 and 0 <= loss_fraction < 1, "invalid sold/loss")
    return sold_mwh/(1-loss_fraction)

def tes_next(e_mwh: float, q_charge_mw: float, q_discharge_mw: float, dt_h: float, capacity_mwh: float, loss_rate_per_h: float, eta_charge: float, eta_discharge: float):
    assert_physical(capacity_mwh >= 0 and 0 <= e_mwh <= capacity_mwh, "invalid initial SOC")
    assert_physical(q_charge_mw >= 0 and q_discharge_mw >= 0 and not(q_charge_mw > 0 and q_discharge_mw > 0), "TES simultaneous charge/discharge")
    assert_physical(dt_h > 0 and 0 <= loss_rate_per_h*dt_h <= 1, "loss parameter outside discrete range")
    assert_physical(0 < eta_charge <= 1 and 0 < eta_discharge <= 1, "invalid efficiency")
    e1=e_mwh*(1-loss_rate_per_h*dt_h)+eta_charge*q_charge_mw*dt_h-q_discharge_mw*dt_h/eta_discharge
    assert_physical(-1e-10 <= e1 <= capacity_mwh+1e-10, "TES SOC capacity violated")
    return e1

def npv(cash_per_year_eur: float, capex_eur: float, annual_discount: float, years: int):
    assert_physical(capex_eur >= 0 and annual_discount >= 0 and years > 0, "invalid NPV assumptions")
    annuity=years if annual_discount == 0 else -math.expm1(-years*math.log1p(annual_discount))/annual_discount
    return cash_per_year_eur*annuity-capex_eur

def discounted_payback(cash_per_year_eur: float, capex_eur: float, annual_discount: float):
    assert_physical(capex_eur >= 0 and cash_per_year_eur > 0 and annual_discount >= 0, "invalid DPP")
    if annual_discount==0:
        return capex_eur/cash_per_year_eur
    if cash_per_year_eur <= capex_eur*annual_discount:
        return math.inf
    return -math.log1p(-capex_eur*annual_discount/cash_per_year_eur)/math.log1p(annual_discount)

class TestAnalyticalPreflight(unittest.TestCase):
    def test_source_limited_hp(self):
        q,p,s=heat_pump(9,37,4)
        self.assertAlmostEqual(q,12,places=11)
        self.assertAlmostEqual(p,3,places=11)
        self.assertAlmostEqual(s,9,places=11)
        self.assertAlmostEqual(q,p+s,places=12)
    def test_zero_source_and_invalid_cop(self):
        self.assertEqual(heat_pump(0,37,4), (0,0,0))
        with self.assertRaises(ValueError): heat_pump(9,37,1)
        with self.assertRaises(ValueError): heat_pump(-1,37,4)
    def test_hiltunen_figure3_first_law(self):
        self.assertAlmostEqual(10,7.2+2.8)
        self.assertAlmostEqual(10/2.8, 3.5714285714285716)
        self.assertNotAlmostEqual(10/2.8,3.7,places=3)
    def test_frankfurt_network_accounting(self):
        generated=dh_input_from_sold(144000,.052)
        self.assertAlmostEqual(generated,151898.7341772152,places=5)
        self.assertAlmostEqual(generated*(1-.052),144000,places=8)
    def test_hx_counterflow_energy(self):
        q,thout,tcout=heat_exchanger(4,3,25,20,.8)
        self.assertAlmostEqual(q,12)
        self.assertAlmostEqual(4*(25-thout),3*(tcout-20))
        self.assertLess(tcout,25)
        self.assertGreater(thout,20)
        self.assertEqual(heat_exchanger(4,3,15,20,.8)[0],0)
    def test_storage_energy_with_losses(self):
        self.assertAlmostEqual(tes_next(10,2,0,1,20,.01,.9,.8),11.7)
        self.assertAlmostEqual(tes_next(10,0,2,1,20,.01,.9,.8),7.4)
        with self.assertRaises(ValueError): tes_next(10,2,2,1,20,.01,.9,.8)
        with self.assertRaises(ValueError): tes_next(19,4,0,1,20,.01,.9,.8)
    def test_npv_zero_rate_and_payback(self):
        self.assertAlmostEqual(npv(100,1000,0,10),0)
        self.assertTrue(npv(120000,1000000,.06,20) > 0)
        self.assertTrue(0 < discounted_payback(120000,1000000,.06) < 20)
        self.assertTrue(math.isinf(discounted_payback(60000,1000000,.06)))
        self.assertAlmostEqual(discounted_payback(120000,1000000,0),1000000/120000)
    def test_dimensional_water_tes(self):
        # E [MWh] = rho [kg/m3] * V [m3] * cp [J/kg/K] * dT[K] / 3.6e9
        mwh=1000*2400*4180*29.4/3.6e9
        self.assertAlmostEqual(mwh,81.928,places=2)
    def test_capacity_tes_and_boiler_limits_are_separate(self):
        # Example of explicitly finite backup and unmet 75 MW peak
        demand=75.0; hp_direct=37.0; discharge=5.0
        gas=min(20.,max(0.,demand-hp_direct-discharge))
        unmet=max(0.,demand-hp_direct-discharge-gas)
        self.assertEqual(gas,20)
        self.assertEqual(unmet,13)

if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestAnalyticalPreflight)
    results=unittest.TestResult(); suite.run(results)
    output={"suite":"analytical_preflight_v06","tests_run":results.testsRun,"failures":[repr(x) for _,x in results.failures],"errors":[repr(x) for _,x in results.errors],"success":results.wasSuccessful(),"qualifier":"Analytical identity tests only; not article replication or MATLAB/Simulink validation."}
    out=Path(__file__).with_name("analytical_preflight_v06.json")
    out.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False,indent=2),flush=True)
    if not results.wasSuccessful():
        raise SystemExit(1)
