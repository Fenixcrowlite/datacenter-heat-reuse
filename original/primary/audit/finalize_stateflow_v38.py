"""Seal executed v38 scoped acceptance. Never overwrite prior evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT))
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def main():
    folder=ROOT/Path(sys.argv[1]);qa_path=ROOT/Path(sys.argv[2]);qa=read(qa_path);summary=read(folder/'summary_v38.json')
    receipt_paths=[ROOT/Path(x) for x in sys.argv[3:]];receipts=[read(p) for p in receipt_paths]
    assert len(receipts)==4 and all(r['exit_code']==0 for r in receipts)
    expected=('build_dispatch_stateflow_v38','run_stateflow_acceptance_v38','export_stateflow_resolution_v38','export_stateflow_numeric_metadata_v38')
    assert all(name in r['command'] for name,r in zip(expected,receipts))
    assert summary['harness_failed']==0 and summary['harness_passed']>0
    assert read(folder/'numeric_metadata_v38.json')['stateflow_license_test']==1
    required={'artifact','domain','numeric','clock','equation','reference','HP','fault','archive','preservation','synthetic'}
    assert set(qa['counts'])==required and all(v['failed']==0 and isinstance(v['passed'],int) and v['passed']>0 for v in qa['counts'].values())
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v38.slx';assert sha(model)==qa['model_sha256']
    assertions=read(folder/'assertions_v38.json');assert len(assertions)==summary['harness_passed'] and all(x['passed'] for x in assertions)
    faults=read(folder/'runtime_faults_v38.json');assert len(faults)==30 and all(x['rejected'] for x in faults)
    executions=read(folder/'execution_v38.json');assert len(executions)==summary['scenarios'] and sum(x['rejected'] for x in executions)==summary['rejected']
    assert (ROOT/'audit/TES_numerical_repair_derivation_v38.md').exists()
    ts=datetime.now(timezone.utc);stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    passed=sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic');synthetic=qa['counts']['synthetic']['passed']
    handoff=('Audit the normalized HP solver near the COP cutoff and across extreme source/output ratios, '
        'and verify compensated-clock initial residual/bound and event-guard domains before broadening acceptance. '
        'Use independent analytic/exact-input counterexamples rather than repeating the current suite. '
        'Then return to primary heat-pump/equipment evidence and physical parameter traceability; '
        'no calibrated or article-derived control values are accepted yet. Preserve all prior models/evidence.')
    limits=[
        'Scoped numerical implementation acceptance only: finite fixtures, not all finite inputs or physical validation.',
        '80-iteration HP source search and near-COP-cutoff classification retain a domain audit; subnormal tests are numerical stress fixtures, not plausible equipment sizes.',
        'Compensated clock initial expansion is a supplied exact seed; full adversarial residual/domain and strict event-ordering proof with nonzero error bounds remain open.',
        'Conservative band domain excludes zero/near-zero cutoff and bands <=128 capacity-scale energy ulps; this is numerical policy, not a physical equipment restriction.',
        'Normal-mode host planner/HP, bounded analytic segments at macro solver timestamps; standalone code generation and solver-clock events untested.',
        'No calibrated hydraulics/stratification/startup loss model, article replication or measured-system validation; primary signoffs remain 0/31.',
        'Independent algorithms/artifact QA in the same agent, not separate human/agent review. Synthetic reviewer checks are separately counted.',
        'Stateflow license test and actual saved-chart execution pass; ver(Stateflow) lacks a standalone version entry, and none is fabricated. Formal-argument shadow warnings remain in logs.'
    ]
    status=dict(version='0.38',inherits='STATUS_stateflow_v37.json',research_inherits='STATUS_v25.json',timestamp_utc=ts.isoformat(),
        checkpoint='Executed versioned Stateflow numerical-domain repair',stateflow_acceptance='PASS_SCOPED_IMPLEMENTATION',model_version='0.38',new_model=True,
        generated_model=rel(model),model_sha256=sha(model),controller_defect='v37 clock drift, band-progress and HP slope overflow repaired in tested fixtures; broader numerical domains remain unproved',
        result_directory=rel(folder),independent_qa=rel(qa_path),matlab_batch_receipts=[rel(p) for p in receipt_paths],matlab_batch_exit_code=0,
        scenarios=summary['scenarios'],completed_scenarios=summary['completed'],domain_runtime_rejections=summary['rejected'],completed_intervals=summary['intervals'],positive_segments=summary['positive_segments'],
        harness_checks_passed=summary['harness_passed'],harness_checks_failed=0,hp_component_probes=summary['hp_probes'],runtime_fault_rejections=30,
        independent_checks_passed=passed,independent_checks_failed=0,synthetic_reviewer_checks_passed=synthetic,synthetic_reviewer_checks_failed=0,independent_check_breakdown=qa['counts'],
        max_report_clock_error_h=max(x['max_report_error_h'] for x in qa['clock_ledger']),max_expansion_error_h=max(x['max_expansion_error_h'] for x in qa['clock_ledger']),
        max_independent_balance_residual_MWh=qa['max_independent_balance_residual_MWh'],previous_immutable_entries_preserved=qa['previous_immutable_entries'],
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next=handoff)
    report=f'''# v38 executed numerical-domain Stateflow repair

UTC {ts.isoformat()}. Scoped implementation acceptance PASS.

New actual saved model: `{rel(model)}`; SHA256 `{sha(model)}`.
MATLAB R2026a Update 5 builds and executes its six thermal states and two HP
supervisor states. The Stateflow license check passes. ver('Stateflow') is empty;
no standalone product version is asserted. All earlier SLX models are preserved.

MATLAB harness **{summary['harness_passed']}/{summary['harness_passed']} PASS**:
{summary['scenarios']} scenarios, {summary['completed']} completed,
{summary['rejected']} deliberate unsupported-domain runtime rejections,
{summary['intervals']} completed intervals and {summary['positive_segments']} positive
segments. All six required modes execute. Ten representative cases execute the
preserved v36 model afresh; six-mode and changing-input outputs agree. The
independent inherited v34 reference covers all 51 v36 fixture scenarios.
219 component probes cover normalized HP request/source/part-load limits and
subnormal full/partial load. 30/30 actual runtime faults reject. Exact restored
clean traces agree after temporary in-memory fault injection; saved SLX is unchanged.

Separate MAT-export and numeric-metadata batches exit zero. Independent QA:
**{passed}/{passed} actual evidence/algorithm/artifact checks PASS**, with
**{synthetic}/{synthetic} separately labelled synthetic reviewer checks PASS**.
{qa['previous_immutable_entries']} prior immutable entries retain sizes/hashes.
There are {qa['counts']['equation']['passed']} independent equation checks and
{qa['counts']['clock']['passed']} clock checks; counts are per assertion, not
independent experiments or measured plant observations.

## Repair observations

| v37 counterexample | Saved v38 result |
|---|---|
| Age 1e6 h, 1024 intervals of 1e-10 h; bias 1.6809289550781246e-8 h | Maximum reported-high error 5.817381143570185e-11 h; final residual -4.548320770263299e-11 h; exact-input expansion error zero in held/changing-demand fixtures |
| 1e-12 h increment cannot advance binary64 age at 1e6 h | Executed with unchanged high age and retained +1e-12 h residual |
| Restart gaps <=64 ulps lead to zero-time EventProgress failure | Gaps <=128 ulps reject explicitly before event planning; 256-ulp control remains OFF |
| Unresolved cutoff/restart overlap not exercised | 1/64/128-ulp gaps reject; 129/256-ulp controls execute |
| HP cap/output 1e-309 MW returns Inf COP | Actual model executes finite normalized COP=4 with nonzero electricity; analytic component references pass |
| Smallest subnormal output cannot represent electricity | Explicit HPResolution component rejection |

The maximum independent segment first-law residual is
{qa['max_independent_balance_residual_MWh']:.17g} MWh, occurring within the
inherited large-capacity numerical stress scope. Energy and clock tolerances
remain separate; this does not establish measurement accuracy.

## Evidence and failures retained

Evidence directory: `{rel(folder)}`. Primary numeric artifacts are execution,
positive segment/plan traces, saved SimulationOutput MATs, independent QA,
component MAT/JSON, actual v36 comparison MATs, and source/spec snapshots.
All successful batch commands and observed exits are in the status receipts.
Derivation: `audit/TES_numerical_repair_derivation_v38.md`.

Sandbox MATLAB startup failed before simulation. First local compile exposed
assignment to an outer Stateflow input name; its source snapshot and receipt
remain. Renaming the TwoSum local sum repaired compilation. The first reviewer
run encountered a manifest-size field mismatch; the next found two packaging
issues (harmless generator revision/source binding and a model-workspace value
stored outside XML). The executed generator was restored from its source
snapshot and the archive check now verifies its clock variable/dimension.
Failed reviewer logs/reports and source revisions are retained. Numeric
artifacts and the saved model were not changed during reviewer repairs.

## Limits and handoff

'''+''.join('- '+x+'\n' for x in limits)+f'\nNext actionable task: {handoff}\n'
    report_path=ROOT/'audit/TES_numerical_repair_results_v38.md';assert not report_path.exists();report_path.write_text(report,encoding='utf-8')
    write(ROOT/'STATUS_stateflow_v38.json',status)
    board=ROOT/'MASTER_STAGEBOARD_stateflow_v38.md';assert not board.exists()
    board.write_text(f'''# v38 executed Stateflow numerical-domain repair

UTC {ts.isoformat()}. PASS_SCOPED_IMPLEMENTATION, model release 0.38.

Actual new saved v38 executes 80 scenarios (69 complete, 11 intended domain
rejections), 3725 intervals, 3910 positive segments and all six modes.
MATLAB 2110/2110 PASS, 219 HP probes, 30 actual runtime fault rejections;
independent actual checks {passed}/{passed}, synthetic reviewer checks 3/3,
zero failures. Ten fresh saved-v36 comparisons and independent references pass;
{qa['previous_immutable_entries']} prior immutable entries preserved.

v37 drift/band-progress/HP-slope defects repaired in tested fixtures. Clock
high error <=5.817381143570185e-11 h; retained expansion matches exact-input
Decimal clocks in the executed fixtures. Implementation QA only; no calibrated
physical validation or paper replication. Broader clock seed/event and HP
numerical domains retain explicit audit limits.

Evidence: STATUS_stateflow_v38.json; audit/TES_numerical_repair_derivation_v38.md;
audit/TES_numerical_repair_results_v38.md; {rel(qa_path)}.

Next: {handoff}
''',encoding='utf-8')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## {ts.isoformat()} — v38 executed numerical-domain Stateflow repair

Read current Stateflow/research STATUS, MASTER_STAGEBOARD, acceptance, frontier,
progress and implementation/reference code before edits. Added normalized HP
component, conservative energy-band rejection, compensated physical-hour clock
memory and actual saved v38 Stateflow supervision/contract gates. Derived
equations and independently reviewed exact-input Decimal clocks, analytic
quadratic HP limits, Decimal TES ODEs, source/request limits and artifacts.

Pass/fail: build/simulation/separate MAT export/metadata exit0; MATLAB
2110/2110 PASS; 80 scenarios (69 complete, 11 intended runtime domain rejections),
3725 intervals/3910 positive segments/six modes; 219 HP component probes;
30/30 actual runtime faults reject; ten fresh saved-v36 comparisons; independent
actual checks {passed}/{passed}, separate synthetic3/3; {qa['previous_immutable_entries']}
prior immutable entries preserved. Clock maximum high error5.817381143570185e-11h,
expanded errorzero in executed fixtures. Maximum independent balance residual
{qa['max_independent_balance_residual_MWh']:.17g}MWh in numerical stress scope.
Startup/compile/reviewer packaging failures retained and repaired; final gates
have zero failures. No numerical artifact or saved-model edits after execution.

Files created: matlab/+dchr/+components/heat_pump_step_v38.m;
matlab/simulink/*v38.m and DCHR_Dispatch_Stateflow_v38.slx;
audit v38 generator/spec/reviewer/finalizer/local-batch scripts, derivation/results,
versioned status/stageboard; fresh specs/results/MAT/JSON/source/QA evidence,
timestamped receipts/logs and manifest. Only progress/acceptance ledgers appended.

Remaining limitations: scoped finite-fixture implementation acceptance only.
HP 80-iteration search/near-cutoff domains and adversarial clock residual seeds/
strict event ordering with nonzero bounds need focused audit. Conservative
band support excludes zero/near-zero cutoff. No calibrated equipment/hydraulics/
stratification/startup losses, standalone code generation, solver-clock event
scheduling, measured physical validation or article replication. Full primary
article signoffs remain0/31; no new primary article equation/value adopted.
Independent algorithms/artifacts in same agent, not separate personnel.
Actual Stateflow licensing/execution pass; no invented standalone version;
formal-argument shadow warnings retained.

Next actionable task: {handoff}

Run stops at coherent scoped repair acceptance and handoff. No Jarvice/unrelated
files, user settings, scheduler, agent runner, secrets or external publication
touched. Evidence: `{rel(folder)}`; independent QA `{rel(qa_path)}`.
''')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Scoped numerical-domain repair acceptance — {ts.isoformat()} / v38

New saved v38 executes all six modes in80 scenarios/3725 intervals/3910 positive
segments; MATLAB2110/2110, 219 HP probes, 30 actual fault rejections, independent
actual checks{passed}/{passed} and separate synthetic3/3, zero failures.
v37 clock drift, unresolved-band progress and HP slope overflow repaired in
tested fixtures. Prior evidence/models preserved. STATUS/stageboard v38 and
audit/TES_numerical_repair_results_v38.md are authoritative. Broader initial-clock/
event and HP solver numerical domains remain audit limits; scoped implementation
acceptance only, no calibrated physical validation or article replication.
''')
    completion=dict(timestamp_utc=ts.isoformat(),evidence_class='closure_bindings_only',model_sha256=sha(model),
        actual_independent_checks=passed,synthetic_reviewer_checks=synthetic,receipts=[rel(p) for p in receipt_paths],result_directory=rel(folder),qa=rel(qa_path),
        passed=True,status_sha256=sha(ROOT/'STATUS_stateflow_v38.json'))
    completion_path=ROOT/'audit'/('Stateflow_completion_QA_v38_'+stamp+'.json');write(completion_path,completion)
    files=set(folder.rglob('*'))
    for pattern in ('*v38*','Stateflow_execution_v38_*.json'):
        files.update((ROOT/'audit').glob(pattern))
    files.update((ROOT/'matlab/simulink').glob('*v38*'))
    files.add(ROOT/'matlab/+dchr/+components/heat_pump_step_v38.m')
    files.update((ROOT/'automation/logs').glob('stateflow_v38_*.log'))
    files.update([ROOT/'STATUS_stateflow_v38.json',board,completion_path])
    for p in list(files):
        if p.is_dir():files.update(p.rglob('*'))
    files={p for p in files if p.is_file() and '__pycache__' not in p.parts and '_finalize_console_' not in p.name}
    manifest_path=ROOT/'audit'/('Stateflow_manifest_v38_'+stamp+'.json')
    write(manifest_path,dict(timestamp_utc=ts.isoformat(),model_release='0.38',previous_immutable_entries_preserved=qa['previous_immutable_entries'],
        mutable_exclusions=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','active finalizer console log','codegen/cache'],
        files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
    print('STATUS=STATUS_stateflow_v38.json');print('MANIFEST='+rel(manifest_path));print('SEALED_FILES='+str(len(files)))
if __name__=='__main__':main()
