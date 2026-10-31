"""A52 cross-product independent checks and baseline cross-parity."""
import csv,json,sys,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A50=D.parent/"AUTONOMOUS_RUN_20261027_0351_A50_SENSOR_LAG_MATLAB"
A51=D.parent/"AUTONOMOUS_RUN_20261027_0450_A51_TRIP_DELAY_GRAPHICAL"
sys.path.insert(0,str(D))
from a52_sensitivity import analyze
class Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((D/"SENSITIVITY_A52.json").read_text(encoding="utf-8"))
  cls.cases={(x["scenario"],x["sensor_lag_steps"],x["trip_delay_steps"]):x for x in cls.data["cases"]}
 def test_complete_unique_matrix(self):
  self.assertEqual(len(self.cases),18)
  self.assertEqual(set(self.cases),{(s,l,t) for s in ("neither","backup_only") for l in (0,1,4) for t in (0,2,4)})
 def test_independent_recompute(self):
  other=analyze()
  self.assertEqual(other,self.data)
 def test_cross_parity_with_matlab_a50_sensor(self):
  for scenario in ("neither","backup_only"):
   for lag in (0,1,4):
    p=A50/f"REF_{scenario}_lag{lag}.csv"
    with p.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    first=next(i for i,r in enumerate(rows) if r["state"]=="TRIPPED")
    self.assertEqual(first,self.cases[(scenario,lag,2)]["first_trip_index"])
 def test_cross_parity_with_matlab_a51_trip(self):
  for scenario in ("neither","backup_only"):
   for delay in (0,2,4):
    p=A51/f"REF_{scenario}_trip{delay}.csv"
    with p.open(newline="",encoding="utf-8") as f:rows=list(csv.DictReader(f))
    first=next(i for i,r in enumerate(rows) if r["state"]=="TRIPPED")
    self.assertEqual(first,self.cases[(scenario,0,delay)]["first_trip_index"])
 def test_no_reject_sensor_independent(self):
  for trip in (0,2,4):
   self.assertEqual([self.cases[("neither",lag,trip)]["first_trip_index"] for lag in (0,1,4)],[96+trip]*3)
 def test_backup_sensor_trip_interaction(self):
  self.assertEqual(self.cases[("backup_only",4,4)]["first_trip_index"],105)
  self.assertEqual(self.cases[("backup_only",0,4)]["first_trip_index"],100)
  self.assertEqual(self.cases[("backup_only",4,2)]["first_trip_index"],103)
 def test_thermal_risk_and_energy_ledger(self):
  self.assertGreater(self.cases[("neither",0,4)]["max_temperature_C"],90)
  for item in self.data["cases"]:
   self.assertLess(item["max_flow_residual_W"],1e-5)
   self.assertGreaterEqual(item["unhandled_heat_kWh"],0)
   self.assertGreaterEqual(item["unmet_heat_kWh"],0)
 def test_scope_limit(self):
  self.assertFalse(self.data["physical_release"])
  self.assertFalse(self.data["matlab_crossproduct_executed"])
  self.assertTrue(self.data["synthetic_only"])
if __name__=="__main__":unittest.main(verbosity=2)
