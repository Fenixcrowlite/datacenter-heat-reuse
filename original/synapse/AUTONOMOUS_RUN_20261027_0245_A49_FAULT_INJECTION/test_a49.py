"""Independent A49 acceptance tests; read-only upstream, no MATLAB."""
import hashlib, json, unittest
from pathlib import Path
import a49_independent_audit as a49

D=Path(__file__).resolve().parent
class A49Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.rows=a49.plant.verified_inputs()
  cls.trace=a49.plant.simulate(cls.rows[:120],"neither")
 def test_independent_ledger(self):
  result=a49.independent_audit(self.trace)
  self.assertEqual(result["samples"],120)
  self.assertEqual(result["first_trip_index"],98)
 def test_sensor_lag_observable(self):
  trace=a49.plant.simulate(self.rows[:120],"neither",sensor_lag_steps=4)
  self.assertEqual(a49.independent_audit(trace,sensor_lag_steps=4)["first_trip_index"],98)
  with self.assertRaises(a49.LedgerError):
   a49.independent_audit(trace,sensor_lag_steps=0)
 def test_tes_mutation_detected(self):
  trace=[dict(r) for r in self.trace]
  trace[100]["E_next_J"]+=1e6
  with self.assertRaisesRegex(a49.LedgerError,"TES ledger"):
   a49.independent_audit(trace)
 def test_temperature_mutation_detected(self):
  trace=[dict(r) for r in self.trace]
  trace[100]["T_next_C"]+=2
  with self.assertRaisesRegex(a49.LedgerError,"temperature ledger"):
   a49.independent_audit(trace)
 def test_reject_mutation_detected(self):
  trace=[dict(r) for r in self.trace]
  trace[100]["reject_W"]+=1000
  with self.assertRaises(a49.LedgerError):
   a49.independent_audit(trace)
 def test_hp_tau_zero_and_nonzero(self):
  for tau in (0,1800,7200):
   trace=a49.plant.simulate(self.rows[:120],"both",compressor_tau_s=tau)
   self.assertEqual(a49.independent_audit(trace,compressor_tau_s=tau)["samples"],120)
 def test_trip_delay_cases(self):
  for delay in (0,2,4):
   trace=a49.plant.simulate(self.rows[:120],"neither",trip_delay_steps=delay)
   self.assertEqual(a49.independent_audit(trace)["first_trip_index"],96+delay)
 def test_baseline_immutable(self):
  model=D.parent/"AUTONOMOUS_RUN_20261027_0150_A48_EXECUTABLE_QA"/"DCHR_A48_Graphical_Closed_Loop.slx"
  self.assertEqual(hashlib.sha256(model.read_bytes()).hexdigest(),
                   "063f9afb5816cd4f6bed415256293eee67b328718b141c29d84853ddafab25cb")
 def test_full_fault_injection(self):
  result=a49.run()
  self.assertEqual(len(result["baseline"]),7)
  self.assertEqual(len(result["randomized_trials"]),24)
  self.assertEqual(len(result["mutation_probes_detected"]),5)
  self.assertEqual(len(result["zero_cap_trip_indices"]),9)
  self.assertFalse(result["physical_release"])
  self.assertFalse(result["matlab_a49_executed"])
if __name__=="__main__": unittest.main(verbosity=2)
