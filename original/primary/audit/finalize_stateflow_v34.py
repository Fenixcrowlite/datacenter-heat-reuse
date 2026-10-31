"""Close v34 only after actual execution and independent artifact QA pass."""
import argparse,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    assert not path.exists(),path
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('folder');parser.add_argument('qa');parser.add_argument('receipt');a=parser.parse_args()
    folder=Path(a.folder).resolve();qa_path=Path(a.qa).resolve();receipt_path=Path(a.receipt).resolve()
    qa=load(qa_path);summary=load(folder/'acceptance_summary_v34.json');receipt=load(receipt_path)
    spec=folder/'source_snapshot/spec';equations=load(spec/'equation_checks.json')
    assert summary['failed']==0 and receipt['exit_code']==0 and equations['failed']==0
    assert not any(c['failed'] for c in qa['counts'].values())
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v34.slx'
    assert digest(model)==qa['model_sha256'] and digest(ROOT/'audit/verify_stateflow_v34.py')==qa['reviewer_sha256']
    now=datetime.now(timezone.utc);tag=now.strftime('%Y%m%dT%H%M%S_%fZ')
    next_task=('Audit primary equipment/engineering evidence for the minimum-load COP cutoff, compressor dwell and cycling-loss assumptions; '
        'derive admissible restart-band constraints under changing source/demand. Preserve accepted v34 and distinguish screening assumptions '
        'from calibrated hardware before adding an equipment-fault or cycling-loss plant model.')
    limitations=[
        'Implementation acceptance of assumed mixed TES/HP screening plant only; no calibrated or measured physical validation or article replication.',
        'ON dwell is overridden by capacity/HP infeasibility; OFF dwell remains binding. The first near-capacity ON leg may be shorter than the nominal ON dwell.',
        'Bounded 64-slot analytic segments share the macro solver timestamp. Explicit physical-hour timers are executed; no solver-clock event scheduler or seconds-based temporal logic.',
        'Normal-mode host HP/event planner; standalone code generation, deployment, hydraulic/network model, stratification, ramping and startup/cycling losses remain untested.',
        'Restart band requires positive usable TES capacity; zero-capacity and zero-width-band control are rejected.',
        'Held-input partition evidence covers the tested finite fixtures only; no arbitrary input-partition equivalence, universal policy superiority or economic optimum.',
        'Host screening availability is trusted for safety-off decisions. Domain/monitor injections do not establish physical equipment or sensor fault behavior.',
        'Nonfatal formal-argument Stateflow shadow warnings remain in logs; no warnings were hidden by settings changes.',
        'Independent algorithm/artifact QA includes Decimal/bisection, RK4, alternate closed recurrence, saved-MAT/SLX and immutable hashes; it is not a separate human/agent review. Synthetic reviewer tests are separately counted.',
        'No new primary article equation or calibrated value adopted; full primary signoffs remain 0/31.'
    ]
    status=dict(version='0.34',inherits='STATUS_stateflow_v33.json',research_inherits='STATUS_v25.json',timestamp_utc=now.isoformat(),
        checkpoint='Executed persistent physical-hour HP hysteresis/dwell Stateflow and capacity-fallback repair',stateflow_acceptance='PASS',
        model_version='0.34',new_model=True,generated_model=str(model.relative_to(ROOT)),model_sha256=digest(model),
        controller_defect='v33 capacity-tail TES-service defect repaired for tested v34 fixtures',
        result_directory=str(folder.relative_to(ROOT)),independent_qa=str(qa_path.relative_to(ROOT)),execution_receipt=str(receipt_path.relative_to(ROOT)),
        execution_log=receipt['log_path'],matlab_batch_exit_code=receipt['exit_code'],scenarios=summary['scenarios'],intervals=summary['intervals'],
        segment_slots=summary['slots'],positive_segments=summary['positive_segments'],matlab_checks_passed=summary['passed'],matlab_checks_failed=summary['failed'],
        runtime_fault_rejections=summary['runtime_rejected'],independent_check_breakdown=qa['counts'],equation_checks_passed=equations['passed'],
        equation_checks_failed=equations['failed'],previous_immutable_entries_preserved=qa['previous_unique_entries'],
        max_abs_balance_residual_MWh=summary['max_abs_balance_residual_MWh'],full_primary_signoffs=0,total_sources=31,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limitations,next=next_task)
    report=[f'# v34 executed HP hysteresis/dwell Stateflow\n\nUTC: {now.isoformat()}. Actual saved model v34 acceptance PASS.\n',
        f'MATLAB {summary["passed"]}/{summary["passed"]} assertions PASS; {summary["scenarios"]} scenarios / {summary["intervals"]} intervals / '
        f'{summary["slots"]} slots ({summary["positive_segments"]} positive-duration); all six modes; '
        f'{summary["runtime_rejected"]}/{summary["runtime_faults"]} actual runtime rejections. '
        f'Maximum first-law residual {summary["max_abs_balance_residual_MWh"]:.9g} MWh. Independent RK4 equation checks {equations["passed"]}, zero failures.\n',
        'The saved SLX contains actual persistent HP_ON/HP_OFF states, six thermal modes, physical-hour elapsed accumulation, TES and clock memories, '
        'bounded 64-segment execution and a separate runtime monitor. Compilation alone was not treated as completion.\n',
        'The v33 low-load capacity tail is repaired in the tested fixtures: TES serves heat throughout HP OFF until cutoff. '
        'Both E0=9.9 and E0=10 cases have zero unmet over four hours at every tested macro partition. '
        'The fresh saved-v32 comparison retains the original unmet-demand counterexample.\n',
        '| Case | Macro step (h) | End TES (MWh) | HP electricity (MWh) | Unmet (MWh) | End physical age (h) |\n|---|---:|---:|---:|---:|---:|']
    for family in ['fallback','initial_capacity']:
        for dt in [4,2,1,.5,.25,.125]:
            v=qa['experiment_ledger'][f'{family}_h_{dt:g}']
            report.append(f'| {family} | {dt:g} | {v["E"]:.9f} | {v["electric"]:.9f} | {v["unmet"]:.9f} | {v["clock"][1]:.9f} |')
    report.extend(['\nThe independent closed-cycle recurrence verifies these energy, electricity, discharge and clock endpoints; '
        'fixture invariance is not an arbitrary-input or measured-equipment claim. Six base physical flow/energy cases also agree with newly executed saved v32; '
        'v34 explicitly commands request zero while HP OFF, whereas v32 recorded an unavailable nonzero request.\n',
        'Other executed cases include source/demand changes, feasible capacity-hold ON dwell, OFF dwell above/below restart, cutoff before dwell, '
        'finite backup/unmet, source limitation, zero/small loss and HP-only operation. Runtime faults include domain/control/clock violations, '
        'two delayed input faults (one NaN), explicit event-budget exhaustion, eleven allocation/clock corruption cases and iterator-tick timing corruption.\n',
        'Independent QA breakdown: `'+json.dumps(qa['counts'])+'`. Prior unique immutable entries preserved: '+str(qa['previous_unique_entries'])+'. '
        'Read-only saved MAT re-export binds every trace and fault diagnostic; SLX graph/functions bind the actual saved implementation. '
        'Synthetic reviewer challenges are separate from actual execution evidence.\n',
        'Failed attempts retained: sandbox MATLAB startup failed before execution; authorized local retry succeeded. '
        'First builder missed the additive choose-mode source; second compile exposed integer/double collector indexing, captured with diagnostic diary and repaired. '
        'First full harness had seven assertion failures (four unavailable-request diagnostic comparisons and three singleton empty-array shape checks). '
        'Its physical/oracle tests and 30 runtime rejections passed; corrected harness reran against the unchanged saved SLX. '
        'The first independent reviewer encountered empty eml XML tags on ordinary states; it was corrected to skip those tags, '
        'then required all four embedded function bindings and reran successfully. Failed source snapshot/log and exact successful reviewer source are retained.\n',
        'Evidence: `'+str(folder.relative_to(ROOT))+'`, `'+str(qa_path.relative_to(ROOT))+'`, `'+str(receipt_path.relative_to(ROOT))+'`. '
        'Policy/equations: `audit/TES_hysteresis_derivation_v34.md`.\n',
        'Remaining limitations:\n']+['- '+x for x in limitations]+['\nNext: '+next_task])
    result_report=ROOT/'audit/TES_hysteresis_results_v34.md';assert not result_report.exists();result_report.write_text('\n'.join(report)+'\n')
    save(ROOT/'STATUS_stateflow_v34.json',status)
    board=ROOT/'MASTER_STAGEBOARD_stateflow_v34.md';assert not board.exists()
    board.write_text(f'# v34: persistent HP hysteresis/dwell Stateflow\n\n{now.isoformat()}. Implementation acceptance PASS; model v34 saved and simulated.\n\n'
        f'{summary["scenarios"]} scenarios / {summary["intervals"]} intervals / {summary["positive_segments"]} positive analytic segments / six modes. '
        f'{summary["passed"]} MATLAB assertions; {summary["runtime_rejected"]} runtime rejections; {equations["passed"]} independent RK4 checks; '
        f'QA `{json.dumps(qa["counts"])}`; zero failures.\n\n'
        'v33 capacity-tail service defect repaired for tested v34 fixtures; zero unmet and matching energy/electricity/physical clock over six held-input partitions. '
        'All earlier baselines preserved. ON dwell has explicit safety overrides.\n\n'
        'Evidence: `audit/TES_hysteresis_results_v34.md`, `audit/TES_hysteresis_derivation_v34.md`, `'+str(folder.relative_to(ROOT))+'`, `'+str(qa_path.relative_to(ROOT))+'`.\n\n'
        'No calibrated/physical validation, article replication, real compressor-cycle data, standalone code generation or solver-clock event scheduling. Full primary signoffs 0/31.\n\nNext: '+next_task+'\n')
    progress=ROOT/'automation/engineering_progress.md'
    with progress.open('a',encoding='utf-8') as f:
        f.write(f'\n\n## {now.isoformat()} — v34 executed HP hysteresis/dwell Stateflow\n\n'
            'Read current status/stageboards, acceptance/frontier/primary TES evidence and production/oracle code first. Implemented an additive saved v34 model '
            'with two persistent HP states, explicit physical-hour clocks, TES OFF service, 64 bounded event slots and runtime gates. '
            'Derived event/dwell equations; created Decimal/bisection fixtures, RK4 checks and an alternate closed-cycle QA lane.\n\n'
            f'Pass/fail: MATLAB batch exit0, {summary["passed"]}/{summary["passed"]} assertions PASS; {summary["scenarios"]} scenarios/{summary["intervals"]} intervals/'
            f'{summary["positive_segments"]} positive segments; six modes; {summary["runtime_rejected"]} actual runtime rejections; '
            f'equations {equations["passed"]}/{equations["passed"]}; independent QA {json.dumps(qa["counts"])}; zero failures. '
            f'Max residual {summary["max_abs_balance_residual_MWh"]:.9g} MWh; {qa["previous_unique_entries"]} earlier immutable entries preserved. '
            'Sandbox startup, missing source, integer collector compile and seven harness assertion failures were repaired and rerun; earlier logs/results retained. '
            'Independent reviewer empty-eml XML failure repaired; failed and passing source snapshots/logs retained.\n\n'
            'Finding: E0=9.9 and10 low-load capacity cases now serve TES while HP OFF, with zero unmet over4h; end energy/electricity/physical clock agree '
            'across4,2,1,.5,.25,.125h partitions and an independent closed recurrence. Dwell is conditional on feasibility: safety overrides ON dwell; OFF dwell binds.\n\n'
            'Files created: matlab/simulink/*v34.m and DCHR_Dispatch_Stateflow_v34.slx; audit v34 spec/reviewer/finalizer/runner, derivation/results/QA/MAT evidence; '
            'timestamped logs/receipts, both failed and passing results; STATUS_stateflow_v34.json, MASTER_STAGEBOARD_stateflow_v34.md and immutable manifest. '
            'Existing edits only append this ledger and acceptance record; baseline files preserved.\n\n'
            'Remaining limits: '+ ' '.join(limitations)+'\n\nNext actionable task: '+next_task+'\n\n'
            'Run stops at coherent implementation acceptance and handoff. No Jarvice/unrelated files, settings, scheduler, agent runner, secrets or external publication changed.\n')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Persistent HP hysteresis/dwell acceptance — {now.isoformat()} / v34\n\n'
            f'New saved v34 executes {summary["scenarios"]} scenarios/{summary["intervals"]} intervals/{summary["positive_segments"]} positive segments/six modes; '
            f'{summary["passed"]} MATLAB assertions, {summary["runtime_rejected"]} actual runtime fault rejections and {equations["passed"]} independent RK4 checks, '
            'with independent numeric, closed-cycle, MAT, SLX and preservation QA, zero failures. v33 capacity-tail TES-service defect is repaired for tested fixtures. '
            'Physical-hour latch/timers persist; events are analytic intra-macro segments. ON dwell has safety overrides. All baselines preserved. '
            'Authoritative status/stageboard v34 and audit/TES_hysteresis_results_v34.md record implementation acceptance only; physical validation/article replication remain open.\n')
    # Close immutable manifest; active finalizer log and mutable ledgers excluded.
    paths={ROOT/'STATUS_stateflow_v34.json',board,result_report,Path(__file__).resolve(),qa_path,receipt_path,model}
    for base in [ROOT/'audit',ROOT/'automation/logs',ROOT/'matlab/simulink']:
        for path in base.glob('*v34*'):
            if path.is_dir():paths.update(p for p in path.rglob('*') if p.is_file() and '__pycache__' not in str(p))
            elif path.is_file() and 'finalize_console' not in path.name:paths.add(path)
    for path in (ROOT/'results').glob('stateflow_v34_*'):
        paths.update(p for p in path.rglob('*') if p.is_file())
    entries=[dict(path=str(p.relative_to(ROOT)),bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(paths)]
    manifest=ROOT/'audit'/f'Stateflow_manifest_v34_{tag}.json'
    save(manifest,dict(version='0.34',timestamp_utc=now.isoformat(),previous_entries_preserved=qa['previous_unique_entries'],
         mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active finalizer console','generated caches'],files=entries))
    assert all(digest(ROOT/e['path'])==e['sha256'] for e in entries)
    print(json.dumps(dict(status='PASS',checkpoint='STATUS_stateflow_v34.json',manifest=str(manifest.relative_to(ROOT)),immutable_files=len(entries))))
if __name__=='__main__':main()
