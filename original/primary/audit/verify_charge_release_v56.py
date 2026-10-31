"""Independent original-MAT binary binding, dwell and provenance acceptance gate.
Standard library only; never imports MATLAB implementation or substitutes results.
The equation/RK4 reviewer is a separate mandatory gate, counted separately.
"""
from pathlib import Path
from datetime import datetime, timezone
from fractions import Fraction as F
import copy, hashlib, json, math, struct, sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    'matlab/run_charge_regimes_v56.m', 'matlab/run_charge_temporal_v56.m',
    'matlab/export_charge_release_v56.m',
    'matlab/+dchr/+components/charge_regime_events_v56.m',
    'audit/verify_charge_regimes_v56.py', 'audit/verify_charge_release_v56.py',
    'audit/prepare_charge_regimes_v56.py', 'audit/run_charge_release_v56.ps1',
    'audit/finalize_charge_release_v56.py', 'audit/Charge_regime_derivation_v56.md',
    'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx',
}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def flatten(x):
    if isinstance(x, list): return [v for row in x for v in flatten(row)]
    return [x]
def same_binary(raw, expected):
    values = flatten(expected)
    if len(raw) != 8 * len(values): return False
    for (actual,), value in zip(struct.iter_unpack('<d', raw), values):
        if value is None:
            if not math.isnan(actual): return False
        elif struct.pack('<d', actual) != struct.pack('<d', float(value)): return False
    return True
def lower_age(clock):
    return F.from_float(clock[1]) + F.from_float(clock[2]) - F.from_float(clock[3])

