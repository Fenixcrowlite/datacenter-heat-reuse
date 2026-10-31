# -*- coding: utf-8 -*-
"""Tests verify dimensional analysis, physical partition, and compliance warnings."""
import math
import unittest
from benchmark_calculator import Inputs, calculate

class CalculatorTests(unittest.TestCase):
    def test_geometry_500m3(self):
        r=calculate(Inputs())
        self.assertAlmostEqual(r["pool"]["volume_m3"],500)
    def test_reference_original_warmup(self):
        r=calculate(Inputs(target_C=28,switch_off_C=28.2))
        self.assertAlmostEqual(r["pool"]["ideal_heatup_MWh"],6.94909,places=4)
    def test_temperature_guard(self):
        r=calculate(Inputs(switch_off_C=28.2))
        self.assertTrue(any("switch-off temperature exceeds" in w for w in r["warnings"]))
    def test_pue_correct_MWh_not_kWh(self):
        r=calculate(Inputs())
        self.assertAlmostEqual(r["datacentre"]["annual_EIT_MWh"],71832.0)
        self.assertAlmostEqual(r["datacentre"]["annual_EDC_MWh"],86198.4)
        self.assertAlmostEqual(r["datacentre"]["reference_PUE_2026_EDC_MWh"],109184.64)
    def test_heat_pump_first_law(self):
        r=calculate(Inputs())
        p=r["pool"]
        self.assertAlmostEqual(p["ideal_hp_dc_source_MWh"]+p["ideal_hp_electric_MWh"],p["ideal_heatup_MWh"])
    def test_source_boundary_versus_output(self):
        r=calculate(Inputs())
        self.assertLess(r["datacentre"]["pool_HP_source_boundary_ERF_screening"],0.1)
    def test_direct_exchange_approach(self):
        r=calculate(Inputs(source_C=29,approach_K=3))
        self.assertFalse(r["direct_exchange_possible_screening"])
    def test_large_pool(self):
        r=calculate(Inputs(width_m=20,depth_m=2))
        self.assertAlmostEqual(r["pool"]["volume_m3"],1000)
    def test_invalid_pue(self):
        with self.assertRaises(ValueError):calculate(Inputs(pue=0.9))
    def test_insufficient_power(self):
        r=calculate(Inputs(heater_kW=20,holding_loss_kW=31.45))
        self.assertIsNone(r["pool"]["constant_loss_heatup_h"])
    def test_ERF_definition(self):
        r=calculate(Inputs())
        d=r["datacentre"]
        self.assertAlmostEqual(d["pool_HP_source_boundary_ERF_screening"], 
            (r["pool"]["screening_annual_heat_MWh"]*(1-1/4))/d["annual_EDC_MWh"])
if __name__=="__main__":unittest.main(verbosity=2)
