"""Independent v14 HP checks and immutable MATLAB comparison-vector export.

Run from the project: python audit/test_heat_pump_reference_v14.py.
Every run saves a timestamped log, JSON evidence, and (on pass) CSV vectors.
These tests execute Python only; MATLAB and primary-paper validation are not
claimed. The quadratic reference is independent of the MATLAB root search.
"""
from __future__ import annotations

import csv
from dataclasses import asdict, replace
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import unittest

from heat_pump_reference_v14 import HeatPumpParameters as P, heat_pump_step as step

ROOT = Path(__file__).resolve().parents[1]
SEED = 14026


def vectors() -> list[tuple[str, float, float, float, float, P]]:
    default = P()
    threshold = P(capacity_MW=10, carnot_efficiency=1, cop_min=4.5,
                  cop_max=6, part_load_penalty=0.5)
    rounded_threshold = P(capacity_MW=47.2168758922395, cop_max=3.1241842071393187,
                          cop_min=2.8777279484625278, part_load_penalty=0.5840613219340423)
    cases = [
        ("hand_35_70_no_penalty", 5, 35, 70, 12, replace(default, part_load_penalty=0)),
        ("part_load_source_bound", 5, 32, 70, 12, default),
        ("capacity_bound", 50, 32, 70, 50, default),
        ("request_bound", 50, 32, 70, 4, default),
        ("carnot_infeasible_legacy_floor", 5, -100, 80, 12, default),
        ("raw_between_one_and_cutoff", 5, -20, 70, 12, default),
        ("positive_subkelvin_lift", 5, 35, 35.5, 12, default),
        ("cutoff_request_below", 20, -23.15, 26.85, 4.9, threshold),
        ("cutoff_request_at", 20, -23.15, 26.85, 5, threshold),
        ("cutoff_source_below", 3.8, -23.15, 26.85, 10, threshold),
        ("cutoff_source_at", 35/9, -23.15, 26.85, 10, threshold),
        ("cutoff_source_above", 4, -23.15, 26.85, 10, threshold),
        ("cutoff_roundoff_at", 50, 35, 70, 40.839499934205705, rounded_threshold),
        ("off_zero_source", 0, 35, 70, 12, default),
        ("off_zero_request", 5, 35, 70, 0, default),
        ("off_zero_capacity", 5, 35, 70, 12, replace(default, capacity_MW=0)),
        ("penalty_near_one", 5, 35, 70, 12, replace(default, part_load_penalty=0.99)),
        ("reversible_cap_full_load", 20, -23.15, 26.85, 10,
         replace(threshold, cop_min=1.01, part_load_penalty=0)),
    ]
    rng = random.Random(SEED)
    for i in range(500):
        source_c = rng.uniform(-120, 80)
        sink_c = source_c + rng.uniform(0.05, 200)
        capacity = rng.uniform(0.01, 50)
        maximum = rng.uniform(3, 12)
        minimum = rng.uniform(1.01, min(4.0, maximum))
        p = P(capacity_MW=capacity, carnot_efficiency=rng.uniform(0.1, 1),
              cop_min=minimum, cop_max=maximum, part_load_penalty=rng.uniform(0, 0.99))
        cases.append((f"random_{i:03d}", rng.uniform(0.001, 50), source_c, sink_c,
                      rng.uniform(0.001, 2*capacity), p))
    return cases


