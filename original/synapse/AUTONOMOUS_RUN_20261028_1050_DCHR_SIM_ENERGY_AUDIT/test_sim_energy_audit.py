import csv, tempfile, unittest
from pathlib import Path
from dchr_sim_energy_audit import audit, FIELDS

HEAD=["Time"]+list(FIELDS)
def row(time="01-Jan-2026 00:00:00", **changes):
    d=dict(zip(FIELDS,["10","12","3","1","4","4","0","3.5","2"]))
    d.update(changes)
    return {"Time":time,**d}
def fixture(rows,fn):
    with open(fn,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=HEAD);w.writeheader();w.writerows(rows)

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"input.csv"
    def tearDown(self):self.tmp.cleanup()
    def test_one_hour_energy_and_boundary(self):
        fixture([row()],self.path)
        r=audit(self.path,1)
        self.assertEqual(r["PUE_simulated"],"1.2")
        self.assertEqual(r["integrated_mwh"]["HP_Source_Used_MW"],"3")
        self.assertIsNone(r["ERF"])
        self.assertEqual(r["data_class"],"SIMULATED_MODEL_OUTPUT_NOT_METERED")
    def test_two_hours(self):
        fixture([row(),row("01-Jan-2026 01:00:00")],self.path)
        r=audit(self.path,2)
        self.assertEqual(r["integrated_mwh"]["IT_MW"],"20")
        self.assertEqual(r["period_end_assumed_naive"],"2026-01-01T02:00:00")
    def test_gap(self):
        fixture([row(),row("01-Jan-2026 02:00:00")],self.path)
        with self.assertRaisesRegex(ValueError,"non-hourly"):audit(self.path)
    def test_duplicate_time(self):
        fixture([row(),row()],self.path)
        with self.assertRaisesRegex(ValueError,"duplicate"):audit(self.path)
    def test_negative(self):
        fixture([row(IT_MW="-1")],self.path)
        with self.assertRaisesRegex(ValueError,"negative"):audit(self.path)
    def test_nan(self):
        fixture([row(IT_MW="NaN")],self.path)
        with self.assertRaisesRegex(ValueError,"nonfinite"):audit(self.path)
    def test_valid_curtailed_heat(self):
        fixture([row(HP_Heat_MW="5",Curtailed_HP_Heat_MW="1")],self.path)
        r=audit(self.path)
        self.assertEqual(r["integrated_mwh"]["Curtailed_HP_Heat_MW"],"1")
    def test_wrong_balance(self):
        fixture([row(HP_Heat_MW="5")],self.path)
        with self.assertRaisesRegex(ValueError,"physical consistency"):audit(self.path)
    def test_exceeds_dc(self):
        fixture([row(IT_MW="20")],self.path)
        with self.assertRaisesRegex(ValueError,"physical consistency"):audit(self.path)
    def test_hp_source_exceeds_hx(self):
        fixture([row(HX_Heat_to_HP_MW="2")],self.path)
        with self.assertRaisesRegex(ValueError,"physical consistency"):audit(self.path)
    def test_wrong_count(self):
        fixture([row()],self.path)
        with self.assertRaisesRegex(ValueError,"expected 2"):audit(self.path,2)
    def test_truncated(self):
        self.path.write_text(",".join(HEAD)+"\n01-Jan-2026 00:00:00,10\n")
        with self.assertRaisesRegex(ValueError,"missing/truncated"):audit(self.path)
    def test_empty(self):
        self.path.write_text(",".join(HEAD)+"\n")
        with self.assertRaisesRegex(ValueError,"empty"):audit(self.path)
if __name__=="__main__":unittest.main()
