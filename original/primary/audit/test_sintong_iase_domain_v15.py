"""Independent endpoint-energy verification and scenario domain comparison.

No MATLAB runtime, original-author simulation, or calibrated performance claim.
Exact rational arithmetic tests the domain independently of float diagnostics.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction as F
import csv
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import unittest

from sintong_iase_domain_v15 import epsilon_limit, source_diagnostic, passive_reference

ROOT = Path(__file__).resolve().parents[1]
SEED = 15026
RATIOS = [F(1,20), F(1,10), F(1,5), F(1,4), F(1,2), F(1),
          F(2), F(3), F(5), F(10), F(20)]


class DomainTests(unittest.TestCase):
    def test_hidden_outdoor_violation_at_supply_setpoint(self):
        d = source_diagnostic(35, 5, 1, .25, .8)
        self.assertEqual(d.return_out_C, 20)
        self.assertEqual(d.outdoor_out_C, 65)
        self.assertEqual(d.heat_from_return_W, 15075)
        self.assertEqual(d.max_passive_heat_magnitude_W, 7537.5)
        self.assertTrue(d.return_envelope_pass)
        self.assertFalse(d.outdoor_envelope_pass)
        self.assertFalse(d.endpoint_energy_pass)

    def test_high_flow_return_overshoot(self):
        d = source_diagnostic(35, 5, 1, 3, .8)
        self.assertAlmostEqual(d.return_out_C, -13)
        self.assertAlmostEqual(d.outdoor_out_C, 21)
        self.assertAlmostEqual(d.heat_from_return_W, 48240)
        self.assertFalse(d.return_envelope_pass)
        self.assertTrue(d.outdoor_envelope_pass)

    def test_hand_derived_boundaries_and_balanced_case(self):
        for r, e, tr, to, q in [(.25,.4,27.5,35,7537.5),
                                 (4,.4,5,12.5,30150), (1,.8,11,29,24120)]:
            with self.subTest(r=r):
                d = source_diagnostic(35,5,1,r,e)
                self.assertAlmostEqual(d.return_out_C,tr)
                self.assertAlmostEqual(d.outdoor_out_C,to)
                self.assertAlmostEqual(d.heat_from_return_W,q)
                self.assertTrue(d.endpoint_energy_pass)

    def test_exact_rational_envelope_matches_derived_bound(self):
        # Compute both outlets directly as Fractions, independent of module.
        # 11 ratios x 61 coefficients x 2 inlet orderings = 1342 exact points.
        for r in RATIOS:
            bound = 2 * min(F(1),r) / (1+r)
            for e in [F(i,30) for i in range(61)]:
                for tr,to in [(F(35),F(5)),(F(5),F(35))]:
                    alpha = e*(1+r)/2
                    ra = tr+alpha*(to-tr)
                    oa = to+alpha/r*(tr-to)
                    envelope = min(tr,to)<=ra<=max(tr,to) and min(tr,to)<=oa<=max(tr,to)
                    self.assertEqual(envelope, e<=bound, (r,e,tr,to))
            self.assertAlmostEqual(epsilon_limit(float(r)),float(bound))

    def test_alternative_notation_exact_bound(self):
        # Alternative extra-r interpretation only; not a paper transcription.
        for r in RATIOS:
            bound = 2*min(F(1),r)/(r*(1+r))
            for e in [F(i,30) for i in range(61)]:
                alpha = e*r*(1+r)/2
                ra = 35-alpha*30
                oa = 5+alpha/r*30
                self.assertEqual(5<=ra<=35 and 5<=oa<=35,e<=bound,(r,e))
            self.assertAlmostEqual(epsilon_limit(float(r),"literal_r_product"),float(bound))
        a = source_diagnostic(35,5,1,2,.5,interpretation="literal_r_product")
        self.assertAlmostEqual(a.alpha,1.5)
        self.assertFalse(a.endpoint_energy_pass)

    def test_fixed_epsilon_interval_by_exact_inversion(self):
        # e=.7 => r in [7/13,13/7]; e=.8 => r in [2/3,3/2].
        for e,lo,hi in [(F(7,10),F(7,13),F(13,7)),(F(4,5),F(2,3),F(3,2))]:
            for r in [lo/2,lo, F(1),hi,hi*2]:
                self.assertEqual(e*(1+r)/2<=min(F(1),r),lo<=r<=hi)

    def test_zero_temperature_difference_is_degenerate(self):
        d = source_diagnostic(20,20,1,.1,3)
        self.assertTrue(d.equal_inlets)
        self.assertTrue(d.endpoint_energy_pass)
        self.assertEqual(d.heat_from_return_W,0)
        self.assertEqual(d.return_out_C,d.outdoor_out_C)

    def test_passive_reference_unequal_cp_manual_case(self):
        # CR=2000 W/K, CO=500 W/K, dT30 K, epsQ .8 => Q12000 W.
        d = passive_reference(35,5,2,.5,.8,1000,1000)
        self.assertEqual(d['heat_from_return_W'],12000)
        self.assertEqual(d['return_out_C'],29)
        self.assertEqual(d['outdoor_out_C'],29)
        u = passive_reference(35,5,1,.5,.8,2000,1000)
        self.assertEqual(d,u)

    def test_reference_handles_zero_outdoor_flow_by_bypass(self):
        d = passive_reference(35,5,1,0,.8)
        self.assertEqual(d['heat_from_return_W'],0)
        self.assertEqual(d['return_out_C'],35)
        self.assertEqual(d['outdoor_out_C'],5)
        with self.assertRaises(ValueError):
            source_diagnostic(35,5,1,0,.8)

    def test_balanced_source_and_reference_agree(self):
        for e in [0,.4,.7,1]:
            a = source_diagnostic(35,5,1,1,e)
            b = passive_reference(35,5,1,1,e)
            for field in ['return_out_C','outdoor_out_C','heat_from_return_W']:
                self.assertAlmostEqual(getattr(a,field),b[field])

    def test_normalization_conversion_on_admissible_point(self):
        # Mean-capacity coefficient .4 at r=.25 corresponds to epsQ=1.
        a = source_diagnostic(35,5,1,.25,.4)
        b = passive_reference(35,5,1,.25,1)
        self.assertEqual(a.heat_from_return_W,b['heat_from_return_W'])
        self.assertEqual(a.return_out_C,b['return_out_C'])
        self.assertEqual(a.outdoor_out_C,b['outdoor_out_C'])

    def test_random_endpoint_energy_and_entropy_reference(self):
        rng = random.Random(SEED)
        for _ in range(2000):
            tr,to = rng.uniform(-30,70),rng.uniform(-30,70)
            mr,mo = 10**rng.uniform(-2,2),10**rng.uniform(-2,2)
            cpr,cpo = rng.uniform(800,1200),rng.uniform(800,1200)
            e = rng.random()
            d = passive_reference(tr,to,mr,mo,e,cpr,cpo)
            q,cr,co = d['heat_from_return_W'],d['C_return_W_K'],d['C_outdoor_W_K']
            self.assertAlmostEqual(q,cr*(tr-d['return_out_C']),delta=1e-8*max(1,abs(q)))
            self.assertAlmostEqual(q,co*(d['outdoor_out_C']-to),delta=1e-8*max(1,abs(q)))
            for field in ['return_out_C','outdoor_out_C']:
                self.assertTrue(min(tr,to)-1e-10<=d[field]<=max(tr,to)+1e-10)
            sgen = cr*math.log((d['return_out_C']+273.15)/(tr+273.15))
            sgen += co*math.log((d['outdoor_out_C']+273.15)/(to+273.15))
            self.assertGreaterEqual(sgen,-1e-8*max(cr,co))

    def test_diagnostic_classification_matches_direct_outlets(self):
        rng = random.Random(SEED+1)
        for _ in range(1000):
            r,e = 10**rng.uniform(-2,2),rng.uniform(0,1)
            d = source_diagnostic(35,5,1,r,e)
            self.assertEqual(d.return_envelope_pass,5<=d.return_out_C<=35)
            self.assertEqual(d.outdoor_envelope_pass,5<=d.outdoor_out_C<=35)
            self.assertEqual(d.endpoint_energy_pass,abs(d.heat_from_return_W)<=d.max_passive_heat_magnitude_W)

    def test_invalid_scalar_inputs(self):
        for args in [(True,5,1,1,.7),(35,5,[1],1,.7),(35,5,1,1,float('nan')),
                     (35,5,1,1,complex(1,1)),(35,float('inf'),1,1,.7)]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                source_diagnostic(*args)

    def test_invalid_physical_domains(self):
        for args in [(-273.15,5,1,1,.7),(35,5,0,1,.7),(35,5,1,-1,.7),
                     (35,5,1,1,-.1),(35,5,1,1,.7,0)]:
            with self.subTest(args=args),self.assertRaises(ValueError):
                source_diagnostic(*args)
        for e in [-.1,1.1,float('inf')]:
            with self.assertRaises(ValueError):
                passive_reference(35,5,1,1,e)
        with self.assertRaises(ValueError):
            epsilon_limit(1,"invented")


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%S_%fZ")
    log = ROOT / f"automation/logs/Sintong_IASE_tests_v15_{stamp}.log"
    with log.open('x',encoding='utf-8') as stream:
        stream.write(f"UTC {now.isoformat()}\nCategory: mathematical source-domain diagnostic and independent sensible-HX endpoint reference\n")
        result = unittest.TextTestRunner(stream=stream,verbosity=2).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(DomainTests))
    records = []
    for r in RATIOS:
        for e in [.4,.7,.8]:
            for interpretation in ['flow_function','literal_r_product']:
                d = source_diagnostic(35,5,1,float(r),e,interpretation=interpretation)
                b = passive_reference(35,5,1,float(r),e)
                records.append({'interpretation':interpretation,'epsilon_coefficient':e,
                                **asdict(d),
                                'source_meets_20C_setpoint':d.return_out_C<=20,
                                'reference_epsilon_Q':e,
                                **{f'reference_{k}':v for k,v in b.items()}})
    csv_path = ROOT / f"audit/Sintong_IASE_domain_comparison_v15_{stamp}.csv"
    with csv_path.open('x',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]))
        writer.writeheader(); writer.writerows(records)
    evidence = ROOT / f"audit/Sintong_IASE_tests_v15_{stamp}.json"
    sources = [Path(__file__).resolve(),ROOT/'audit/sintong_iase_domain_v15.py']
    data = {'timestamp_utc':now.isoformat(),'version':'0.15',
            'category':'mathematical_domain_audit_not_author_simulation',
            'tests_run':result.testsRun,
            'passed':result.testsRun-len(result.failures)-len(result.errors),
            'failed':len(result.failures),'errors':len(result.errors),
            'failure_details':[v for _,v in result.failures+result.errors],
            'random_seed':SEED,'random_reference_cases':2000,'random_diagnostic_cases':1000,
            'exact_primary_interpretation_cases':1342,'exact_alternative_cases':671,
            'comparison_vectors':len(records),
            'source_coefficient_values_are_scenarios':True,
            'alternative_interpretation_is_primary_verified':False,
            'paper_replication':False,'matlab_executed':False,'simulink_executed':False,
            'stateflow_executed':False,
            'source_sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
            'log':log.relative_to(ROOT).as_posix(),'comparison':csv_path.relative_to(ROOT).as_posix(),
            'equations':{'alpha_flow_function':'epsilon*(1+r)/2',
                         'two_outlet_bound':'0<=alpha<=min(1,r)',
                         'epsilon_bound':'2*min(1,r)/(1+r)',
                         'fixed_epsilon_interval':'epsilon/(2-epsilon)<=r<=(2-epsilon)/epsilon for 0<epsilon<=1',
                         'independent_reference':'Q=epsilon_Q*min(C_RA,C_OA)*(T_RA-T_OA)'},
            'limitations':['Thesis notation and epsilon normalization need author-code/upstream provenance resolution',
                           'No UA, geometry, moist-air, fan work, leakage, frost or calibrated controller',
                           'Reference uses a different defined normalization; it is not a source correction']}
    with evidence.open('x',encoding='utf-8') as stream:
        json.dump(data,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'passed':data['passed'],'failed':data['failed'],'errors':data['errors'],
                      'evidence':evidence.relative_to(ROOT).as_posix(),
                      'comparison':csv_path.relative_to(ROOT).as_posix(),'log':data['log']}))
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__':
    sys.exit(main())
