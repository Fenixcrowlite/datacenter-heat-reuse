"""Publish workspace checkpoint only after independent evidence QA passes."""
from datetime import datetime,timezone
from pathlib import Path
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):
    if p.exists():raise FileExistsError(p)
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    folder=ROOT/Path(sys.argv[1]);qa_path=ROOT/Path(sys.argv[2]);receipt_paths=[ROOT/Path(x) for x in sys.argv[3:]]
    qa=read(qa_path);summary=qa['summary'];spec=read(folder/'source_snapshot/spec/cases.json')
    supplement=ROOT/qa['supplement_directory']
    assert qa['qa_failed']==0 and qa['synthetic']['failed']==0 and qa['unresolved_transitions']==10
    assert qa['certainly_premature_transitions']==0 and summary['harness_failed']==0
    assert len(receipt_paths)==4 and all(read(p)['exit_code']==0 for p in receipt_paths)
    stamp=datetime.now(timezone.utc);iso=stamp.isoformat();tag=stamp.strftime('%Y%m%dT%H%M%S_%fZ')
    relative=folder.relative_to(ROOT).as_posix();qarel=qa_path.relative_to(ROOT).as_posix()
    next_task=('Implement additive Stateflow v42 uncertainty-aware dwell decisions in planner, saved supervisor and runtime gate: '
        'require physical-age lower endpoint hi+lo-bound >= minimum dwell using cancellation-safe comparisons; '
        'schedule a conservative wait with certified post-add enclosure or explicitly reject unresolvable progress. '
        'Retain ON-dwell safety overrides and all v41 seeds/ties, then execute new SLX with independent interval timing, '
        'six-mode/reference, actual fault and saved-MAT QA. Preserve v40/v41 evidence. Then resume primary equipment traceability.')
    limitations=[
        'Audit evidence QA passes; uncertainty-aware controller acceptance FAILS for ten interval-unresolved transitions.',
        'No certainly premature physical transition is proved: admissible error sign/history of stress seeds is unknown.',
        'The 1e-9-hour seeds and 2^-80-hour seed are numerical fixtures, not measured clocks/equipment or demonstrated long-run histories.',
        'No corrected model is generated; model release remains 0.40 and its earlier acceptance stays scoped.',
        'Near-tie fixtures are assessed within existing energy/time resolution; exhaustive exact real-input ordering remains open.',
        'Normal-mode host planner executes analytic intra-macro segments; generated code/solver-clock event execution untested.',
        'No measured physical validation/article replication or new primary-text signoff; research remains 0/31 full signoffs.',
        'Independent algorithms in same agent, not independent personnel. Separate synthetic reviewer checks are not simulations.',
        'Inherited formal-argument shadow warnings and failed sandbox startup are retained in timestamped logs.',
        'Broad fixtures missed BACKUP; initial commentary misidentified missing mode as HEAT_RECOVERY. Targeted BACKUP supplement closes coverage. Initial reviewer assumed physical-cutoff precedence and aborted; failed attempts preserved.'
    ]
    status=dict(version='0.41',inherits='STATUS_stateflow_v40.json',research_inherits='STATUS_v25.json',timestamp_utc=iso,
        checkpoint='Saved-v40 clock uncertainty dwell-guard defect audit',stateflow_acceptance='DEFECT_CONFIRMED_OPEN',
        model_version='0.40',new_model=False,generated_model='matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx',
        model_sha256=hashlib.sha256((ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx').read_bytes()).hexdigest(),
        controller_defect='Clock bound persisted but ignored in ON/OFF dwell guards and nominal wait scheduling',
        result_directory=relative,supplement_directory=qa['supplement_directory'],independent_qa=qarel,matlab_batch_receipts=[p.relative_to(ROOT).as_posix() for p in receipt_paths],
        matlab_batch_exit_code=0,**{k:summary[k] for k in ('scenarios','completed_scenarios','intervals','positive_segments','harness_passed','harness_failed')},
        actual_runtime_fault_rejections=summary['scenarios']-summary['completed_scenarios'],six_modes_executed=True,
        independent_evidence_checks_passed=qa['qa_passed'],independent_evidence_checks_failed=qa['qa_failed'],
        synthetic_reviewer_checks_passed=qa['synthetic']['passed'],synthetic_reviewer_checks_failed=qa['synthetic']['failed'],
        independent_check_breakdown=qa['breakdown'],uncertainty_dwell_guarantee_failures=qa['unresolved_transitions'],
        certainly_premature_transitions=qa['certainly_premature_transitions'],max_independent_balance_residual_MWh=qa['max_balance_residual_MWh'],
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        limitations=limitations,next=next_task)
    write(ROOT/'STATUS_stateflow_v41.json',status)
    report=f'''# Saved-v40 clock uncertainty results — checkpoint v41

{iso}. **DEFECT_CONFIRMED_OPEN**. No new SLX or corrected-model acceptance.

Fresh saved model release 0.40 executes {summary['completed_scenarios']}/{summary['scenarios']} scenarios,
{summary['intervals']} intervals and {summary['positive_segments']} positive segments. Two deliberate
out-of-budget clock seeds reject at runtime. All six thermal modes are now executed,
including dedicated HP-only and BACKUP fixtures. MATLAB harness {summary['harness_passed']}/{summary['harness_passed']+summary['harness_failed']} PASS.
Four successful batches execute the broad fixtures and targeted BACKUP supplement,
then separately re-export each set of saved MAT traces. Supplement: {qa['supplement_directory']}.
Independent actual evidence checks {qa['qa_passed']} PASS / {qa['qa_failed']} FAIL;
separate synthetic reviewer checks {qa['synthetic']['passed']} PASS / {qa['synthetic']['failed']} FAIL.
These counts validate defect evidence, not a corrected controller.

The persisted clock represents age in [hi+lo-bound,hi+lo+bound]. The saved
planner, supervisor guard and runtime guard omit bound in their minimum-dwell
decision. **Ten transitions have lower age below the dwell threshold while
upper age reaches it.** No certainly premature physical transition is proved.
The guarantee is unresolved for those valid seeds, so broadening acceptance
is blocked until an uncertainty-aware policy is implemented and tested.

| Seed (both ON and OFF) | Transition offset, hours | Lower-age shortfall, hours |
|---|---:|---:|
| hi=1, lo=0, bound=1e-9 | 0 | 1e-9 |
| hi=1-5e-10, lo=0, bound=1e-9 | 5.000000413701855e-10 | 1e-9 |
| hi=1+5e-10, lo=0, bound=1e-9 | 0 | 4.999999586298146e-10 |
| hi=1-2e-9, lo=0, bound=1e-9 | 2.0000000544584395e-9 | 1e-9 |
| hi=1, lo=0, bound=2^-80 | 0 | 8.271806125530277e-25 |

All seeds use minimum dwell=1 hour. Shortfalls are exact-input interval
properties, not measured errors. Positive/negative zero-bound residuals,
zero-bound threshold and confidently late controls pass. The certainly early
bound control waits to nominal equality but still ignores the remaining
uncertainty. Decimal compensated-add enclosures, TES ODE, bounds and first laws
pass; maximum independent system residual {qa['max_balance_residual_MWh']:.17g} MWh.

Zero-loss ties at dwell=1 hour and adjacent doubles are executed. At cutoff,
the earlier dwell event precedes the cutoff; exact tie selects cutoff; later
dwell retains a tiny additional OFF segment. At capacity, later ON dwell has
the documented unavailable-HP safety override. These are scoped resolution
observations, not a proof over all real input ordering. The independent
six-mode baseline comparison passes.

The first audit completed but lacked BACKUP; its failed coverage report
is preserved at results/stateflow_clock_v41_20261010T125341508Z. Its initial
reviewer assumed all cutoff fixtures would contain a cutoff event, which was
wrong for an earlier dwell event; the aborted source/log are retained. Added
HP-only control, the targeted BACKUP supplement and the corrected independent
earliest-event expectation pass. The supplement avoids another broad rerun.
Initial commentary misidentified the missing mode; saved traces and final
mode assertions establish the corrected coverage. No prior model evidence changes.

Evidence: {relative}; {qarel}; STATUS_stateflow_v41.json;
audit/Clock_uncertainty_derivation_v41.md; timestamped logs/receipts.

Limitations:
'''+''.join('- '+x+'\n' for x in limitations)+f'\nNext actionable task: {next_task}\n'
    (ROOT/'audit/Clock_uncertainty_results_v41.md').write_text(report,encoding='utf-8')
    (ROOT/'MASTER_STAGEBOARD_stateflow_v41.md').write_text(f'''# v41 saved-v40 clock uncertainty defect checkpoint

{iso}. DEFECT_CONFIRMED_OPEN; saved model remains 0.40; no new SLX.
{summary['scenarios']} scenarios / {summary['completed_scenarios']} completed / {summary['intervals']} intervals /
{summary['positive_segments']} positive segments / six modes. MATLAB {summary['harness_passed']} PASS / 0 FAIL;
two actual clock-budget rejections. Independent actual QA {qa['qa_passed']} PASS / 0 FAIL;
synthetic {qa['synthetic']['passed']} PASS / 0 FAIL. Ten interval-unresolved dwell transitions;
zero certainly premature physical transitions proved. Controller guarantee defect OPEN.

Evidence: STATUS_stateflow_v41.json; audit/Clock_uncertainty_derivation_v41.md;
audit/Clock_uncertainty_results_v41.md; {qarel}.

Next: {next_task}
''',encoding='utf-8')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Saved-v40 clock uncertainty defect — {iso} / checkpoint v41

Saved v40 freshly executed: {summary['scenarios']} scenarios/{summary['completed_scenarios']} completed/
{summary['intervals']} intervals/{summary['positive_segments']} positive segments/six modes;
MATLAB {summary['harness_passed']}/0 failures, two actual clock-budget rejections;
independent actual QA {qa['qa_passed']}/0 failures and separate synthetic {qa['synthetic']['passed']}/0.
Ten interval-unresolved minimum-dwell decisions confirm an OPEN guarantee
defect: bound is persisted but omitted from dwell guards/waits. No certainly
premature physical transition proved, no new SLX or repaired acceptance.
STATUS/stageboard v41 and audit/Clock_uncertainty_results_v41.md are authoritative.
Prior v40 acceptance remains scoped. Next: additive v42 uncertainty-aware repair.
''')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## {iso} — v41 saved-Stateflow clock uncertainty audit

Read acceptance, latest STATUS/stageboards, research frontier and production
code before editing. Derived exact-input age enclosure and safe dwell
criterion, added numerical seeds/event ties, executed immutable saved v40,
separately re-exported MAT traces and ran independent Decimal/interval QA.
Meaningful deliverable: documented OPEN dwell guarantee defect and v42 handoff.

Pass/fail: four MATLAB execution/MAT-export batches exit 0. Harness
{summary['harness_passed']} PASS / 0 FAIL; {summary['scenarios']} scenarios/{summary['completed_scenarios']} completed/
{summary['intervals']} intervals/{summary['positive_segments']} positive segments/six modes; two deliberate
clock-budget runtime rejections. Independent actual evidence {qa['qa_passed']} PASS / 0 FAIL;
separate synthetic {qa['synthetic']['passed']} PASS / 0 FAIL. Controller guarantee: ten
interval-unresolved dwell transitions, OPEN; zero certainly premature
physical transitions proved. First-law max residual {qa['max_balance_residual_MWh']:.17g} MWh.

Files added: matlab/simulink/run_stateflow_clock_v41.m and
export_stateflow_clock_v41.m; audit prepare/verifier/launcher/finalizer v41;
timestamped v41 specs, results/source/MAT/QA, logs/receipts, derivation/results,
STATUS/stageboard and artifact manifest. Only progress and acceptance ledgers
are appended. No saved SLX/production code overwritten. First run/reviewer
coverage/precedence failures and sandbox startup failure remain preserved.

Limitations: evidence QA is not corrected-controller acceptance; seed bounds
are engineering uncertainty fixtures with unknown physical error sign/history.
Same-agent independent algorithms, normal-mode intra-macro events, no measured
physical validation or article replication/primary calibration; full signoffs 0/31.
Existing warnings retained. No Jarvice/unrelated files, settings, scheduler,
runner, secrets or external publication touched.

Next actionable task: {next_task}
Evidence: {relative}; {qarel}; audit/Clock_uncertainty_results_v41.md.
Stop after this coherent defect audit and clear handoff.
''')
    # Seal all release artifacts after tests; cache/ongoing finalizer logs omitted.
    paths=set(folder.rglob('*'))
    paths.update(supplement.rglob('*'))
    paths.update(ROOT/'audit'/x for x in ('prepare_stateflow_clock_v41.py','verify_stateflow_clock_v41.py','run_stateflow_clock_v41.ps1',
        'finalize_stateflow_clock_v41.py','prepare_stateflow_clock_supplement_v41.py','check_stateflow_clock_checkpoint_v41.py','Clock_uncertainty_derivation_v41.md','Clock_uncertainty_results_v41.md'))
    paths.update(ROOT/'matlab/simulink'/x for x in ('run_stateflow_clock_v41.m','export_stateflow_clock_v41.m'))
    paths.update(ROOT/x for x in ('STATUS_stateflow_v41.json','MASTER_STAGEBOARD_stateflow_v41.md'))
    paths.update(receipt_paths)
    paths.update(ROOT/read(p)['log_path'] for p in receipt_paths)
    paths.update((ROOT/'audit').glob('Stateflow_execution_v41_*.json'))
    paths.update((ROOT/'audit').glob('stateflow_clock_spec_v41_*/cases.json'))
    paths.update((ROOT/'audit').glob('stateflow_clock_spec_v41_*/preservation.json'))
    paths.update((ROOT/'automation/logs').glob('stateflow_clock_v41_QA_*.log'))
    paths.update((ROOT/'automation/logs').glob('stateflow_clock_v41_console_*.log'))
    paths.update((ROOT/'results/stateflow_clock_v41_20261010T125341508Z').rglob('*'))
    files=[]
    for path in sorted(paths):
        if path.is_file() and 'local_build' not in path.parts:
            files.append(dict(path=path.relative_to(ROOT).as_posix(),bytes=path.stat().st_size,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest=ROOT/'audit'/('Stateflow_clock_manifest_v41_'+tag+'.json')
    write(manifest,dict(timestamp_utc=iso,model_release='0.40',new_model=False,scope='Defect-audit evidence; no repaired acceptance',
        mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','local_build','active finalizer log'],files=files))
    print('STATUS=STATUS_stateflow_v41.json');print('MANIFEST='+manifest.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
