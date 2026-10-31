import unittest
from decimal import Decimal
from eu_dc_metrics import metrics,applicability,integrate_hourly
BASE={"edc_kwh":"1200000","eit_kwh":"1000000","ereuse_kwh":"300000",
      "eres_total_kwh":"600000","win_m3":"2000"}
class MetricsTest(unittest.TestCase):
 def test_01_pue(self):self.assertEqual(Decimal(metrics(BASE)["PUE"]),Decimal("1.2"))
 def test_02_erf(self):self.assertEqual(Decimal(metrics(BASE)["ERF"]),Decimal("0.25"))
 def test_03_ref(self):self.assertEqual(Decimal(metrics(BASE)["REF"]),Decimal("0.5"))
 def test_04_wue_units(self):self.assertEqual(Decimal(metrics(BASE)["WUE_m3_per_MWh_IT"]),Decimal("2"))
 def test_05_no_float(self):
  with self.assertRaises(ValueError):metrics({**BASE,"edc_kwh":1.2})
 def test_06_no_bool(self):
  with self.assertRaises(ValueError):metrics({**BASE,"edc_kwh":True})
 def test_07_no_nan(self):
  with self.assertRaises(ValueError):metrics({**BASE,"edc_kwh":"NaN"})
 def test_08_no_inf(self):
  with self.assertRaises(ValueError):metrics({**BASE,"edc_kwh":"Infinity"})
 def test_09_no_negative(self):
  with self.assertRaises(ValueError):metrics({**BASE,"win_m3":"-1"})
 def test_10_no_zero_edc(self):
  with self.assertRaises(ValueError):metrics({**BASE,"edc_kwh":"0"})
 def test_11_no_zero_eit(self):
  with self.assertRaises(ValueError):metrics({**BASE,"eit_kwh":"0"})
 def test_12_no_it_above_dc(self):
  with self.assertRaises(ValueError):metrics({**BASE,"eit_kwh":"1200001"})
 def test_13_no_reuse_above_dc(self):
  with self.assertRaises(ValueError):metrics({**BASE,"ereuse_kwh":"1200001"})
 def test_14_no_res_above_dc(self):
  with self.assertRaises(ValueError):metrics({**BASE,"eres_total_kwh":"1200001"})
 def test_15_missing_field(self):
  with self.assertRaises(ValueError):metrics({"edc_kwh":"1"})
 def test_16_reporting_499(self):self.assertFalse(applicability("499.99","2000")["article12_reporting_500kW_or_more"])
 def test_17_reporting_500(self):self.assertTrue(applicability("500","2000")["article12_reporting_500kW_or_more"])
 def test_18_heat_1000(self):self.assertFalse(applicability("500","1000")["article26_heat_reuse_over_1MW"])
 def test_19_heat_over_1000(self):self.assertTrue(applicability("499","1000.01")["article26_heat_reuse_over_1MW"])
 def test_20_separate_threshold_bases(self):
  x=applicability("600","900")
  self.assertTrue(x["article12_reporting_500kW_or_more"])
  self.assertFalse(x["article26_heat_reuse_over_1MW"])
 def test_21_hourly_integration(self):
  h=[{"duration_h":"0.5","edc_kw":"120","eit_kw":"100","ereuse_kw":"30","eres_total_kw":"60","water_m3_per_h":"0.2"},
     {"duration_h":"1.5","edc_kw":"120","eit_kw":"100","ereuse_kw":"30","eres_total_kw":"60","water_m3_per_h":"0.2"}]
  o=integrate_hourly(h)
  self.assertEqual(o["integrated"]["edc_kwh"],"240.0")
  self.assertEqual(Decimal(o["indicators"]["ERF"]),Decimal("0.25"))
  self.assertEqual(Decimal(o["indicators"]["WUE_m3_per_MWh_IT"]),Decimal("2"))
 def test_22_zero_interval(self):
  with self.assertRaises(ValueError):integrate_hourly([{"duration_h":"0"}])
 def test_23_empty_intervals(self):
  with self.assertRaises(ValueError):integrate_hourly([])
 def test_24_not_pool_heat(self):
  x=metrics({**BASE,"delivered_pool_kwh":"8000000"})
  self.assertEqual(Decimal(x["ERF"]),Decimal("0.25"))
 def test_25_equal_boundaries(self):
  x=metrics({"edc_kwh":"100","eit_kwh":"100","ereuse_kwh":"100","eres_total_kwh":"100","win_m3":"0"})
  self.assertEqual(Decimal(x["PUE"]),1)
  self.assertEqual(Decimal(x["ERF"]),1)
if __name__=="__main__":unittest.main(verbosity=2)
