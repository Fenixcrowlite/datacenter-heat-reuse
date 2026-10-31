"""Independent A53 QA: graphical Stateflow parity, Decimal ledgers, and immutable source checks."""
import csv,hashlib,json,sys,unittest,zipfile
from pathlib import Path
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A49=D.parent/"AUTONOMOUS_RUN_20261027_0245_A49_FAULT_INJECTION"
A51=D.parent/"AUTONOMOUS_RUN_20261027_0450_A51_TRIP_DELAY_GRAPHICAL"
sys.path[:0]=[str(A45),str(A49)]
import finite_trip_a45 as plant
from a49_independent_audit import independent_audit,mutation_probes
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class A53QA(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads((D/"MATLAB_A53_RESULT.json").read_text(encoding="utf-8-sig"))
  cls.refs=json.loads((D/"REFERENCE_MANIFEST.json").read_text(encoding="utf-8-sig"))["cases"]
 def test_full_matrix(self):
  self.assertEqual(self.report["status"],"A53_GRAPHICAL_CROSSPRODUCT_PARITY_PASS")
  self.assertEqual(self.report["comparisons"],47520)
  self.assertEqual(len(self.report["cases"]),18)
  self.assertEqual(len(self.refs),18)
  self.assertEqual({(x["scenario"],x["lag"],x["trip"]) for x in self.refs},{(s,l,t) for s in ("neither","backup_only") for l in (0,1,4) for t in (0,2,4)})
 def test_independent_decimal_ledgers(self):
  rows=plant.verified_inputs()[:240]
  for x in self.refs:
   trace=plant.simulate(rows,x["scenario"],sensor_lag_steps=x["lag"],trip_delay_steps=x["trip"])
   audit=independent_audit(trace,sensor_lag_steps=x["lag"])
   self.assertEqual(audit["samples"],240)
   self.assertEqual(audit["first_trip_index"],x["first_trip"])
   self.assertLess(audit["max_reported_flow_residual_W"],1e-5)
 def test_reference_csv_against_producer(self):
  rows=plant.verified_inputs()[:240]
  for x in self.refs:
   with (D/x["file"]).open(newline="",encoding="utf-8-sig") as f: csvrows=list(csv.DictReader(f))
   trace=plant.simulate(rows,x["scenario"],sensor_lag_steps=x["lag"],trip_delay_steps=x["trip"])
   self.assertEqual(len(csvrows),240)
   for i in (0,30,95,100,150,239):
    self.assertEqual(csvrows[i]["state"],trace[i]["state"])
    for field in ("T_next_C","E_next_J","unhandled_W","active_it_W"):
     self.assertAlmostEqual(float(csvrows[i][field]),trace[i][field],delta=max(1e-6,abs(trace[i][field])*1e-12))
 def test_matlab_channel_tolerances(self):
  for key,v in self.report["cases"].items():
   self.assertEqual(v["samples"],240)
   self.assertEqual(len(v["max_abs_differences"]),11)
   for dif,tol in zip(v["max_abs_differences"],(1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3)):
    self.assertLessEqual(dif,tol)
 def test_trip_indices(self):
  for x in self.refs:
   key=f'{x["scenario"]}_lag{x["lag"]}_trip{x["trip"]}'
   self.assertEqual(self.report["cases"][key]["first_trip_index_zero_based"],x["first_trip"])
  self.assertEqual(self.report["cases"]["backup_only_lag4_trip4"]["first_trip_index_zero_based"],105)
  self.assertEqual(self.report["cases"]["neither_lag4_trip4"]["first_trip_index_zero_based"],100)
 def test_saved_graphical_models(self):
  for trip in (0,2,4):
   p=D/f"DCHR_A53_TripDelay_{trip}.slx"
   with zipfile.ZipFile(p) as z:
    self.assertIsNone(z.testzip())
    data=b"".join(z.read(n) for n in z.namelist() if "stateflow" in n.lower())
    self.assertIn(f"pending&gt;={trip}".encode(),data)
 def test_source_models_unchanged(self):
  hashes={0:"3691770ae5f531824389035eafe19bafbdbd2e674d109d68c4a92ca8dacd073c",2:"c78bf64b0b2b1ac4d1436498db6caed535d3a174c7d78656baa02f7016eeeda4",4:"1c569018b7c8cadcf94845086a01c886c99f3551e7da9b3948aaae1a22021789"}
  for trip,want in hashes.items():
   self.assertEqual(sha(A51/f"DCHR_A51_TripDelay_{trip}.slx"),want)
 def test_mutations_rejected(self):
  trace=plant.simulate(plant.verified_inputs()[:120],"neither")
  self.assertEqual(len(mutation_probes(trace)),5)
 def test_synthetic_scope(self):
  self.assertTrue(self.report["synthetic_only"])
  self.assertFalse(self.report["physical_release"])
  self.assertTrue(self.report["source_a51_unmodified"])
 def test_matlab_serialization(self):
  self.assertTrue((D/"MATLAB_A53_RESULT.json").read_bytes().rstrip().endswith(b"}"))
  self.assertEqual(self.report["sensor_lag_steps"],[0,1,4])
  self.assertEqual(self.report["trip_delay_steps"],[0,2,4])
if __name__=="__main__":unittest.main(verbosity=2)

