"""Independent dimensional, edge and source-integrity checks."""
import math
import unittest
from decimal import Decimal, getcontext
from pathlib import Path
import storage_volume_gate as s
getcontext().prec=35

class TestVolumeGate(unittest.TestCase):
    def test_one_mwh_one_kelvin(self):
        self.assertAlmostEqual(s.water_volume_m3(1,72,71),3.6e9/(4180*1000))
    def test_zero_energy(self):
        self.assertEqual(s.water_volume_m3(0,72,60),0)
    def test_no_temperature_headroom(self):
        self.assertIsNone(s.water_volume_m3(2500,65,65))
        self.assertIsNone(s.water_volume_m3(2500,55,64.95))
    def test_reject_bad_volume(self):
        for kwargs in ({"capacity_mwh":-1,"hot_c":72,"min_usable_c":60},
                       {"capacity_mwh":1,"hot_c":72,"min_usable_c":60,"cp":0},
                       {"capacity_mwh":1,"hot_c":float("nan"),"min_usable_c":60}):
            with self.assertRaises(ValueError):s.water_volume_m3(**kwargs)
    def test_linear_capacity(self):
        a=s.water_volume_m3(100,72,64.95)
        b=s.water_volume_m3(2500,72,64.95)
        self.assertAlmostEqual(b/a,25)
    def test_inverse_temperature_span(self):
        a=s.water_volume_m3(2500,72,62)
        b=s.water_volume_m3(2500,82,62)
        self.assertAlmostEqual(a/b,2)
    def test_independent_decimal_energy(self):
        v=s.water_volume_m3(2500,72,64.9518479386581)
        E=Decimal(str(v))*Decimal(4180)*Decimal(1000)*(
            Decimal("72")-Decimal("64.9518479386581"))/Decimal("3.6e9")
        self.assertAlmostEqual(float(E),2500,places=8)
    def test_footprint_reconstruction(self):
        vol=305000
        g=s.cylinder_geometry(vol,10)
        self.assertAlmostEqual(g["footprint_m2"]*10,vol)
        self.assertAlmostEqual(math.pi*(g["equivalent_single_cylinder_diameter_m"]/2)**2*10,vol)
    def test_invalid_geometry(self):
        with self.assertRaises(ValueError):s.cylinder_geometry(100,0)
    def test_half_life(self):
        h=s.half_life_hours(.00025)
        self.assertAlmostEqual(s.loss_retention(.00025,h),.5,places=12)
    def test_loss_matches_iterative(self):
        energy=1.
        for _ in range(4320):energy*=1-.00025
        self.assertAlmostEqual(energy,s.loss_retention(.00025,4320),places=12)
    def test_invalid_loss(self):
        for f in (-.1,1.,float("inf")):
            with self.assertRaises(ValueError):s.loss_retention(f,720)
    def test_source_sha(self):
        p=s.source_profile()
        self.assertEqual(p["source_sha256"],s.EXPECTED_SHA)
        self.assertEqual(p["rows"],8760)
        self.assertGreater(p["max_c"],p["p95_c"])
    def test_source_mutation_rejected(self):
        with self.assertRaises(ValueError):s.source_profile(s.SOURCE,"0"*64)
    def test_critical_reference_and_feasibility(self):
        r=s.evaluate()
        self.assertEqual(len(r["cases"]),64)
        self.assertEqual(r["primary_source_signoffs"],0)
        ref=next(x for x in r["cases"] if (x["capacity_mwh"],x["hot_c"],x["supply_statistic"])==(2500,72,"max"))
        self.assertGreater(ref["ideal_water_volume_m3"],300000)
        self.assertLess(ref["ideal_water_volume_m3"],320000)
        no=next(x for x in r["cases"] if (x["capacity_mwh"],x["hot_c"],x["supply_statistic"])==(2500,55,"max"))
        self.assertFalse(no["temperature_feasible"])
        self.assertIsNone(no["ideal_water_volume_m3"])
    def test_capacity_is_not_measured(self):
        r=s.evaluate()
        self.assertIn("SYNTHETIC",r["classification"])
        self.assertEqual(r["baseline_storage_mwh"],100)

if __name__=="__main__":unittest.main(verbosity=2)