class ReferenceTests(unittest.TestCase):
    def assertClose(self, value: float, expected: float, tol: float = 1e-10) -> None:
        self.assertLessEqual(abs(value-expected), tol*max(1, abs(expected)))

    def test_hand_first_law_no_penalty_exact_rational(self):
        c = Fraction(9, 20) * Fraction(34315, 100) / 35
        q = 5*c/(c-1)
        result = step(5, 35, 70, 12, P(part_load_penalty=0))
        self.assertTrue(result.available)
        self.assertClose(result.cop_raw, float(c))
        self.assertClose(result.heat_output_MW, float(q))
        self.assertClose(result.electric_MW, float(q/c))
        self.assertClose(result.source_used_MW, 5)

    def test_hand_nonzero_penalty_exact_integer_quadratic(self):
        # Th=300K,Tc=250K,Cnom=6,p=1/2,cap=10 => C=3+0.3Q.
        # With S=4: 0.3Q^2+0.8Q-12=0 => Q=(-8+sqrt(1504))/6.
        p = P(capacity_MW=10, carnot_efficiency=1, cop_min=1.01,
              cop_max=6, part_load_penalty=0.5)
        q = (-8 + math.sqrt(1504))/6
        result = step(4, -23.15, 26.85, 10, p)
        self.assertClose(result.heat_output_MW, q)
        self.assertClose(result.cop_operating, 3 + .3*q)
        self.assertClose(result.source_used_MW, 4)

    def test_large_lift_does_not_apply_upward_floor(self):
        result = step(5, -100, 80, 12)
        self.assertClose(result.cop_carnot, 353.15/180)
        self.assertClose(result.cop_raw, .45*353.15/180)
        self.assertFalse(result.available)
        self.assertTrue(math.isnan(result.cop_operating))
        self.assertEqual(result.heat_output_MW, 0)
        self.assertGreater(2.2, result.cop_carnot)

    def test_legacy_floor_has_negative_reservoir_entropy(self):
        q = 5*2.2/(2.2-1)
        entropy = q/353.15 - 5/173.15
        self.assertLess(entropy, 0)
        self.assertClose(entropy, -.002919832095140549)

    def test_positive_subkelvin_lift_is_not_changed_to_one_kelvin(self):
        result = step(5, 35, 35.5, 12)
        self.assertEqual(result.lift_K, .5)
        self.assertClose(result.cop_raw, .45*308.65/.5)
        self.assertEqual(result.cop_nominal, 7)

    def test_cutoff_uses_unavailable_instead_of_floor(self):
        p = P(capacity_MW=10, carnot_efficiency=1, cop_min=4.5,
              cop_max=6, part_load_penalty=.5)
        for source, request in [(20, 4.9), (3.8, 10)]:
            self.assertFalse(step(source, -23.15, 26.85, request, p).available)
        for source, request in [(20, 5), (35/9, 10)]:
            result = step(source, -23.15, 26.85, request, p)
            self.assertTrue(result.available)
            self.assertClose(result.heat_output_MW, 5)
            self.assertClose(result.cop_operating, 4.5)

    def test_downward_upper_cap(self):
        p = P(cop_min=1.01, cop_max=3, part_load_penalty=0)
        result = step(5, 35, 70, 12, p)
        self.assertGreater(result.cop_raw, 3)
        self.assertEqual(result.cop_nominal, 3)
        self.assertEqual(result.cop_operating, 3)

    def test_exact_cutoff_request_survives_one_ulp_cop_roundoff(self):
        p = P(capacity_MW=47.2168758922395, cop_max=3.1241842071393187,
              cop_min=2.8777279484625278, part_load_penalty=0.5840613219340423)
        request = 40.839499934205705
        result = step(50, 35, 70, request, p)
        self.assertTrue(result.available)
        self.assertClose(result.heat_output_MW, request)
        self.assertClose(result.cop_operating, p.cop_min, 1e-14)

    def test_zero_source_request_capacity_have_no_operating_cop(self):
        for source, request, p in [(0, 10, P()), (5, 0, P()), (5, 10, P(capacity_MW=0))]:
            result = step(source, 35, 70, request, p)
            self.assertFalse(result.available)
            self.assertTrue(math.isnan(result.cop_operating))
            self.assertEqual((result.heat_output_MW,result.electric_MW,result.source_used_MW),(0,0,0))

    def test_all_vectors_obey_first_and_second_laws_and_maximal_output(self):
        available = unavailable = 0
        for label, source, tc, th, request, p in vectors():
            with self.subTest(case=label):
                r = step(source, tc, th, request, p)
                self.assertLessEqual(r.heat_output_MW, min(request,p.capacity_MW)+1e-9)
                self.assertLessEqual(r.source_used_MW, source+1e-9)
                self.assertClose(r.heat_output_MW, r.electric_MW+r.source_used_MW)
                if r.available:
                    available += 1
                    self.assertGreater(r.cop_operating, 1)
                    self.assertGreaterEqual(r.cop_operating, p.cop_min-1e-11)
                    self.assertLessEqual(r.cop_operating, r.cop_carnot+1e-11)
                    entropy = r.heat_output_MW/(th+273.15)-r.source_used_MW/(tc+273.15)
                    self.assertGreaterEqual(entropy, -1e-10)
                    qhi = min(request,p.capacity_MW)
                    if r.heat_output_MW < qhi-1e-7:
                        # A slightly greater candidate remains above the COP cutoff
                        # but must violate available source if the solution is maximal.
                        q = min(qhi,r.heat_output_MW+1e-5)
                        c = r.cop_nominal*(1-p.part_load_penalty*(1-q/p.capacity_MW))
                        self.assertGreater(q-q/c, source)
                else:
                    unavailable += 1
                    self.assertEqual(r.heat_output_MW,0)
                    self.assertTrue(math.isnan(r.cop_operating))
                    if source>0 and request>0 and p.capacity_MW>0 and r.cop_nominal>=p.cop_min:
                        qhi=min(request,p.capacity_MW)
                        a=r.cop_nominal*(1-p.part_load_penalty)
                        b=r.cop_nominal*p.part_load_penalty/p.capacity_MW
                        qlo=max(0,(p.cop_min-a)/b) if b>0 else 0
                        self.assertTrue(qhi<qlo or qlo-qlo/(a+b*qlo)>source)
        self.assertGreater(available, 50)
        self.assertGreater(unavailable, 50)

    def test_reject_invalid_temperatures(self):
        for tc,th in [(35,35),(40,35),(-273.15,70),(-300,70),(35,float('nan'))]:
            with self.subTest(tc=tc,th=th), self.assertRaises(ValueError):
                step(5,tc,th,12)

    def test_reject_invalid_scalar_inputs(self):
        for arguments in [(-1,35,70,12),(5,35,70,-1),(float('inf'),35,70,12),
                          (True,35,70,12),([5],35,70,12),(5,35,70,complex(1,1))]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                step(*arguments)

    def test_reject_invalid_parameter_domains(self):
        for kwargs in [{"capacity_MW":-1},{"capacity_MW":float('nan')},
                       {"carnot_efficiency":0},{"carnot_efficiency":1.01},
                       {"cop_min":1},{"cop_max":2},{"part_load_penalty":-.1},
                       {"part_load_penalty":1},{"backend":"misspelled"}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                P(**kwargs)

    def test_polynomial_above_carnot_is_rejected(self):
        p=P(backend="lift_polynomial",poly_c0=7,poly_c1=0,poly_c2=0)
        with self.assertRaises(ValueError):
            step(5,-100,80,12,p)

    def test_polynomial_within_carnot_is_supported(self):
        p=P(backend="lift_polynomial",poly_c0=3,poly_c1=0,poly_c2=0,
            part_load_penalty=0)
        result=step(5,35,70,12,p)
        self.assertTrue(result.available)
        self.assertEqual(result.cop_raw,3)
        self.assertClose(result.heat_output_MW,7.5)

    def test_nominal_source_limit_is_conservative_under_penalty(self):
        p=P()
        r=step(5,32,70,12,p)
        old_q=5*r.cop_nominal/(r.cop_nominal-1)
        old_c=r.cop_nominal*(1-p.part_load_penalty*(1-old_q/p.capacity_MW))
        old_source=old_q*(1-1/old_c)
        self.assertLess(old_source,5)
        self.assertGreater(r.heat_output_MW,old_q)
        self.assertClose(r.source_used_MW,5)


def main() -> int:
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    log=ROOT/"automation/logs"/f"hp_reference_v14_{stamp}.log"
    evidence=ROOT/"audit"/f"heat_pump_reference_tests_v14_{stamp}.json"
    vector_path=ROOT/"audit"/f"heat_pump_vectors_v14_{stamp}.csv"
    log.parent.mkdir(parents=True,exist_ok=True)
    with log.open("x",encoding="utf-8") as stream:
        stream.write(f"UTC timestamp: {stamp}\nCategory: independent Python mathematical reference; not MATLAB runtime or paper replication\n")
        suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReferenceTests)
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    cases=vectors()
    records=[]
    if result.wasSuccessful():
        for label,source,tc,th,request,p in cases:
            r=step(source,tc,th,request,p)
            records.append({"case_id":label,"q_source_MW":source,"source_C":tc,"sink_C":th,
                            "request_MW":request,"capacity_MW":p.capacity_MW,
                            "carnot_efficiency":p.carnot_efficiency,"cop_min":p.cop_min,
                            "cop_max":p.cop_max,"part_load_penalty":p.part_load_penalty,
                            **{f"expected_{k}":v for k,v in asdict(r).items()}})
        with vector_path.open("x",encoding="utf-8",newline="") as stream:
            writer=csv.DictWriter(stream,fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    sources=[Path(__file__).resolve(),ROOT/"audit/heat_pump_reference_v14.py"]
    data={"version":"0.14","timestamp_utc":stamp,
          "category":"independent_analytical_heat_pump_reference",
          "not_matlab_runtime_validation":True,"not_primary_paper_replication":True,
          "tests_run":result.testsRun,"passed":result.testsRun-len(result.failures)-len(result.errors),
          "failed":len(result.failures),"errors":len(result.errors),
          "random_seed":SEED,"comparison_vectors":len(records),
          "available_vectors":sum(bool(x["expected_available"]) for x in records),
          "unavailable_vectors":sum(not bool(x["expected_available"]) for x in records),
          "log":str(log.relative_to(ROOT)),
          "vectors":str(vector_path.relative_to(ROOT)) if records else None,
          "source_sha256":{str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in sources},
          "equations":{"COP_Carnot":"Th/(Th-Tc)","COP_operating":"a+b*Qh",
                       "source_boundary":"b*Qh^2+(a-1-S*b)*Qh-S*a=0",
                       "entropy_generation":"Qh/Th-Qe/Tc >= 0"},
          "assumptions":["isothermal reservoir temperature proxy","constant fractional Carnot efficiency",
                         "linear part-load COP penalty","minimum COP as continuous-operation cutoff",
                         "zero-source and below-cutoff points unavailable; no cycling or resistance model"],
          "limitations":["no measurement calibration","no primary-paper equation match",
                         "no annual dispatch integration or Simulink/Stateflow execution"]}
    with evidence.open("x",encoding="utf-8") as stream:
        json.dump(data,stream,indent=2,allow_nan=False)
        stream.write("\n")
    print(json.dumps({"tests_run":data["tests_run"],"passed":data["passed"],"failed":data["failed"],
                      "errors":data["errors"],"vectors":data["vectors"],
                      "evidence":str(evidence.relative_to(ROOT)),"log":str(log.relative_to(ROOT))}))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
