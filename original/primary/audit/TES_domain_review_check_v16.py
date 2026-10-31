"""Independent rational-arithmetic TES domain checks, not MATLAB execution.

The legacy algebra is represented directly with Fraction. These scenario checks
document counterexamples and operator-split timestep sensitivity; they do not
claim article replication or validation of a physical storage asset.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[1]


def legacy(e, surplus=0, deficit=0, *, capacity=20, charge_limit=5,
           discharge_limit=5, eta_c=F(9, 10), eta_d=F(4, 5),
           loss=0, dt=1):
    e, surplus, deficit = map(F, (e, surplus, deficit))
    capacity, charge_limit, discharge_limit = map(F, (capacity, charge_limit, discharge_limit))
    eta_c, eta_d, loss, dt = map(F, (eta_c, eta_d, loss, dt))
    available = max(F(0), e * (1 - loss * dt))
    charge = discharge = F(0)
    if capacity > 0 and surplus > 0:
        charge = min(surplus, charge_limit, max(F(0), capacity - available) / (eta_c * dt))
        end = available + eta_c * charge * dt
    elif capacity > 0 and deficit > 0:
        discharge = min(deficit, discharge_limit, available * eta_d / dt)
        end = max(F(0), available - discharge * dt / eta_d)
    else:
        end = available
    return dict(charge_MW=charge, discharge_MW=discharge, energy_next_MWh=end)


def number_dict(values):
    return {k: float(v) if isinstance(v, F) else v for k, v in values.items()}


def main():
    checks = []

    def check(name, actual, expected, classification):
        passed = actual == expected
        checks.append(dict(name=name, passed=passed, classification=classification,
                           actual=number_dict(actual), expected=number_dict(expected)))

    check("negative_charge_limit", legacy(10, surplus=5, charge_limit=-2),
          dict(charge_MW=F(-2), discharge_MW=F(0), energy_next_MWh=F(41, 5)),
          "LEGACY_DOMAIN_DEFECT_ANALYTICAL")
    check("negative_discharge_limit", legacy(10, deficit=5, discharge_limit=-2),
          dict(charge_MW=F(0), discharge_MW=F(-2), energy_next_MWh=F(25, 2)),
          "LEGACY_DOMAIN_DEFECT_ANALYTICAL")
    check("overfilled_state_idle", legacy(25),
          dict(charge_MW=F(0), discharge_MW=F(0), energy_next_MWh=F(25)),
          "DIRECT_COMPONENT_DOMAIN_DEFECT_ANALYTICAL")
    check("zero_capacity_nonzero_state", legacy(1, capacity=0),
          dict(charge_MW=F(0), discharge_MW=F(0), energy_next_MWh=F(1)),
          "DIRECT_COMPONENT_DOMAIN_DEFECT_ANALYTICAL")
    check("excessive_decay_clamp", legacy(10, loss=2),
          dict(charge_MW=F(0), discharge_MW=F(0), energy_next_MWh=F(0)),
          "DIRECT_COMPONENT_HIDES_INVALID_DECAY_ANALYTICAL")
    check("simultaneous_requests", legacy(10, surplus=5, deficit=5),
          dict(charge_MW=F(5), discharge_MW=F(0), energy_next_MWh=F(29, 2)),
          "DIRECT_COMPONENT_SILENT_CHARGE_PRIORITY_ANALYTICAL")
    check("empty_store_charge_room_bound", legacy(0, surplus=100, charge_limit=100),
          dict(charge_MW=F(200, 9), discharge_MW=F(0), energy_next_MWh=F(20)),
          "VALID_DOMAIN_BOUNDARY")
    check("full_store_discharge_bound", legacy(20, deficit=100, discharge_limit=100),
          dict(charge_MW=F(0), discharge_MW=F(16), energy_next_MWh=F(0)),
          "VALID_DOMAIN_BOUNDARY")
    check("complete_linear_loss_then_charge", legacy(10, surplus=5, loss=1),
          dict(charge_MW=F(5), discharge_MW=F(0), energy_next_MWh=F(9, 2)),
          "VALID_SPLIT_ENDPOINT_NOT_CONTINUOUS_LEAKAGE")

    two_hour = legacy(10, loss=F(1, 5), dt=2)["energy_next_MWh"]
    one_hour = legacy(10, loss=F(1, 5))["energy_next_MWh"]
    two_one_hour = legacy(one_hour, loss=F(1, 5))["energy_next_MWh"]
    check("linear_decay_timestep_sensitivity", dict(single=two_hour, split=two_one_hour),
          dict(single=F(6), split=F(32, 5)), "DECLARED_NUMERICAL_POLICY_LIMITATION")
    failed = sum(not c["passed"] for c in checks)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    artifacts = [Path(__file__).relative_to(ROOT), Path("matlab/+dchr/+components/storage_step.m"),
                 Path("matlab/+dchr/simulate_system_v13.m"),
                 Path("sources/papers/17_Jurgens_Frankfurt_2024.extracted.txt")]
    payload = dict(utc=datetime.now(timezone.utc).isoformat(), suite="TES_domain_review_check_v16",
                   qualifier="Independent Fraction algebra only; MATLAB not executed by this reviewer; no physical or article replication validation.",
                   passed=len(checks)-failed, failed=failed, checks=checks,
                   continuous_rate_comparison_MWh=10 * math.exp(-.2 * 2),
                   source_hashes={str(p).replace("\\", "/"): hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in artifacts})
    report = ROOT / "audit" / f"TES_domain_review_checks_v16_{stamp}.json"
    log = ROOT / "automation" / "logs" / f"TES_domain_review_checks_v16_{stamp}.log"
    report.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    log.write_text(f"UTC {payload['utc']}\nIndependent Fraction checks: {len(checks)-failed}/{len(checks)} PASS; {failed} FAIL\n"
                   + payload["qualifier"] + "\nJSON: " + str(report.relative_to(ROOT)).replace("\\", "/") + "\n", encoding="utf-8")
    print(json.dumps(dict(passed=len(checks)-failed, failed=failed,
                         report=str(report.relative_to(ROOT)).replace("\\", "/"),
                         log=str(log.relative_to(ROOT)).replace("\\", "/")), indent=2))
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
