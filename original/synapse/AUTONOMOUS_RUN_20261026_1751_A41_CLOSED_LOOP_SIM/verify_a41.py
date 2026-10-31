"""Independent saved-artifact acceptance for A41. Does not import implementation."""
import csv, json, math, unittest, zipfile
from decimal import Decimal as D
from pathlib import Path
ROOT=Path(__file__).resolve().parent
UPSTREAM=ROOT.parent/"AUTONOMOUS_RUN_20261026_1054_A38_TES_N1_INTEGRATION"
SCENARIOS=("both","main_only","backup_only","neither")
def load(name):
    with (ROOT/name).open(newline="",encoding="utf8") as f:
        return list(csv.DictReader(f))
def d(x):return D(str(x))
def oracle(mode,required,cap,T,soc):
    critical=T>=42 or cap<=0
    shortage=required>cap+1e-6
    margin=required+5000<=cap
    if mode==0:
        if critical:return 2
        if shortage:return 1
        if soc>=.999 and required<=cap:return 3
    if mode==1:
        if critical:return 2
        if margin and T<39:return 3 if soc>=.999 else 0
    if mode==2:
        if T<39 and cap>0:return 1
    if mode==3:
        if critical:return 2
        if shortage:return 1
        if soc<=.98 and margin and T<39:return 0
    return mode
