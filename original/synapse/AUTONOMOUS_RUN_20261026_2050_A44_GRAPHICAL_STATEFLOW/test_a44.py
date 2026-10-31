"""A44 independent event-state regression and no-hardware checks."""
import csv
import hashlib
import json
import unittest
from pathlib import Path
import reference_a44 as a

HERE = Path(__file__).resolve().parent

class GraphicalSupervisorAcceptance(unittest.TestCase):
    def test_four_cases_and_lengths(self):
        for case in ("nominal", "short_fault", "sustained_fault", "interrupted_recovery"):
            with self.subTest(case=case):
                r = a.reference(a.stimuli(case))
                self.assertEqual(len(r), 672)
                self.assertEqual([x["k"] for x in r], list(range(672)))
                self.assertTrue(all(0 <= x["mode"] <= 3 for x in r))
    def test_short_fault_is_cancelled(self):
        r = a.reference(a.stimuli("short_fault"))
        self.assertEqual(r[96]["mode"], 1)
        self.assertEqual(r[97]["mode"], 0)
        self.assertEqual(sum(x["mode"] == 2 for x in r), 0)
    def test_sustained_fault_trips_after_two_pending_samples(self):
        r = a.reference(a.stimuli("sustained_fault"))
        self.assertEqual([r[i]["mode"] for i in (95,96,97,98,99)], [0,1,1,2,2])
        self.assertEqual(r[145]["mode"], 2)
        self.assertEqual(r[146]["mode"], 3)
        self.assertEqual(r[147]["mode"], 3)
        self.assertEqual(r[160]["mode"], 0)
    def test_recovery_interrupt_retrips(self):
        r = a.reference(a.stimuli("interrupted_recovery"))
        transitions = [(i,r[i-1]["mode"],r[i]["mode"]) for i in range(1,len(r))
                       if r[i-1]["mode"] != r[i]["mode"]]
        self.assertGreaterEqual(sum(new == 1 for _,_,new in transitions), 3)
        self.assertGreaterEqual(sum(new == 2 for _,_,new in transitions), 2)
    def test_saved_reference_csv_matches_replay(self):
        for case in ("nominal", "short_fault", "sustained_fault", "interrupted_recovery"):
            with (HERE / ("STIM_A44_" + case + ".csv")).open(newline="",encoding="utf8") as f:
                stored = [{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
            self.assertEqual(stored,a.reference(a.stimuli(case)))
    def test_no_hardware_io(self):
        s=(HERE/"reference_a44.py").read_text(encoding="utf8").lower()
        for token in ("subprocess", "socket.", "requests.", "serial.", "modbus", "opcua"):
            self.assertNotIn(token,s)
    def test_release_gate(self):
        d=json.loads((HERE/"REFERENCE_A44.json").read_text(encoding="utf8"))
        self.assertFalse(d["physical_release"])
        self.assertEqual(len(d["cases"]),4)
    def test_upstream_a43_is_immutable(self):
        upstream=HERE.parent/"AUTONOMOUS_RUN_20261026_1945_A43_FINITE_TRIP_RESIDUAL"
        manifest=json.loads((upstream/"SHA256_MANIFEST.json").read_text(encoding="utf8"))
        for filename in ("finite_trip_a43.py","build_a43.m"):
            expected=manifest.get(filename)
            self.assertIsNotNone(expected)
            self.assertEqual(hashlib.sha256((upstream/filename).read_bytes()).hexdigest(),expected)

if __name__=="__main__":
    unittest.main(verbosity=2)
