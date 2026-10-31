"""Independent property and boundary tests for v0.7 reference physics."""
import json,math,random,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from reference_physics_v07 import Parameters,dispatch_step,counterflow_hx

class TestReference(unittest.TestCase):
    def test_first_law_hand_vector(self):
        p=Parameters(storage_capacity_mwh=0,charge_limit_mw=0,discharge_limit_mw=0)
        x=dispatch_step(p,10,7.2,3.5714285714285716,0)
        self.assertAlmostEqual(x.hp_heat_mw,10.,places=10)
        self.assertAlmostEqual(x.evaporator_mw,7.2,places=10)
        self.assertAlmostEqual(x.compressor_mw,2.8,places=10)
    def test_source_limited_not_evap_overshoot(self):
        x=dispatch_step(Parameters(),50,2,4,0)
        self.assertAlmostEqual(x.hp_heat_mw,8./3.)
        self.assertAlmostEqual(x.evaporator_mw,2.)
    def test_boiler_cap_unmet(self):
        x=dispatch_step(Parameters(storage_capacity_mwh=0),100,0,4,0)
        self.assertEqual(x.boiler_mw,20.)
        self.assertEqual(x.unmet_mw,80.)
    def test_storage_charge_bounds(self):
        p=Parameters(storage_capacity_mwh=10,charge_limit_mw=20,standing_loss_fraction_per_hour=0)
        x=dispatch_step(p,0,50,4,9)
        self.assertAlmostEqual(x.charge_mw,1./.95)
        self.assertAlmostEqual(x.storage_end_mwh,10)
    def test_storage_discharge_eta(self):
        p=Parameters(hp_capacity_mw=0,storage_capacity_mwh=10,discharge_limit_mw=20,
                     standing_loss_fraction_per_hour=0)
        x=dispatch_step(p,20,0,4,10)
        self.assertAlmostEqual(x.discharge_mw,9.5)
        self.assertAlmostEqual(x.storage_end_mwh,0.)
        self.assertAlmostEqual(x.boiler_mw,10.5)
    def test_invalid_inputs(self):
        p=Parameters()
        for args in [(-1,0,4,0),(0,-1,4,0),(0,0,1,0),(0,0,float('nan'),0),(0,0,4,90)]:
            with self.assertRaises(ValueError):dispatch_step(p,*args)
        for d in [{"dt_h":0},{"charge_efficiency":1.01},{"standing_loss_fraction_per_hour":1.1}]:
            with self.assertRaises(ValueError): Parameters(**d)
    def test_passive_hx_equilibrium(self):
        h=counterflow_hx(20,30,.4,.4,.05)
        self.assertEqual(h.heat_mw,0)
        self.assertEqual(h.hot_out_c,20)
        self.assertEqual(h.cold_out_c,30)
    def test_hx_energy_and_pinch(self):
        h=counterflow_hx(40,20,.12,.20,.08)
        self.assertAlmostEqual(h.heat_mw,.12*(40-h.hot_out_c))
        self.assertAlmostEqual(h.heat_mw,.20*(h.cold_out_c-20))
        self.assertGreaterEqual(h.hot_out_c,20)
        self.assertLessEqual(h.cold_out_c,40)
        self.assertTrue(0 <= h.effectiveness <= 1)
    def test_hx_equal_capacities_limit(self):
        h=counterflow_hx(40,20,.1,.1,.1)
        self.assertAlmostEqual(h.effectiveness,.5)
        self.assertAlmostEqual(h.heat_mw,1.)
    def test_randomized_conservation_1500(self):
        rng=random.Random(701)
        for _ in range(1500):
            p=Parameters(hp_capacity_mw=rng.uniform(0,60),boiler_capacity_mw=rng.uniform(0,40),
                         storage_capacity_mwh=rng.uniform(0,300),charge_limit_mw=rng.uniform(0,40),
                         discharge_limit_mw=rng.uniform(0,40),charge_efficiency=rng.uniform(.65,1),
                         discharge_efficiency=rng.uniform(.65,1),
                         standing_loss_fraction_per_hour=rng.uniform(0,.05),dt_h=rng.choice([.25,.5,1,2]))
            e0=rng.random()*p.storage_capacity_mwh
            x=dispatch_step(p,rng.uniform(0,100),rng.uniform(0,35),rng.uniform(1.05,8),e0)
            self.assertAlmostEqual(x.hp_heat_mw,x.evaporator_mw+x.compressor_mw,delta=1e-9)
            self.assertLessEqual(x.evaporator_mw,x.source_available_mw+1e-9)
            self.assertLessEqual(x.hp_heat_mw,p.hp_capacity_mw+1e-9)
            self.assertLessEqual(x.boiler_mw,p.boiler_capacity_mw+1e-9)
            self.assertAlmostEqual(x.demand_mw,x.direct_mw+x.discharge_mw+x.boiler_mw+x.unmet_mw,delta=1e-9)
            self.assertAlmostEqual(x.hp_heat_mw,x.direct_mw+x.charge_mw,delta=1e-9)
            self.assertFalse(x.charge_mw>1e-9 and x.discharge_mw>1e-9)
            self.assertGreaterEqual(x.storage_end_mwh,-1e-9)
            self.assertLessEqual(x.storage_end_mwh,p.storage_capacity_mwh+1e-9)
            self.assertAlmostEqual(x.storage_end_mwh,e0-x.storage_loss_mwh+
                p.charge_efficiency*x.charge_mw*p.dt_h-x.discharge_mw*p.dt_h/p.discharge_efficiency,delta=1e-9)
    def test_annual_energy_closure_synthetic(self):
        p=Parameters()
        e0=30;storage=e0;totals=dict(demand=0,hp=0,gas=0,unmet=0,loss=0,charge=0,discharge=0)
        for i in range(8760):
            d=max(0,22+18*math.cos((i%8760)*2*math.pi/8760)+4*math.cos(i*math.pi/12))
            source=10+4*math.sin(i*math.pi/12)
            x=dispatch_step(p,d,source,3.8,storage)
            storage=x.storage_end_mwh
            for key,value in [('demand',x.demand_mw),('hp',x.hp_heat_mw),('gas',x.boiler_mw),
                 ('unmet',x.unmet_mw),('charge',x.charge_mw),('discharge',x.discharge_mw)]:
                totals[key]+=value*p.dt_h
            totals['loss']+=x.storage_loss_mwh
        self.assertAlmostEqual(totals['demand'],totals['hp']-totals['charge']+
               totals['discharge']+totals['gas']+totals['unmet'],delta=1e-7)
        self.assertAlmostEqual(storage,e0+totals['charge']*p.charge_efficiency-
                         totals['discharge']/p.discharge_efficiency-totals['loss'],delta=1e-7)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestReference)
    result=unittest.TestResult();suite.run(result)
    report={'kernel':'independent first-law v0.7','status':'PASS' if result.wasSuccessful() else 'FAIL',
           'tests_run':result.testsRun,'failures':[str(y) for x,y in result.failures],
           'errors':[str(y) for x,y in result.errors],
           'notes':'Tests include 1500 randomized scenarios and 8760h synthetic annual closure. NOT paper validation.'}
    target=Path(__file__).with_name('reference_physics_tests_v07.json')
    target.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    if not result.wasSuccessful():raise SystemExit(1)
