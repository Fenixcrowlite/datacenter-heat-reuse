"""Independent A47 migration-contract acceptance tests."""
import csv, importlib.util, json, unittest
from pathlib import Path
import parity_probe as p

class ContractTests(unittest.TestCase):
    def test_source_hashes_are_pinned(self):
        self.assertEqual(p.hash_file(p.A44/"DCHR_A44_Graphical_Supervisor.slx"),
                         "c55dc5a1d4311104e675aebd6045e19883f95f27ea33db42d155edbdffe12307")
        self.assertEqual(p.hash_file(p.A46/"DCHR_A46_Compressor_Closed_Loop.slx"),
                         "a26fa2f0ca04555c20b806417efff390d0b605bc2a82b0ac1459fa860f6c2e49")

    def test_seven_real_a45_traces_match_a44_fsm(self):
        result=p.run()
        self.assertEqual(result["total_steps"],4704)
        self.assertEqual(result["mismatches"],0)
        self.assertEqual(len(result["cases"]),7)

    def test_wrong_ramp_target_is_detected(self):
        with (p.A41/"INPUTS_A41.csv").open(newline="",encoding="utf-8") as f:
            true_qdc=[float(x["qdc"]) for x in csv.DictReader(f)]
        with (p.A45/"TRACE_A45_backup_only.csv").open(newline="",encoding="utf-8") as f:
            rows=list(csv.DictReader(f))
        # Deliberately wrong adapter: uses actual active IT rather than requested IT.
        wrong=[float(x["active_it_W"]) for x in rows]
        predicted=p.graphical_reference(rows,wrong)
        self.assertGreater(sum(s!=r["state"] for s,r in zip(predicted,rows)),0)
        correct=p.graphical_reference(rows,true_qdc)
        self.assertEqual(sum(s!=r["state"] for s,r in zip(correct,rows)),0)

    def test_a44_reference_cases_still_match_saved_csv(self):
        spec=importlib.util.spec_from_file_location("a44_reference",p.A44/"reference_a44.py")
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for name in ("nominal","short_fault","sustained_fault","interrupted_recovery"):
            with self.subTest(name=name):
                expected=mod.reference(mod.stimuli(name))
                with (p.A44/("STIM_A44_"+name+".csv")).open(newline="",encoding="utf-8") as f:
                    saved=list(csv.DictReader(f))
                self.assertEqual(len(expected),len(saved))
                self.assertEqual([x["mode"] for x in expected],[int(x["mode"]) for x in saved])
                self.assertEqual([x["alarm"] for x in expected],[int(x["alarm"]) for x in saved])

    def test_fault_recover_hysteresis_and_pending_timing(self):
        rows=[{"nominal_cap_W":"330000","T_start_C":"30","active_it_W":"200000","residual_it_W":"0"} for _ in range(12)]
        for i in (2,3,4):rows[i]["nominal_cap_W"]="0"
        for i in range(5,12):rows[i]["nominal_cap_W"]="330000"
        modes=p.graphical_reference(rows,[200000]*12)
        self.assertEqual(modes[2:5],["TRIP_PENDING","TRIP_PENDING","TRIPPED"])
        self.assertEqual(modes[5:7],["TRIPPED","RAMPING"])

if __name__=="__main__":
    unittest.main()
