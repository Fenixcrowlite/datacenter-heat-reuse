"""Close a scoped equation checkpoint with explicit OPEN coupled-model defects."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):
    assert not p.exists();p.write_text(json.dumps(value,indent=2)+'\n' if isinstance(value,(dict,list)) else value,encoding='utf-8')
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    qp=sorted(folder.glob('independent_QA_v54_*.json'))[-1];q=json.loads(qp.read_text());r=json.loads((folder/'report.json').read_text())
    assert q['actual_failed']==q['reviewer_selfchecks_failed']==r['summary']['failed']==0
    assert q['report_sha256']==sha(folder/'report.json') and q['exact_branch_classification_failures']==12
    assert q['actual_successful_intervals']==15 and len(r['vectors'])==168 and len(r['analytic'])==12 and len(r['faults'])==14
    assert len(q['branch_flags'])==12 and all(f['status']=='OPEN_UNCERTIFIED_BRANCH_AT_ROUNDOFF_SCALE' for f in q['branch_flags'])
    model=ROOT/'matlab/simulink/DCHR_Dispatch_Stateflow_v52.slx';assert sha(model)==json.loads((ROOT/'STATUS_v53.json').read_text())['model_sha256']
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    next_task=('Implement an additive conservative tank/outlet branch domain gate, reproduce the exact-binary E=5MWh,C=0.2MWh/K,Ta=20C kink and reject or explicitly resolve uncertainty. '
        'Then derive/verify all charge-side limiter regimes and their earliest event times before integrating energy-linked condenser/COP/flow and variable-power integrals into a new versioned Stateflow planner/allocation/contract. '
        'Keep demand service, cutoff/restart/dwell memory and exact padding/handoff strict; execute required six modes, fault tests and independent equation/MAT QA before any new SLX acceptance. '
        'Preserve accepted v52 and fixed-temperature v53; do not rerun unchanged annual policies or claim continuous coupling from sampled restarts. Primary equipment calibration remains OPEN.')
    limitations=[
        'No new SLX and no accepted coupled Stateflow model. Saved v52 remains accepted only within its previous fixed-temperature scope; fresh v54 successes cover 15 charge-only intervals, not all six modes or an annual run.',
        'Twelve exact-input branch classifications disagree at roundoff-scale kink: mathematical tank-branch gap -1.3877787807814456e-15K versus nominal rounded zero. Continuous powers pass tolerance; discrete branch/crossing certification remains OPEN.',
        'New analytic component supports one source-limited charging regime with no demand/discharge/capacity/limiter event. Its nominal endpoint branch test is not a certified general guard at unresolved kinks.',
        'Variable-flow tank-return topology is a synthetic engineering assumption distinct from v53 fixed return; no UA, hydraulics, pump/minimum-flow law, calibrated equipment map or physical validation.',
        'Exact affine derivation uses constant source/factor/ambient and no HP clips/part-load penalty. General charge/hot/request regimes, direct/discharge service and complete coupled controller remain unimplemented.',
        'Primary source20 local p8 definitions visually verified; upstream62 accessible record is metadata/abstract only and provides no primary equipment equations. Full primary signoffs0/31; no article replication.',
        'Independent QA is 70-digit equations and separately programmed min-envelope RK4/actual trace review by the same agent, not independent personnel or universal floating-point proof.',
        'Inherited v52 64-slot host-planner, normal-mode deployment and shadow warnings remain. Stateflow license/charts/execution observed; ver(Stateflow) empty is not an installed-version claim.',
        'Sandbox startup failure, initial reviewer singleton-struct exception and 5314-pass/12-fail exact-branch QA retained. Final scoped QA retains those 12 flags as OPEN; no MATLAB model/guard/tolerance was relaxed.'
    ]
    status=dict(version='0.54',timestamp_utc=stamp,inherits='STATUS_v53.json',
        result='SCOPED_COUPLED_EQUATIONS_PASS_STATEFLOW_INTEGRATION_AND_EXACT_BRANCH_GUARDS_OPEN',
        model_version='0.52',new_model=False,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        matlab_version=r['metadata']['matlab_version'],stateflow_license_observed=True,stateflow_version=r['metadata']['stateflow_version'],chart_count=r['metadata']['chart_count'],
        component_vectors=168,analytic_regime_vectors=12,matlab_passed=r['summary']['passed'],matlab_failed=0,component_domain_rejections=14,
        saved_model_successful_intervals=15,saved_model_expected_unsupported_rejections=1,actual_modes_this_run=[2],prior_six_mode_acceptance='STATUS_stateflow_v52.json',
        scoped_independent_passed=q['actual_passed'],scoped_independent_failed=0,exact_branch_classification_failures=12,exact_branch_defect_status='OPEN',
        reviewer_selfchecks_passed=q['reviewer_selfchecks_passed'],reviewer_selfchecks_failed=0,
        sampled_end_energy_error_MWh=q['energy_errors_MWh'],sampled_compressor_error_MWh=q['compressor_errors_MWh'],
        coupled_stateflow_acceptance=False,full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        result_directory=rel,independent_qa=qp.relative_to(ROOT).as_posix(),limitations=limitations,next_actionable_task=next_task)
    write(ROOT/'STATUS_v54.json',status)
    lines=['# Coupled tank-temperature checkpoint v54\n\n',f'UTC {stamp}. Exact restricted equations and scoped numeric QA PASS; coupled Stateflow integration and exact branch guards remain OPEN. Saved model stays0.52, unchanged.\n\n',
        f'MATLAB {r["summary"]["passed"]}PASS/0FAIL;168 instantaneous vectors,12 source-affine regimes,14 component-domain rejections. Actual saved v52 executes15 charge-only intervals and one expected unsupported cold-tank rejection. Scoped independent QA {q["actual_passed"]}/0 plus5 reviewer mutations. Twelve exact-input branch classifications remain OPEN; these are not counted as certified discrete decisions.\n\n',
        'The source-limited coupled charge ODE is affine even though COP varies with tank temperature. Independent70-digit closed form and separate min-envelope RK4 agree with MATLAB at all tested positive/negative/zero/near-zero rates. Aux heat is fully rejected outside storage. No paper fixture values, calibrated equipment or continuous Stateflow release are claimed.\n\n',
        '| External macro chunks over0.05h | Terminal inventory MWh | Absolute energy error MWh | Absolute compressor error MWh |\n|---:|---:|---:|---:|\n']
    for ex,ee,we in zip(r['experiments'],q['energy_errors_MWh'],q['compressor_errors_MWh']):
        lines.append(f'| {ex["chunks"]} | {ex["end_energy_MWh"]:.12f} | {float(ee):.9g} | {float(we):.9g} |\n')
    lines+=['\nThese errors compare matched synthetic source-limited charging against the restricted continuous ODE. Each actual macro holds its sampled condenser/factor; externally carrying energy and clock between simulations is an approximation, not a new continuous controller. Refinement approaches the reference with approximately first-order error.\n\n',
        'Cold tank example T=25C requires condenser52C at this imposed outlet floor, below the saved v52 tank maximum70C. The actual runtime correctly rejects that unsupported new interface. Its conservative old guard must be replaced only alongside a coupled flow/COP/energy contract.\n\n',
        'At E=5MWh and binary C=0.2MWh/K, Ta=20C, charge approach2K and delivery/direct floor47C, nominal arithmetic yields tank45C and selects the tank branch. Exact arithmetic on those binary inputs yields T slightly below45C: gap -1.3877787807814456e-15K. Twelve related vectors have this unresolved discrete classification. Original failed exact-branch QA remains retained; the final reviewer records the flags and their2.8421709430404007e-14K rounding enclosure separately. This is an OPEN numerical guard/domain defect in the new component, not a v52 fixed-boundary regression.\n\n',
        'Evidence: '+rel+'; independent QA: '+qp.relative_to(ROOT).as_posix()+'. Derivation: audit/Coupled_temperature_derivation_v54.md. Original SimulationOutputs/report MATs/reopens, source snapshots, hashes and timestamped MATLAB/reviewer logs are preserved.\n\n',
        'Limitations:\n\n']
    lines += ['- '+v+'\n' for v in limitations]
    lines+=['\nNext actionable task: '+next_task+'\n']
    report=''.join(lines);write(ROOT/'audit/Coupled_temperature_results_v54.md',report);write(ROOT/'MASTER_STAGEBOARD_v54.md',report)
    newfiles=['matlab/+dchr/+components/coupled_temperature_boundary_v54.m','matlab/+dchr/+components/source_affine_charge_step_v54.m','matlab/run_coupled_interface_v54.m',
        'audit/prepare_coupled_interface_v54.py','audit/run_coupled_interface_v54.ps1','audit/verify_coupled_interface_v54.py','audit/finalize_coupled_interface_v54.py',
        'audit/Coupled_temperature_derivation_v54.md','audit/Coupled_temperature_results_v54.md','STATUS_v54.json','MASTER_STAGEBOARD_v54.md']
    progress=f'\n\n## {stamp} — v54 coupled temperature derivation and actual saved-v52 limitation audit\n\n'
    progress+='Read latest STATUS/stageboardsv53 and stateflowv52, acceptance ledger, frontier, progress and actual builder/planner/HP/storage/adapter code before edits. Prior immediate versioned Stateflow acceptance was already complete; followed its coupled-interface handoff. Visually reinspected source20 p8 and recorded current publisher429 and upstream repository metadata/no-files.\n\n'
    progress+=f'Work: derived/implemented tank-return variable-flow instantaneous boundary and exact single-source-limited charging ODE with conservative event rejection except the unresolved nominal branch kink. Tested168 boundary vectors and12 analytic regimes (positive/negative/zero/near-zero k),14 domain rejections; MATLAB621/0. Actual savedv52 runs15 charging intervals at1/2/4/8 external macro chunks and correctly rejects one cold-tank coupled envelope. Scoped independent QA{q["actual_passed"]}/0 and5 separate mutations; independent exact branch comparisons retain12 OPEN flags. No new SLX accepted.\n\n'
    progress+='Failures retained: sandbox MATLAB startup filesystem inconsistency; initial reviewer singleton-struct JSON exception; subsequent exact-branch QA5314PASS/12FAIL. Corrected reviewer normalizes the shape and explicitly separates uncertified branch decisions from continuous-power/energy checks, preserving original sources/reports/logs. No production/model tolerance or guard was weakened.\n\n'
    progress+='Files created: '+', '.join(newfiles)+'. Shared progress/acceptance appended only; fresh immutable evidence '+rel+'. Existing models/MATLAB/status/data hashes unchanged; no Jarvice, unrelated files, settings, schedules, runner, secrets or publication touched.\n\n'
    progress+='Remaining limitations: '+' '.join(limitations)+'\n\nNext actionable task: '+next_task+'\nStop this coherent checkpoint with explicit OPEN-defect handoff.\n'
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Coupled-temperature derivation/limitation checkpoint — {stamp} / v54\n\nNo new SLX; accepted saved0.52 remains unchanged. MATLAB621/0; actual15 charge-only intervals plus one expected unsupported cold-tank rejection; scoped independent{q["actual_passed"]}/0 and reviewer5/0. Exact-input branch classification12 flags OPEN; coupled Stateflow integration not accepted. Restricted affine ODE derivation and first-order sampled discrepancy retained. STATUS_v54 and audit/Coupled_temperature_results_v54.md are authoritative. Next: conservative kink domain/event handling and all limiter regimes before an additive coupled model with six-mode executable acceptance.\n')
    files=[ROOT/p for p in newfiles]+[ROOT/'automation/engineering_progress.md',ROOT/'automation/STATEFLOW_ACCEPTANCE.md']
    files += [p for p in folder.rglob('*') if p.is_file() and 'local_build' not in p.relative_to(folder).parts]
    manifest=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p),size=p.stat().st_size) for p in sorted(set(files))]
    name='Coupled_temperature_manifest_v54_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    write(ROOT/'audit'/f'{name}.json',dict(timestamp_utc=stamp,files=manifest,excludes='local_build disposable cache; no deletion performed'))
    failed=[v['path'] for v in manifest if sha(ROOT/v['path'])!=v['sha256'] or (ROOT/v['path']).stat().st_size!=v['size']]
    preservation=json.loads((folder/'preservation.json').read_text());old_failed=[v['path'] for v in preservation if sha(ROOT/v['path'])!=v['sha256']]
    write(ROOT/'audit'/f'{name}_postclose.json',dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),sealed_files=len(manifest),unchanged_prior_files=len(preservation),failures=failed+old_failed,
        result='SCOPED_EVIDENCE_SEALED_WITH_12_OPEN_BRANCH_FLAGS',exact_branch_classification_failures=12))
    assert not failed and not old_failed
    print(json.dumps(dict(status='STATUS_v54.json',matlab_passed=621,scoped_independent_passed=q['actual_passed'],exact_branch_failures_open=12,model_version='0.52',new_model=False,sealed_files=len(manifest),prior_files_preserved=len(preservation))))
if __name__=='__main__':main()
