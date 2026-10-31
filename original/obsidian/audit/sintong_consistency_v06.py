"""Mathematical consistency smoke tests for formula transcriptions.
Do not infer authors' intent or declare source error without page-image verification.
"""
import json,math,unittest
from pathlib import Path

def test_outputs():
    mass_flow=1.0; cp_air=1005.0; supply=20.0; exhaust=35.0
    eq22_as_extracted=mass_flow*cp_air*(supply-exhaust)
    positive_heat_removed=mass_flow*cp_air*(exhaust-supply)
    source=7.2; electrical=2.8; transmission_eff=0.97
    generated=source+electrical
    eq24_as_extracted=source+electrical/transmission_eff
    physically_delivered=generated*transmission_eff
    # Alternative constraint for free cooling, mass OA=3xRA, epsilon=.8
    t_return=35;t_outdoor=5; m_oa=3;m_ra=1; eps=.8
    hx_flow_ratio=(m_oa+m_ra)/(2*m_ra)
    t_star=t_return+eps*hx_flow_ratio*(t_outdoor-t_return)
    # Seasonal method: energy-weighted, not arithmetic avg COP.
    thermal=[10.,10.];power=[2.,5.]
    seasonal=sum(thermal)/sum(power)
    arithmetic=sum(q/p for q,p in zip(thermal,power))/len(power)
    return {
        "eq22_as_extracted_W":eq22_as_extracted,"physical_load_positive_W":positive_heat_removed,
        "generated_HP_MW":generated,"eq24_as_extracted_MW":eq24_as_extracted,
        "physically_delivered_MW":physically_delivered,
        "free_cooling_tra_star_C":t_star,"outside_C":t_outdoor,"return_C":t_return,
        "seasonal_ratio":seasonal,"arithmetic_mean_hourly_COP":arithmetic
    }

class TestSignAndDimensions(unittest.TestCase):
    def test_negative_sign_issue(self):
        d=test_outputs()
        self.assertAlmostEqual(d["eq22_as_extracted_W"],-15075)
        self.assertAlmostEqual(d["physical_load_positive_W"],15075)
        self.assertTrue(d["eq22_as_extracted_W"]<0<d["physical_load_positive_W"])
    def test_loss_accounting_issue(self):
        d=test_outputs()
        self.assertAlmostEqual(d["generated_HP_MW"],10)
        self.assertAlmostEqual(d["physically_delivered_MW"],9.7)
        self.assertGreater(d["eq24_as_extracted_MW"],d["generated_HP_MW"])
    def test_free_cooling_outlet_overshoot_possible(self):
        d=test_outputs()
        self.assertLess(d["free_cooling_tra_star_C"],d["outside_C"])
        # This violates passive two-fluid HX outlet temperature constraints
    def test_seasonal_ratio_is_weighted(self):
        d=test_outputs()
        self.assertNotAlmostEqual(d["seasonal_ratio"],d["arithmetic_mean_hourly_COP"])
    def test_cashflow_mw_to_eur_needs_hours(self):
        power_mw=10.;price_eur_per_mwh=50.;dt_h=.25
        self.assertAlmostEqual(power_mw*price_eur_per_mwh*dt_h,125)
        self.assertNotAlmostEqual(power_mw*price_eur_per_mwh,125)

if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestSignAndDimensions)
    res=unittest.TestResult();suite.run(res)
    out={"tests_run":res.testsRun,"failures":len(res.failures),"errors":len(res.errors),
         "passed":res.wasSuccessful(),"test_vectors":test_outputs(),
         "interpretation":"Detected sign/energy/temperature/KPI formula vulnerabilities in an extracted thesis representation, not proved publication errors. Visual source confirmation required."}
    Path(__file__).with_name("sintong_consistency_v06.json").write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(out,indent=2,ensure_ascii=False),flush=True)
    if not res.wasSuccessful():raise SystemExit(1)
