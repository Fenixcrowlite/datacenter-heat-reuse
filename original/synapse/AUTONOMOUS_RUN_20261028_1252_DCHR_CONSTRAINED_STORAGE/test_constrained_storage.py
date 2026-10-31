import unittest
from dataclasses import replace
from constrained_storage import Config, step, simulate, validate, load

def row(**kw):
    v={"COP":5.0,"Temperature_Lift_K":30.0,"DH_Supply_C":60.0,
       "DC_Total_MW":10.0,"Source_Heat_Available_MW":10.0,"HP_Source_Used_MW":2.0,
       "HP_Electric_MW":1.0,"Curtailed_HP_Heat_MW":5.0,"Gas_Heat_MW":0.0}
    v.update(kw)
    return v

class StorageTests(unittest.TestCase):
    def test_charge_soc(self):
        c=Config(capacity_mwh=10,charge_mw=2,extra_hp_electric_mw=3,
                 charge_efficiency=1,hourly_loss_fraction=0)
        soc,z=step(row(),0,c)
        self.assertAlmostEqual(soc,2)
        self.assertAlmostEqual(z["charge_mwh"],2)
    def test_electric_cap(self):
        c=Config(extra_hp_electric_mw=0.1)
        _,z=step(row(),0,c)
        self.assertLessEqual(z["additional_electric_mwh"],0.1+1e-9)
    def test_site_electric_cap(self):
        _,z=step(row(DC_Total_MW=11.99),0,Config())
        self.assertLessEqual(z["additional_electric_mwh"],0.01+1e-9)
    def test_hp_total_electric_cap(self):
        _,z=step(row(HP_Electric_MW=2.49),0,Config())
        self.assertLessEqual(z["additional_electric_mwh"],0.01+1e-9)
    def test_source_cap(self):
        _,z=step(row(Source_Heat_Available_MW=2.1),0,Config())
        self.assertLessEqual(z["source_heat_mwh"],0.1+1e-9)
    def test_no_source_headroom(self):
        _,z=step(row(Source_Heat_Available_MW=1),0,Config())
        self.assertEqual(z["charge_mwh"],0)
    def test_no_charge_if_no_curtailment(self):
        _,z=step(row(Curtailed_HP_Heat_MW=0),0,Config())
        self.assertEqual(z["charge_mwh"],0)
    def test_discharge_temperature_gate(self):
        c=Config(storage_temperature_c=62,discharge_efficiency=1)
        soc,z=step(row(Gas_Heat_MW=2,Curtailed_HP_Heat_MW=0),5,c)
        self.assertEqual(z["delivered_mwh"],0)
        self.assertFalse(z["temperature_gate_open"])
        self.assertLess(soc,5)
    def test_discharge_and_demand_limit(self):
        c=Config(discharge_mw=2,discharge_efficiency=1,hourly_loss_fraction=0)
        soc,z=step(row(Gas_Heat_MW=4,Curtailed_HP_Heat_MW=0),5,c)
        self.assertEqual(z["delivered_mwh"],2)
        self.assertEqual(soc,3)
    def test_discharge_efficiency(self):
        c=Config(discharge_efficiency=0.5,hourly_loss_fraction=0)
        soc,z=step(row(Gas_Heat_MW=1,Curtailed_HP_Heat_MW=0),5,c)
        self.assertAlmostEqual(soc,3)
        self.assertAlmostEqual(z["delivered_mwh"],1)
    def test_loss(self):
        c=Config(hourly_loss_fraction=0.1)
        soc,z=step(row(Gas_Heat_MW=0,Curtailed_HP_Heat_MW=0),5,c)
        self.assertAlmostEqual(soc,4.5)
        self.assertAlmostEqual(z["loss_mwh"],0.5)
    def test_capacity_bound(self):
        c=Config(capacity_mwh=1)
        soc,_=step(row(),0.999,c)
        self.assertLessEqual(soc,1+1e-8)
    def test_cop_derate(self):
        c=Config(storage_temperature_c=80)
        _,z=step(row(),0,c)
        self.assertLess(z["effective_cop"],5)
    def test_bad_config(self):
        for c in (Config(charge_efficiency=0),Config(hourly_loss_fraction=1),
                  Config(capacity_mwh=-1),Config(extra_hp_electric_mw=float("nan"))):
            with self.assertRaises(ValueError):validate(c)
    def test_zero_storage(self):
        x=simulate([row(),row(Gas_Heat_MW=2,Curtailed_HP_Heat_MW=0)],
                   Config(capacity_mwh=0),1)["year_results"][0]
        self.assertEqual(x["delivered_mwh"],0)
    def test_zero_electric(self):
        x=simulate([row(),row(Gas_Heat_MW=2,Curtailed_HP_Heat_MW=0)],
                   Config(extra_hp_electric_mw=0),1)["year_results"][0]
        self.assertEqual(x["charge_mwh"],0)
    def test_two_hour_conservation(self):
        c=Config(capacity_mwh=10,hourly_loss_fraction=0,
                 charge_efficiency=1,discharge_efficiency=1,charge_mw=2)
        x=simulate([row(),row(Curtailed_HP_Heat_MW=0,Gas_Heat_MW=1)],c,1)["year_results"][0]
        self.assertAlmostEqual(x["final_soc_mwh"],1)
    def test_real_source_hash_and_length(self):
        rows,sha=load()
        self.assertEqual(len(rows),8760)
        self.assertEqual(len(sha),64)
    def test_monotonic_capacity_in_fixture(self):
        year=[row()]*4+[row(Curtailed_HP_Heat_MW=0,Gas_Heat_MW=4)]*4
        small=simulate(year,Config(capacity_mwh=1),1)["year_results"][0]["delivered_mwh"]
        large=simulate(year,Config(capacity_mwh=10),1)["year_results"][0]["delivered_mwh"]
        self.assertGreaterEqual(large,small)
    def test_three_year_replay(self):
        x=simulate([row(),row(Curtailed_HP_Heat_MW=0,Gas_Heat_MW=1)],
                   Config(),3)
        self.assertEqual(len(x["year_results"]),3)
        self.assertEqual(x["year_results"][1]["initial_soc_mwh"],x["year_results"][0]["final_soc_mwh"])

if __name__=="__main__": unittest.main(verbosity=2)
