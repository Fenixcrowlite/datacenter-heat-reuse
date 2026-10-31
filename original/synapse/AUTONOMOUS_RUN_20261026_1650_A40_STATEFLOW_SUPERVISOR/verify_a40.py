"""Independent A40 synthetic Stateflow trace and saved-SLX acceptance."""
from __future__ import annotations
import csv, math, unittest, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parent
TRACE=ROOT/"STATEFLOW_TRACE.csv"
MODEL=ROOT/"DCHR_A40_Safety_Controller.slx"

def step(state, req, cap, temp, soc):
    # Disjoint guards reproduce the documented Stateflow state transitions.
    critical = temp >= 42 or cap <= 0
    shortage = req > cap + 1e-6
    margin = req + 5000 <= cap
    if state == 0:
        if critical: return 2
        if shortage: return 1
        if soc >= .999 and req <= cap: return 3
    elif state == 1:
        if critical: return 2
        if margin and temp < 39:
            return 3 if soc >= .999 else 0
    elif state == 2:
        if temp < 39 and cap > 0: return 1
    elif state == 3:
        if critical: return 2
        if shortage: return 1
        if soc <= .98 and margin and temp < 39: return 0
    else: raise ValueError(state)
    return state

class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with TRACE.open(newline="",encoding="utf-8") as f:
            cls.rows=[{k:float(v) for k,v in row.items()} for row in csv.DictReader(f)]
    def test_saved_model_zip_integrity(self):
        with zipfile.ZipFile(MODEL) as z:
            self.assertIsNone(z.testzip())
            chart=z.read("simulink/stateflow/chart_24.xml")
            root=ET.fromstring(chart)
            states=root.findall("./Children/state")
            transitions=root.findall("./Children/transition")
            self.assertEqual(len(states),4)
            self.assertEqual(len(transitions),11)
            labels=[next(p.text for p in s.findall("P") if p.attrib.get("Name")=="labelString") for s in states]
            self.assertEqual({x.splitlines()[0] for x in labels},{"NORMAL","DEGRADED","CRITICAL","TES_FULL"})
            guards=[next(x.text for x in tr.findall("P") if x.attrib.get("Name")=="labelString") for tr in transitions if any(x.attrib.get("Name")=="labelString" for x in tr.findall("P"))]
            self.assertTrue(any("capacityW <= 0" in g for g in guards))
            self.assertTrue(any("soc >= 0.999" in g for g in guards))
    def test_672_rows(self):
        self.assertEqual(len(self.rows),672)
        for i,row in enumerate(self.rows):
            self.assertEqual(row["t_s"],900*i)
            self.assertTrue(all(math.isfinite(x) for x in row.values()))
            self.assertGreaterEqual(row["capacity_W"],0)
            self.assertGreaterEqual(row["required_W"],0)
            self.assertGreaterEqual(row["tes_soc"],0)
            self.assertLessEqual(row["tes_soc"],1+1e-6)
    def test_oracle_exact_parity(self):
        state=0
        mismatches=[]
        for i,row in enumerate(self.rows):
            state=step(state,row["required_W"],row["capacity_W"],row["temperature_C"],row["tes_soc"])
            if int(row["mode"])!=state:
                mismatches.append((i,state,int(row["mode"])))
        self.assertFalse(mismatches,mismatches[:12])
    def test_outputs_and_mode_coverage(self):
        seen=set()
        for r in self.rows:
            mode=int(r["mode"]);seen.add(mode)
            self.assertIn(mode,(0,1,2,3))
            self.assertAlmostEqual(r["shed_ceiling_fraction"],.4 if mode in (1,2) else 0)
            self.assertEqual(r["alarm"],1 if mode==3 else mode)
        self.assertEqual(seen,{0,1,2,3})
    def test_critical_priority_and_recovery(self):
        self.assertEqual(step(0,220000,0,30,.5),2)
        self.assertEqual(step(3,220000,0,30,1),2)
        self.assertEqual(step(1,220000,180000,42,.5),2)
        self.assertEqual(step(2,100000,180000,40,.5),2)
        self.assertEqual(step(2,100000,180000,38,.5),1)
    def test_soc_hysteresis(self):
        self.assertEqual(step(0,100000,180000,30,1),3)
        self.assertEqual(step(3,100000,180000,30,.99),3)
        self.assertEqual(step(3,100000,180000,30,.98),0)
        self.assertEqual(step(1,100000,180000,30,1),3)
    def test_capacity_hysteresis(self):
        self.assertEqual(step(0,181000,180000,30,.5),1)
        self.assertEqual(step(1,177000,180000,30,.5),1)
        self.assertEqual(step(1,175000,180000,30,.5),0)
    def test_no_external_hardware_blocks(self):
        with zipfile.ZipFile(MODEL) as z:
            xml=z.read("simulink/systems/system_root.xml").decode("utf-8")
        self.assertEqual(xml.count('BlockType="FromWorkspace"'),4)
        self.assertEqual(xml.count('BlockType="ToWorkspace"'),3)
        for forbidden in ("TCPIP","SerialPort","UDP","MQTT","Modbus","IODevice"):
            self.assertNotIn(forbidden,xml)


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
                self.assertAlmostEqual(r["shed_ceiling_fraction"],.4 if state in (1,2) else 0)
                self.assertEqual(r["alarm"],1 if state==3 else state)
            self.assertEqual(observed,counts[name],name)
        self.assertEqual(counts["neither"],[96,0,576,0])

if __name__=="__main__":
    unittest.main(verbosity=2)
