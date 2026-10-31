"""A51 independent regression and energy ledger checks."""
import csv,hashlib,json,sys,unittest
from pathlib import Path
D=Path(__file__).resolve().parent
A45=D.parent/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A49=D.parent/"AUTONOMOUS_RUN_20261027_0245_A49_FAULT_INJECTION"
sys.path.insert(0,str(A45));sys.path.insert(0,str(A49))
import finite_trip_a45 as plant
from a49_independent_audit import independent_audit,mutation_probes,LedgerError
class A51Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=plant.verified_inputs()[:240]
  cls.manifest=json.loads((D/"REFERENCE_MANIFEST.json").read_text(encoding="utf-8"))
 def test_six_references_and_independent_energy_ledgers(self):
  self.assertEqual(len(self.manifest["cases"]),6)
  for item in self.manifest["cases"]:
   with self.subTest(item=item):
    scenario=item["scenario"];delay=item["trip_delay_steps"]
    trace=plant.simulate(self.rows,scenario,trip_delay_steps=delay)
    result=independent_audit(trace)
    self.assertEqual(result["samples"],240)
    self.assertEqual(result["first_trip_index"],item["first_trip_index"])
    self.assertLess(result["max_reported_flow_residual_W"],1e-5)
 def test_trip_delay_exact_steps(self):
  for scenario in ("neither","backup_only"):
   self.assertEqual([next(i for i,t in enumerate(plant.simulate(self.rows,scenario,trip_delay_steps=k)) if t["state"]=="TRIPPED") for k in (0,2,4)],[96,98,100])
 def test_reference_columns_match_model(self):
  for item in self.manifest["cases"]:
   trace=plant.simulate(self.rows,item["scenario"],trip_delay_steps=item["trip_delay_steps"])
   with (D/item["filename"]).open(newline="",encoding="utf-8") as f:
    rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),len(trace))
   for i in (0,95,96,98,100,120,239):
    for key in ("T_next_C","E_next_J","active_it_W","unhandled_W","it_balance_W","tes_balance_J"):
     self.assertAlmostEqual(float(rows[i][key]),float(trace[i][key]),places=5)
    self.assertEqual(rows[i]["state"],trace[i]["state"])
 def test_reject_zero_interlock(self):
  for delay in (0,2,4):
   trace=plant.simulate(self.rows,"neither",trip_delay_steps=delay)
   self.assertTrue(all(t["trip_trigger"] for t in trace[96:101]))
 def test_mutation_detected(self):
  trace=plant.simulate(self.rows,"backup_only",trip_delay_steps=2)
  self.assertEqual(len(mutation_probes(trace)),5)
 def test_invalid_delay_fails_closed(self):
  for value in (-1,13,2.5):
   with self.assertRaises(ValueError):plant.simulate(self.rows,"neither",trip_delay_steps=value)
 def test_source_integrity(self):
  p=D.parent/"AUTONOMOUS_RUN_20261027_0351_A50_SENSOR_LAG_MATLAB"/"DCHR_A50_Sensor_Lag.slx"
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),"8edb7f64b9fe27c54be4c5d1223e242feb6f733cde97dce4c044b25729dc5cbe")
 def test_saved_graphical_models(self):
  import zipfile
  for delay in (0,2,4):
   p=D/f"DCHR_A51_TripDelay_{delay}.slx"
   self.assertTrue(p.is_file())
   with zipfile.ZipFile(p) as z:
    self.assertIsNone(z.testzip())
    parts=[n for n in z.namelist() if "stateflow" in n.lower()]
    self.assertGreaterEqual(len(parts),1)
    data=b"".join(z.read(n) for n in parts)
    self.assertIn(f"pending&gt;={delay}".encode(),data)
 def test_matlab_numeric_acceptance(self):
  r=json.loads((D/"MATLAB_A51_RESULT.json").read_text(encoding="utf-8"))
  self.assertEqual(r["status"],"A51_GRAPHICAL_TRIP_DELAY_PARITY_PASS")
  self.assertEqual(r["comparisons"],15840)
  self.assertEqual(len(r["cases"]),6)
  self.assertFalse(r["physical_release"])
  for key,item in r["cases"].items():
   self.assertEqual(item["samples"],240)
   self.assertLess(max(item["max_abs_differences"]),0.001)
if __name__=="__main__":unittest.main(verbosity=2)

