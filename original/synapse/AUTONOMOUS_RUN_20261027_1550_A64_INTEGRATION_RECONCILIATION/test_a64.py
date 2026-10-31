"""A64 regression tests, including adversarial time/provenance mutations."""
import copy
from decimal import Decimal as D
import json
import unittest
from pathlib import Path
import a64_reconcile as m

def rows(q=(100,200,300),dt=900):
    a=[]; b=[]
    for i,p in enumerate(q):
        r={k:str(1) for k in m.FIELDS}
        r["time_s"]=str(i*dt)
        for k in m.POWER:r[k]=str(p)
        a.append(r)
        b.append(dict(r,E_pool_input_cum_J=str(sum(q[:i+1])*dt)))
    return a,b

class TestA64(unittest.TestCase):
    def test_analytic_decomposition(self):
        a,b=rows()
        c=m.reconcile(a,b)
        x=c["channels"]["Q_pool_W"]
        self.assertEqual(D(x["trapezoid_MWh"])*m.MWH,D(360000))
        self.assertEqual(D(x["discrete_MWh"])*m.MWH,D(540000))
        self.assertEqual(D(x["terminal_rectangle_kWh"])*D(3600000),D(270000))
        self.assertEqual(D(x["sample_slope_correction_kWh"])*D(3600000),D(-90000))
    def test_constant_power_endpoint(self):
        a,b=rows((250,250,250))
        x=m.reconcile(a,b)["channels"]["Q_pool_W"]
        self.assertEqual(D(x["discrete_minus_trapezoid_kWh"])*D(3600000),D(225000))
    def test_nonuniform_rejected(self):
        a,b=rows()
        a[1]["time_s"]=b[1]["time_s"]="850"
        with self.assertRaisesRegex(ValueError,"TIMEBASE"):m.reconcile(a,b)
    def test_row_count_rejected(self):
        a,b=rows()
        with self.assertRaisesRegex(ValueError,"ROW_COUNT"):m.reconcile(a,b[:-1])
    def test_source_field_mismatch_rejected(self):
        a,b=rows()
        b[1]["Q_pool_W"]="201"
        with self.assertRaisesRegex(ValueError,"UPSTREAM_COLUMN"):m.reconcile(a,b)
    def test_nan_rejected(self):
        a,b=rows()
        a[1]["Q_pool_W"]=b[1]["Q_pool_W"]="NaN"
        with self.assertRaisesRegex(ValueError,"NONFINITE"):m.reconcile(a,b)
    def test_cumulative_mismatch_rejected(self):
        a,b=rows()
        b[-1]["E_pool_input_cum_J"]="999"
        with self.assertRaisesRegex(ValueError,"CUMULATIVE"):m.reconcile(a,b)
    def test_nonzero_origin_rejected(self):
        a,b=rows()
        a[0]["time_s"]=b[0]["time_s"]="1"
        with self.assertRaisesRegex(ValueError,"TIMEBASE"):m.reconcile(a,b)
    def test_real_v08(self):
        x=m.load_verified("V08")
        self.assertEqual(x["samples"],672)
        self.assertEqual(x["time_span_h"],"167.75")
        self.assertEqual(x["discrete_duration_h"],"168")
        self.assertAlmostEqual(float(x["channels"]["Q_pool_W"]["discrete_minus_trapezoid_kWh"]),20.00039772,places=6)
    def test_real_v09(self):
        x=m.load_verified("V09")
        self.assertEqual(x["samples"],672)
        self.assertAlmostEqual(float(x["channels"]["Q_pool_W"]["discrete_minus_trapezoid_kWh"]),20.00039771,places=6)
    def test_provenance_no_physical_release(self):
        for v in ("V08","V09"):
            x=m.load_verified(v)
            self.assertFalse(x["physical_release"])
            self.assertEqual(x["source_kind"],"derived_simulation")
    def test_output_static_and_informative(self):
        p=m.D/"OUTPUT/comparison.html"
        txt=p.read_text(encoding="utf-8")
        for term in ("DERIVED SIMULATION","167.75","168","20.000398","Q_pool_W","A60","A62"):
            self.assertIn(term,txt)
        self.assertNotIn("<script",txt)
if __name__=="__main__":unittest.main()
