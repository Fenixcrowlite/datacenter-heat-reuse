"""Close only an observed successful, independently reviewed v31 experiment."""
import argparse
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write_new(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)
def item(path):return dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=digest(path))

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('result_directory',type=Path);ap.add_argument('qa',type=Path);ap.add_argument('receipt',type=Path)
    args=ap.parse_args();folder=args.result_directory.resolve();qa=json.loads(args.qa.read_text());receipt=json.loads(args.receipt.read_text(encoding='utf-8-sig'))
    summary=json.loads((folder/'summary_v31.json').read_text());spec=json.loads((folder/'source_snapshot/spec/cases.json').read_text())
    eq=json.loads((folder/'source_snapshot/spec/equation_qa.json').read_text())
    assert qa['failed']==summary['failed']==eq['failed']==receipt['exit_code']==0
    assert qa['receipt_sha256']==digest(args.receipt) and qa['execution_log_sha256']==digest(ROOT/receipt['log_path'])
    assert qa['reviewer_sha256']==digest(ROOT/'audit/verify_TES_event_v31.py')
    assert qa['result_directory']==str(folder.relative_to(ROOT))
    expected_categories={'actual_numeric','static_saved_v30_model','artifact_runtime_and_preservation','synthetic_reviewer_self_checks'}
    assert set(qa['breakdown'])==expected_categories
    for category,counts in qa['breakdown'].items():
        checks=qa['checks'][category]
        assert counts['passed']==len(checks)>0 and counts['failed']==0 and all(c['passed'] for c in checks)
    assert summary['passed']==summary['checks']==3544 and summary['saved_model_scenarios']==50 and summary['saved_model_intervals']==310
    assert summary['component_domain_rejections']==12 and summary['saved_v30_modes']==list(range(6))
    for path in folder.joinpath('source_snapshot').glob('*.m'):
        matches=list((ROOT/'matlab').rglob(path.name));assert len(matches)==1 and digest(path)==digest(matches[0])
    preserved=0
    for name in ['Stateflow_manifest_v30_20261009T213038_443584Z.json','Stateflow_fault_manifest_v29_20261009T204014_224631Z.json']:
        for entry in json.loads((ROOT/'audit'/name).read_text())['files']:
            path=ROOT/entry['path'];assert item(path)==entry;preserved+=1
    assert preserved==qa['previous_immutable_entries_checked']
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v30.slx'
    assert digest(model)==json.loads((ROOT/'STATUS_stateflow_v30.json').read_text())['model_sha256']
    with (folder/'policy_comparison_v31.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    timestamp=datetime.now(timezone.utc);stamp=timestamp.strftime('%Y%m%dT%H%M%S_%fZ')
    next_task=('Design and implement additive Stateflow v32 with explicit intra-interval segments: '
               'HP request/COP/electricity per segment, capacity hold/recovery curtailment, '
               'cutoff shutdown and segment-level finite boiler/unmet balance. Preserve v24/v28/v30. '
               'Use v31 event/backup counterexamples as independent acceptance fixtures; never calculate finite backup from average TES power.')
    limitations=[
        'Checkpoint v31 executes the saved v30 Stateflow model and a new MATLAB event comparator. No new SLX and no event controller embedded in Stateflow.',
        'Constant ambient/heat capacity/loss coefficient and held available TES requests; no hydraulic, stratified or measured tank validation.',
        'Charging modulates to replace ambient loss at capacity; it does not implement shutdown/restart cycling, hysteresis or dwell.',
        'Charging compares accepted TES heat/loss only. Event comparator has no piecewise HP scheduling, nonlinear COP/electricity or full-system event monitor.',
        'Discharge backup/unmet is integrated over actual segments. Full-power event dispatch has no universal advantage over uniform throttling.',
        'Timestep sweep is h=2,1,0.5,0.25,0.125 hours over two hours for ten assumed scenario families, not a general optimizer or empirical sensitivity study.',
        'Saved v30 normal-mode host HP and helper shadow warnings remain; no standalone generated-code or event Stateflow transition timing acceptance.',
        '566 reduced-equation checks and independent Python artifact/numeric QA are not separate human/agent review, article replication or physical validation. Full primary signoffs remain 0/31.'
    ]
    state=dict(version='0.31',inherits='STATUS_stateflow_v30.json',research_inherits='STATUS_v25.json',timestamp_utc=timestamp.isoformat(),
               checkpoint='Executed boundary-event comparator versus preserved uniform v30 Stateflow',
               experiment_acceptance='PASS',stateflow_acceptance='INHERITED_V30_PASS_WITH_FRESH_50_SCENARIO_EXECUTION',
               model_version='0.30',generated_model=str(model.relative_to(ROOT)).replace('\\','/'),model_sha256=digest(model),
               new_stateflow_model=False,event_component_embedded_in_stateflow=False,
               result_directory=folder.relative_to(ROOT).as_posix(),independent_qa=args.qa.as_posix(),execution_receipt=args.receipt.as_posix(),
               execution_log=receipt['log_path'],matlab_batch_exit_code=receipt['exit_code'],matlab_version=summary['matlab_version'],
               component_cases=141,component_domain_rejections=12,saved_model_scenarios=50,saved_model_intervals=310,
               matlab_checks_passed=summary['passed'],matlab_checks_failed=0,equation_checks_passed=eq['passed'],
               independent_check_breakdown=qa['breakdown'],independent_checks_failed=0,
               max_abs_saved_v30_balance_residual_MWh=summary['max_abs_v30_balance_MWh'],
               previous_immutable_entries_preserved=preserved,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
               full_primary_signoffs=0,total_sources=31,limitations=limitations,next=next_task)
    write_new(ROOT/'STATUS_stateflow_v31.json',json.dumps(state,indent=2)+'\n')
    report=['# v31 executed TES event-policy comparison','',
            f'UTC: {timestamp.isoformat()}. Gate PASS: {summary["passed"]}/{summary["checks"]} MATLAB assertions; 141 component cases; 12 actual component domain rejections; 50 actual saved-v30 simulations / 310 intervals / all six modes. Independent equations 566/566 PASS. Independent evidence categories: `{qa["breakdown"]}`. Synthetic reviewer checks are separate. Maximum saved-model balance residual {summary["max_abs_v30_balance_MWh"]:.8g} MWh.','',
            'The production model remains release **0.30**. New event MATLAB component is tested before its future Stateflow integration. Existing model and immutable numerical baselines are preserved.','',
            '## Two-hour totals at the coarse h=2-hour boundary','',
            '| Scenario | Uniform TES discharge MWh | Event TES discharge MWh | Uniform unmet MWh | Event unmet MWh | Uniform accepted charge MWh | Event accepted charge MWh |',
            '|---|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        if float(row['dt_h'])!=2:continue
        columns=['v30_discharge_MWh','event_discharge_MWh','v30_unmet_MWh','event_unmet_MWh','v30_charge_MWh','event_charge_MWh']
        report.append('| '+row['family']+' | '+' | '.join(f'{float(row[n]):.9f}' for n in columns)+' |')
    report+=['','The cutoff example serves more TES heat under the event policy but leaves more unmet demand because full early discharge prevents simultaneous use of backup and the late deficit exceeds the boiler limit. The zero-rate example has equal TES energy under both policies but different unmet demand. Treating event TES energy/h as a constant power would conceal this difference. Near-cutoff cases show that uniform coarse-step throttling can reject all storage service while an initial event pulse is feasible. No policy dominance or optimization claim is made.','',
             '## Partition comparison','',
             '| Family | Uniform discharge at h=2 / h=0.125 MWh | Event discharge range MWh | Event endpoint range MWh |','|---|---:|---:|---:|']
    for family in sorted({r['family'] for r in rows}):
        group=[r for r in rows if r['family']==family];ds=[float(r['event_discharge_MWh']) for r in group];ends=[float(r['event_endpoint_MWh']) for r in group]
        report.append(f'| {family} | {float(group[0]["v30_discharge_MWh"]):.9f} / {float(group[-1]["v30_discharge_MWh"]):.9f} | {max(ds)-min(ds):.3g} | {max(ends)-min(ends):.3g} |')
    report+=['','The event policy preserves endpoint and integrated heat/loss/backup/unmet across these five partitions. The v30 uniform policy changes its constrained port allocation with h; its unbounded controls agree with the event model. This experiment tests the chosen reduced equations and control policy, not calibrated physical behavior.','',
             '## Evidence and reproduction','',
             f'- Result package: `{folder.relative_to(ROOT).as_posix()}`: original MAT simulations, separate MAT export, actual trace CSVs, event trace, comparison, source/model/spec snapshots and assertion ledger.',
             f'- Independent QA: `{args.qa.as_posix()}`; observed batch receipt: `{args.receipt.as_posix()}`; log: `{receipt["log_path"]}`.',
             '- Derivation/provenance: `audit/TES_boundary_event_derivation_v31.md`; new component `matlab/+dchr/+components/storage_event_kernel_v31.m`.',
             '- Run `python -X utf8 audit/TES_event_reference_v31.py` for a fresh spec, then `matlab -batch "addpath(\'matlab\',\'matlab/simulink\'); out=run_TES_event_comparison_v31(\'<fresh-spec>\'); export_TES_event_mat_audit_v31(out);"`. Capture a zero-exit receipt and run `python -X utf8 audit/verify_TES_event_v31.py <fresh-result> <receipt>`.',
             '- Initial sandbox startup failed before tests. First actual batch passed 3534/3544 but exposed ten empty-array shape failures in the one-sample feedback assertion. The assertion was repaired and the complete batch freshly rerun. Prior logs/results are retained. A speculative unused metadata field in the exporter was removed before its first execution; executed exporter source is separately snapshotted.',
             '', '## Limitations','']+['- '+v for v in limitations]+['','Next: '+next_task,'']
    write_new(ROOT/'audit/TES_event_results_v31.md','\n'.join(report))
    write_new(ROOT/'MASTER_STAGEBOARD_stateflow_v31.md',
              '# v31: executed TES boundary-event comparison\n\n'+report[2]+'\n\nModel release remains 0.30; the event component is not embedded in Stateflow. '
              'See `audit/TES_event_results_v31.md` and `audit/TES_boundary_event_derivation_v31.md`.\n\nNext: '+next_task+'\n')
    progress=f'''\n\n## {timestamp.isoformat()} — v31 event equations/component and actual saved-v30 comparison

Read latest research v25 and Stateflow v30 status/stageboards, acceptance, frontier, progress, prior primary TES evidence and relevant component/builder/harness/oracle code before edits. The immediate Stateflow acceptance was already executed at v30. Completed its next handoff: derived full-power capacity/cutoff events, implemented a new MATLAB event comparator and compared it with the actual preserved v30 SLX over five timesteps. Newly opened EnergyPlus 9.5 primary engineering documentation verifies target-temperature time inversion/piecewise integration; event control decisions and all scenario values are our engineering assumptions. No new article equation/result is adopted.

Pass/fail: final authorized local MATLAB batch exit 0; 3544/3544 assertions PASS; 141 component cases; 12 actual component domain rejections; 50 saved-v30 simulations/310 intervals/all six modes; independent equations 566/566 PASS; independent evidence {qa['breakdown']}, zero failures. Max saved-v30 residual {summary['max_abs_v30_balance_MWh']:.8g} MWh. Sandbox startup FAIL before tests; first actual batch 3534/3544 exposed a one-sample empty-vector shape assertion defect, corrected and rerun. All failed logs, receipt and result package preserved. Nonfatal existing Stateflow helper shadow warnings retained. Separate read-only MAT exporter and ZIP/XML structure review bind evidence to actual execution/saved model. No separate human/agent review claimed.

Finding: an event pulse can serve heat that coarse uniform throttling rejects. Full-power early discharge can also increase unmet demand with finite backup: the late deficit exceeds capacity even when total TES service is greater. Backup must be integrated per segment; average-TES backup arithmetic is invalid. Capacity control modulates to replace ambient loss; it does not implement cycling. Event integrated totals are partition invariant across the tested constant-input sweeps.

Files created: matlab/+dchr/+components/storage_event_kernel_v31.m; matlab/simulink/run_TES_event_comparison_v31.m and export_TES_event_mat_audit_v31.m; audit/TES_event_reference_v31.py, verify_TES_event_v31.py, finalize_TES_event_v31.py, TES_boundary_event_derivation_v31.md and TES_event_results_v31.md; timestamped specs/QA/receipts/logs; {folder.relative_to(ROOT).as_posix()}; STATUS_stateflow_v31.json; MASTER_STAGEBOARD_stateflow_v31.md; immutable manifest. Mutable engineering_progress and acceptance ledgers appended. No existing numerical/model/source baseline overwritten; {preserved} previous immutable manifest entries verified unchanged.

Remaining limits: {" ".join(limitations)}

Next actionable task: {next_task}

Run stops at this coherent comparison/QA checkpoint. Scheduler, runner, user settings, Jarvice, unrelated files and external publication were not touched.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Event-policy comparison checkpoint — {timestamp.isoformat()} / v31\n\nSaved v30 model executed afresh in 50 scenarios / 310 intervals / six modes. New standalone MATLAB event comparator passes 3544 MATLAB assertions including 12 domain rejections and 566 independent equation checks; independent evidence QA passes with separately labelled synthetic reviewer checks. No new SLX or event Stateflow implementation is claimed. Versioned status/stageboard v31 and audit/TES_event_results_v31.md record finite-backup timing counterexamples and the concrete v32 integration handoff. Existing v30 acceptance remains intact.\n')
    paths=set()
    for path in folder.rglob('*'):
        if path.is_file() and not any(v in path.relative_to(folder).parts for v in ['cache','codegen']):paths.add(path)
    for pattern in ['*v31*.py','*v31*.md','*v31*.json']:
        paths.update((ROOT/'audit').glob(pattern))
    for path in (ROOT/'audit').glob('TES_event_spec_v31_*'):
        paths.update(p for p in path.rglob('*') if p.is_file())
    for result in (ROOT/'results').glob('TES_event_v31_*'):
        paths.update(p for p in result.rglob('*') if p.is_file() and not any(v in p.relative_to(result).parts for v in ['cache','codegen']))
    paths.update((ROOT/'automation/logs').glob('TES_event_*v31*.log'))
    paths.update([ROOT/'STATUS_stateflow_v31.json',ROOT/'MASTER_STAGEBOARD_stateflow_v31.md',ROOT/'matlab/+dchr/+components/storage_event_kernel_v31.m',
                  ROOT/'matlab/simulink/run_TES_event_comparison_v31.m',ROOT/'matlab/simulink/export_TES_event_mat_audit_v31.m'])
    manifest=dict(version='0.31',timestamp_utc=timestamp.isoformat(),model_release='0.30',previous_immutable_entries_preserved=preserved,
                  mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active closure log','cache/codegen'],
                  files=[item(p) for p in sorted(paths)])
    manifest_path=ROOT/'audit'/f'TES_event_manifest_v31_{stamp}.json';write_new(manifest_path,json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(dict(status='STATUS_stateflow_v31.json',report='audit/TES_event_results_v31.md',manifest=manifest_path.relative_to(ROOT).as_posix(),immutable_files=len(paths),previous_preserved=preserved)))
    return 0

if __name__=='__main__':raise SystemExit(main())
