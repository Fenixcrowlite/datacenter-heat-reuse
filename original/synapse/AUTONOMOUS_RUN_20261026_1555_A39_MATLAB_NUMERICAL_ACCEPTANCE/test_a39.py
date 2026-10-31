"""Independent A39 acceptance gates for actual MATLAB R2026a batch replay."""
from pathlib import Path
import unittest,json,hashlib,sqlite3,csv
HERE=Path(__file__).resolve().parent
CENTER=HERE.parent.parent
A38=HERE.parent/'AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION'
A36=HERE.parent/'AUTONOMOUS_RUN_20261026_0744_A36_DCHR_REDISPATCH_REFERENCE'
V08=Path(r'C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse\results\pool_measurement_v08\sim_v08_zdravy_SK.csv')
TASK='scc-3d9d172beb6e1b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class A39Acceptance(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.result=json.loads((HERE/'MATLAB_RESULT.json').read_text(encoding='utf8'))
  cls.preflight=json.loads((HERE/'PREFLIGHT.json').read_text(encoding='utf8'))
  cls.upstream=json.loads((A38/'RESULTS_A38.json').read_text(encoding='utf8'))
 def test_actual_matlab_output(self):
  self.assertEqual(self.result['status'],'MATLAB_NUMERICAL_ACCEPTANCE_PASS')
  self.assertEqual(self.result['run_type'],'MATLAB_R2026a_BATCH_NUMERICAL_ONLY')
  self.assertIn('A39_MATLAB_NUMERICAL_PASS',(HERE/'MATLAB_STDOUT.txt').read_text(encoding='utf8'))
 def test_comparison_cardinality(self):
  self.assertEqual((self.result['cases'],self.result['samples_per_case'],self.result['comparisons']),(12,672,80640))
 def test_numeric_accuracy(self):
  self.assertLessEqual(self.result['max_error'],1e-6)
  self.assertGreaterEqual(self.result['max_error'],0)
 def test_no_false_release(self):
  self.assertIs(self.result['stateflow_executed'],False)
  self.assertIs(self.result['physical_release_allowed'],False)
  self.assertIs(self.result['release_allowed'],False)
 def test_stderr_and_failure_absent(self):
  self.assertEqual((HERE/'MATLAB_STDERR.txt').read_text(encoding='utf8').strip(),'')
  self.assertFalse((HERE/'MATLAB_FAILURE.txt').exists())
 def test_pinned_inputs(self):
  self.assertEqual(sha(V08),self.preflight['source_v08_sha256'])
  self.assertEqual(sha(A36/'scenario_both_off.csv'),self.preflight['source_a36_sha256'])
  self.assertEqual(sha(A38/'dchr_a38_step.m'),self.preflight['a38_step_sha256'])
  self.assertEqual(sha(A38/'dchr_a38_replay_acceptance.m'),self.preflight['a38_acceptance_sha256'])
 def test_immutable_trace_hashes(self):
  self.assertEqual(len(self.upstream['cases']),12)
  for name,case in self.upstream['cases'].items():
   with self.subTest(case=name):
    self.assertEqual(sha(A38/case['trace']),case['sha256'])
 def test_trace_dimensions(self):
  for name,case in self.upstream['cases'].items():
   with (A38/case['trace']).open(encoding='utf8',newline='') as f:
    self.assertEqual(sum(1 for _ in csv.DictReader(f)),672,name)
 def test_existing_registry_state(self):
  db=sqlite3.connect('file:'+str(CENTER/'tasks.sqlite3').replace('\\','/')+'?mode=ro',uri=True)
  self.assertEqual(db.execute('pragma quick_check').fetchone()[0],'ok')
  self.assertEqual(db.execute('select status,stage,worker_pid,owner from tasks where id=?',(TASK,)).fetchone(),('review','planned',None,'MATLAB/Stateflow QA'))
  db.close()
 def test_no_stop(self):
  for root in (CENTER,CENTER/'recovery',HERE,V08.parent.parent.parent):
   for n in ('STOP','STOP.flag','STOP.txt','.stop','.STOP','PAUSE','PAUSE.flag','PAUSE.txt','STOP_MANAGED_WORKERS.txt'):
    self.assertFalse((root/n).exists(),str(root/n))
if __name__=='__main__':unittest.main(verbosity=2)
