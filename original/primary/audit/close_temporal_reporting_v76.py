"""Close only executed v76 evidence with passing independent QA; append ledgers."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,indent=2);f.write('\n')
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    assert not (ROOT/'STATUS_v76.json').exists()
    report=json.loads((folder/'report.json').read_text());qapath=sorted(folder.glob('independent_QA_v76_*.json'))[-1];qa=json.loads(qapath.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in report['assertions']+qa['checks']+qa['reviewer_selfchecks'])
    prior=json.loads((ROOT/'STATUS_v75.json').read_text());assert qa['model_sha256']==prior['model_sha256']
    ts=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(r['summary']['held_intervals'] for r in report['runs']);segments=sum(r['summary']['positive_segments'] for r in report['runs']);events=sum(r['summary']['interior_events'] for r in report['runs'])
    next_task=('Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md. Seek a new accessible route to source20 upstream [62] primary text and performance-correlation supplement, DOI 10.1016/j.tsep.2025.103513. Distinguish verified coefficients/domains from metadata; document access blockers and refrigerant/water/compressor/auxiliary boundaries before a separately calibrated backend. Preserve accepted saved v75 and v76 reporting evidence; no annual or calibrated-performance inference.')
    limits=[
        'Synthetic bounded schedules only. No annual, calibration, primary replication, measured physical validation or generated-code acceptance. Full primary signoffs remain 0/31.',
        'Same-agent algorithmic QA with Fraction exact-binary temporal checks and inherited 120/160-digit closed exp/log equations. MATLAB reopens original MAT; Python consumes its binary exports, not HDF5 independently. No independent personnel claim.',
        'No new SLX/controller or thermal-policy change. Saved model and trace schema remain 0.75; additive reporting API is 0.76. Production v75 reporting API remains preserved for compatibility and remains permissive for demonstrated controls.',
        'Temporal consistency is not authentication or a replacement for nonlinear trajectory QA. Coordinated record replacement and independent event/dwell feasibility proofs remain outside this production gate.',
        'Inherited finite span, segment-budget, clock and event-order domains remain. Four interior events execute in accepted schedules; the 19 isolated reporting controls use the second held interval of one non-event chain.'
    ]
    sources=['matlab/+dchr/validate_temporal_trace_v76.m','matlab/+dchr/report_held_schedule_v76.m','matlab/run_temporal_reporting_v76.m','audit/run_temporal_reporting_v76.ps1','audit/temporal_reporting_v76.py','audit/close_temporal_reporting_v76.py','audit/verify_temporal_release_v76.py']
    status=dict(version='0.76',timestamp_utc=ts,inherits='STATUS_v75.json',result='SAVED_V75_TEMPORAL_REPORTING_GATE_ACCEPTED_QA_PASS',
        new_model=False,saved_model=prior['saved_model'],saved_model_version='0.75',trace_schema=75,reporting_api_version='0.76',
        model_executed_this_run=True,model_sha256=qa['model_sha256'],inherited_model_acceptance_preserved=True,
        correction_scope='Temporal reporting continuity; thermal dispatch and SLX unchanged',
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),actual_reporting_corruption_rejections=len(report['mutations']),
        legacy_v75_acceptance_counterexamples=len(report['mutations']),complete_saved_model_runs=len(report['runs']),
        completed_held_intervals=intervals,positive_event_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'],matlab_metadata=report['metadata'],result_directory=rel,
        independent_qa=qapath.relative_to(ROOT).as_posix(),derivation='audit/Temporal_reporting_derivation_v76.md',results='audit/Temporal_reporting_results_v76.md',
        source_code=sources,primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limits,next_actionable_task=next_task)
    body=f'''UTC {ts}. Preserved saved Stateflow v75 freshly executes all six required modes.
MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent algorithmic QA
{status['independent_passed']} PASS / 0 FAIL; six separate reviewer self-checks.
{len(report['runs'])} complete actual saved-model runs / {intervals} held intervals /
{segments} positive segments / {events} interior events. All 19 isolated temporal
reporting corruptions are accepted by v75 and rejected by the additive v76 API.
Corrupted records are reporting controls, never physical simulation results.

No new SLX or thermal controller change. Model and trace schema remain 0.75;
reporting API is 0.76. Original saved-model hash `{qa['model_sha256']}` and
prior model/code/checkpoints are preserved. Reporting summaries match v75 for
all actual complete schedules except the reporting API version.

Evidence `{rel}` contains timestamped MATLAB logs, both restricted-startup
failure and successful batch receipts, Simulink diagnostics, original/reopened
MAT, binary exports, closed-equation numeric CSV, source snapshots and hashes.

New gate binds physical-clock copies and held boundaries, segment elapsed and
remaining duration, incoming/endpoint TES, HP latch/age and symbolic contacts,
boundary transition reasons and event/reset identities. Independent QA uses
exact-binary Fraction enclosure sums/differences and 120/160-digit closed
exp/log equations for complete nonlinear trajectories and all energy totals.
No production MATLAB function is called by Python.

Limitations:
'''+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {next_task}\n\nStop after this coherent executed deliverable and clear handoff.\n'
    dump(ROOT/'STATUS_v76.json',status);dump(ROOT/'STATUS_stateflow_v76.json',status)
    for name in ['MASTER_STAGEBOARD_v76.md','MASTER_STAGEBOARD_stateflow_v76.md','audit/Temporal_reporting_results_v76.md']:
        with (ROOT/name).open('x',encoding='utf-8') as f:f.write('# Executed saved-v75 temporal reporting repair v76\n\n'+body)
    progress='\n\n## '+ts+' — v76 saved-Stateflow temporal reporting repair\n\nRead latest STATUS/stageboards, Stateflow acceptance, frontier/progress, saved v75 builder/kernel and v74/v75 adapter/reporter/harness/reviewer code before changes. Work stayed in this project; no Jarvice, unrelated files, settings, scheduler, runner, secrets or external publication touched.\n\nFiles added: '+', '.join(sources)+', derivation/results and STATUS/stageboard twins. Existing ledgers append only.\n\n'+body
    for relpath in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
        text=progress if relpath.endswith('engineering_progress.md') else '\n\n## Temporal reporting gate acceptance — '+ts+' / checkpoint v76\n\n'+body
        with (ROOT/relpath).open('ab') as f:f.write(text.encode('utf-8'))
    supplement=[]
    for relpath in sources+['audit/Temporal_reporting_derivation_v76.md','audit/Temporal_reporting_results_v76.md']:
        src=ROOT/relpath;dst=folder/'closure_snapshot'/relpath;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes())
        supplement.append(dict(path=relpath,sha256=sha(src)))
    dump(folder/'closure_source_hashes.json',supplement)
    dump(folder/'checkpoint_hashes.json',[dict(path=p,sha256=sha(ROOT/p)) for p in ['STATUS_v76.json','STATUS_stateflow_v76.json','MASTER_STAGEBOARD_v76.md','MASTER_STAGEBOARD_stateflow_v76.md','audit/Temporal_reporting_derivation_v76.md','audit/Temporal_reporting_results_v76.md']])
    dump(folder/'evidence_seal.json',[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in sorted(folder.rglob('*')) if p.is_file() and not {'cache','codegen'}.intersection(p.relative_to(folder).parts)])
    print(json.dumps(dict(status=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],intervals=intervals,segments=segments,events=events,evidence=rel)))
if __name__=='__main__':main()
