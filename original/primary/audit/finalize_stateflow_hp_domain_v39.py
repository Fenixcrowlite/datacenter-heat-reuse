"""Seal a documented defect checkpoint; never accept the defective controller."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p): return str(p.relative_to(ROOT))
def write(p, value):
    assert not p.exists(), p
    p.write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
def markdown(p, value):
    assert not p.exists(), p
    p.write_text(value, encoding='utf-8')

def main():
    folder, qp = (ROOT/Path(x) for x in sys.argv[1:3])
    rps = [ROOT/Path(x) for x in sys.argv[3:]]
    qa, summary = read(qp), read(folder/'summary_v39.json')
    receipts = [read(p) for p in rps]
    assert len(receipts)==2 and all(r['exit_code']==0 for r in receipts)
    assert 'run_stateflow_hp_domain_v39' in receipts[0]['command']
    assert 'export_stateflow_resolution_v38' in receipts[1]['command']
    assert summary['harness_failed']==0 and summary['harness_passed']>0
    assert all(v['failed']==0 and v['passed']>0 for v in qa['counts'].values())
    assert qa['implementation_comparisons']['failed']>0
    assert qa['implementation_status']=='FAIL_OPEN_HP_DYNAMIC_RANGE'
    assert qa['new_model'] is False and summary['new_model'] is False
    model = ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v38.slx'
    assert sha(model)==qa['model_sha256']==read(ROOT/'STATUS_stateflow_v38.json')['model_sha256']
    assertions=read(folder/'assertions_v39.json')
    assert len(assertions)==summary['harness_passed'] and all(a['passed'] for a in assertions)
    assert (ROOT/'audit/HP_dynamic_range_derivation_v39.md').is_file()
    for receipt in receipts:
        log=ROOT/receipt['log_path']; raw=log.read_bytes()
        text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
        marker='AUDIT_OUTPUT=' if 'run_stateflow_hp_domain_v39' in receipt['command'] else 'MAT_AUDIT_OUTPUT='
        assert marker in text and folder.name in text
    ts=datetime.now(timezone.utc); stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    actual=sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic')
    synth=qa['counts']['synthetic']['passed']; comparison=qa['implementation_comparisons']
    handoff=('Implement additive Stateflow v40 with a source-relative bracket or stable scaled HP root, '
        'explicit unsupported-resolution rejection, and source-limited request invariance. Execute v39 '
        'dynamic-range/cutoff counterexamples plus all six modes and prior v38 representative references; '
        'independently verify analytic maximal output, nonzero electricity, SOC/port limits and first-law closure. '
        'Preserve v38 and all v39 evidence. Do not broaden clock seed/bound/event-order acceptance or claim '
        'equipment calibration; those audits and primary parameter traceability remain open.')
    limits=[
        'Documented numerical implementation defect, no new SLX or corrected controller acceptance.',
        'Extreme source/output ratios are numerical stress fixtures, not plausible equipment sizes or measured data.',
        'Execution/invariant and defect-evidence QA pass; explicit analytic implementation comparisons FAIL and remain open.',
        'Exact binary64 cutoff fixture is observed but excluded from defect counts; full near-cutoff classification remains unproved.',
        'Clock residual seeds, nonzero error-bound event ordering, code generation and solver-clock events remain untested here.',
        'Normal-mode host HP/planner with analytic intra-macro segments; no calibrated hydraulics, stratification or cycling losses.',
        'Independent algorithms/artifact QA in the same agent, not independent personnel; synthetic checks counted separately.',
        'Stateflow license and saved-chart execution observed; no standalone Stateflow version inferred from empty ver lookup.',
        'No new primary article equation, parameter or literature signoff; full signoffs 0/31, no article replication or physical validation.'
    ]
    status=dict(version='0.39',inherits='STATUS_stateflow_v38.json',research_inherits='STATUS_v25.json',timestamp_utc=ts.isoformat(),
        checkpoint='Fresh saved-v38 HP dynamic-range defect audit',stateflow_acceptance='DEFECT_REPRODUCED_OPEN',
        model_version='0.38',new_model=False,generated_model=rel(model),model_sha256=sha(model),
        controller_defect='Fixed 80-iteration output-space search returns false OFF or nonmaximal output at large request/source ratios.',
        result_directory=rel(folder),independent_qa=rel(qp),matlab_batch_receipts=[rel(p) for p in rps],matlab_batch_exit_code=0,
        scenarios=summary['scenarios'],completed_scenarios=summary['completed_scenarios'],completed_intervals=summary['intervals'],
        positive_segments=summary['positive_segments'],harness_checks_passed=summary['harness_passed'],harness_checks_failed=0,
        hp_component_probes=summary['hp_probes'],independent_evidence_checks_passed=actual,independent_evidence_checks_failed=0,
        synthetic_reviewer_checks_passed=synth,synthetic_reviewer_checks_failed=0,independent_check_breakdown=qa['counts'],
        implementation_comparisons=comparison,max_independent_balance_residual_MWh=qa['max_balance_residual_MWh'],
        previous_immutable_entries_preserved=qa['previous_immutable_entries'],full_primary_signoffs=0,total_sources=31,
        preservation_exclusions=qa['preservation_exclusions'],
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next=handoff)
    plant=qa['plant_ledger']; rows=[]
    for bits in (40,60,80,90,120):
        for kind in ('wide_request','tight_request'):
            r=next(a for a in plant if a['id']==f'{kind}_{bits}')
            rows.append(f"| {r['id']} | {r['expected_HP_heat_MW']:.12g} | {r['actual_HP_heat_MW']:.12g} | {r['actual_unmet_MW']:.12g} | {r['actual_mode']} |")
    report=f'''# v39 fresh saved-Stateflow HP numerical-domain defect

UTC {ts.isoformat()}. **OPEN defect; no corrected-controller acceptance.**
Saved model release remains 0.38, SHA256 `{sha(model)}`. Prior acceptance
is preserved within its tested scope; this audit supplies new counterexamples.

Actual MATLAB batches exit zero. Execution harness {summary['harness_passed']}/{summary['harness_passed']} PASS:
{summary['scenarios']} completed scenarios, {summary['intervals']} intervals,
{summary['positive_segments']} positive segments and all six required modes;
{summary['hp_probes']} component probes. Separate read-only MAT export binds
the persisted SimulationOutputs and component MAT to the JSON traces.

Independent evidence QA {actual}/{actual} PASS; synthetic oracle checks
{synth}/{synth} PASS, counted separately. Analytic implementation comparisons:
**{comparison['passed']} PASS / {comparison['failed']} FAIL**. These failures
are neither discarded nor counted as successful controller tests. The evidence
gate passes because independently predicted defects are actually reproduced.
{qa['previous_immutable_entries']} prior sealed entries retain hashes/sizes.
Max independent segment balance residual: {qa['max_balance_residual_MWh']:.17g} MWh.

| Fixture | Analytic HP output MW | Actual output MW | Actual unmet MW | Actual mode |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

Mode 1 is HEAT_RECOVERY, 2 STORAGE_CHARGE, 5 UNMET_DEMAND. With COP=4,
source S=8*2^-90 MW and a 3 MW charging request, the analytic maximum is
4S/3 while the actual model returns zero and reports all demand unmet.
Disabling charging with the same source and demand gives feasible Q=S and
serves all demand. This is request-dependent numerical loss of service, not
a first-law violation: energy conservation can pass for a falsely OFF plant.
Positive-penalty and capacities 8/1e-100/1e100 MW are also component stress
fixtures. The report ledger retains every input, expected and actual result.

Derivation: `audit/HP_dynamic_range_derivation_v39.md`. No paper formula,
experimental value or calibrated equipment parameter is claimed. The oracle
uses exact-input Decimal stable quadratic roots, distinct from production
bisection, plus Decimal TES ODEs and the inherited independent six-mode reference.

## Failures retained

An earlier unfinished batch executed plant fixtures then failed because the
heterogeneous hp_probes JSON decodes to a MATLAB cell array. Its MATs, logs and
receipt remain. The harness now normalizes structs/cells; fresh execution uses
a new directory and a new source snapshot. This run's sandbox MATLAB startup
failed before simulation; authorized local execution succeeds. Stateflow formal
argument shadow warnings remain visible. Reviewer/packaging failures, if any,
are retained alongside the successful reports without replacing numeric traces.
The first v39 reviewer failed two legacy hash checks: it treated the intentionally
mutable progress ledger and an originally open v22 finalizer log as immutable.
The corrected v22 manifest explicitly supersedes that seal and excludes these
files. The reviewer now honors those declarations, records both exclusions,
and still verifies every immutable model/numeric/source artifact. The failed
QA report, log and exact reviewer source snapshot remain preserved.

## Limitations and next action

'''+''.join('- '+x+'\n' for x in limits)+f'\nNext actionable task: {handoff}\n'
    markdown(ROOT/'audit/HP_dynamic_range_results_v39.md',report)
    write(ROOT/'STATUS_stateflow_v39.json',status)
    markdown(ROOT/'MASTER_STAGEBOARD_stateflow_v39.md',f'''# v39 saved-v38 HP defect checkpoint

UTC {ts.isoformat()}. DEFECT_REPRODUCED_OPEN. No new SLX.

Executed {summary['scenarios']} scenarios / {summary['intervals']} intervals / six modes;
MATLAB {summary['harness_passed']}/{summary['harness_passed']} execution checks PASS and {summary['hp_probes']} HP probes.
Independent evidence QA {actual}/{actual} PASS; synthetic {synth}/{synth} PASS.
Analytic implementation comparisons {comparison['passed']} PASS / {comparison['failed']} FAIL.
Fixed 80-step search falsely returns OFF or nonmaximal output at extreme
request/source ratios; same-source tight-request controls serve demand.
No physical validation or article replication; prior models/evidence preserved.

Evidence: STATUS_stateflow_v39.json; audit/HP_dynamic_range_derivation_v39.md;
audit/HP_dynamic_range_results_v39.md; {rel(qp)}.

Next: {handoff}
''')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## {ts.isoformat()} — v39 fresh saved-v38 HP dynamic-range defect audit

Read acceptance, latest Stateflow/research STATUS/stageboards, frontier,
progress and production/reference code before edits. Resumed unfinished v39,
preserved its harness before fixing heterogeneous JSON struct/cell decoding.
Derived monotone source law and independent stable quadratic maximum, executed
saved v38 afresh and separately re-exported MATs; no production model edits.

Pass/fail: local MATLAB simulation and MAT export exit0; execution harness
{summary['harness_passed']}/{summary['harness_passed']} PASS; {summary['scenarios']} scenarios / {summary['intervals']} intervals /
{summary['positive_segments']} positive segments / six modes / {summary['hp_probes']} HP probes.
Independent evidence QA {actual}/{actual} PASS, synthetic {synth}/{synth} PASS.
Analytic implementation comparisons {comparison['passed']} PASS / {comparison['failed']} FAIL, defect OPEN.
{qa['previous_immutable_entries']} prior immutable entries preserved. Sandbox startup and
earlier harness failures retained; no numerical artifacts overwritten.

Finding: source/output dynamic range defeats fixed 80-step output-space search;
zero/nonmaximal HP output passes balance gates but loses service. Matched tight
request serves demand. Extreme ratios are numerical fixtures, not equipment.

Files changed: matlab/simulink/run_stateflow_hp_domain_v39.m (cell normalization).
Files created: derivation/results, finalizer/checkpoint/manifest, fresh MAT/JSON/
source snapshots, QA reports, timestamped receipts/logs. Pre-existing unclosed
v39 sources, results and failures preserved. Acceptance/progress appended only.

Limitations: OPEN HP defect, no new SLX/corrected acceptance. Exact cutoff
boundary excluded from defect counts; broader cutoff and clock seed/bound/event
ordering remain unproved. Host normal-mode analytic intra-macro segments; no
code generation, solver-clock event schedule, physical calibration/validation
or primary article replication; full signoffs0/31. Independent algorithms and
artifacts in same agent, not independent personnel. Synthetic checks separate.
Stateflow license/execution observed; no fabricated standalone version.

Next actionable task: {handoff}

Evidence: `{rel(folder)}`; `{rel(qp)}`. Run stops at coherent defect checkpoint
and handoff. No Jarvice/unrelated files, settings, scheduler, agent runner,
secrets or external publication touched.
''')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Saved-v38 HP dynamic-range defect checkpoint — {ts.isoformat()} / v39

Saved v38 freshly executes {summary['scenarios']} scenarios/{summary['intervals']} intervals/six modes;
{summary['hp_probes']} HP probes, MATLAB execution checks and independent evidence QA PASS.
Analytic implementation comparisons {comparison['passed']} PASS/{comparison['failed']} FAIL:
fixed 80-step search falsely OFF/nonmaximal at extreme request/source ratios.
Defect OPEN; no new SLX or corrected acceptance. Prior acceptance remains
scoped. STATUS/stageboard v39 and audit/HP_dynamic_range_results_v39.md provide
counterexamples and additive-v40 handoff. No physical validation/article replication.
''')
    paths=set()
    for pattern in ('*v39*','Stateflow*39*'):
        paths.update((ROOT/'audit').glob(pattern))
    paths.update((ROOT/'automation/logs').glob('*v39*'))
    paths.update((ROOT/'results').glob('stateflow_hp_domain_v39*'))
    paths.update([ROOT/'STATUS_stateflow_v39.json',ROOT/'MASTER_STAGEBOARD_stateflow_v39.md',
                  ROOT/'matlab/simulink/run_stateflow_hp_domain_v39.m'])
    files=set()
    for p in paths:
        files.update(x for x in p.rglob('*') if x.is_file()) if p.is_dir() else files.add(p)
    files={p for p in files if not any(x in p.parts for x in ('local_build','__pycache__'))
           and not p.name.startswith('stateflow_hp_v39_finalize_')}
    manifest=ROOT/'audit'/f'Stateflow_HP_manifest_v39_{stamp}.json'
    write(manifest,dict(timestamp_utc=ts.isoformat(),model_release='0.38',new_model=False,
        mutable_exclusions=['engineering_progress.md','STATEFLOW_ACCEPTANCE.md','active finalizer log','local_build/cache'],
        files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)]))
    print('STATUS='+rel(ROOT/'STATUS_stateflow_v39.json')); print('MANIFEST='+rel(manifest))

if __name__=='__main__': main()
