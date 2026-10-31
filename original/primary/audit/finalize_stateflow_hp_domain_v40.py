"""Close v40 only after actual simulation and independent repair QA pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(ROOT).as_posix()
def write(p,v):
    assert not p.exists(),p
    p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def textfile(p,v):
    assert not p.exists(),p
    p.write_text(v,encoding='utf-8')

def main():
    folder=ROOT/Path(sys.argv[1]); qp=ROOT/Path(sys.argv[2]); receipts=[ROOT/Path(x) for x in sys.argv[3:]]
    qa=read(qp);summary=read(folder/'summary_v40.json');ts=datetime.now(timezone.utc)
    stamp=ts.strftime('%Y%m%dT%H%M%S_%fZ')
    assert summary['harness_failed']==0 and summary['runtime_faults']==30
    assert qa['implementation_comparisons']['failed']==0
    assert not any(v['failed'] for v in qa['counts'].values())
    assert len(receipts)==2 and all(read(p)['exit_code']==0 for p in receipts)
    actual=sum(v['passed'] for k,v in qa['counts'].items() if k!='synthetic')
    synthetic=qa['counts']['synthetic']['passed'];model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v40.slx'
    assert sha(model)==qa['model_sha256']
    handoff=('Audit saved-v40 clock residual seeds, nonzero accumulated error bounds and event ordering '
             'near dwell/capacity/cutoff boundaries against independent interval or high-precision timing. '
             'Use focused fresh simulations and document any defect before broadening acceptance. '
             'Then resume primary-source equipment/parameter traceability; preserve all v38-v40 evidence.')
    limits=[
        'Scoped numerical implementation acceptance, not measured physical validation or article replication.',
        'Extreme ratios/subnormal powers and COP near one are numerical fixtures, not plausible equipment sizes.',
        'Exact v39 binary64 cutoff fixture observed only; comprehensive near-cutoff classification remains unproved.',
        'Clock residual seeds, nonzero error-bound event ordering, generated code and solver-clock events remain open.',
        'Host HP/planner executes in normal mode with analytic intra-macro physical segments; no calibrated hydraulics, stratification or cycling losses.',
        'Independent algorithms and artifact checks in same agent, not independent personnel; synthetic checks separate.',
        'Stateflow license and saved-chart execution observed; empty ver(Stateflow) does not establish a standalone product version.',
        'No new primary-source equation/value/signoff; full primary signoffs remain 0/31.',
        'Inherited Stateflow formal-argument shadow warnings remain in timestamped logs.'
    ]
    status=dict(version='0.40',inherits='STATUS_stateflow_v39.json',research_inherits='STATUS_v25.json',
        timestamp_utc=ts.isoformat(),checkpoint='Source-relative HP solver repair in actual saved Stateflow v40',
        stateflow_acceptance='PASS_SCOPED_IMPLEMENTATION',model_version='0.40',new_model=True,
        generated_model=rel(model),model_sha256=sha(model),controller_defect='v39 false OFF/nonmaximal source-limited HP output repaired in tested fixtures',
        result_directory=rel(folder),independent_qa=rel(qp),matlab_batch_receipts=[rel(p) for p in receipts],matlab_batch_exit_code=0,
        scenarios=summary['scenarios'],completed_scenarios=summary['completed_scenarios'],completed_intervals=summary['intervals'],
        positive_segments=summary['positive_segments'],harness_checks_passed=summary['harness_passed'],harness_checks_failed=0,
        hp_component_probes=summary['hp_probes'],actual_runtime_fault_rejections=30,
        independent_evidence_checks_passed=actual,independent_evidence_checks_failed=0,
        synthetic_reviewer_checks_passed=synthetic,synthetic_reviewer_checks_failed=0,
        independent_check_breakdown=qa['counts'],implementation_comparisons=qa['implementation_comparisons'],
        max_independent_balance_residual_MWh=qa['max_balance_residual_MWh'],previous_immutable_entries_preserved=qa['previous_immutable_entries'],
        preservation_exclusions=qa['preservation_exclusions'],full_primary_signoffs=0,total_sources=31,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next=handoff)
    rows=[]
    for bits in (60,80,90,120):
        a=next(r for r in qa['plant_ledger'] if r['id']==f'wide_request_{bits}')
        rows.append(f"| {a['id']} | {a['expected_HP_heat_MW']:.12g} | {a['actual_HP_heat_MW']:.12g} | {a['actual_unmet_MW']:.12g} | {a['actual_mode']} |")
    report=f'''# v40 HP numerical-domain repair results

UTC {ts.isoformat()}. **PASS scoped implementation acceptance.**
New actual saved model: `{rel(model)}`, SHA256 `{sha(model)}`.
v38, v39 defect traces and all prior sealed evidence remain preserved.

Source-relative search replaces fixed 80-step output-space search; floating-point
adjacency ends bisection. Stable evaporator evaluation avoids Q-W cancellation
near COP=1. Unrepresentable positive electricity/source flow rejects explicitly.
Derivation: `audit/HP_dynamic_range_derivation_v40.md`. These are assumed
engineering screening equations, with no newly adopted article/equipment values.

Actual MATLAB build/simulation and separate read-only saved-MAT export exit zero.
{summary['scenarios']} scenarios / {summary['intervals']} completed intervals /
{summary['positive_segments']} positive physical segments execute all six modes.
MATLAB harness {summary['harness_passed']}/{summary['harness_passed']} PASS;
{summary['hp_probes']} HP probes and 30 actual runtime fault rejections.
Clean model traces agree before and after temporary in-memory corruption tests.

Independent actual evidence checks {actual}/{actual} PASS; separate synthetic
oracle self-checks {synthetic}/{synthetic} PASS. Analytic implementation comparisons
{qa['implementation_comparisons']['passed']} PASS / 0 FAIL. The reviewer evaluates
150-digit exact-input quadratic maxima, Decimal TES ODEs and the independently
implemented prior six-mode/dwell/fallback reference. It binds JSON to MATs
re-exported in another MATLAB batch and checks saved chart/source hashes.
Source-limited request invariance covers source ratios through 2^-1070 with
positive representable electricity. ULP and relative tolerances remain explicit.
{qa['previous_immutable_entries']} prior immutable entries retain hashes/sizes.
Maximum independent segment balance residual {qa['max_balance_residual_MWh']:.17g} MWh.

| Retained counterexample | Analytic HP MW | Actual HP MW | Actual unmet MW | Mode |
|---|---:|---:|---:|---:|
'''+ '\n'.join(rows)+'''

Mode 2 is STORAGE_CHARGE. The formerly false-OFF wide-request cases at source
ratios 2^-90 and 2^-120 now operate and serve their complete tiny demands.
The old failed comparisons remain sealed in v39; this release does not relabel them.

The sandbox startup failure occurred before any simulation and is retained
with its receipt/log. Authorized local batches then completed. Stateflow formal
argument shadow warnings are retained. Any unsuccessful reviewer reports retain
their exact source snapshots and logs beside the successful report.

## Limits and next task

'''+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {handoff}\n'
    textfile(ROOT/'audit/HP_dynamic_range_results_v40.md',report)
    write(ROOT/'STATUS_stateflow_v40.json',status)
    textfile(ROOT/'MASTER_STAGEBOARD_stateflow_v40.md',f'''# v40 Stateflow HP repair checkpoint

{ts.isoformat()}. PASS_SCOPED_IMPLEMENTATION. Actual new saved release 0.40.
{summary['scenarios']} scenarios / {summary['intervals']} intervals / six modes;
MATLAB {summary['harness_passed']}/{summary['harness_passed']} PASS; {summary['hp_probes']} HP probes;
30 actual runtime fault rejections. Independent actual QA {actual}/{actual};
synthetic {synthetic}/{synthetic}; analytic comparisons {qa['implementation_comparisons']['passed']} PASS / 0 FAIL.
v39 false OFF/nonmaximal defect repaired for tested fixtures. No physical
validation/article replication; all existing baselines/evidence preserved.

Evidence: STATUS_stateflow_v40.json; audit/HP_dynamic_range_derivation_v40.md;
audit/HP_dynamic_range_results_v40.md; {rel(qp)}.

Next: {handoff}
''')
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## {ts.isoformat()} — v40 actual Stateflow HP source-bracket repair

Read acceptance, latest research/Stateflow STATUS and stageboards, frontier,
progress, HP/Stateflow code and independent references before editing.
Derived source-relative bracket, implemented adjacent-endpoint search and
stable evaporator evaluation, generated new saved v40 SLX and executed it.
Independent exact-input quadratic/Decimal/reference QA and separate MATLAB
MAT export bind numeric evidence to actual saved simulation artifacts.

Pass/fail: MATLAB build/simulation and read-only MAT export exit0;
harness {summary['harness_passed']}/{summary['harness_passed']} PASS;
{summary['scenarios']} scenarios / {summary['intervals']} intervals /
{summary['positive_segments']} positive segments / six modes / {summary['hp_probes']} probes;
30 actual runtime fault rejections. Independent actual QA {actual}/{actual}
PASS; separate synthetic {synthetic}/{synthetic} PASS; analytic comparisons
{qa['implementation_comparisons']['passed']} PASS / 0 FAIL.
Retained v39 wide-request false OFF/nonmaximal fixtures now pass. Source-limited
request invariance, nonzero electricity, ports/TES bounds and first laws pass.
{qa['previous_immutable_entries']} sealed prior entries preserved. Sandbox startup
failure retained; all test/reviewer logs and receipts are timestamped.

Files created: additive matlab/+dchr/+components/heat_pump_step_v40.m;
matlab/simulink/*v40.m and actual DCHR_Dispatch_Stateflow_v40.slx;
audit/*v40* specification/preparation, reviewer, launcher, derivation/results,
status/stageboard/manifests; results/stateflow_hp_domain_v40_* MAT/JSON/source
snapshots and timestamped automation/logs. Existing model/code/data untouched;
only engineering_progress.md and STATEFLOW_ACCEPTANCE.md append new records.

Limitations: scoped numerical implementation only. Exact cutoff observed only;
clock seed/bound/event-order audit remains open; host normal-mode intra-macro
segments, no code generation or solver-clock event scheduling, no measured
physical validation or article replication/calibration; full signoffs0/31.
QA uses independent algorithms in same agent, not independent personnel.
Stateflow license/execution observed without fabricated standalone version.

Next actionable task: {handoff}
Evidence: `{rel(folder)}` and `{rel(qp)}`.
Run stops after this coherent task and clear handoff. No Jarvice/unrelated
files, settings, scheduler, agent runner, secrets or external publication touched.
''')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'''\n\n## Source-relative HP solver repair acceptance — {ts.isoformat()} / v40

Actual saved v40 executes {summary['scenarios']} scenarios/{summary['intervals']} intervals/six modes;
MATLAB {summary['harness_passed']}/{summary['harness_passed']}, {summary['hp_probes']} HP probes,
30 actual fault rejections, independent actual QA {actual}/{actual}, separate
synthetic {synthetic}/{synthetic}, analytic comparisons {qa['implementation_comparisons']['passed']} PASS/0 FAIL.
v39 false OFF/nonmaximal defect repaired in tested fixtures; source-limited
request invariance reaches subnormal source ratios. Prior models/evidence preserved.
STATUS/stageboard v40 and audit/HP_dynamic_range_results_v40.md are authoritative.
Scoped implementation acceptance only; exact-cutoff/clock/event-order, physical
validation and primary calibration/article replication remain open.
''')
    paths={model,ROOT/'STATUS_stateflow_v40.json',ROOT/'MASTER_STAGEBOARD_stateflow_v40.md'}
    for parent in (ROOT/'audit',ROOT/'matlab/simulink',ROOT/'matlab/+dchr/+components',ROOT/'automation/logs'):
        for p in parent.glob('*v40*'):
            if p.is_dir():paths.update(x for x in p.rglob('*') if x.is_file())
            else:paths.add(p)
    paths.update(x for x in folder.rglob('*') if x.is_file())
    paths={p for p in paths if not any(v in p.parts for v in ('local_build','__pycache__')) and
           not p.name.startswith('stateflow_hp_v40_finalize_')}
    manifest=ROOT/'audit'/f'Stateflow_HP_manifest_v40_{stamp}.json'
    write(manifest,dict(timestamp_utc=ts.isoformat(),model_release='0.40',new_model=True,
        mutable_exclusions=['engineering_progress.md','STATEFLOW_ACCEPTANCE.md','active finalizer log','local_build/cache'],
        files=[dict(path=rel(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(paths)]))
    print('STATUS='+rel(ROOT/'STATUS_stateflow_v40.json'));print('MANIFEST='+rel(manifest))
if __name__=='__main__':main()
