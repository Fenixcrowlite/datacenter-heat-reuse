"""A48 static integration gate. No MATLAB execution or physical certification."""
import unittest,re,csv,sys,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
SOURCE=ROOT/'AUTONOMOUS_RUN_20261026_2255_A46_INTEGRATION'
A44=ROOT/'AUTONOMOUS_RUN_20261026_2050_A44_GRAPHICAL_STATEFLOW'
A47=ROOT/'AUTONOMOUS_RUN_20261026_2347_A47_SUPERVISOR_CONTRACT'
TXT=(HERE/'build_a48.m').read_text(encoding='utf-8')
class A48StaticGate(unittest.TestCase):
    def test_upstream_sha(self):
        self.assertEqual(hashlib.sha256((SOURCE/'DCHR_A46_Compressor_Closed_Loop.slx').read_bytes()).hexdigest(),'a26fa2f0ca04555c20b806417efff390d0b605bc2a82b0ac1459fa860f6c2e49')
        self.assertEqual(hashlib.sha256((A44/'DCHR_A44_Graphical_Supervisor.slx').read_bytes()).hexdigest(),'c55dc5a1d4311104e675aebd6045e19883f95f27ea33db42d155edbdffe12307')
    def test_graphical_chart_is_copied_and_wired(self):
        self.assertIn("load_system(a44file);",TXT)
        self.assertIn("add_block('DCHR_A44_Graphical_Supervisor/Supervisor'",TXT)
        self.assertIn("add_line(mdl,'GraphicalSupervisor/1','CoupledController/9'",TXT)
        self.assertIn("add_line(mdl,'GraphicalSupervisor/2','UnusedAlarm/1'",TXT)
    def test_plant_does_not_own_fsm(self):
        self.assertIn('"state=modeIn;"',TXT)
        self.assertNotIn('"persistent E T state ',TXT)
        self.assertNotIn('"pending=0;"',TXT)
        self.assertNotIn('"good=good+1;"',TXT)
        self.assertNotIn('"fault=nominalCap<=0 || T>=42;"',TXT)
    def test_delayed_feedback_breaks_direct_cycle(self):
        for name,initial in [('DelayTemp','30'),('DelayActive','0')]:
            self.assertIn(f"[mdl '/{name}']",TXT)
            self.assertIn(f"'InitialCondition','{initial}'",TXT)
        for line in ["CoupledController/1','DelayTemp/1","CoupledController/4','DelayActive/1","DelayTemp/1','SupervisorSignals/1","DelayActive/1','SupervisorSignals/2"]:
            self.assertIn(line,TXT)
        self.assertIn("rampDone=(previousActive+15000>=qdc-1e-8)",TXT)
    def test_synthetic_scope_and_full_parity_assertions(self):
        self.assertIn("'physical_release',false",TXT)
        self.assertIn("assert(diff(k)<=tolerance(k),'A48:Parity')",TXT)
        self.assertIn("cases={'both','main_only','backup_only','neither','CF_both','CF_backup_only','CF_neither'}",TXT)
        self.assertIn("assert(size(v,1)==672,'A48:SimRows')",TXT)
    def test_a47_reference_still_replays_all_seven(self):
        sys.path.insert(0,str(A47))
        import parity_probe
        parity_probe.HERE=HERE
        result=parity_probe.run()
        self.assertEqual(result['total_steps'],4704)
        self.assertEqual(result['mismatches'],0)
    def test_no_model_masquerading_as_completed(self):
        self.assertFalse((HERE/'DCHR_A48_Graphical_Closed_Loop.slx').exists())
        self.assertFalse((HERE/'SIMULINK_A48_RESULT.json').exists())
if __name__=='__main__':
    unittest.main(verbosity=2)
