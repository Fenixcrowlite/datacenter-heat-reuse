"""Close only successful, independently bound v32 implementation evidence."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.resolve().relative_to(ROOT).as_posix()
def create(p,value):
    with p.open('x',encoding='utf-8') as f:f.write(value)
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('result_directory',type=Path)
    ap.add_argument('qa_report',type=Path)
    ap.add_argument('receipt',type=Path)
    args=ap.parse_args()
    folder=args.result_directory.resolve();qa_path=args.qa_report.resolve();receipt_path=args.receipt.resolve()
    for p in (folder,qa_path,receipt_path):rel(p)
    summary=load(folder/'acceptance_summary_v32.json');qa=load(qa_path);receipt=load(receipt_path)
    spec=load(folder/'source_snapshot/spec/cases.json');eq=load(folder/'source_snapshot/spec/equation_qa.json')
    categories={'actual_numeric','static_saved_model','artifact_runtime_preservation','synthetic_reviewer_checks'}
    assert summary['failed']==0 and summary['passed']>0 and summary['actual_saved_model_executed'] is True
    assert summary['scenarios']==len(spec['cases']) and summary['intervals']==sum(len(c['inputs']) for c in spec['cases'])
    assert summary['segments']==2*summary['intervals'] and summary['modes_observed']==list(range(6))
    assert summary['runtime_rejected']==summary['runtime_faults']==len(spec['domain_faults'])+2+len(spec['monitor_faults'])
    assert qa['failed']==0 and Path(qa['result_directory']).as_posix()==rel(folder)
    assert Path(qa['receipt']).resolve()==receipt_path
    assert set(qa['categories'])==set(qa['checks'])==categories
    for name in categories:
        count=qa['categories'][name];checks=qa['checks'][name]
        assert type(count['passed']) is int and count['passed']>0 and count['failed']==0
        assert len(checks)==count['passed'] and all(c['passed'] is True for c in checks)
    assert eq['failed']==0 and eq['passed']==len(eq['checks']) and all(c['passed'] is True for c in eq['checks'])
    verifier=ROOT/qa['verifier_path'];assert sha(verifier)==qa['verifier_sha256']
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v32.slx'
    assert sha(model)==qa['model_sha256']==sha(folder/'source_snapshot'/model.name)
    assert receipt['exit_code']==0 and receipt['evidence_class']=='observed_matlab_batch_receipt'
    log=ROOT/receipt['log_path'];rel(log);logtext=log.read_text(encoding='utf-8-sig')
    for marker in ('BATCH_ACCEPT_PASS','ACCEPTANCE_OUTPUT='+str(folder),'MAT_AUDIT_OUTPUT='+str(folder/'mat_audit_v32.json')):
        assert marker in logtext,marker
    from verify_stateflow_completion_v32 import receipt_binding
    assert receipt_binding(receipt,folder/'source_snapshot')
    prior_paths=[ROOT/'audit'/n for n in ('TES_event_manifest_v31_20261009T214244_178000Z.json',
        'Stateflow_manifest_v30_20261009T213038_443584Z.json','Stateflow_fault_manifest_v29_20261009T204014_224631Z.json')]
    preserved=0
    for manifest in prior_paths:
        for e in load(manifest)['files']:
            p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256'],e['path'];preserved+=1
    assert preserved==qa['previous_entries_preserved']
    utc=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    next_task=('Audit capacity-hold HP unavailability/source-limited fallback across macro timesteps; independently derive '
        'a justified restart/hysteresis/dwell policy before a new Stateflow version. Preserve v24/v28/v30/v32 and '
        'the finite-backup/electricity counterexamples; do not claim universal event-policy superiority.')
    limits=[
        'Two ordered analytic physical segments execute within each macro Simulink timestep; no solver-clock event activation claim.',
        'Normal-mode host HP planner is required. Standalone generated code remains untested.',
        'Constant ambient/heat capacity/loss coefficient and assumed screening COP/temperatures; no calibrated, stratified or hydraulic plant validation.',
        'Capacity fallback can cool until the next sample if the low-load HP hold is unavailable or source-limited; no cycling, hysteresis, dwell or equipment/sensor faults.',
        '64-ulp capacity-energy/equilibrium recognition handles binary roundoff; this is not a physical controller deadband.',
        'Fault coverage is 13 finite domain, two delayed finite and eight actual allocator corruption cases; delayed NaN/Inf timing is untested.',
        'A sample at StopTime represents a complete following interval. Interval mode summarizes segment modes, whose ordered traces remain authoritative.',
        'Independent algorithm/artifact QA is not separate human/agent review, article replication or measured physical validation. Full primary signoffs remain 0/31.',
        'Preserved v30 reference helper shadow warnings remain in the logs; no universal partition-invariance or policy superiority claim.'
    ]
    status=dict(version='0.32',inherits='STATUS_stateflow_v31.json',research_inherits='STATUS_v25.json',timestamp_utc=utc,
        checkpoint='Executed two-segment Stateflow with segment HP electricity and finite backup',stateflow_acceptance='PASS',
        model_version='0.32',generated_model=rel(model),model_sha256=sha(model),result_directory=rel(folder),
        independent_qa=rel(qa_path),execution_receipt=rel(receipt_path),execution_log=rel(log),matlab_batch_exit_code=0,
        matlab_version=summary['matlab_version'],scenarios=summary['scenarios'],intervals=summary['intervals'],
        segments=summary['segments'],positive_duration_segments=summary['positive_duration_segments'],
        matlab_checks_passed=summary['passed'],matlab_checks_failed=0,runtime_fault_rejections=summary['runtime_rejected'],
        equation_checks_passed=eq['passed'],equation_checks_failed=0,independent_check_breakdown=qa['categories'],
        independent_checks_failed=0,max_abs_balance_residual_MWh=summary['max_abs_balance_residual_MWh'],
        previous_immutable_entries_preserved=preserved,standalone_codegen=False,solver_clock_event_activations=False,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limits,next=next_task)
    statuspath=ROOT/'STATUS_stateflow_v32.json';board=ROOT/'MASTER_STAGEBOARD_stateflow_v32.md'
    assert not statuspath.exists() and not board.exists()
    counts=qa['categories'];gate=(f'{summary["passed"]}/{summary["passed"]} MATLAB assertions; '
        f'{summary["scenarios"]} scenarios / {summary["intervals"]} intervals / {summary["segments"]} segment slots '
        f'({summary["positive_duration_segments"]} positive-duration) / six modes; '
        f'{summary["runtime_rejected"]} runtime fault rejections; {eq["passed"]} independent equation checks')
    create(statuspath,json.dumps(status,indent=2)+'\n')
    create(board,f'# v32: executed segment Stateflow acceptance\n\nUTC: {utc}. PASS: {gate}.\n\n'
        f'Independent QA: `{counts}`; zero failures. Synthetic reviewer checks are separate. '
        f'Maximum interval balance residual: {summary["max_abs_balance_residual_MWh"]:.8g} MWh.\n\n'
        f'Model `{rel(model)}` uses `dchr_segment_plan_v32.m`; HP operating point/electricity and finite boiler/unmet '
        'are calculated per physical segment. Iterated chart activations occur within the macro timestep.\n\n'
        f'Evidence: `{rel(folder)}`, `{rel(qa_path)}`, `{rel(receipt_path)}`. '
        'See `audit/Stateflow_completion_review_v32.md`, `audit/TES_segment_Stateflow_derivation_v32.md` '
        'and `audit/TES_segment_Stateflow_results_v32.md`.\n\n'
        'Reproduce using `audit/run_stateflow_batch_v32.ps1 -Operation accept -SpecDirectory <spec>` '
        'and `python -X utf8 audit/verify_stateflow_completion_v32.py <fresh-result-directory> <receipt>`. '
        'The builder refuses to overwrite the saved release.\n\n'+
        '\n'.join('- '+s for s in limits)+f'\n\nNext: {next_task}\n')
    paths={p for p in folder.rglob('*') if p.is_file()}
    failed=ROOT/'results/stateflow_v32_20261010T022319311Z'
    if failed.exists():paths.update(p for p in failed.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'matlab').rglob('*v32.m'))
    paths.update(p for p in (ROOT/'audit').glob('*v32*') if p.is_file())
    paths.update(p for d in (ROOT/'audit').glob('stateflow_spec_v32_*') for p in d.rglob('*') if p.is_file())
    paths.update(p for p in (ROOT/'automation/logs').glob('*v32*') if p.is_file() and 'checkpoint_close' not in p.name)
    paths.update((model,statuspath,board,qa_path,receipt_path,verifier,Path(__file__).resolve()))
    paths={p for p in paths if not {'cache','codegen'}.intersection(p.relative_to(ROOT).parts)}
    manifestpath=ROOT/'audit'/f'Stateflow_manifest_v32_{stamp}.json'
    manifest=dict(version='0.32',timestamp_utc=utc,prior_manifests=[rel(p) for p in prior_paths],
        previous_entries_preserved=preserved,mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active closure console'],
        files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)])
    create(manifestpath,json.dumps(manifest,indent=2)+'\n')
    note=(f'\n\n## {utc} — v32 completed actual segment Stateflow and independent QA\n\n'
        'Resumed saved unaccepted v32 after reading latest Stateflow/research STATUS, stageboards, acceptance, frontier, progress '
        'and production/oracle sources. Completed fresh saved-model execution, fault assertions, independent equation/numeric '
        'QA, MAT re-export, SLX graph review, receipt/source/spec binding and preserved-baseline checks. '
        'Defined a 64-ulp capacity roundoff convention in the host planner and independent oracle. '
        'Corrected false-negative runtime diagnostic matching and unfinished static/receipt reviewer defects.\n\n'
        f'Pass/fail: final MATLAB batch exit 0; {gate}; all PASS. Independent QA {counts}; zero failures. '
        f'Maximum interval residual {summary["max_abs_balance_residual_MWh"]:.8g} MWh. '
        'Initial sandbox startup failed before simulations. First actual full batch executed all scenarios but failed 465 '
        'assertions (capacity segment classification and eight false-negative corruption labels); its receipt/MATs/logs are preserved. '
        'Static reviewer failures exposed hierarchical chart naming, label indentation and omitted defaults, corrected in a separate reviewer. '
        'Fresh local execution after repairs passed; no failed run is accepted. Existing model baselines were not overwritten.\n\n'
        'Files changed: matlab/simulink/dchr_segment_plan_v32.m, run_stateflow_faults_v32.m; audit/stateflow_reference_v32.py. '
        'New deliverables: audit/verify_stateflow_completion_v32.py, finalize_stateflow_completion_v32.py, '
        'Stateflow_completion_review_v32.md, TES_segment_Stateflow_results_v32.md, timestamped specs/reports/logs; '
        f'`{rel(folder)}`, `{rel(statuspath)}`, `{rel(board)}`, `{rel(manifestpath)}`. '
        'The saved v32 SLX/builder/harness are inherited from the unfinished work and now have executed acceptance; '
        f'{preserved} prior immutable manifest entries verified preserved. Mutable progress/acceptance ledgers appended.\n\n'
        'Remaining limits: '+' '.join(limits)+f'\n\nNext actionable task: {next_task}\n\n'
        'Run stops at this coherent implementation acceptance/handoff. No settings, scheduler, agent runner, Jarvice, '
        'unrelated files, secrets or external publication were changed.\n')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(note)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Actual segment-Stateflow acceptance — {utc} / v32\n\nSaved v32 model passes {gate}, '
            'with independent numeric/MAT/archive/receipt QA. Versioned STATUS/stageboard v32 are authoritative. '
            'Physical segments execute within a macro timestep, not at solver-clock events. Baselines preserved; '
            'implementation acceptance only, no article replication/calibrated physical validation.\n')
    for e in manifest['files']:
        p=ROOT/e['path'];assert p.stat().st_size==e['bytes'] and sha(p)==e['sha256']
    print(json.dumps(dict(status=rel(statuspath),manifest=rel(manifestpath),immutable_files_verified=len(manifest['files']),
        prior_entries_preserved=preserved),indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
