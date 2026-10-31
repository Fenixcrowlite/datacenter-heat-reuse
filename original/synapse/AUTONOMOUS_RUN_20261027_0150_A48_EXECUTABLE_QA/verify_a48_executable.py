"""Independent post-MATLAB acceptance gate for isolated A48 (no runtime writes)."""
from pathlib import Path
from zipfile import ZipFile
import json, hashlib, unittest
D=Path(__file__).resolve().parent
R=D.parent
J=json.loads((D/'SIMULINK_A48_RESULT.json').read_text(encoding='utf-8-sig'))
TOL=[1e-7,1e-3,0,1e-6,1e-6,1e-6,1e-6,1e-6,1e-6,1e-5,1e-3]
CASES=['both','main_only','backup_only','neither','CF_both','CF_backup_only','CF_neither']
class A48Acceptance(unittest.TestCase):
 def test_zip_integrity(self):
  with ZipFile(D/'DCHR_A48_Graphical_Closed_Loop.slx') as z:self.assertIsNone(z.testzip())
 def test_graphical_stateflow_real(self):
  with ZipFile(D/'DCHR_A48_Graphical_Closed_Loop.slx') as z:
   names=z.namelist();root=z.read('simulink/systems/system_root.xml');
   self.assertIn(b'GraphicalSupervisor',root)
   self.assertIn(b'CoupledController',root)
   self.assertIn(b'SupervisorSignals',root)
   charts=[z.read(n) for n in names if n.startswith('simulink/stateflow/chart_') and n.endswith('.xml')]
   self.assertTrue(any(all(v in ch for v in (b'ACTIVE',b'TRIP_PENDING',b'TRIPPED',b'RAMPING')) for ch in charts))
 def test_complete_scenario_set(self):self.assertEqual(set(J['scenarios']),set(CASES))
 def test_numeric_volume(self):
  self.assertEqual(J['samples'],7*672)
  self.assertEqual(J['numeric_comparisons'],7*672*11)
 def test_all_numeric_tolerances(self):
  for case in CASES:
   row=J['scenarios'][case];self.assertEqual(row['samples'],672)
   self.assertEqual(row['parity'],'PASS');self.assertEqual(len(row['max_abs_differences']),11)
   for k,(diff,tol) in enumerate(zip(row['max_abs_differences'],TOL)):
    self.assertLessEqual(diff,tol,f'{case} col{k} diff={diff} tol={tol}')
 def test_fsm_exact(self):
  self.assertTrue(all(J['scenarios'][x]['max_abs_differences'][2]==0 for x in CASES))
 def test_no_physical_release(self):self.assertFalse(J['physical_release'])
 def test_source_models_immutable(self):
  p=R/'AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW'/'DCHR_A44_Graphical_Supervisor.slx'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'c55dc5a1d4311104e675aebd6045e19883f95f27ea33db42d155edbdffe12307')
  p=R/'AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION'/'DCHR_A46_Compressor_Closed_Loop.slx'
  self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),'a26fa2f0ca04555c20b806417efff390d0b605bc2a82b0ac1459fa860f6c2e49')
 def test_matlab_stdout(self):
  s=(D/'MATLAB_STDOUT.txt').read_text(encoding='utf-8-sig')
  self.assertEqual(s.count('A48_SIMULINK_PASS '),7)
  self.assertIn('A48_SIMULINK_ALL_PASS 51744',s)
  self.assertFalse((D/'MATLAB_STDERR.txt').read_text(encoding='utf-8-sig').strip())
 def test_executable_artifact(self):
  self.assertGreater((D/'DCHR_A48_Graphical_Closed_Loop.slx').stat().st_size,100000)
  self.assertEqual(J['status'],'A48_GRAPHICAL_COUPLED_PARITY_PASS')
if __name__=='__main__':unittest.main(verbosity=2)
