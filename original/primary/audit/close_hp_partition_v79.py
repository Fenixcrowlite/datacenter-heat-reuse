"""Close the local v79 checkpoint only after actual execution and all QA pass."""
from datetime import datetime,timezone
import hashlib,json,sys
from hp_partition_v79 import ROOT,MODEL,NEW,LEDGERS,dump,sha

def close(folder):
    report=json.loads((folder/'report.json').read_text())
    branch=json.loads((folder/'branch_report.json').read_text())
    paths={
        'independent':sorted(folder.glob('independent_QA_v79_*.json'))[-1],
        'capacity':sorted(folder.glob('strict_capacity_QA_v78_*.json'))[-1],
        'branch':sorted(folder.glob('branch_QA_v79_*.json'))[-1]}
    qa={name:json.loads(path.read_text()) for name,path in paths.items()}
    assert report['summary']['failed']==branch['summary']['failed']==0
    assert all(c['passed'] for c in report['assertions']+branch['checks'])
    for v in qa.values():
        assert v['summary']['failed']==0 and all(c['passed'] for c in v['checks']+v.get('reviewer_selfchecks',[]))
    assert qa['capacity']['report_sha256']==qa['branch']['report_sha256']==sha(folder/'report.json')
    assert qa['capacity']['reviewer_sha256']==sha(ROOT/'audit/strict_capacity_v78.py')
    assert qa['branch']['branch_sha256']==sha(folder/'branch_report.json')
    assert qa['branch']['reviewer_sha256']==sha(ROOT/'audit/verify_hp_branches_v79.py')
    assert qa['independent']['model_sha256']==sha(ROOT/MODEL)
    assert report['mode_coverage']==list(range(6))
    assert all(f['runtime_rejected'] for f in report['faults']+branch['faults'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    for run in ['run_hp_partition_v79(', 'run_hp_partition_branches_v79(']:
        assert any(v['exit_code']==0 and run in v['command'] for v in receipts)
    for e in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/e['path'])==e['sha256']
    for e in json.loads((folder/'ledger_prefixes.json').read_text()):
        assert hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256']
    for e in json.loads((folder/'branch_source_hashes.json').read_text()):
        assert sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256']
    prior=json.loads((ROOT/'STATUS_v78.json').read_text());assert sha(ROOT/prior['saved_model'])==prior['model_sha256']
    ts=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(r['summary']['held_intervals'] for r in report['runs'])
    segments=sum(r['summary']['positive_segments'] for r in report['runs'])
    events=sum(r['summary']['interior_events'] for r in report['runs'])
    sources=NEW+['matlab/run_hp_partition_branches_v79.m','audit/run_hp_partition_branches_v79.ps1',
        'audit/verify_hp_branches_v79.py','audit/preflight_hp_faults_v79.py','audit/close_hp_partition_v79.py','audit/verify_hp_partition_release_v79.py']
    limits=[
        'Reduced engineering HP assumption COP_h=1+A/lift; refrigerant/water temperature proxies and eta are not equipment calibration. No new primary-source signoff, article replication, measured validation, annual or generated-code acceptance; signoffs 0/31.',
        'Necessary integral overlap contract only: a recorded wide hull may include inadmissible members while overlapping valid values. An explicit independent wide-hull self-check documents this limit. No authentication or complete nonlinear trajectory certification is claimed by the runtime gate.',
        'Endpoint temperature extrema use monotonicity of held constant-forcing TES segments. Inherited closed exp/log QA independently checks actual trajectories. The gate does not independently reconstruct their ODE or event root.',
        'Same-agent algorithmic independence: exact Fraction HP bounds and 120/160-digit closed exp/log QA call no production MATLAB solver. MATLAB reopens original MAT and exports binary; no independent personnel or independent MAT parser claim.',
        'Bounded normal-mode synthetic schedules only. The added outward HP-bound arithmetic can reject unresolved/nonfinite extreme axes; unchanged policy/kernel retain finite span, clock, collision and segment-budget refusals.',
        'Six coordinated post-kernel record controls are unsaved chart instrumentation, never physical plant results. Thermal output, trace schema 75 and reporting API 0.76 remain unchanged.'
    ]
    next_task=('Resume primary equipment-map evidence and boundary audit from audit/HP_upstream_boundary_results_v44.md. '
        'Seek accessible primary text and performance-correlation supplement for DOI 10.1016/j.tsep.2025.103513. '
        'Distinguish verified equations/coefficients/domains from metadata and access blockers; trace refrigerant/water '
        'and compressor/auxiliary boundaries before a separately calibrated HP backend. Preserve v75-v79 acceptance.')
    status=dict(version='0.79',timestamp_utc=ts,inherits='STATUS_v78.json',
        result='SAVED_STATEFLOW_HP_TEMPERATURE_PARTITION_ACCEPTED_QA_PASS',new_model=True,
        saved_model=MODEL,saved_model_version='0.79',model_executed_this_run=True,model_sha256=sha(ROOT/MODEL),
        trace_schema=75,reporting_api_version='0.76',inherited_model_acceptance_preserved=True,
        correction_scope='Necessary source/compressor integral bounds from reduced temperature-dependent COP before trace emission and memory commit',
        matlab_passed=report['summary']['passed']+branch['summary']['passed'],matlab_failed=0,
        independent_passed=qa['independent']['summary']['passed'],independent_failed=0,
        exact_capacity_passed=qa['capacity']['summary']['passed'],exact_capacity_failed=0,
        branch_qa_passed=qa['branch']['summary']['passed'],branch_qa_failed=0,
        complete_saved_model_runs=len(report['runs']),fresh_saved_v78_comparisons=len(report['runs']),
        HP_axis_variants=12,completed_held_intervals=intervals,positive_event_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=report['mode_coverage'],actual_interior_event_types=[1,2,3],
        actual_runtime_fault_rejections=6,exact_bypass_fault_witnesses=6,legacy_v78_acceptance_witnesses=6,
        reviewer_selfchecks=sum(len(v.get('reviewer_selfchecks',[])) for v in qa.values()),
        matlab_metadata=report['metadata'],result_directory=rel,
        independent_qa=paths['independent'].relative_to(ROOT).as_posix(),
        exact_capacity_qa=paths['capacity'].relative_to(ROOT).as_posix(),branch_qa=paths['branch'].relative_to(ROOT).as_posix(),
        retained_failed_attempts=['results/hp_partition_v79_20261013T052939_919464Z','results/hp_partition_v79_20261013T053219_104653Z','results/hp_partition_v79_20261013T053510_914316Z'],
        derivation='audit/HP_partition_derivation_v79.md',results='audit/HP_partition_results_v79.md',source_code=sources,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limits,next_actionable_task=next_task)
    body=f'''UTC {ts}. Actual saved v79 Stateflow executes all six required modes.
MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent actual equation/artifact QA
{status['independent_passed']} PASS / 0 FAIL; exact MW/MWh capacity QA
{status['exact_capacity_passed']} PASS / 0 FAIL; focused independent runtime branch QA
{status['branch_qa_passed']} PASS / 0 FAIL. Reviewer self-checks are separately counted:
{status['reviewer_selfchecks']} PASS, including explicit wide-hull overlap acceptance.

{len(report['runs'])} schedules / {intervals} held intervals / {segments} positive segments /
{events} interior events (stop/cutoff/restart); 12 eta/source-temperature/inventory
variants include both floor-limited and inventory-dependent hot proxies. Every valid
trace double matches fresh saved-v78 execution. Saved kernel remains exactly v75.

Six coordinated source/work/auxiliary/copy corruptions pass the unsaved v78
energy/temporal-monitored chart and are rejected by v79 before emission/commit.
Four source-partition controls use work shares 0, 1, .5 and .01. A source-wide
zero-work control specifically reaches the compressor assertion; a zero-HP
spurious-source hull reaches the OFF assertion. Exact bypass witnesses prove
the changes reached output. Both harnesses reopen the clean saved model after
all unsaved instrumentation. No corrupt chart is saved or called plant evidence.

The new monitor derives necessary whole-segment HP integral bounds from TES
endpoint extrema, monotone source/work fractions and positive Kelvin axes.
It invokes no thermal solver, event finder or production quadrature loop.
Independent Fraction equations and inherited 120/160-digit exp/log trajectories
review original-MAT binary exports, conservation, source/work and reporting.

Model `{MODEL}` SHA256 `{status['model_sha256']}`.
Timestamped logs, receipts, original/reopened MAT, binary exports, numeric CSV,
fault logs, snapshots and preservation hashes: `{rel}`.
Three attempts executed all 25 valid schedules but failed in the fault harness
before fault acceptance: char/string concatenation, exact-zero handling, then
cumulative source/work copy indexing. All are preserved. The repaired harness
and scaffolder cast script text to char, retain exact zero, and use the correct
cumulative source/work columns 33:36. A separately labelled synthetic Python
preflight verifies all six fixture algebra controls before the completed batch.
The harness reuses the saved artifact without rebuilding or overwriting it.
Restricted-startup failure is also retained. Only complete successful batches count.
Compiler unused-monitor warnings arise in deliberate unsaved bypass copies.

Limitations:
'''+''.join('- '+v+'\n' for v in limits)+'\nNext actionable task: '+next_task+'\n'
    dump(ROOT/'STATUS_v79.json',status);dump(ROOT/'STATUS_stateflow_v79.json',status)
    for name in ['MASTER_STAGEBOARD_v79.md','MASTER_STAGEBOARD_stateflow_v79.md','audit/HP_partition_results_v79.md']:
        with (ROOT/name).open('x',encoding='utf-8') as f:f.write('# Executed Stateflow HP temperature partition v79\n\n'+body)
    progress=('\n\n## '+ts+' — v79 executed HP temperature-partition contract\n\n'
        'Read latest STATUS/stageboards v78, Stateflow acceptance, research frontier/progress and thermal '
        'kernel, monitors, builder, harness, adapter and reviewers before changes. Immediate Stateflow '
        'work takes priority. All work stayed in this project; Jarvice, unrelated files, settings, '
        'scheduled tasks and runner untouched. No external publication.\n\n'
        'Files added: versioned monitor, builder and generated SLX, main/branch MATLAB harnesses, '
        'local batch scripts, Fraction/closed-form/branch/release QA, initial scaffolder, derivation, '
        'results and STATUS/stageboard twins. New main harness repaired after preserved failed '
        'attempt. Prior code/models/data preserved and shared ledgers append only.\n\n'+body+
        '\nStop after this coherent executed deliverable and clear handoff.\n')
    for name in LEDGERS:
        text=progress if name.endswith('engineering_progress.md') else '\n\n## HP partition acceptance — '+ts+' / v79\n\n'+body
        with (ROOT/name).open('ab') as f:f.write(text.encode('utf-8'))
    artifacts=sources+[MODEL,'audit/HP_partition_results_v79.md','STATUS_v79.json','STATUS_stateflow_v79.json',
        'MASTER_STAGEBOARD_v79.md','MASTER_STAGEBOARD_stateflow_v79.md']
    for name in artifacts:
        dst=folder/'closure_snapshot'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/name).read_bytes())
    dump(folder/'checkpoint_hashes.json',[dict(path=name,sha256=sha(ROOT/name)) for name in artifacts])
    dump(folder/'evidence_seal.json',[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p))
        for p in sorted(folder.rglob('*')) if p.is_file() and not {'cache','codegen'}.intersection(p.relative_to(folder).parts)])
    print(json.dumps(dict(result=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],evidence=rel)))

if __name__=='__main__':
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results');close(folder)
