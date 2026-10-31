from pathlib import Path
import hashlib,json,unittest,zipfile
HERE=Path(__file__).resolve().parent
REC=HERE.parent
A45=REC/"AUTONOMOUS_RUN_20261026_2200_A45_COMPRESSOR_LAG_REFERENCE"
A43=REC/"AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL"
A44=REC/"AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class A46Acceptance(unittest.TestCase):
 def test_upstream_unchanged(self):
  self.assertEqual(sha(A43/"DCHR_A43_Finite_Trip_Closed_Loop.slx"),"afe6752077d6bea440ac85d7b700fb867879bc38306840a11fc50ba53c91f162")
  self.assertEqual(sha(A44/"DCHR_A44_Graphical_Supervisor.slx"),"c55dc5a1d4311104e675aebd6045e19883f95f27ea33db42d155edbdffe12307")
  m=json.loads((A45/"SHA256_MANIFEST.json").read_text())
  for k,v in m.items():self.assertEqual(sha(A45/k),v,k)
 def test_model_archive(self):
  with zipfile.ZipFile(HERE/"DCHR_A46_Compressor_Closed_Loop.slx") as z:
   self.assertIsNone(z.testzip())
   self.assertIn("simulink/blockdiagram.xml",z.namelist())
 def test_numerical_audit(self):
  a=json.loads((HERE/"SIMULINK_A46_RESULT.json").read_text())
  b=json.loads((A45/"RESULTS_A45.json").read_text())
  self.assertEqual(a["status"],"A46_SIMULINK_EMCHART_COMPRESSOR_PARITY_PASS")
  self.assertEqual(a["numeric_comparisons"],51744)
  self.assertEqual(a["samples"],4704)
  self.assertEqual(set(a["scenarios"]),set(b["cases"]))
  for name,item in a["scenarios"].items():
   self.assertEqual(item["parity"],"PASS")
   self.assertEqual(item["samples"],672)
   self.assertLess(abs(item["max_temperature_C"]-b["cases"][name]["max_temperature_C"]),1e-5)
 def test_compressor_dynamics_and_limitations(self):
  script=(HERE/"build_a46.m").read_text(encoding="utf8")
  self.assertIn("hpAvailable=hpAvailable+(1-exp(-dt/1800))*(sourceTarget-hpAvailable);",script)
  self.assertIn("source=min(sourceTarget,hpAvailable);",script)
  self.assertIn("Stateflow.EMChart",script)
  self.assertNotIn("add_block('sflib/Chart'",script)
  self.assertFalse(json.loads((HERE/"SIMULINK_A46_RESULT.json").read_text())["physical_release"])
if __name__=="__main__":unittest.main()
