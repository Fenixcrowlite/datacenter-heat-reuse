import unittest, math
from thermal_n1 import (advance,simulate,Policy,POLICIES,CAPACITIES,
                        DT_S,C_IT_J_K,T_FLOOR_C,T_ALARM_C)

def row(h,required=200000,qdc=220000,unhandled=0):
    return dict(cas_h=h,Q_reject_required_W=required,Q_DC_eff_W=qdc,Q_unhandled_W=unhandled)

class ThermalN1Tests(unittest.TestCase):
    def test_v07_recurrence_no_shedding(self):
        r=advance(200000,220000,150000,30,0,POLICIES["no_shed"])
        self.assertAlmostEqual(r["unhandled_W"],50000)
        self.assertAlmostEqual(r["T_IT_next_C"],35.625)
    def test_v07_passive_cooling(self):
        r=advance(200000,220000,150000,35,0,POLICIES["no_shed"])
        self.assertAlmostEqual(r["passive_W"],10000)
        self.assertAlmostEqual(r["T_IT_next_C"],39.5)
    def test_ideal_prevents_unhandled_with_sufficient_fraction(self):
        r=advance(200000,220000,150000,30,0,POLICIES["ideal_40pct"])
        self.assertAlmostEqual(r["shed_W"],50000)
        self.assertEqual(r["unhandled_W"],0)
        self.assertEqual(r["T_IT_next_C"],30)
    def test_ramp_causes_transient(self):
        r=advance(200000,220000,150000,30,0,POLICIES["ramp15k_40pct"])
        self.assertAlmostEqual(r["shed_W"],15000)
        self.assertAlmostEqual(r["unhandled_W"],35000)
        self.assertAlmostEqual(r["T_IT_next_C"],33.9375)
    def test_shed_fraction_bounded(self):
        r=advance(200000,100000,0,30,0,POLICIES["ideal_40pct"])
        self.assertEqual(r["shed_W"],40000)
        self.assertEqual(r["unhandled_W"],160000)
    def test_full_capacity_no_shed(self):
        r=advance(200000,220000,330000,30,0,POLICIES["ramp15k_40pct"])
        self.assertEqual(r["shed_W"],0)
        self.assertEqual(r["unhandled_W"],0)
    def test_reject_conservation(self):
        for req in (0,50000,200000):
            for cap in CAPACITIES.values():
                for pol in POLICIES.values():
                    r=advance(req,220000,cap,30,0,pol)
                    self.assertAlmostEqual(req,r["shed_W"]+r["reject_actual_W"]+r["unhandled_W"])
    def test_floor(self):
        r=advance(0,100000,0,40,0,POLICIES["no_shed"])
        self.assertGreaterEqual(r["T_IT_next_C"],30)
    def test_alarm(self):
        r=advance(200000,220000,0,41,0,POLICIES["no_shed"])
        self.assertEqual(r["alarm_next"],1)
        self.assertGreater(r["T_IT_next_C"],T_ALARM_C)
    def test_pre_fault_uses_both_branches(self):
        trace=simulate([row(23.75),row(24.0)],POLICIES["no_shed"],0)
        self.assertEqual(trace[0]["fault_capacity_W"],330000)
        self.assertEqual(trace[0]["unhandled_W"],0)
        self.assertEqual(trace[1]["fault_capacity_W"],0)
    def test_timestamp_gap_rejected(self):
        with self.assertRaisesRegex(ValueError,"15-minute"):
            simulate([row(0),row(0.5)],POLICIES["no_shed"],0)
    def test_existing_unhandled_rejected(self):
        with self.assertRaisesRegex(ValueError,"baseline unhandled"):
            simulate([row(0,unhandled=1)],POLICIES["no_shed"],0)
    def test_negative_and_nonfinite_rejected(self):
        for v in (-1,float("nan"),float("inf")):
            with self.assertRaises(ValueError):
                advance(v,220000,0,30,0,POLICIES["no_shed"])
    def test_bad_fraction_rejected(self):
        with self.assertRaises(ValueError):
            Policy("bad",1.01)
    def test_ramp_up_and_down(self):
        p=Policy("ramp",1.0,15000)
        a=advance(200000,220000,0,30,0,p)
        b=advance(200000,220000,0,30,a["shed_W"],p)
        c=advance(0,220000,0,30,b["shed_W"],p)
        self.assertEqual(a["shed_W"],15000)
        self.assertEqual(b["shed_W"],30000)
        self.assertEqual(c["shed_W"],0) # cannot shed more than remaining demand
    def test_model_source_validation(self):
        from run_a37 import read_inputs
        rows,meta,p=read_inputs()
        self.assertEqual(len(rows),672)
        self.assertEqual(float(rows[0]["cas_h"]),0.0)
        self.assertEqual(float(rows[-1]["cas_h"]),167.75)

if __name__=="__main__":
    unittest.main()
