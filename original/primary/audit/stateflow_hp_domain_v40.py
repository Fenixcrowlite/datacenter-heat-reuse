"""Repair fixtures: retained v39 failures, prior references and binary64 stress."""
from pathlib import Path
from datetime import datetime, timezone
import copy, json, math
ROOT = Path(__file__).resolve().parents[1]

def main():
    prior = json.loads((ROOT / 'results/stateflow_hp_domain_v39_20261010T123256940Z/source_snapshot/spec/cases.json').read_text())
    spec = copy.deepcopy(prior)
    v38 = json.loads((ROOT / 'audit/stateflow_spec_v38_20261010T081108_895717Z/cases.json').read_text())
    selected = {'mode_sequence', 'fallback_h_4', 'fallback_h_0.25', 'physical_off_dwell',
                'capacity_on_dwell', 'source_demand_changes', 'source_limited', 'zero_loss_cycles',
                'small_loss_cycles', 'long_off_dwell_cutoff', 'scale_1e+09'}
    for c in v38['cases']:
        if c['id'] in selected:
            c = copy.deepcopy(c); c['kind'] = 'baseline'; spec['cases'].append(c)
    for q in v38['hp_probes']:
        q = copy.deepcopy(q); q['id'] = 'prior38_' + q['id']; q['kind'] = 'prior38'; spec['hp_probes'].append(q)
    # Source-limited request invariance: wide/tight requests both above the root.
    for bits in (90, 400, 900, 1020, 1070):
        for penalty in (0., .3):
            source = math.ldexp(8., -bits)
            pair = f'invariance_{bits}_{penalty}'
            for label, request in [('wide', 8.), ('bounded', 8.*source)]:
                spec['hp_probes'].append(dict(id=pair+'_'+label, kind='invariance', pair=pair,
                    cap_MW=8., request_MW=request, source_MW=source, penalty=penalty,
                    cop_min=1.2, expected_reject=False))
    # COP near one maximizes the source-relative bracket width; finite normal inputs.
    for request in (8., 1.):
        spec['hp_probes'].append(dict(id=f'cop_near_one_{request}', kind='near_one',
            cap_MW=8., request_MW=request, source_MW=1e-100, penalty=0.,
            cop_min=math.nextafter(1., math.inf), nominal_cop=math.nextafter(1., math.inf),
            expected_reject=False))
    # Smallest subnormal positive heat cannot represent positive electricity at COP4.
    for cap in (math.ulp(0.), 8.):
        spec['hp_probes'].append(dict(id=f'unrepresentable_electric_{cap}', kind='resolution',
            cap_MW=cap, request_MW=math.ulp(0.), source_MW=math.ulp(0.),
            penalty=0., cop_min=1.2, expected_reject=True))
    spec.update(version='0.40', model_release='0.40', new_model=True,
        prior_counterexamples='retained v39 exact-input fixtures',
        assumptions='Engineering numerical stress fixtures; no article/equipment calibration',
        cutoff_exact_boundary_policy='Exact v39 cutoff observed only; near-boundary classification not broadly accepted')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    folder = ROOT / 'audit' / ('stateflow_hp_spec_v40_' + stamp); folder.mkdir()
    (folder / 'cases.json').write_text(json.dumps(spec, indent=2)+'\n', encoding='utf-8')
    print('SPEC=' + str(folder.relative_to(ROOT)))
if __name__ == '__main__': main()
