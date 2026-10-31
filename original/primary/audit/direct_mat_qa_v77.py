"""Prepare and review fresh saved-Stateflow runs from original HDF5 MAT files.

No MATLAB exports, JSON trace or production solver is used in the numeric lane.
Closed exp/log equations and exact-binary temporal checks are inherited from
v73/v76. This is algorithmic independence, not independent personnel.
"""
from pathlib import Path
from datetime import datetime, timezone
from decimal import localcontext
import copy
import csv
import hashlib
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v75.slx'
OLD = 'results/temporal_reporting_v76_20261012T082629_130610Z'
LEDGERS = ['automation/engineering_progress.md', 'automation/STATEFLOW_ACCEPTANCE.md', 'audit/research_frontier_2026_10_08.md']


def stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    with path.open('x', encoding='utf-8') as out:
        json.dump(value, out, indent=2)
        out.write('\n')


def prepare(folder):
    from temporal_reporting_v76 import FILES
    prior = json.loads((ROOT / OLD / 'spec.json').read_text())
    cases = [c for c in prior['cases'] if c['family'] == 'six_mode' or c['id'] in ['variable_holds', 'enable_changes', 'temporal_chain']]
    event_spec = ROOT / 'results/earliest_repair_v73r2_20261012T073823_950801Z/spec.json'
    for c in json.loads(event_spec.read_text())['cases']:
        if c['id'] not in ['multiple_cycles_one_call', 'repeated_0p25', 'repeated_0p5', 'repeated_1p0']:
            continue
        end = 0.
        schedule = []
        for u in c['input']:
            end += u[4]
            schedule.append([u[4], end, *u[5:9]])
        cases.append(dict(id=c['id'], p=c['p'], initial=c['input'][0][9:12], schedule=schedule, family='direct_event_QA'))
    dump(folder / 'spec.json', dict(version='0.77', scope='SAVED_V75_ORIGINAL_MAT_DIRECT_QA', cases=cases))
    existing = list((ROOT / 'matlab').rglob('*.m')) + list((ROOT / 'matlab').rglob('*.slx')) + list(ROOT.glob('STATUS*.json')) + list(ROOT.glob('MASTER_STAGEBOARD*.md'))
    dump(folder / 'preservation.json', [dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p)) for p in existing if 'v77' not in p.name])
    dump(folder / 'ledger_prefixes.json', [dict(path=p, size=(ROOT/p).stat().st_size, sha256=sha(ROOT/p)) for p in LEDGERS])
    sources = set(FILES + [MODEL, 'matlab/simulink/build_earliest_dispatch_v75.m', 'audit/mat73_numeric_v77.py', 'audit/direct_mat_qa_v77.py', 'audit/run_direct_mat_v77.ps1', 'matlab/run_direct_mat_v77.m'])
    records = []
    for rel in sorted(sources):
        target = folder / 'source_snapshot' / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, target)
        records.append(dict(path=rel, sha256=sha(ROOT/rel)))
    dump(folder / 'source_hashes.json', records)
    dump(folder / 'prior_mat_seal.json', dict(path=OLD+'/temporal_reporting_v76.mat', sha256=sha(ROOT/OLD/'temporal_reporting_v76.mat')))
    dump(folder / 'documentation.json', dict(timestamp_utc=datetime.now(timezone.utc).isoformat(), verified_documentation=[
        dict(url='https://www.mathworks.com/help/matlab/import_export/mat-file-versions.html', claim='Version 7.3 MAT files are HDF5 based. No settings changes needed.'),
        dict(url='https://docs.h5py.org/en/stable/refs.html', claim='h5py dereferences object references with file[ref].')],
        implementation_observation='MATLAB dimension reversal and empty shape encoding are tested against actual MATLAB fixtures, not inferred from general HDF5 documentation.'))
    print(folder.relative_to(ROOT).as_posix())


