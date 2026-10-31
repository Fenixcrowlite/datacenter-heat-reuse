"""Close only after actual saved-model execution and independent QA pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
from temporal_commit_v77 import ROOT,MODEL,NEW,LEDGERS,dump,sha
def close(folder):
    report=json.loads((folder/'report.json').read_text());qapath=sorted(folder.glob('independent_QA_v77_*.json'))[-1];qa=json.loads(qapath.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in report['assertions']+qa['checks']+qa['reviewer_selfchecks'])
    assert report['mode_coverage']==list(range(6)) and all(f['runtime_rejected'] for f in report['faults'])
    for e in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/e['path'])==e['sha256']
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):assert hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256']
    assert sha(ROOT/MODEL)==qa['model_sha256']
    ts=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(r['summary']['held_intervals'] for r in report['runs']);segments=sum(r['summary']['positive_segments'] for r in report['runs']);events=sum(r['summary']['interior_events'] for r in report['runs'])
    next_task=('Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513. Distinguish verified coefficients/domains from metadata and record access blockers; trace refrigerant/water and compressor/auxiliary boundaries before a separately calibrated backend. Preserve accepted v75/v76/v77 evidence; no annual or calibrated performance inference.')
    limits=[
        'Synthetic bounded normal-mode schedules only; no annual, equipment calibration, primary replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.',
        'Same-agent algorithmic QA using Fraction exact-binary temporal equations and inherited 120/160-digit closed exp/log equations. MATLAB reopens original MAT and exports binary; no independent HDF5-reader or personnel claim.',
        'Release 0.77 embeds a pre-commit temporal monitor; thermal kernel, policy, trace schema 75 and v76 reporting API are unchanged. All accepted trace doubles match freshly executed saved v75.',
        'Runtime controls inject output-record faults into unsaved in-memory chart copies, with exact monitor-bypass witnesses. These controls are not physical plant simulations and are never saved as accepted models.',
        'The runtime guard proves protocol consistency, not every nonlinear event/dwell inequality or authentication against coordinated internally consistent replacement. Independent nonlinear QA remains required; inherited collision/span/clock/segment-budget domains remain.'
    ]
    sources=NEW+['audit/close_temporal_commit_v77.py','audit/verify_temporal_commit_release_v77.py']
    status=dict(version='0.77',timestamp_utc=ts,inherits='STATUS_v76.json',result='SAVED_STATEFLOW_TEMPORAL_PRECOMMIT_MONITOR_ACCEPTED_QA_PASS',
        new_model=True,saved_model=MODEL,saved_model_version='0.77',trace_schema=75,reporting_api_version='0.76',model_executed_this_run=True,
        model_sha256=qa['model_sha256'],inherited_model_acceptance_preserved=True,correction_scope='Runtime temporal candidate verification before Stateflow trace emission and retained-memory commit; unchanged thermal dispatch',
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),actual_runtime_fault_rejections=len(report['faults']),exact_bypass_fault_witnesses=len(report['faults']),
        complete_saved_model_runs=len(report['runs']),fresh_saved_v75_comparisons=len(report['runs']),completed_held_intervals=intervals,
        positive_event_segments=segments,interior_events=events,required_actual_final_mode_coverage=report['mode_coverage'],actual_interior_event_types=[1,2,3],
        matlab_metadata=report['metadata'],result_directory=rel,independent_qa=qapath.relative_to(ROOT).as_posix(),
        retained_failed_attempt='results/temporal_commit_v77_20261012T123551_584301Z',
        derivation='audit/Temporal_commit_derivation_v77.md',results='audit/Temporal_commit_results_v77.md',source_code=sources,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,limitations=limits,next_actionable_task=next_task)
    body=f'''UTC {ts}. New saved v77 Stateflow model executes all six required modes.
MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent algorithmic QA
{status['independent_passed']} PASS / 0 FAIL; {len(qa['reviewer_selfchecks'])} separate synthetic reviewer self-checks.
{len(report['runs'])} complete accepted schedules / {intervals} held intervals /
{segments} positive segments / {events} interior events, with actual stop/cutoff/restart coverage.
Every output double matches {len(report['runs'])} fresh saved-v75 comparisons.
The clean saved v77 artifact is reopened after all unsaved instrumentation
and matches its original valid trace again.

{len(report['faults'])} actual runtime assertion rejections have matching exact
single-fault monitor-bypass traces. These deliberately corrupted chart copies
are unsaved QA controls, not physical plant results. The saved artifact has
the exact original v75 thermal kernel and new v77 temporal monitor, with both
entry/during actions in every state checking before trace emission and commit.
Trace schema stays 75; reporting API stays 0.76.

Saved model `{MODEL}` SHA256 `{qa['model_sha256']}`.
Evidence `{rel}` retains timestamped MATLAB batch and Simulink diagnostics,
original/reopened MAT, binary exports, precision numeric CSV, all runtime
fault logs, source snapshots, preservation hashes and QA receipts.
Earlier failed restricted startup and heterogeneous-fixture attempt are retained
in `results/temporal_commit_v77_20261012T123551_584301Z`; neither counts as acceptance.

Limitations:
'''+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {next_task}\n\nStop after this coherent executed deliverable and clear handoff.\n'
    dump(ROOT/'STATUS_v77.json',status);dump(ROOT/'STATUS_stateflow_v77.json',status)
    for name in ['MASTER_STAGEBOARD_v77.md','MASTER_STAGEBOARD_stateflow_v77.md','audit/Temporal_commit_results_v77.md']:
        with (ROOT/name).open('x',encoding='utf-8') as f:f.write('# Executed Stateflow temporal pre-commit monitor v77\n\n'+body)
    progress='\n\n## '+ts+' — v77 actual Stateflow temporal pre-commit monitor\n\nRead latest STATUS/stageboards, Stateflow acceptance, research frontier/progress and saved v75/v76 kernel, builder, validators, adapter, harness and closed-form reviewer before edits. Immediate Stateflow work took priority; all work stayed in this project. No Jarvice, unrelated files, settings, scheduler, runner, secrets or external publication touched.\n\nFiles added: '+', '.join(sources)+', new SLX, derivation/results and STATUS/stageboard twins. Prior model/code/data preserved; shared ledgers append only.\n\n'+body
    for name in LEDGERS:
        text=progress if name.endswith('engineering_progress.md') else '\n\n## Stateflow temporal pre-commit acceptance — '+ts+' / v77\n\n'+body
        with (ROOT/name).open('ab') as f:f.write(text.encode('utf-8'))
    artifacts=sources+[MODEL,'audit/Temporal_commit_derivation_v77.md','audit/Temporal_commit_results_v77.md',
        'STATUS_v77.json','STATUS_stateflow_v77.json','MASTER_STAGEBOARD_v77.md','MASTER_STAGEBOARD_stateflow_v77.md']
    for name in artifacts:
        target=folder/'closure_snapshot'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
    dump(folder/'checkpoint_hashes.json',[dict(path=name,sha256=sha(ROOT/name)) for name in artifacts])
    dump(folder/'evidence_seal.json',[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in sorted(folder.rglob('*')) if p.is_file() and not {'cache','codegen'}.intersection(p.relative_to(folder).parts)])
    print(json.dumps(dict(result=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],runtime_faults=len(report['faults']),evidence=rel)))
if __name__=='__main__':
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');close(folder)
