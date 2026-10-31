from pathlib import Path
import hashlib,json,unittest,zipfile,csv
D=Path(__file__).resolve().parent
A48=D.parent/"AUTONOMOUS_RUN_20261027_0150_A48_EXECUTABLE_QA"/"DCHR_A48_Graphical_Closed_Loop.slx"
class A50Acceptance(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r=json.loads((D/"MATLAB_A50_RESULT.json").read_text(encoding="utf-8-sig"))
  cls.m=json.loads((D/"REFERENCE_MANIFEST.json").read_text(encoding="utf-8-sig"))
 def test_source_immutable(self):
  self.assertEqual(hashlib.sha256(A48.read_bytes()).hexdigest(),"063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb")
 def test_real_model(self):
  p=D/"DCHR_A50_Sensor_Lag.slx"
  self.assertTrue(zipfile.is_zipfile(p))
  with zipfile.ZipFile(p) as z:self.assertTrue(any("stateflow" in n.lower() for n in z.namelist()))
 def test_status(self):
  self.assertEqual(self.r["status"],"A50_GRAPHICAL_SENSOR_LAG_PARITY_PASS")
  self.assertFalse(self.r["physical_release"])
  self.assertTrue(self.r["source_a48_unmodified"])
 def test_coverage(self):
  self.assertEqual(self.r["comparisons"],6*240*11)
  self.assertEqual(len(self.r["scenarios"]),6)
  self.assertEqual(len(self.m["cases"]),6)
 def test_trip_timing(self):
  for item in self.m["cases"]:
   key=f'{item["scenario"]}_lag{item["lag"]}'
   with self.subTest(key=key):
    self.assertEqual(self.r["scenarios"][key]["trip_index_zero_based"],item["first_trip"])
  self.assertEqual(self.r["scenarios"]["backup_only_lag4"]["trip_index_zero_based"],103)
  self.assertEqual(self.r["scenarios"]["backup_only_lag0"]["trip_index_zero_based"],98)
 def test_numeric_tolerances(self):
  tol=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3]
  for key,v in self.r["scenarios"].items():
   self.assertEqual(v["samples"],240)
   self.assertEqual(len(v["max_abs_differences"]),11)
   for n,(err,limit) in enumerate(zip(v["max_abs_differences"],tol)):
    with self.subTest(case=key,column=n):self.assertLessEqual(err,limit)
 def test_reference_csv_integrity(self):
  for item in self.m["cases"]:
   with (D/item["file"]).open(newline="",encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),240)
   self.assertEqual(rows[item["first_trip"]]["state"],"TRIPPED")
if __name__=="__main__":unittest.main(verbosity=2)
