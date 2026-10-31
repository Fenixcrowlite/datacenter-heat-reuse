"""Independent constant-coefficient TES derivation checks; no production imports."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "sources/papers/Cadau_2019_TES_v28_20261009T102911_076286Z.pdf"

def analytic(e, power, rate, duration):
    if rate == 0:
        return e + power * duration
    return math.exp(-rate * duration) * e - power * math.expm1(-rate * duration) / rate

def rk4(e, power, rate, duration, steps=2048):
    h = duration / steps
    f = lambda state: power - rate * state
    for _ in range(steps):
        a = f(e)
        b = f(e+h*a/2)
        c = f(e+h*b/2)
        d = f(e+h*c)
        e += h*(a+2*b+2*c+d)/6
    return e

def main():
    checks = []
    def check(name, condition, **evidence):
        checks.append(dict(name=name, passed=bool(condition), **evidence))
    # All values below are declared arbitrary unit/algorithm scenarios.
    capacity_J_K = 3.6e9
    conductance_W_K = 2e5
    lambda_h = 3600 * conductance_W_K / capacity_J_K
    start_C, ambient_C, duration_h = 50., 20., 2.
    temperature_next = ambient_C + (start_C-ambient_C)*math.exp(-conductance_W_K/capacity_J_K*duration_h*3600)
    e_MWh = capacity_J_K*(start_C-ambient_C)/3.6e9
    mapped = capacity_J_K*(temperature_next-ambient_C)/3.6e9
    check("SI_to_MWh_h_mapping", abs(mapped-analytic(e_MWh,0,lambda_h,duration_h))<1e-12,
          lambda_per_h=lambda_h, SI_temperature_result_MWh=mapped)
    for power in (0., 1.8, -1.25):
        exact = analytic(10.,power,.2,2.)
        numeric = rk4(10.,power,.2,2.)
        check(f"independent_RK4_power_{power}", abs(exact-numeric)<2e-11,
              exact_MWh=exact, RK4_MWh=numeric)
        split = analytic(analytic(10.,power,.2,.75),power,.2,1.25)
        check(f"continuous_partition_power_{power}", abs(split-exact)<5e-14,
              whole_MWh=exact, partitioned_MWh=split)
    for power in (1.8,-1.25):
        continuous=analytic(10.,power,.2,2.)
        loss_first=10.*math.exp(-.4)+power*2.
        discrepancy=loss_first-continuous
        expected=power*(2.+math.expm1(-.4)/.2)
        check(f"split_bias_power_{power}", discrepancy*power>0 and abs(discrepancy-expected)<5e-14,
              split_MWh=loss_first, continuous_MWh=continuous, discrepancy_MWh=discrepancy)
    check("zero_rate_limit", analytic(10.,1.8,0,2.)==13.6,
          zero_rate_MWh=analytic(10.,1.8,0,2.))
    check("legacy_passive_partition_counterexample", abs(10*(1-.2*2)-6)<1e-14 and abs(10*(1-.2)**2-6.4)<1e-14,
          whole_linear_MWh=10*(1-.2*2), partitioned_linear_MWh=10*(1-.2)**2,
          continuous_MWh=analytic(10.,0,.2,2.))
    useful_start, offset, rate, time = 1.,10.,.2,1.
    actual_useful=(useful_start+offset)*math.exp(-rate*time)-offset
    wrong=useful_start*math.exp(-rate*time)
    check("useful_cutoff_reference_counterexample", actual_useful<0<wrong,
          unconstrained_useful_MWh=actual_useful, wrong_zero_equilibrium_MWh=wrong,
          physical_interpretation="Useful delivery stops at cutoff; ambient sensible energy remains.")
    one_hour_fraction=1-math.exp(-.2)
    check("fraction_rate_conversion", abs(-math.log1p(-one_hour_fraction)-.2)<1e-15 and one_hour_fraction!=.2,
          rate_per_h=.2, resulting_one_hour_loss_fraction=one_hour_fraction)
    check("above_one_rate_step_retention", 0<math.exp(-2)<1,
          lambda_dt=2, exponential_retention=math.exp(-2), linear_retention=-1)
    passed=sum(c["passed"] for c in checks)
    stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    payload=dict(utc=datetime.now(timezone.utc).isoformat(), suite="TES_derivation_v28", passed=passed,
                 failed=len(checks)-passed, checks=checks,
                 qualifier="Independent reduced-equation/unit QA only; scenario values, no equipment or article replication.",
                 source_pdf_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),
                 reviewer_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    report=ROOT/"audit"/f"TES_derivation_checks_v28_{stamp}.json"
    log=ROOT/"automation"/"logs"/f"TES_derivation_checks_v28_{stamp}.log"
    report.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    log.write_text(f"UTC {payload['utc']}\n{passed}/{len(checks)} PASS; {len(checks)-passed} FAIL\n{payload['qualifier']}\nReport: {report.relative_to(ROOT)}\n",encoding="utf-8")
    print(json.dumps(dict(passed=passed,failed=len(checks)-passed,report=str(report.relative_to(ROOT)),log=str(log.relative_to(ROOT))),indent=2))
    return int(passed!=len(checks))

if __name__ == "__main__":
    raise SystemExit(main())
