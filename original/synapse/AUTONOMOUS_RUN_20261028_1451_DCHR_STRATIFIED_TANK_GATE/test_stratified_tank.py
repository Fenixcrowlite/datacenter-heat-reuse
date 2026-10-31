import unittest, tempfile, pathlib, csv, json, math
from dataclasses import replace
import stratified_tank as m

def row(**kw):
    r=dict(COP=3.,Temperature_Lift_K=40.,DH_Supply_C=55.,DC_Total_MW=5.,
        Source_Heat_Available_MW=10.,HP_Source_Used_MW=2.,HP_Electric_MW=0.5,
        Curtailed_HP_Heat_MW=4.,Gas_Heat_MW=0.)
    r.update(kw);return r

class TankTests(unittest.TestCase):
    def test_geometry(self):
        for vol in (0,-1):
            with self.assertRaises(ValueError):m.validate(replace(m.Config(),volume_m3=vol))
    def test_temperature_order(self):
        with self.assertRaises(ValueError):m.validate(replace(m.Config(),charge_temp_c=30.))
    def test_negative_ua(self):
        with self.assertRaises(ValueError):m.validate(replace(m.Config(),ua_kw_per_k=-1))
    def test_layer_count(self):
        with self.assertRaises(ValueError):m.validate(replace(m.Config(),layers=1))
    def test_empty(self):
        with self.assertRaises(ValueError):m.simulate([],m.Config())
    def test_bad_profile(self):
        with self.assertRaises(ValueError):m.hourly([35.],row(),m.Config())
    def test_source_hash(self):
        a,sha=m.load()
        self.assertEqual(len(a),8760);self.assertEqual(sha,m.SOURCE_SHA)
    def test_bad_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=pathlib.Path(d)/"a.csv";p.write_text("Time,COP\n01-Jan-2026 00:00:00,3\n")
            with self.assertRaises(ValueError):m.load(p,expected_sha="bad",expected_rows=1)
    def test_charge_without_discharge(self):
        c=replace(m.Config(),ua_kw_per_k=0.,mixing_kw_per_k=0.)
        t,z=m.hourly([35.]*8,row(),c)
        self.assertGreater(z["charge_mwh"],0)
        self.assertEqual(z["delivered_mwh"],0)
        self.assertAlmostEqual(z["charge_mwh"],z["added_electric_mwh"]+z["source_heat_mwh"])
        self.assertAlmostEqual(z["charge_mwh"],z["final_energy_mwh"]-z["initial_energy_mwh"],places=7)
        self.assertGreater(t[0],t[-1])
    def test_source_headroom_gate(self):
        _,z=m.hourly([35.]*8,row(Source_Heat_Available_MW=2.,HP_Source_Used_MW=2.),m.Config())
        self.assertEqual(z["charge_mwh"],0.)
    def test_site_electric_gate(self):
        _,z=m.hourly([35.]*8,row(DC_Total_MW=20.),m.Config())
        self.assertEqual(z["charge_mwh"],0.)
    def test_gas_temperature_gate(self):
        _,z=m.hourly([35.]*8,row(Gas_Heat_MW=3.),m.Config())
        self.assertEqual(z["delivered_mwh"],0.)
    def test_discharge_energy(self):
        c=replace(m.Config(),ua_kw_per_k=0.,mixing_kw_per_k=0.)
        _,z=m.hourly([75.]*8,row(Gas_Heat_MW=3.,Curtailed_HP_Heat_MW=0.),c)
        self.assertGreater(z["delivered_mwh"],0)
        self.assertLessEqual(z["delivered_mwh"],3+1e-8)
        self.assertAlmostEqual(z["initial_energy_mwh"]-z["final_energy_mwh"],z["delivered_mwh"],places=7)
    def test_simultaneous_balance(self):
        c=replace(m.Config(),ua_kw_per_k=0.,mixing_kw_per_k=0.)
        _,z=m.hourly([65.]*8,row(Gas_Heat_MW=2.),c)
        self.assertGreater(z["charge_mwh"],0)
        self.assertGreater(z["delivered_mwh"],0)
        self.assertLess(abs(z["final_energy_mwh"]-z["initial_energy_mwh"]-z["charge_mwh"]+z["delivered_mwh"]),1e-7)
    def test_ambient_loss(self):
        _,z=m.hourly([70.]*8,row(Curtailed_HP_Heat_MW=0.),m.Config())
        self.assertGreater(z["loss_mwh"],0)
    def test_mixing_energy_conserves(self):
        c=replace(m.Config(),ua_kw_per_k=0.,mixing_kw_per_k=50.)
        _,z=m.hourly([75.,70.,65.,60.,55.,50.,45.,40.],row(Curtailed_HP_Heat_MW=0.),c)
        self.assertAlmostEqual(z["final_energy_mwh"],z["initial_energy_mwh"],places=7)
    def test_toy_year(self):
        c=replace(m.Config(),volume_m3=500,ua_kw_per_k=0.5)
        out=m.simulate([row(),row(Gas_Heat_MW=2.,Curtailed_HP_Heat_MW=0.)]*12,c,years=3)
        self.assertEqual(len(out["yearly"]),3)
        for y in out["yearly"]:self.assertLess(abs(y["balance_residual_mwh"]),1e-6)
    def test_power_cap(self):
        c=replace(m.Config(),charge_mw=0.4,discharge_mw=0.2)
        _,z=m.hourly([75.]*8,row(Gas_Heat_MW=10.),c)
        self.assertLessEqual(z["charge_mwh"],.4+1e-8)
        self.assertLessEqual(z["delivered_mwh"],.2+1e-8)
    def test_no_overheat(self):
        c=replace(m.Config(),volume_m3=100.,ua_kw_per_k=0.,mixing_kw_per_k=0.)
        t=[35.]*8
        for _ in range(80):t,_=m.hourly(t,row(),c)
        self.assertLessEqual(max(t),c.charge_temp_c+1e-7)

    def test_geometry_ua_scaling(self):
        self.assertGreater(m.geometry_ua_kw_per_k(305485.8),m.geometry_ua_kw_per_k(10000.))
        self.assertAlmostEqual(m.geometry_ua_kw_per_k(10000.,u_w_m2_k=0.),0.)
        with self.assertRaises(ValueError):m.geometry_ua_kw_per_k(-1.)
    def test_lossless_baseline_ua(self):
        self.assertAlmostEqual(m.geometry_ua_kw_per_k(10000.,height_m=10.,u_w_m2_k=0.15),0.468352274,delta=0.01)

if __name__=="__main__":unittest.main(verbosity=2)