def main():
    folder = (ROOT / sys.argv[1]).resolve()
    assert folder.is_relative_to(ROOT / 'results')
    report = json.loads((folder / 'report.json').read_text())
    temporal = json.loads((folder / 'temporal_report.json').read_text())
    qa_path = max(folder.glob('independent_QA_v56_*.json'))
    qa = json.loads(qa_path.read_text())
    manifest = json.loads((folder / 'binary_manifest.json').read_text())
    checks = []
    def check(kind, name, passed): checks.append(dict(kind=kind, name=name, passed=bool(passed)))
    check('scope', 'accepted_model_preserved', report['new_model'] is False and report['model_version'] == '0.52')
    check('matlab', 'main_assertions', report['summary']['failed'] == 0 and all(c['passed'] for c in report['assertions']))
    check('matlab', 'temporal_assertions', temporal['summary']['failed'] == 0 and all(c['passed'] for c in temporal['assertions']))
    check('equation_QA', 'independent_gate', qa['summary']['failed'] == 0 and all(x['passed'] for x in qa['checks']))
    check('equation_QA', 'separate_mutations', len(qa['reviewer_selfchecks']) >= 5 and all(x['passed'] for x in qa['reviewer_selfchecks']))
    check('equation_QA', 'temporal_required', qa['temporal_counts'] is not None and qa['temporal_counts']['intervals'] == 7)
    check('coverage', 'all_ten_regimes', len(qa['regime_coverage']) == 10)
    check('coverage', 'fresh_six_modes', {int(x['dispatch'][0]) for x in report['runs']} == set(range(6)))
    check('fault', 'actual_runtime_fault', 'Runtime physical-domain rejection' in report['runtime_fault_message'])
    originals = json.loads((folder / 'original_simulation_reopen.json').read_text())
    check('binding', 'original_main_JSON', originals == report['runs'])
    run = temporal['run']
    check('binding', 'original_temporal_JSON', run == json.loads((folder / 'temporal_original_reopen.json').read_text()))
    indexed = {r['id']: r for r in report['runs']}
    binary_checks = []; binary_hashes = []
    expected_fields = {'dispatch', 'raw_segments', 'raw_plans', 'clock_start', 'clock_end', 'energy_start',
        'case.p', 'case.h', 'case.c', 'case.inputs', 'case.initial_energy_MWh', 'case.initial_clock'}
    seen = set(); source_mats = set()
    for rec in manifest['records']:
        key = (rec['kind'], rec['id'], rec['field'])
        check('binary', 'unique_' + str(key), key not in seen); seen.add(key)
        path = (folder / rec['file']).resolve(); assert path.is_relative_to(folder / 'binary')
        raw = path.read_bytes(); source_mats.add(rec['source_mat'])
        check('binary', 'shape_' + str(key), len(raw) == rec['rows'] * rec['columns'] * 8)
        value = None
        if rec['kind'] == 'run':
            saved = indexed[rec['id']]
            if rec['field'] in ('clock_start', 'clock_end', 'energy_start'):
                # Each single-step control has one positive segment, so clock
                # end is reconstructed from the actual saved plan, not a timer assumption.
                p = saved['raw_plans'][-1]
                value = {'clock_start': saved['case']['initial_clock'],
                         'clock_end': [p[14], p[17], p[19], p[21]],
                         'energy_start': saved['case']['initial_energy_MWh']}[rec['field']]
            elif rec['field'].startswith('case.'): value = saved['case'][rec['field'][5:]]
            else: value = saved[rec['field']]
        elif rec['field'] == 'blocker.witness':
            v = run['blocker']['input']
            value = [v['E'], v['p']['heat_capacity_MWh_per_K'], v['p']['ambient_C'],
                     v['s']['charge_approach_K'], v['s']['delivery_C'], v['s']['direct_approach_K']]
        elif rec['field'].startswith('case.'): value = run['case'][rec['field'][5:]]
        else: value = run[rec['field']]
        ok = same_binary(raw, value)
        check('binary', 'original_values_' + str(key), ok)
        binary_checks.append(ok); binary_hashes.append(dict(path=rec['file'], sha256=sha(path)))
    required_keys = {('run', id, field) for id in indexed for field in expected_fields}
    required_keys |= {('temporal', 'sequence', field) for field in expected_fields | {'blocker.witness'}}
    check('binary', 'complete_original_MAT_field_set', seen == required_keys and len(source_mats) == 7)
    check('binary', 'documented_encoding', manifest['encoding'] == 'IEEE_BINARY64_LITTLE_ENDIAN_ROW_MAJOR')
    # Independently require lower-bound dwell authorization at real latch changes.
    previous = run['case']['initial_clock']; dwell_changes = 0
    for interval in range(7):
        check('clock', f'{interval}_macro_start', run['clock_start'][interval] == previous)
        raw = run['raw_plans'][interval]
        for slot in range(64):
            p = raw[slot * 23:(slot + 1) * 23]
            if p[0] == 0: continue
            on = p[14]; reason = int(p[16])
            if on != previous[0]:
                dwell_changes += 1
                if on == 1:
                    check('dwell', f'{interval}_{slot}_restart_reason', reason == 3)
                    check('dwell', f'{interval}_{slot}_off_lower_age', lower_age(previous) >= F.from_float(run['case']['c'][2]))
                    check('dwell', f'{interval}_{slot}_restart_energy', p[1] <= run['case']['c'][0] + 64 * math.ulp(max(1, run['case']['p'][1])))
                else:
                    check('dwell', f'{interval}_{slot}_stop_reason', reason in (1, 2))
                    if reason == 2:
                        check('dwell', f'{interval}_{slot}_on_lower_age', lower_age(previous) >= F.from_float(run['case']['c'][1]))
            previous = [on, p[17], p[19], p[21]]
        check('clock', f'{interval}_macro_end', run['clock_end'][interval] == previous)
    check('dwell', 'actual_latch_changes_observed', dwell_changes >= 2)
    b = run['blocker']; v = b['input']
    gap = F.from_float(v['p']['ambient_C']) + F.from_float(b['nominal_endpoint_MWh']) / F.from_float(v['p']['heat_capacity_MWh_per_K']) + F.from_float(v['s']['charge_approach_K']) - F.from_float(v['s']['delivery_C']) - F.from_float(v['s']['direct_approach_K'])
    check('blocker', 'exact_fraction_and_actual_rejection', gap == F(-5, 3602879701896397) and b['endpoint_identifier'] == 'DCHR:v55:UnresolvedBranch' and b['coupled_release_blocked'])
    hashes = json.loads((folder / 'source_hashes.json').read_text())
    check('provenance', 'complete_harness_reviewer_snapshot', REQUIRED <= {x['path'] for x in hashes})
    for item in hashes:
        check('provenance', item['path'], sha(ROOT / item['path']) == item['sha256'] == sha(folder / 'source_snapshot' / item['path']))
    for item in json.loads((folder / 'preservation.json').read_text()):
        check('preservation', item['path'], sha(ROOT / item['path']) == item['sha256'])
    receipts = [json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_release_*.json')]
    check('execution', 'fresh_success_receipt', any(x['exit_code'] == 0 and all(name in x['command'] for name in ['run_charge_regimes_v56', 'run_charge_temporal_v56', 'export_charge_release_v56']) for x in receipts))
    logs = '\n'.join(p.read_text(encoding='utf-8', errors='replace') for p in folder.glob('matlab_release_*.log'))
    check('execution', 'all_three_log_summaries', all(s in logs for s in ['CHARGE_REGIMES_V56 PASS=', 'CHARGE_TEMPORAL_V56 PASS=', 'CHARGE_BINARY_V56 RECORDS=']))
    mutation_raw = bytearray((folder / manifest['records'][0]['file']).read_bytes())
    mutation_raw[0:8] = struct.pack('<d', 99.)
    selfchecks = [dict(name='original_binary_mode_corruption', passed=not same_binary(mutation_raw, report['runs'][0]['dispatch'])),
                  dict(name='early_dwell_lower_bound', passed=lower_age([0., .1, 0., .01]) < F.from_float(.25))]
    out = dict(version='0.56', timestamp_utc=datetime.now(timezone.utc).isoformat(),
        equation_QA=qa_path.relative_to(ROOT).as_posix(), passed=sum(c['passed'] for c in checks),
        failed=sum(not c['passed'] for c in checks), binary_records=len(manifest['records']),
        binary_values=sum(x['rows'] * x['columns'] for x in manifest['records']), original_mats=len(source_mats),
        dwell_latch_changes=dwell_changes, exact_endpoint_gap_fraction=str(gap),
        reviewer_selfchecks=selfchecks, binary_hashes=binary_hashes, checks=checks,
        scope='FRESH_SAVED_V52_ACCEPTANCE_AND_V56_NOMINAL_CHARGE_EVENT_BLOCKER_NO_NEW_SLX')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    path = folder / f'release_QA_v56_{stamp}.json'
    path.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({k: v for k, v in out.items() if k not in ('checks', 'binary_hashes')}))
    print(path.relative_to(ROOT).as_posix())
    if out['failed'] or not all(x['passed'] for x in selfchecks):
        print(json.dumps([c for c in checks if not c['passed']][:20], indent=2)); raise SystemExit(1)

if __name__ == '__main__': main()