class A41Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inputs=load("INPUTS_A41.csv")
        cls.py={s:load("TRACE_A41_"+s+".csv") for s in SCENARIOS}
        cls.ml={s:load("MATLAB_TRACE_"+s+".csv") for s in SCENARIOS}
        cls.result=json.loads((ROOT/"MATLAB_RESULT.json").read_text(encoding="utf8"))
    def test_samples(self):
        self.assertEqual(len(self.inputs),672)
        for s in SCENARIOS:
            self.assertEqual(len(self.py[s]),672,s)
            self.assertEqual(len(self.ml[s]),672,s)
    def test_grid(self):
        for s in SCENARIOS:
            for k,(p,m) in enumerate(zip(self.py[s],self.ml[s])):
                self.assertEqual(int(p["k"]),k)
                self.assertEqual(float(p["cas_h"]),k*.25)
                self.assertEqual(float(m["t_s"]),k*900)
    def test_matlab_python_parity_saved(self):
        fields={"mode":("mode",0),"T_next_C":("T_next_C",1e-8),
            "E_next_J":("E_next_J",1e-4),"shed_W":("shed_W",1e-6),
            "required_W":("required_W",1e-6),"reject_W":("reject_W",1e-6),
            "unhandled_W":("unhandled_W",1e-6),
            "dc_residual_W":("dc_residual_W",1e-5),
            "tes_residual_J":("tes_residual_J",1e-4)}
        for s in SCENARIOS:
            for k,(p,m) in enumerate(zip(self.py[s],self.ml[s])):
                for a,(b,tol) in fields.items():
                    self.assertLessEqual(abs(float(p[a])-float(m[b])),tol,(s,k,a))
    def test_stateflow_independent_oracle(self):
        for s in SCENARIOS:
            mode=0
            for k,r in enumerate(self.py[s]):
                mode=oracle(mode,float(r["required_W"]),float(r["capacity_W"]),
                    float(r["T_start_C"]),float(r["TES_SOC_start"]))
                self.assertEqual(mode,int(r["mode"]),(s,k))
    def test_branch_switch_delay(self):
        cap=[float(r["capacity_W"]) for r in self.py["backup_only"]]
        self.assertEqual(cap[95],330000)
        self.assertEqual(cap[96:98],[0,0])
        self.assertEqual(cap[98],150000)
        self.assertEqual(cap[383],150000)
    def test_fault_and_recovery(self):
        for s in SCENARIOS:
            r=self.py[s]
            self.assertEqual(float(r[383]["capacity_W"]),{"both":330000,"main_only":180000,"backup_only":150000,"neither":0}[s])
            self.assertEqual(float(r[384]["capacity_W"]),330000)
            self.assertTrue(all(float(x["unhandled_W"])<1e-6 for x in r[384:]),s)
    def test_tes_energy_recurrence_decimal(self):
        for s in SCENARIOS:
            for k,(r,i) in enumerate(zip(self.py[s],self.inputs)):
                E=d(r["E_start_J"]);En=d(r["E_next_J"])
                qcharge=d(r["charge_W"]);qdis=d(i["qdis"])
                loss=D(".002")*E/D(86400)
                expected=E+D(900)*(D(".93")*qcharge-qdis/D(".91")-loss)
                self.assertLess(abs(expected-En),D(".005"),(s,k))
                self.assertGreaterEqual(En,-D(".001"))
                self.assertLessEqual(En,D(900)*D("3600000")+D(".001"))
    def test_dc_first_law_decimal(self):
        for s in SCENARIOS:
            for k,r in enumerate(self.py[s]):
                residual=d(r["qdc_W"])-d(r["shed_W"])-d(r["hx_W"])-d(r["hp_source_W"])-d(r["leak_W"])-d(r["reject_W"])-d(r["unhandled_W"])
                self.assertLess(abs(residual),D(".0001"),(s,k))
    def test_temperature_recurrence_decimal(self):
        for s in SCENARIOS:
            for k,r in enumerate(self.py[s]):
                t=d(r["T_start_C"])
                passive=D(2000)*max(D(0),t-D(30))
                expected=max(D(30),t+D(900)*(d(r["unhandled_W"])-passive)/D(8000000))
                self.assertLess(abs(expected-d(r["T_next_C"])),D(".00000001"),(s,k))
    def test_shed_ramp_and_mode(self):
        for s in SCENARIOS:
            prev=0.
            for k,r in enumerate(self.py[s]):
                shed=float(r["shed_W"]);qdc=float(r["qdc_W"])
                self.assertGreaterEqual(shed,-1e-8)
                self.assertLessEqual(shed,.4*qdc+1e-7)
                self.assertLessEqual(shed,prev+15000+1e-7)
                if int(r["mode"]) in (0,3):self.assertEqual(shed,0,(s,k))
                prev=shed
    def test_prefault_A38_parity(self):
        with (UPSTREAM/"trace_both_no_shed.csv").open(newline="",encoding="utf8") as f:
            old=list(csv.DictReader(f))
        for s in SCENARIOS:
            for k in range(96):
                r=self.py[s][k];o=old[k]
                self.assertLess(abs(float(r["E_next_J"])-float(o["E_TES_next_J"])),.0001,(s,k))
                self.assertLess(abs(float(r["T_next_C"])-float(o["T_IT_next_C"])),1e-9,(s,k))
    def test_model_saved_feedback_and_no_hardware(self):
        with zipfile.ZipFile(ROOT/"DCHR_A41_Closed_Loop.slx") as z:
            self.assertIsNone(z.testzip())
            xml=z.read("simulink/systems/system_root.xml").decode("utf8")
            for name in ("Supervisor","TESDispatch","ThermalPlant","TemperatureMemory","TESMemory","ShedMemory","SOC"):
                self.assertIn(name,xml)
            self.assertGreaterEqual(xml.count('BlockType="UnitDelay"'),3)
            for forbidden in ("MQTT","Modbus","TCPIP","SerialPort","IODevice"):
                self.assertNotIn(forbidden,xml)
    def test_fail_closed_and_hazard_detection(self):
        self.assertEqual(self.result["status"],"STATEFLOW_CLOSED_LOOP_SIM_PASS")
        self.assertIs(self.result["physical_release"],False)
        self.assertGreater(max(float(r["T_next_C"]) for r in self.py["backup_only"]),42)
        self.assertGreater(max(float(r["T_next_C"]) for r in self.py["neither"]),42)
        self.assertEqual(self.result["scenarios"]["both"]["critical_steps"],0)
    def test_delay_sensitivity_and_threshold(self):
        sweep=json.loads((ROOT/"DELAY_SWEEP.json").read_text(encoding="utf8"))["delay_steps"]
        temps=[sweep[str(k)]["max_temperature_C"] for k in range(5)]
        self.assertEqual(temps,sorted(temps))
        self.assertLess(temps[0],42)
        self.assertGreater(temps[1],42)
        self.assertEqual(sweep["0"]["alarm_intervals"],0)
        self.assertEqual(sweep["2"]["critical_steps"],8)
    def test_matlab_output_and_no_stderr(self):
        self.assertEqual((ROOT/"MATLAB_STDERR.txt").stat().st_size,0)
        log=(ROOT/"MATLAB_STDOUT.txt").read_text(encoding="utf8")
        for s in SCENARIOS:self.assertIn("A41_CLOSED_LOOP_PASS "+s,log)
        self.assertIn("A41_ALL_SCENARIOS_PASS",log)
if __name__=="__main__":unittest.main(verbosity=2)