def verify(folder):
    sys.path.insert(0, str(folder/'python_deps'))
    import h5py
    import numpy as np
    from mat73_numeric_v77 import Mat73Numeric, plain
    from temporal_reporting_v76 import temporal_checks
    from earliest_closed_form_v73 import analyze, rows
    from verify_held_schedule_v74 import total_earliest, review_report

    checks, selfchecks, numeric, evidence_files = [], [], [], []
    aggregates, run_counts = {}, []

    def check(kind, name, ok):
        checks.append(dict(kind=kind, name=name, passed=bool(ok)))

    def bits_equal(x, y):
        return x.shape == y.shape and x.dtype == y.dtype and x.tobytes(order='F') == y.tobytes(order='F')

    def audit_run(run, label):
        for c in temporal_checks(run):
            check('exact_binary_temporal', label+'_'+c['name'], c['passed'])
        inherited = copy.deepcopy(run)
        inherited['trace'] = copy.deepcopy(rows(run['trace']))
        for row in inherited['trace']:
            check('trace_schema', label+f'_{len(numeric)}', row[1] == 75)
            row[1] = 73
            row[72:75] = [0, 0, 0]
        with localcontext() as ctx:
            ctx.prec = 160
            cs, ns = analyze(inherited)
            for c in cs:
                check('closed_equations', label+'_'+c['name'], c['passed'])
            with localcontext() as lower:
                lower.prec = 120
                again, _ = analyze(inherited)
            check('precision', label, [c['passed'] for c in cs] == [c['passed'] for c in again])
            totals = total_earliest(inherited, ns)
            for name, ok in review_report(run, totals).items():
                check('energy_report', label+'_'+name, ok)
            aggregates[label] = {k: str(v) for k, v in totals.items()}
            numeric.extend(dict(evidence_lane=label, **n) for n in ns)
        return inherited, ns

    with Mat73Numeric(folder/'parser_fixture.mat') as reader:
        expected = {
            'fixture_matrix': np.array([[11,12,13],[21,22,23]], dtype=np.float64),
            'fixture_tensor': np.arange(1,25,dtype=np.float64).reshape((2,3,4),order='F'),
            'fixture_row': np.array([[3,5,7]],dtype=np.float64),
            'fixture_column': np.array([[2],[4],[8]],dtype=np.float64),
            'fixture_scalar': np.array([[42]],dtype=np.float64),
            'fixture_empty': np.empty((0,3),dtype=np.float64),
            'fixture_signed_zero': np.array([[0.,-0.]],dtype=np.float64),
            'fixture_logical': np.array([[True,False],[False,True]])}
        for name, want in expected.items():
            check('actual_MAT_parser_fixture', name, bits_equal(reader.read(name), want))
        v = reader.read('fixture_nonfinite')
        check('actual_MAT_parser_fixture','nonfinite_preserved',v.shape==(1,3) and np.isnan(v[0,0]) and v[0,1]==np.inf and v[0,2]==-np.inf)
        check('actual_MAT_parser_fixture','char',reader.read('fixture_char')=='MAT77')
        cells=reader.read('fixture_cell')
        check('actual_MAT_parser_fixture','cell_refs',len(cells)==2 and bits_equal(cells[0],expected['fixture_matrix']) and plain(cells[1])=={'value':17})

    spec=json.loads((folder/'spec.json').read_text())
    report=json.loads((folder/'execution_report.json').read_text())
    with Mat73Numeric(folder/'execution_report.mat') as reader:
        check('direct_MAT_execution','summary',plain(reader.read('report/summary'))==report['summary'])
        check('direct_MAT_execution','metadata',plain(reader.read('report/metadata'))==report['metadata'])
        check('direct_MAT_execution','mode_coverage',plain(reader.read('report/mode_coverage'))==list(range(6)))
    by_id = {r['id']: r for r in report['runs']}
    actual_modes=set()
    fresh_runs=[]
    for case in spec['cases']:
        path=folder/(case['id']+'.mat')
        evidence_files.append(dict(path=path.name,sha256=sha(path)))
        with Mat73Numeric(path) as reader:
            raw=reader.read('raw_data');trace=reader.read('trace');ticks=reader.read('raw_time')
            a=plain(reader.read('a'));rr=plain(reader.read('rr'))
            shape=plain(reader.read('native_shape'))
            check('native_signal',case['id']+'_shape',list(raw.shape)==shape)
            check('native_signal',case['id']+'_reshape',bits_equal(raw.reshape((1380,-1),order='F').T,trace))
            check('native_signal',case['id']+'_ticks',bits_equal(ticks,np.arange(len(case['schedule']),dtype=np.float64).reshape(-1,1)))
            check('native_signal',case['id']+'_finite',np.isfinite(raw).all())
            check('native_signal',case['id']+'_dimensions',trace.shape==(len(case['schedule']),1380))
        check('fixture_binding',case['id'],rows(a['schedule'])==case['schedule'] and a['p']==case['p'] and a['initial']==case['initial'])
        u=rows(a['input'])
        for k,(row,inp,s) in enumerate(zip(trace.tolist(),u,case['schedule'])):
            check('physical_input_binding',case['id']+f'_{k}',inp==[1,0,s[1],0,s[0],*s[2:],*case['initial']] and row[72:75]==[s[0],s[3],s[4]+2*s[5]])
        r=dict(id=case['id'],adapter=a,p=a['p'],input=a['input'],trace=plain(trace),summary=rr)
        _,ns=audit_run(r,'fresh_'+r['id']);fresh_runs.append(r)
        segments=int(trace[:,12].sum());events=int(trace[:,13].sum());actual_modes.update(trace[:,0].astype(int).tolist())
        observed=dict(id=r['id'],intervals=len(trace),segments=segments,events=events)
        run_counts.append(observed)
        check('execution_counts',r['id'],all(by_id[r['id']][k]==observed[k] for k in ['intervals','segments','events']))
    # Retrospective lane reads the original scalar structs and cell references.
    # It does not read the v76 JSON or binary exports.
    seal=json.loads((folder/'prior_mat_seal.json').read_text());prior_path=ROOT/seal['path']
    check('preservation','original_v76_MAT',sha(prior_path)==seal['sha256'])
    with Mat73Numeric(prior_path) as reader:
        prior_runs=plain(reader.read('report/runs'))
    for r in prior_runs:
        audit_run(r,'prior_direct_'+r['id'])

    target=copy.deepcopy(next(r for r in fresh_runs if r['id']=='multiple_cycles_one_call'))
    # Reviewer self-checks operate on private memory, not original files.
    for name,col in [('inventory',112),('work',136),('duration',106),('event',102)]:
        bad=copy.deepcopy(target);bad['trace']=copy.deepcopy(rows(target['trace']))
        bad['trace'][0][col]+=1
        mapped=copy.deepcopy(bad)
        for row in mapped['trace']:row[1]=73;row[72:75]=[0,0,0]
        try:
            with localcontext() as ctx:
                ctx.prec=160;cs,_=analyze(mapped)
            detected=any(not c['passed'] for c in cs)
        except (ArithmeticError,IndexError,ValueError):
            detected=True
        selfchecks.append(dict(name='synthetic_closed_'+name,passed=detected))
    raw_bad=np.arange(24,dtype=np.float64).reshape((2,3,4),order='F')
    selfchecks.append(dict(name='wrong_axis_order',passed=not bits_equal(raw_bad,raw_bad.transpose(2,1,0))))
    check('Stateflow','fresh_six_modes',actual_modes==set(range(6)))
    check('Stateflow','fresh_event_trajectory',next(r for r in run_counts if r['id']=='multiple_cycles_one_call')['events']>=2)
    check('Stateflow','observed_license_and_chart',report['metadata']['license_observed']==1 and report['metadata']['chart_count']==1 and report['metadata']['simulation_mode']=='normal')
    check('MATLAB','all_assertions',report['summary']['failed']==0 and all(c['passed'] for c in report['assertions']))
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json') if p.name!='execution_report.json']
    check('execution','successful_batch',any(e['exit_code']==0 for e in receipts))
    for e in json.loads((folder/'preservation.json').read_text()):check('preservation',e['path'],sha(ROOT/e['path'])==e['sha256'])
    for e in json.loads((folder/'source_hashes.json').read_text()):check('sources',e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256'])
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('ledger_prefix',e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
    ts=stamp();csvpath=folder/('direct_closed_traces_v77_'+ts+'.csv')
    with csvpath.open('x',newline='',encoding='utf-8') as out:
        writer=csv.DictWriter(out,fieldnames=list(numeric[0]));writer.writeheader();writer.writerows(numeric)
    # Pin the exact loaded package bytes without changing global environments.
    dep_manifest=[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in sorted((folder/'python_deps').rglob('*')) if p.is_file() and '__pycache__' not in p.parts]
    result=dict(version='0.77',timestamp_utc=datetime.now(timezone.utc).isoformat(),model_sha256=sha(ROOT/MODEL),
        evidence_class='DIRECT_ORIGINAL_MAT_HDF5_SAME_AGENT_INDEPENDENT_ALGORITHMS',
        dependencies=dict(h5py=h5py.__version__,numpy=np.__version__,hdf5=h5py.version.hdf5_version),dependency_files=dep_manifest,
        fresh_runs=run_counts,retrospective_runs=len(prior_runs),numeric_csv=csvpath.name,original_mat_files=evidence_files,
        checks=checks,reviewer_selfchecks=selfchecks,aggregates=aggregates,
        summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
    path=folder/('independent_QA_v77_'+ts+'.json');dump(path,result)
    log=dict(qa=path.relative_to(ROOT).as_posix(),summary=result['summary'],selfchecks=selfchecks,failed=[c for c in checks if not c['passed']][:40])
    dump(folder/('independent_QA_v77_'+ts+'.log'),log);print(json.dumps(log))
    return int(result['summary']['failed']>0 or not all(c['passed'] for c in selfchecks))


if __name__=='__main__':
    folder=(ROOT/sys.argv[2]).resolve();assert folder.is_relative_to(ROOT/'results')
    if sys.argv[1]=='prepare':prepare(folder)
    elif sys.argv[1]=='verify':sys.exit(verify(folder))
    else:raise ValueError('prepare or verify required')
