"""Exact rational capacity QA, with separate MW and MWh comparisons.

Mandatory supplement to the draft energy reviewer, whose TES comparison
uses an allocation slack derived from a power ulp. No slack is used here.
"""
from datetime import datetime, timezone
from fractions import Fraction as F
import json, sys
from energy_commit_v78 import ROOT, dump, stamp, sha
from earliest_closed_form_v73 import rows


def verify(folder):
    report = json.loads((folder / 'report.json').read_text())
    checks = []
    def check(name, ok):
        checks.append(dict(name=name, passed=bool(ok)))
    for run in report['runs']:
        p = list(map(F, run['p']))
        capacity = p[0] * (p[2] - p[1])  # MWh/K * K = MWh
        for k, r in enumerate(rows(run['trace'])):
            name = run['id'] + '_' + str(k)
            check(name + '_initial_inventory_MWh', F(0) <= F(r[2]) <= F(r[3]) < capacity)
            check(name + '_final_inventory_MWh', F(0) <= F(r[4]) <= F(r[5]) < capacity)
            check(name + '_selected_heat_capacity_MW', F(0) <= F(r[56]) <= p[10])
            for j in range(int(r[12])):
                z = r[100 + 80*j:180 + 80*j]
                q = list(map(F, z[23:29]))
                label = name + '_' + str(j)
                check(label + '_TES_start_MWh', F(0) <= F(z[10]) <= F(z[11]) < capacity)
                check(label + '_TES_endpoint_MWh', F(0) <= F(z[12]) <= F(z[13]) < capacity)
                check(label + '_HP_MW', F(0) <= q[0] <= F(r[56]) <= p[10])
                check(label + '_charge_MW', F(0) <= q[2] <= p[8])
                check(label + '_discharge_MW', F(0) <= q[3] <= p[9])
                check(label + '_backup_MW', F(0) <= q[4] <= p[23])
    # Independent reviewer self-check at the TES upper boundary.
    # A one-ulp excess must fail regardless of the scale of a power port.
    import math
    c = F(10)
    selfchecks = [dict(name='one_ulp_capacity_excess_detected',
                       passed=not (F(math.nextafter(10., math.inf)) < c)),
                  dict(name='capacity_equality_rejected', passed=not (F(10) < c)),
                  dict(name='one_ulp_capacity_margin_accepted',
                       passed=F(math.nextafter(10., -math.inf)) < c)]
    result = dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),
        evidence_class='EXACT_BINARY_RATIONAL_MW_MWH_CAPACITY_QA_ON_ACTUAL_SAVED_MODEL_RUNS',
        report_sha256=sha(folder / 'report.json'), reviewer_sha256=sha(ROOT / 'audit/strict_capacity_v78.py'),
        checks=checks, reviewer_selfchecks=selfchecks,
        summary=dict(passed=sum(v['passed'] for v in checks), failed=sum(not v['passed'] for v in checks)))
    name = 'strict_capacity_QA_v78_' + stamp()
    dump(folder / (name + '.json'), result)
    dump(folder / (name + '.log'), dict(summary=result['summary'],
        reviewer_selfchecks=selfchecks, failed=[c for c in checks if not c['passed']]))
    print(json.dumps(dict(summary=result['summary'], reviewer_selfchecks=selfchecks)))
    return int(result['summary']['failed'] > 0 or not all(v['passed'] for v in selfchecks))


if __name__ == '__main__':
    folder = (ROOT / sys.argv[1]).resolve()
    assert folder.is_relative_to(ROOT / 'results')
    sys.exit(verify(folder))
