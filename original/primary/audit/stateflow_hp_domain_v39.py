"""Focused v39 fixtures; production release remains saved v38.

No article/equipment values are inferred. Finite numerical stress fixtures.
"""
from pathlib import Path
from datetime import datetime, timezone
import copy, json, math

ROOT = Path(__file__).resolve().parents[1]

def main():
    prior = ROOT / 'results/stateflow_v38_20261010T081205294Z/source_snapshot/spec/cases.json'
    cases = copy.deepcopy(json.loads(prior.read_text())['cases'][:6])
    for c in cases:
        c['kind'] = 'baseline'
    probes = []
    excluded = []
    for cap in (8., 1e-100, 1e100):
        for bits in (20, 40, 60, 75, 80, 81, 90, 120, 400, 900):
            for penalty in (0., .3):
                source = math.ldexp(cap, -bits)
                if source == 0:
                    excluded.append(dict(cap_MW=cap, ratio_bits=bits, penalty=penalty,
                        reason='Source underflows to zero; not a positive representable fixture'))
                    continue
                assert math.isfinite(source)
                probes.append(dict(id=f'range_{len(probes):03d}', kind='dynamic_range',
                    cap_MW=cap, request_MW=cap, source_MW=source,
                    penalty=penalty, cop_min=1.2, ratio_bits=bits))
    for bits in (20, 40, 60, 75, 80, 81, 90, 120):
        source = math.ldexp(8., -bits)
        for kind in ('wide_request', 'tight_request'):
            c = copy.deepcopy(cases[2])
            c.update(id=f'{kind}_{bits}', kind=kind, initial_energy_MWh=0.)
            c['p'][2] = 3. if kind == 'wide_request' else 0.
            c['p'][6] = c['p'][10] = 0.
            c['inputs'] = [[source, 35., 75., source, 45.]] * 2
            cases.append(c)
            probes.append(dict(id=f'{kind}_{bits}', kind='request_control',
                cap_MW=8., request_MW=source + c['p'][2], source_MW=source,
                penalty=0., cop_min=1.2, ratio_bits=bits))
    # Cutoff controls are separated from the threshold by >=1e-10 relative,
    # so binary64 boundary ambiguity is not counted as a defect.
    cutoff = 8. * ((3.5 / 4. - .7) / .3)
    for factor in (1. - 1e-10, 1., 1. + 1e-10, 2.):
        probes.append(dict(id=f'cutoff_{len(probes):03d}', kind='cutoff_control',
            cap_MW=8., request_MW=cutoff * factor, source_MW=8.,
            penalty=.3, cop_min=3.5, boundary_ambiguous=factor == 1.))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = ROOT / 'audit' / ('stateflow_hp_spec_v39_' + stamp)
    folder.mkdir()
    spec = dict(version='0.39', model_release='0.38', cases=cases, hp_probes=probes, excluded=excluded,
        assumptions='Engineering numerical fixtures; not calibrated equipment or primary paper data',
        comparison_relative_tolerance=1e-13, comparison_ulp_allowance=64,
        cutoff_exact_boundary_policy='Observe only; binary64 lower-bound ambiguity is excluded from defect counts')
    (folder / 'cases.json').write_text(json.dumps(spec, indent=2) + '\n', encoding='utf-8')
    print('SPEC=' + str(folder.relative_to(ROOT)))

if __name__ == '__main__':
    main()
