"""Close scoped acceptance only after successful actual execution and QA."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,text):
    assert not p.exists(),f'Preserve {p}'
    p.write_text(text,encoding='utf-8')
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text())
    qa_path=max(folder.glob('independent_QA_v57_*.json'));qa=json.loads(qa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in report['assertions']) and all(c['passed'] for c in qa['checks'])
    assert all(c['passed'] for c in qa['reviewer_selfchecks']) and len(qa['reviewer_selfchecks'])>=7
    assert qa['counts']['mode_coverage']==list(range(6)) and len(report['cases'])==13
    assert len(report['references'])==6 and all(r['passed'] for r in report['references'])
    assert len(report['faults'])==12 and all(f['rejected'] for f in report['faults'])
    executions=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    assert any(x['exit_code']==0 for x in executions)
    for row in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/row['path'])==row['sha256']
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx'
    assert sha(model)==qa['model_sha256']
    saved=folder/'saved_model'/model.name;saved.parent.mkdir();shutil.copy2(model,saved)
    now=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix();counts=qa['counts']
    limits=[
        'v57 accepts a compiled finite-water boundary held per macro interval. It is not continuous tank-temperature/condenser coupling; the v56 exact branch/limiter endpoint blocker remains OPEN.',
        'Synthetic variable-flow feasibility constraints, fixed saturation temperatures per interval, external fully rejected proportional auxiliary electricity. No finite UA, hydraulics, minimum-flow/standby law, equipment map or measured validation.',
        'Tank capacity, ambient reference and cutoff remain fixed per run. New boundary rejects attempts to redefine tank/cutoff or credit auxiliary heat; source/hot axes may change only at macro boundaries.',
        'Inherited host extrinsic planner and bounded 64 segment slots execute in normal mode. Standalone generated-code deployment and universal numerical-domain proof are untested.',
        'Inherited canonical positive endpoint normalization uses 64 ULPs; independent 80-digit comparisons use the existing 72-ULP equation allowance. Zero-span padding and energy/memory handoff are exact.',
        'Independent QA uses separately programmed Decimal/Fraction equations and original-MAT binary64 exports by the same agent, not independent personnel.',
        'Stateflow license, two actual charts and executable simulation observed; version list is empty and no installed-version claim is made. Legacy sfroot is Simulink.Root; inherited shadow warnings remain.',
        'Six v30 physical-output comparisons exclude only attempted-request diagnostic column 22 when the HP latch is OFF. No unchanged annual policy matrix was rerun.',
        'No primary literature retrieved in this run; inherited full signoffs remain 0/31. No article replication or physical calibration accepted.',
        'Initial sandbox startup failure, two incorrect harness sfroot-type assumptions, two reviewer Decimal-type exceptions and two source-snapshot mismatches are preserved in earlier timestamped evidence. Final acceptance uses a fresh complete source snapshot.',
    ]
    nexttask=('Resolve the still-open v56 coupled event-endpoint prerequisite: bounded-error propagation and compressor/source energy integrals for all ten charge regimes, plus an explicit one-sided branch/limiter equality protocol. Then build an additive continuously tank-linked Stateflow version preserving v57 compiled water/auxiliary guards, cutoff/restart/dwell and exact padding/handoff; execute six modes, fault/reference tests and independent original-MAT/equation QA. Preserve v52-v57. Primary equipment calibration remains OPEN; do not repeat unchanged annual matrices.')
    status=dict(version='0.57',timestamp_utc=now,inherits='STATUS_v56.json',result='SCOPED_FINITE_WATER_STATEFLOW_V57_ACCEPTED_CONTINUOUS_COUPLING_OPEN',
        model_version='0.57',new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        coupled_stateflow_acceptance=False,finite_water_stateflow_acceptance=True,matlab_version=report['metadata']['matlab_version'],
        stateflow_license_observed=bool(report['metadata']['stateflow_license_test']),stateflow_version=report['metadata']['stateflow_version'],
        sfroot_class=report['metadata']['sfroot_class'],chart_count=report['metadata']['chart_count'],
        matlab_passed=report['summary']['passed'],matlab_failed=0,actual_scenarios=len(report['cases']),actual_intervals=counts['intervals'],
        actual_positive_segments=counts['positive_segments'],required_mode_coverage=counts['mode_coverage'],
        actual_runtime_fault_rejections=len(report['faults']),reference_comparisons=6,
        dwell_latch_changes=counts['latch_changes'],temporal_macro_transitions=counts['macro_transitions'],
        independent_passed=qa['summary']['passed'],independent_failed=0,original_binary_records=counts['binary_records'],
        original_binary_values=counts['binary_values'],original_mats=counts['original_MATs'],reviewer_selfchecks_passed=len(qa['reviewer_selfchecks']),
        max_segment_residual_MWh=qa['max_segment_residual_MWh'],defect_status='CONTINUOUS_COUPLED_EVENT_ENDPOINT_PROTOCOL_OPEN',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        prior_fixed_temperature_acceptance='STATUS_stateflow_v52.json',result_directory=rel,independent_qa=qa_path.relative_to(ROOT).as_posix(),numeric_traces=rel+'/'+qa['numeric_traces'],
        limitations=limits,next_actionable_task=nexttask)
    encoded=json.dumps(status,indent=2)+'\n'
    write(ROOT/'STATUS_v57.json',encoded);write(ROOT/'STATUS_stateflow_v57.json',encoded)
    stage=f'''# Compiled finite-water Stateflow acceptance v57

UTC {now}. **Scoped v57 acceptance; continuous coupling remains OPEN.**

New saved actual model: `matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx`.
Six guarded thermal modes and persistent HP supervisor execute {counts['intervals']}
intervals / {counts['positive_segments']} positive segments / 13 scenarios.
Compiled water/refrigerant boundary and executed-flow/auxiliary accounting are new.
MATLAB {report['summary']['passed']}/0; twelve runtime fault rejections including
two valid samples before delayed rejection; six verified v30 physical comparisons.
Independent QA {qa['summary']['passed']}/0; {len(qa['reviewer_selfchecks'])} separate mutations;
{counts['latch_changes']} certified latch changes; {counts['macro_transitions']} macro mode changes;
{counts['binary_values']} original binary64 values / {counts['original_MATs']} MATs.

Boundary inputs are held within each macro interval. Tank capacity/cutoff are fixed.
No continuously energy-linked condenser, bounded variable-power charge propagator,
equipment calibration, article replication or measured physical validation accepted.
The v56 endpoint blocker remains OPEN. All prior source/model/data hashes preserved.

Results: `audit/Finite_Stateflow_results_v57.md`; immutable evidence: `{rel}`.
Next actionable task: {nexttask}
'''
    write(ROOT/'MASTER_STAGEBOARD_v57.md',stage);write(ROOT/'MASTER_STAGEBOARD_stateflow_v57.md',stage)
    table='\n## Actual saved-model scenarios\n\n| Case | Intervals | Positive segments | Modes |\n|---|---:|---:|---|\n'
    for case in report['cases']:
        modes=case['modes'];modes=[modes] if isinstance(modes,(int,float)) else modes
        table+=f"| {case['id']} | {case['intervals']} | {case['positive_segments']} | {','.join(str(int(x)) for x in modes)} |\n"
    result=stage+table+'\nNumeric traces: `'+status['numeric_traces']+'`.\n\n## Scope and limitations\n\n'+'\n'.join('- '+x for x in limits)+'\n'
    write(ROOT/'audit/Finite_Stateflow_results_v57.md',result)
    progress=f'''\n\n## {now} — v57 actual compiled finite-water Stateflow acceptance

Read STATUS/stageboard v56, acceptance ledger, research frontier, progress and
v52/v53/v56 actual builder/planner/contract/component/harness code before changes.
Prior Stateflow acceptance existed, but finite water physics was host-only.
Implemented a new additive v57 builder/SLX with compiled finite-water validation,
refrigerant-axis conversion, actual variable-flow checks and auxiliary electricity.
Persistent dispatch/cutoff/restart/dwell and strict canonical endpoints inherited
unchanged from accepted v52; every prior source/model/status hash verified unchanged.

Executed 13 scenarios/{counts['intervals']} intervals/{counts['positive_segments']} positive
segments/all six modes. MATLAB {report['summary']['passed']} PASS/0 FAIL; six v30
physical references6/0; twelve actual runtime fault rejections, one delayed after
two valid samples. Independent80-digit/exact-Fraction/original-MAT/binary/SLX/
preservation QA {qa['summary']['passed']}/0 plus seven separate reviewer mutations.
{counts['latch_changes']} certified latch changes/{counts['macro_transitions']} macro mode
changes; {counts['binary_values']} original binary64 values/{counts['original_MATs']} MATs.
Timestamped execution and reviewer logs retained. Initial sandbox startup and two
harness sfroot-type errors preserved; actual legacy API is Simulink.Root. New-model
compilation alone did not count as acceptance; fresh full simulation/QA gates did.

Files: matlab/simulink/build_dispatch_stateflow_v57.m,
stateflow_finite_boundary_v57.m, stateflow_finite_ports_v57.m, generated
DCHR_Dispatch_Stateflow_v57.slx; matlab/run_stateflow_finite_v57.m; audit/create,
prepare, run, verify, finalize_stateflow_finite_v57 workflows; versioned derivation,
results, STATUS and MASTER_STAGEBOARD. Shared acceptance/progress append only.
No Jarvice/unrelated files, settings, schedules, runner, secrets or publication touched.

Remaining limits: held-macro finite-water scope; continuously tank-linked event/
endpoint/variable-power integration remains OPEN. Synthetic flow/auxiliary laws,
no UA/hydraulics/equipment/physical calibration or article replication; primary
signoffs0/31. Same-agent independent algorithms, not personnel. Stateflow version
list empty; observed license/charts/execution only. Inherited shadow warnings,
normal-mode host planner/64-slot limit; standalone deployment untested.

Evidence: {rel}; {status['independent_qa']}.
Next actionable task: {nexttask}
Stop coherent run after accepted packaging and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as stream:stream.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as stream:
        stream.write(f'\n\n## Compiled finite-water Stateflow acceptance — {now} / v57\n\n'+stage.split('\n',1)[1])
    evidence=[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in sorted(folder.rglob('*')) if p.is_file() and 'local_build' not in p.parts]
    evidence+= [dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in [ROOT/'STATUS_v57.json',ROOT/'STATUS_stateflow_v57.json',ROOT/'MASTER_STAGEBOARD_v57.md',ROOT/'MASTER_STAGEBOARD_stateflow_v57.md',ROOT/'audit/Finite_Stateflow_results_v57.md']]
    write(folder/'closure_manifest.json',json.dumps(dict(timestamp_utc=now,files=evidence),indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],evidence=rel),indent=2))
if __name__=='__main__':main()
