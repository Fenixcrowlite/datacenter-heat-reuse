from pathlib import Path
p=Path(__file__).with_name("verify_a40.py")
s=p.read_text(encoding="utf-8")
needle='if __name__=="__main__":'
assert s.count(needle)==1
addition='''
    def test_all_four_stateflow_replays(self):
        import json
        result=json.loads((ROOT/"MATLAB_RESULT.json").read_text())
        self.assertEqual(result["status"],"STATEFLOW_SIM_PASS")
        counts=result["scenario_mode_counts"]
        for name in ("main_only","both","backup_only","neither"):
            path=TRACE if name=="main_only" else ROOT/f"STATEFLOW_TRACE_{name}.csv"
            with path.open(newline="",encoding="utf-8") as f:
                rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
            self.assertEqual(len(rows),672,name)
            state=0
            observed=[0,0,0,0]
            for i,r in enumerate(rows):
                state=step(state,r["required_W"],r["capacity_W"],r["temperature_C"],r["tes_soc"])
                self.assertEqual(int(r["mode"]),state,(name,i))
                observed[state]+=1
                self.assertAlmostEqual(r["shed_fraction"],.4 if state in (1,2) else 0)
                self.assertEqual(r["alarm"],1 if state==3 else state)
            self.assertEqual(observed,counts[name],name)
        self.assertEqual(counts["neither"],[96,0,576,0])

'''
p.write_text(s.replace(needle,addition+needle),encoding="utf-8")
print("ADDED_FOUR_REPLAY_QA")
