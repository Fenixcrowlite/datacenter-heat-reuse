"""Close only after actual saved-model execution and independent QA both pass."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import hashlib,json,sys
from electrical_ceiling_v83r2 import MODEL,LEDGERS,rows,sha,dump
ROOT=Path(__file__).resolve().parents[1]

def main(folder):
    report=json.loads((folder/'report.json').read_text());qa_path=sorted(folder.glob('independent_QA_v83*.json'))[-1]
    qa=json.loads(qa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in qa['checks']+qa['reviewer_selfchecks'])
    assert report['mode_coverage']==list(range(6)) and len(report['runs'])==25
    assert sha(ROOT/MODEL)==qa['model_sha256']
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    good=next(r for r in receipts if r['exit_code']==0);log=Path(good['log_path']).read_text()
    assert 'COMPLETE_RUNS=25 FAULTS=4' in log and 'ELECTRICAL_V83 PASS=' in log
    now=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(len(rows(r['trace'])) for r in report['runs'])
    segments=sum(int(row[12]) for r in report['runs'] for row in rows(r['trace']))
    events=sum(int(row[13]) for r in report['runs'] for row in rows(r['trace']))
    refs=sum(bool(rows(r['reference_trace'])) for r in report['runs'])
    selected=[r for r in report['runs'] if r['family']=='electrical_binding' and r['raw_policy'][25]==.05]
    next_task=('Audit the conservatism of the new global-Tmax compressor ceiling against '
        'an independently derived temperature-conditioned electrical limiter on identical '
        'cold/hot and charging histories. Quantify foregone delivered service and source '
        'recovery before any new limiter implementation. Seek the reference62 primary '
        'equipment supplement/rating domain via a new accessible route; synthetic Pmax '
        'and constant cooling factor must not become equipment calibration. Preserve v80-v83.')
    limits=[
        'Conservative global maximum-temperature cap, not a maximal instantaneous electrical limiter. Colder operation can leave compressor capacity unused.',
        'Synthetic compressor rating/constant cooling-factor reduction only; no acquired equipment supplement, calibration, article replication, measured physical validation, annual or generated-code acceptance. Full primary signoffs remain 0/31.',
        'Compressor electricity alone is limited. Configured auxiliary electricity remains separate and can make total external electricity exceed the compressor rating.',
        'The raw 26-operand policy is immutable within a schedule. Negative/nonfinite ceilings, invalid axes, nonfinite intermediate arithmetic and inherited span/clock/event-collision/segment-count domains reject.',
        'Trace schema 75 binds the effective 25-operand policy; separate certificate output binds raw electrical policy plus effective cap. Reporter v76 is preserved and does not itself authenticate raw electrical inputs.',
        'Same-agent independent exact Fraction and 120/160-digit closed exp/log algorithms call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.',
        'Saved model executes analytic physical segments inside macro protocol ticks, not at solver-clock events. Tested bounded schedules do not establish arbitrary-input acceptance.',
        'Initial restricted MATLAB startup failure, builder quoting syntax error and first v83 candidate/proof-refinement evidence are retained in prior attempt evidence; only the successful corrected batch counts.'
    ]
    text=(f'# Conservative electrical-ceiling Stateflow acceptance v83\n\nUTC {now}.\n\n'
        f'New actual saved model `{MODEL}` executes {len(report["runs"])} schedules / '
        f'{intervals} held intervals / {segments} positive segments / {events} interior events '
        f'and all six required modes. MATLAB {report["summary"]["passed"]} PASS / 0 FAIL; '
        f'independent equation/artifact QA {qa["summary"]["passed"]} PASS / 0 FAIL; '
        f'{len(qa["reviewer_selfchecks"])} separate reviewer corruptions detected. '
        f'Four actual saved-chart runtime refusals include a delayed nonbinding raw-rating '
        f'change. {refs} fresh saved-v80 reference comparisons are bitwise equal. '
        'The clean saved v83 model is reopened and replayed bitwise.\n\n'
        'The chart transforms an explicit finite compressor ceiling into a conservative '
        'heat-output ceiling using an outward enclosure of the existing tank-capacity guard. The first candidate is preserved; accepted model release is v83r2. Exact rational QA '
        'proves the selected heat rate respects the compressor rating throughout every '
        'accepted segment, including hot tank and repeated stop/restart histories. '
        'Zero rating produces exact zero HP heat and compressor work. Existing source, '
        'water, thermal, TES, dwell and energy guards remain embedded.\n\n'
        '| Initial TES (MWh) | Approaches evap/cond (K) | Compressor ceiling (MW) | Effective heat cap (MW) | Delivered service hull (MWh) | Compressor energy hull (MWh) |\n'
        '|---|---|---:|---:|---|---|\n')
    for r in selected:
        p=r['raw_policy'];s=r['summary']
        text+=f'| {r["adapter"]["initial"][0]} | {p[13]}/{p[17]} | {p[25]} | {r["p"][10]:.10g} | {s["delivered_service_MWh_hull"]} | {s["compressor_work_MWh_hull"]} |\n'
    text+=(f'\nModel SHA256 `{qa["model_sha256"]}`. Evidence `{rel}` contains '
        'timestamped MATLAB/Simulink and independent Python logs, execution receipt, '
        'original and reopened MAT, trace/certificate binary exports, numeric CSV, '
        'specification, sealed source snapshots, preservation hashes and fault logs. '
        'Prior attempted sources and logs remain separately linked in prior_attempts.json. '
        'No new primary article content was acquired or claimed. Derivation: '
        '`audit/Electrical_ceiling_derivation_v83.md`.\n\nLimitations:\n\n'+
        '\n'.join('- '+s for s in limits)+'\n\nNext actionable task: '+next_task+'\n\n'
        'Stop after this coherent executed deliverable and clear handoff.\n')
    status=dict(version='0.83',timestamp_utc=now,inherits='STATUS_v82.json',
        result='CONSERVATIVE_COMPRESSOR_CEILING_SAVED_STATEFLOW_ACCEPTED_CALIBRATION_OPEN',
        new_model=True,saved_model=MODEL,saved_model_version='0.83r2',model_sha256=qa['model_sha256'],
        model_executed_this_run=True,trace_schema=75,reporting_api_version='0.76',
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        complete_saved_model_runs=len(report['runs']),held_intervals=intervals,positive_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'],actual_fault_rejections=4,bitwise_v80_comparisons=refs,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),matlab_metadata=report['metadata'],result_directory=rel,
        independent_qa=qa_path.relative_to(ROOT).as_posix(),derivation='audit/Electrical_ceiling_derivation_v83.md',
        results='audit/Electrical_ceiling_results_v83.md',primary_article_replication=False,
        independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limits,next_actionable_task=next_task)
    for name in ['STATUS_v83.json','STATUS_stateflow_v83.json']:dump(ROOT/name,status)
    for name in ['MASTER_STAGEBOARD_v83.md','MASTER_STAGEBOARD_stateflow_v83.md','audit/Electrical_ceiling_results_v83.md']:
        with (ROOT/name).open('x',encoding='utf-8') as out:out.write(text)
    entry='\n\n## '+now+' вЂ” v83 actual conservative electrical-ceiling Stateflow\n\n'
    entry+=('Read STATUS/stageboards v82, full Stateflow acceptance/frontier, current '
        'code and existing primary-boundary evidence before changes. Work stayed in '
        'this project; Jarvice, unrelated files, settings, scheduler, runner and external '
        'publication untouched.\n\nFiles added: matlab/simulink/electrical_policy_v83r2.m, '
        'matlab/simulink/build_electrical_ceiling_v83r2.m, '+MODEL+', '
        'matlab/run_electrical_ceiling_v83r2.m, audit/electrical_ceiling_v83r2.py, '
        'audit/run_electrical_ceiling_v83r2.ps1, audit/close_electrical_ceiling_v83r2.py, '
        'derivation/results report, STATUS and stageboard twins. All prior production '
        'MATLAB/SLX/checkpoints are hash-preserved; shared ledgers appended only.\n\n'+text)
    for name in LEDGERS:
        with (ROOT/name).open('a',encoding='utf-8') as out:out.write(entry)
    seal=[]
    for p in list(folder.glob('*.json'))+list(folder.glob('*.mat'))+list(folder.glob('*.log'))+list(folder.glob('*.csv'))+list((folder/'binary').glob('*.bin')):
        seal.append(dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)))
    seal+=[dict(path=MODEL,sha256=sha(ROOT/MODEL)),dict(path='audit/close_electrical_ceiling_v83r2.py',sha256=sha(Path(__file__)))]
    dump(folder/'closure_seal.json',seal)
    print(json.dumps({k:status[k] for k in ['result','matlab_passed','independent_passed','held_intervals','positive_segments','interior_events','model_sha256']}))

if __name__=='__main__':main((ROOT/sys.argv[1]).resolve())
