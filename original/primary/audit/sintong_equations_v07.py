"""Source-faithful extraction tests for Sintong (2023), pages 32-33.
Tests printed mathematical relationships, not endorsement of all boundaries.
"""
import json,math,random,unittest
from pathlib import Path

def source_crossflow_epsilon(c_hot_mw_k, c_cold_mw_k, ua_mw_k):
    for v in (c_hot_mw_k,c_cold_mw_k,ua_mw_k):
        if not math.isfinite(v) or v < 0: raise ValueError("capacities,UA>=0")
    if min(c_hot_mw_k,c_cold_mw_k,ua_mw_k) == 0: return 0.
    cmin=min(c_hot_mw_k,c_cold_mw_k)
    cr=cmin/max(c_hot_mw_k,c_cold_mw_k)
    ntu=ua_mw_k/cmin
    # Sintong Eq.17, unmixed cross-flow, printed PDF p.32;
    # Eq.18 used for Cmin/Cmax <= 0.01.
    if cr <= .01:
        eps=-math.expm1(-ntu)
    else:
        a=-cr*ntu**.78
        exponent=ntu**.22*math.expm1(a)/cr
        eps=-math.expm1(exponent)
    return eps

def source_crossflow_hx(t_hot,t_cold,c_hot,c_cold,ua):
    eps=source_crossflow_epsilon(c_hot,c_cold,ua)
    if t_hot <= t_cold or eps==0: return (0.,t_hot,t_cold,eps)
    q=eps*min(c_hot,c_cold)*(t_hot-t_cold)
    return q,t_hot-q/c_hot,t_cold+q/c_cold,eps

class TestPrintedEquations(unittest.TestCase):
    def test_eq17_both_unmixed_formula(self):
        ch=.02;cc=.01;ua=.019;cr=.5;ntu=1.9
        expected=1-math.exp(ntu**.22/cr*(math.exp(-cr*ntu**.78)-1))
        self.assertAlmostEqual(source_crossflow_epsilon(ch,cc,ua),expected,places=13)
    def test_eq18_small_capacity_ratio(self):
        self.assertAlmostEqual(source_crossflow_epsilon(1,.001,.001),1-math.exp(-1))
    def test_eq17_ntu_zero(self):
        self.assertEqual(source_crossflow_epsilon(.1,.2,0),0)
    def test_eq19_20_hx_conservation(self):
        q,th,tc,eps=source_crossflow_hx(35,20,.015,.030,.019)
        self.assertAlmostEqual(q,.015*(35-th),places=12)
        self.assertAlmostEqual(q,.030*(tc-20),places=12)
        self.assertTrue(0<eps<1)
        self.assertGreaterEqual(th,20)
        self.assertLessEqual(tc,35)
    def test_crossflow_random_1000(self):
        r=random.Random(119)
        for _ in range(1000):
            ch=10**r.uniform(-4,0); cc=10**r.uniform(-4,0); ua=10**r.uniform(-5,.5)
            ep=source_crossflow_epsilon(ch,cc,ua)
            self.assertTrue(0<=ep<=1+1e-12,(ch,cc,ua,ep))
            q,th,tc,_=source_crossflow_hx(40,15,ch,cc,ua)
            self.assertAlmostEqual(q,ch*(40-th),delta=1e-10)
            self.assertAlmostEqual(q,cc*(tc-15),delta=1e-10)
            self.assertGreaterEqual(th,15-1e-8)
            self.assertLessEqual(tc,40+1e-8)
    def test_eq22_printed_sign_with_positive_hot_aisle(self):
        m=1.;cp=1005;t_sa=20;t_server_out=35
        published=m*cp*(t_sa-t_server_out)
        self.assertAlmostEqual(published,-15075)
        self.assertAlmostEqual(-published,15075)
    def test_eq24_visual_multiply_not_divide(self):
        qevap=7.2;pel=2.8;eta=.97
        printed=qevap+pel*eta
        physical_hot=qevap+pel
        delivered_if_full_line_loss=eta*physical_hot
        self.assertAlmostEqual(printed,9.916,places=10)
        self.assertAlmostEqual(delivered_if_full_line_loss,9.7)
        self.assertAlmostEqual(printed-delivered_if_full_line_loss,.216)
        self.assertLess(printed,physical_hot)
    def test_eq25_cop_boundary(self):
        qevap=7.2;pel=2.8;eta=.97
        self.assertAlmostEqual((qevap+pel*eta)/pel,3.5414285714285714)
        self.assertAlmostEqual((qevap+pel)/pel,3.5714285714285716)
    def test_invalid_capacity(self):
        for values in [(-1,.1,.1),(.1,float('nan'),.1),(.1,.1,-.1)]:
            with self.assertRaises(ValueError):source_crossflow_epsilon(*values)
if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestPrintedEquations)
    result=unittest.TestResult();suite.run(result)
    status={'paper':'Sintong 2023 pp.32-33','tests':result.testsRun,
      'status':'PASS' if result.wasSuccessful() else 'FAIL',
      'failed':[v for _,v in result.failures],
      'errors':[v for _,v in result.errors],
      'meaning':'Printed-formula verification incl. 1000 random crossflow trials; no independent paper replication'}
    Path(__file__).with_name('sintong_equations_tests_v07.json').write_text(json.dumps(status,indent=2),encoding='utf8')
    print(json.dumps(status))
    if not result.wasSuccessful():raise SystemExit(1)
