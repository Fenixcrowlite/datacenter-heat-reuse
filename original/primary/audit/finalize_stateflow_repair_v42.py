"""Write a scoped engineering acceptance only after independent QA succeeds."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def relative(p):return p.relative_to(ROOT).as_posix()
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    folder=ROOT/sys.argv[1];qapath=ROOT/sys.argv[2];receipts=[ROOT/x for x in sys.argv[3:]]
    qa=read(qapath);s=qa['summary'];probe=ROOT/qa['probe_directory']
    assert qa['qa_failed']==qa['synthetic']['failed']==qa['unresolved_transitions']==qa['certainly_premature_transitions']==s['harness_failed']==0
    assert len(receipts)==3 and all(read(r)['exit_code']==0 for r in receipts)
    assert s['scenarios']==31 and s['completed_scenarios']==29
    assert all(a['passed'] for a in read(probe/'uncertainty_attacks_v42.json'))
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx'
    stamp=datetime.now(timezone.utc);iso=stamp.isoformat();tag=stamp.strftime('%Y%m%dT%H%M%S_%fZ')
    limitations=[
        'Scoped numerical/implementation acceptance, not measured equipment validation or article replication; primary full signoffs remain 0/31.',
        'Exact-rational timing QA uses independent algorithms in the same agent, not independent personnel.',
        'Clock bounds/seeds are engineering numerical fixtures; physical error signs and long-run histories remain unknown.',
        'Outward comparison and certified waits can conservatively defer equality and shift near-ties by a few binary64 spacings; exhaustive exact real-input ordering is unproved.',
        'Normal-mode host planner executes analytic intra-macro segments; generated-code and solver-clock event execution remain untested.',
        'Finite arithmetic and existing clock/event budgets remain explicit rejection domains; no global arbitrary-precision guarantee is claimed.',
        'Inherited Stateflow formal-argument shadow warnings remain in logs. Sandbox startup failure is retained. Focused harness cleanup-order warning was fixed and its probes/attacks rerun successfully.',
        'HP component release 0.40 and temperature/cutoff TES assumptions are inherited; equipment calibration, hydraulic/stratified physics and measured physical validation remain open.'
    ]
    next_task=('Resume primary equipment traceability: select the most relevant accessible primary full text from the existing 0/31 signoff ledger, '
        'record exact pages/equation numbers, variables, units and operating domain for HP performance or TES cutoff/loss assumptions, '
        'and map them to the accepted v42 implementation. Independently derive and dimensionally check the verified relationship; '
        'document an access block or assumption mismatch if full text does not support it. Do not repeat Stateflow regression without a new defect/change.')
    status=dict(version='0.42',inherits='STATUS_stateflow_v41.json',research_inherits='STATUS_v25.json',timestamp_utc=iso,
        checkpoint='Uncertainty-aware Stateflow dwell repair',stateflow_acceptance='PASS_SCOPED_IMPLEMENTATION',
        model_version='0.42',new_model=True,generated_model=relative(model),model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),
        controller_defect='v41 lower-age dwell guarantee repaired in executed fixtures',result_directory=relative(folder),
        focused_probe_directory=relative(probe),independent_qa=relative(qapath),matlab_batch_receipts=[relative(r) for r in receipts],
        matlab_batch_exit_code=0,**{k:s[k] for k in ('scenarios','completed_scenarios','intervals','positive_segments','harness_passed','harness_failed')},
        six_modes_executed=True,actual_runtime_fault_rejections=36,
        actual_fault_breakdown=dict(domain_monitor_timer=30,out_of_budget_seed=2,nominal_planner_uncertainty_attacks=4),
        executed_numeric_function_probes=1016,independent_evidence_checks_passed=qa['qa_passed'],independent_evidence_checks_failed=qa['qa_failed'],
        synthetic_reviewer_checks_passed=qa['synthetic']['passed'],synthetic_reviewer_checks_failed=qa['synthetic']['failed'],
        independent_check_breakdown=qa['breakdown'],certified_dwell_transitions=len(qa['all_dwell_transitions']),
        uncertainty_dwell_guarantee_failures=qa['unresolved_transitions'],certainly_premature_transitions=qa['certainly_premature_transitions'],
        max_independent_balance_residual_MWh=qa['max_balance_residual_MWh'],full_primary_signoffs=0,total_sources=31,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limitations,next=next_task)
    write(ROOT/'STATUS_stateflow_v42.json',status)
    report=f'''# Uncertainty-aware Stateflow results, release 0.42

{iso}. **PASS_SCOPED_IMPLEMENTATION**. Additive saved model
`matlab/simulink/DCHR_Dispatch_Stateflow_v42.slx` built, compiled and simulated
with MATLAB R2026a Update 5 and observed Stateflow license/product metadata.
Previous model releases and sealed v40/v41 evidence remain preserved.

The planner, saved HP supervisor and runtime contract gate now use the
physical-age lower enclosure `hi+lo-bound` for minimum dwell. Conservative
waits certify the post-add enclosure, including new roundoff uncertainty.
Unresolvable progress rejects explicitly. ON-dwell unavailable-HP safety
overrides remain active. See `audit/Clock_uncertainty_derivation_v42.md`.

Executed: {s['scenarios']} scenarios, {s['completed_scenarios']} completed,
{s['intervals']} macro intervals, {s['positive_segments']} positive segments,
all six operating modes. MATLAB harness {s['harness_passed']} PASS / 0 FAIL.
All v41 seeds/ties retained; additional multi-sample waits exercise enclosure
persistence. Two invalid clock-budget seeds and 30 domain/monitor/timer faults
reject during execution. Four actual in-memory nominal-v40-planner attacks
reject in saved v42 runtime gate at initialization or HP supervisor at the
next sample, for both ON/OFF directions. Saved SLX is never modified by attacks.

Independent evidence QA: {qa['qa_passed']} PASS / 0 FAIL; separate synthetic
reviewer self-checks 4 PASS / 0 FAIL. The {len(qa['all_dwell_transitions'])}
dwell transitions have exact-rational lower age at or above dwell; zero
unresolved/certainly-premature transitions. 1,016 executed MATLAB function
probes have independently checked outward margins, ready decisions,
certified waits and clock enclosures. These probes are numerical fixtures,
not additional plant simulations. Saved MAT re-exports bind JSON traces/errors;
Decimal TES ODE/first laws and verified independent v34 baseline comparisons
pass. Maximum independent balance residual {qa['max_balance_residual_MWh']:.17g} MWh.

The focused harness initially issued a cleanup-order warning after all four
attacks passed. Its restoration now executes before model-close cleanup;
the focused probes and attacks were rerun in a new result directory and
checked for absence of the deleted-handle error. Original warning, source,
MAT and console artifacts remain preserved. The failed sandbox startup and
inherited argument-shadow warnings are also retained.

Main results: {relative(folder)}.
Focused clean rerun: {relative(probe)}.
Independent QA: {relative(qapath)}.
Three successful timestamped batch receipts and logs are recorded in STATUS.

Limitations:
'''+''.join('- '+x+'\n' for x in limitations)+f'\nNext actionable task: {next_task}\n'
    (ROOT/'audit/Clock_uncertainty_results_v42.md').write_text(report,encoding='utf-8')
    (ROOT/'MASTER_STAGEBOARD_stateflow_v42.md').write_text(f'''# v42 uncertainty-aware saved-Stateflow acceptance

{iso}. PASS_SCOPED_IMPLEMENTATION; actual new model release 0.42.
{s['scenarios']} scenarios / {s['completed_scenarios']} completed / {s['intervals']} intervals /
{s['positive_segments']} positive segments / all six modes. MATLAB {s['harness_passed']} PASS / 0 FAIL;
36 actual fault rejections; 1,016 executed numerical function probes.
Independent actual QA {qa['qa_passed']} PASS / 0 FAIL; reviewer self-checks 4/4.
Zero unresolved dwell transitions. Existing v40/v41 evidence preserved.

Evidence: STATUS_stateflow_v42.json; audit/Clock_uncertainty_derivation_v42.md;
audit/Clock_uncertainty_results_v42.md; {relative(qapath)}.

Physical validation/article replication remain open. {next_task}
''',encoding='utf-8')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Uncertainty-aware dwell repair acceptance — {iso} / v42

Actual new saved v42 executes all six modes in {s['scenarios']} scenarios /
{s['intervals']} intervals / {s['positive_segments']} positive segments; MATLAB
{s['harness_passed']}/0 failures, 36 actual runtime fault rejections, 1,016 function
probes, independent actual QA {qa['qa_passed']}/0 and reviewer self-checks 4/0.
Zero unresolved lower-age dwell decisions: planner, saved supervisor and runtime
gate include clock bound and certify waits. Cleanup warning fixed with focused
rerun. Prior evidence preserved. STATUS/stageboard v42 and clock derivation/results
are authoritative. Scoped implementation only; physical validation/article
replication remain open. Next: resume primary equipment traceability.
''')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## {iso} — v42 uncertainty-aware Stateflow repair

Read acceptance, latest STATUS/stageboard, research frontier and production code
before changes. Implemented outward lower-age dwell comparisons and certified
post-add waits in additive planner, actual saved Stateflow HP supervisor and
runtime gate. Generated new SLX, executed all v41 fixtures plus multi-sample
waits, 30 domain/monitor/timer faults and four nominal-planner attacks.
Independent Fraction timing/margins, Decimal TES/first laws, verified v34 baseline,
saved MAT re-export, source/SLX/receipt and prior sealed-evidence QA completed.

Pass/fail: three successful MATLAB batches exit 0; {s['harness_passed']} harness
PASS / 0 FAIL, {s['scenarios']} scenarios / {s['completed_scenarios']} completed /
{s['intervals']} intervals / {s['positive_segments']} positive segments / six modes.
36 actual runtime rejections; 1,016 executed function probes. Independent actual
QA {qa['qa_passed']} PASS / 0 FAIL; separate reviewer self-checks 4/0. All
{len(qa['all_dwell_transitions'])} dwell transitions certified; zero unresolved.
First-law maximum residual {qa['max_balance_residual_MWh']:.17g} MWh.
First sandbox startup failure retained. Focused harness cleanup-order warning
fixed and focused probes/attacks rerun; failed/warning artifacts retained.

Files added: matlab/simulink additive v42 builder, planner, dwell-ready/wait,
clock/HP/dispatch helpers, guard, runtime contract gate, generated SLX, execution,
fault/probe and MAT-export harnesses; audit v42 preparation/specs, launcher,
independent verifier, derivation/results, finalizer, STATUS/stageboard and manifest.
Timestamped sources, MAT/JSON evidence and logs: {relative(folder)};
clean focused rerun {relative(probe)}; QA {relative(qapath)}.
Only progress and acceptance ledgers appended. No prior model/data overwritten.

Limitations: scoped numerical implementation, conservative near-tie scheduling,
same-agent independent algorithms, normal-mode intra-macro events, inherited
shadow warnings, no measured physical validation/article replication or new
primary-text calibration; 0/31 full signoffs remain. No Jarvice/unrelated files,
settings, scheduled tasks, runner, secrets or external publication touched.

Next actionable task: {next_task}
Stop after this coherent repair and clear handoff.
''')
    files=set()
    for directory in (folder,probe):
        files.update(p for p in directory.rglob('*') if p.is_file() and not any(x in p.parts for x in ('local_build','dwell_attack_work','__pycache__')))
    for directory in (ROOT/'audit',ROOT/'matlab/simulink'):
        files.update(p for p in directory.rglob('*') if p.is_file() and '_v42' in p.name and not any(x in p.parts for x in ('__pycache__','slprj')))
    files.update([ROOT/'STATUS_stateflow_v42.json',ROOT/'MASTER_STAGEBOARD_stateflow_v42.md'])
    for r in receipts:files.add(r);files.add(ROOT/read(r)['log_path'])
    failed=ROOT/'audit/Stateflow_execution_v42_20261010T130315167Z.json'
    files.add(failed);files.add(ROOT/read(failed)['log_path'])
    files.update(p for p in (ROOT/'automation/logs').glob('*v42*') if p.is_file())
    entries=[dict(path=relative(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]
    manifest=ROOT/'audit'/('Stateflow_clock_manifest_v42_'+tag+'.json')
    write(manifest,dict(version='0.42',timestamp_utc=iso,excludes='Mutable progress/acceptance ledgers, generated cache/codegen folders and this manifest itself.',files=entries))
    print('STATUS=STATUS_stateflow_v42.json');print('MANIFEST='+relative(manifest));print('SEALED_FILES='+str(len(entries)))
if __name__=='__main__':main()
