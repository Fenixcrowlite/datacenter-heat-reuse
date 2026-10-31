"""Independent float-based QA, not importing the Decimal auditor."""
import csv, hashlib, json, math, sqlite3, unittest
from pathlib import Path
H=Path(__file__).resolve().parent
D=Path(r"C:\Users\Lysda\OneDrive\Projects\DataCenter_Heat_Reuse")
R=D/"results"; M=D/"matlab"
P=json.loads((H/"C36_PROVENANCE_RESULTS.json").read_text(encoding="utf-8"))
def rows(name):
    with (R/name).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
class C36QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v1=rows("warm45_storage100_timeseries.csv")
        cls.v2=rows("best_scenario_v2_timeseries.csv")
        cls.s1=rows("scenario_summary.csv")
        cls.s2=rows("scenario_summary_v2.csv")
    def test_files_and_row_count(self):
        self.assertEqual(len(self.v1),8760);self.assertEqual(len(self.v2),8760)
    def test_v1_label(self):
        self.assertEqual(self.s1[-1]["Scenario"],"Warm45_Storage100")
        self.assertEqual(P["v1_100mwh"]["trace"]["scenario"],self.s1[-1]["Scenario"])
    def test_v2_actual_label(self):
        self.assertEqual(self.s2[-1]["Scenario"],"Liquid35_LowTempDH")
        self.assertEqual(P["v2_timeseries_actual_scenario"],self.s2[-1]["Scenario"])
    def test_v2_filename_is_not_best_coverage(self):
        best=max(self.s2,key=lambda x:float(x["Coverage"]))
        self.assertEqual(best["Scenario"],"Warm45_Storage100")
        self.assertNotEqual(best["Scenario"],self.s2[-1]["Scenario"])
    def test_gas_delta(self):
        byname={r["Scenario"]:r for r in self.s2}
        delta=float(byname["Liquid35_LowTempDH"]["GasHeat_MWh"])-float(byname["Warm45_Storage100"]["GasHeat_MWh"])
        self.assertAlmostEqual(delta,2006.5032633916,places=7)
        self.assertAlmostEqual(delta,P["v2_gas_difference_mwh"],places=7)
    def test_source_hashes(self):
        for key,hashval in P["source_hashes"].items():
            path={"v1_driver":M/"run_experiment.m","v2_driver":M/"run_experiment_v2.m",
                  "v1_config":M/"default_config.m","v2_config":M/"default_config_v2.m",
                  "v1_sim":M/"+dchr"/"simulate_system.m","v2_sim":M/"+dchr"/"simulate_system_v2.m",
                  "v2_storage":M/"+dchr"/"+components"/"storage_step.m",
                  "v1_csv":R/"warm45_storage100_timeseries.csv","v2_csv":R/"best_scenario_v2_timeseries.csv",
                  "v1_summary":R/"scenario_summary.csv","v2_summary":R/"scenario_summary_v2.csv"}[key]
            self.assertEqual(checksum(path),hashval,key)
    def test_v2_source_last_scenario_contract(self):
        s=(M/"run_experiment_v2.m").read_text(encoding="utf-8-sig")
        self.assertIn("writetable(O{end}",s)
        self.assertIn("'Liquid35_LowTempDH'",s)
        self.assertIn("'Warm45_Storage100'",s)
        self.assertLess(s.index("'Warm45_Storage100'"),s.index("'Liquid35_LowTempDH'"))
    def test_v1_source_scenario_contract(self):
        s=(M/"run_experiment.m").read_text(encoding="utf-8-sig")
        self.assertIn("writetable(allOut{4}",s)
        self.assertIn("'storage_MWh',{0,0,0,100}",s)
    def test_energy_recursion_independent(self):
        for group in (self.v1,self.v2):
            e=0.0
            for r in group:
                stored=float(r["Storage_E_MWh"])
                self.assertAlmostEqual(stored,e,delta=1e-7)
                c=float(r["Storage_Charge_MW"]);d=float(r["Storage_Discharge_MW"])
                self.assertFalse(c>1e-9 and d>1e-9)
                e=max(0.0,stored*0.9999+0.95*c-d/0.95)
                self.assertGreaterEqual(e,-1e-7);self.assertLessEqual(e,100+1e-7)
    def test_hourly_heat_balance(self):
        for group in (self.v1,self.v2):
            for r in group:
                demand=float(r["Heat_Demand_MW"])
                reconstructed=float(r["HP_Heat_Used_MW"])-float(r["Storage_Charge_MW"])+float(r["Storage_Discharge_MW"])+float(r["Gas_Heat_MW"])
                self.assertAlmostEqual(demand,reconstructed,delta=1e-7)
    def test_annual_gas_sum(self):
        for group,summary in ((self.v1,self.s1[-1]),(self.v2,self.s2[-1])):
            self.assertAlmostEqual(math.fsum(float(r["Gas_Heat_MW"]) for r in group),float(summary["GasHeat_MWh"]),delta=1e-6)
    def test_negative_control_mislabel(self):
        actual=math.fsum(float(r["Gas_Heat_MW"]) for r in self.v2)
        wrong=next(float(x["GasHeat_MWh"]) for x in self.s2 if x["Scenario"]=="Warm45_Storage100")
        self.assertGreater(abs(actual-wrong),2000)
    def test_no_physical_or_matlab_claim(self):
        self.assertIs(P["matlab_executed"],False);self.assertIs(P["source_modified"],False)
        self.assertIn("energy-only",P["v2_100mwh"]["storage"])
        self.assertEqual(P["primary_source_signoffs"],0)
    def test_registry_integrity(self):
        db=sqlite3.connect(f"file:{(H.parent.parent/'tasks.sqlite3').as_posix()}?mode=ro",uri=True)
        try:
            self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")
            t=db.execute("SELECT project,status,worker_pid FROM tasks WHERE id=?",(P["task_id"],)).fetchone()
            self.assertEqual(t[0],"DataCenter Heat Reuse");self.assertIsNone(t[2])
        finally:db.close()
if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(C36QA)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    output={"status":"PASS" if result.wasSuccessful() else "FAIL","passed":result.testsRun-len(result.failures)-len(result.errors),"failed":len(result.failures)+len(result.errors),"tests":result.testsRun,"independent_hourly_records":17520,"verified_against_source_hashes":len(P["source_hashes"]),"negative_control":"v2 warm45 label rejected by 2006.5 MWh annual gas mismatch"}
    (H/"QA_INDEPENDENT_C36.json").write_text(json.dumps(output,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps(output,ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
