"""Publish only local project ledgers after executed v65 and independent QA pass."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qapath=sorted(folder.glob('independent_QA_v65_*.json'))[-1];qa=json.loads(qapath.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(x['passed'] for x in qa['reviewer_selfchecks'])
    assert report['mode_coverage']==list(range(6)) and len(report['runs'])==12
    assert all(x['identifier'] and x['expected_guard'] in x['message'] for x in report['faults'])
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    assert any(x['exit_code']==0 and x['evidence_class']=='OBSERVED_LOCAL_MATLAB_BATCH' for x in receipts)
    model=ROOT/'matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v65.slx';assert sha(model)==qa['model_sha256']
    prior=json.loads((ROOT/'STATUS_v64.json').read_text());assert sha(ROOT/prior['accepted_dispatch_model'])==prior['accepted_dispatch_sha256']
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    limits=[
        'Scoped conservative sampled dispatch. Legacy accepted v57 remains preserved; general repeated exact-event replacement is OPEN.',
        'One retained v64 analytic capacity-OFF/restart prefix; subsequent service uses held-power sampled decisions and conservative capacity/cutoff budgets.',
        'Common hot-water return at tank temperature, fixed water/refrigerant approaches and cooling factor are engineering assumptions without equipment calibration.',
        'Source/compressor energies are enclosures from 128 outward rectangles; service is conservative, may leave capacity unused, and is not optimized.',
        'Authoritative held dt and cumulative physical-clock enclosure differ from solver protocol ticks; no earliest-event thermal firing is claimed.',
        'Inherited exact equivalent-limiter host certificate trust boundary and |lambda*duration|<=1 outward arithmetic domain remain.',
        'MATLAB normal-mode Stateflow chart executed and license observed; empty ver(stateflow) retained; standalone generated code not accepted.',
        'Same-agent independent Fraction and 120/160-digit algorithms, not independent personnel. Original MAT reopened/exported by MATLAB; independent Python HDF5 parser unavailable.',
        'Synthetic fixtures only; no new primary article text, equipment calibration, article replication or measured physical validation.',
        'Startup, compile, fixture, cumulative-clock and stale reviewer-manifest failures are preserved in timestamped development folders.'
    ]
    next_task=('Test and implement repeated capacity/cutoff/HP restart chains for the new v65 interval-service policy. '
        'Derive explicit sampled-vs-earliest-event comparison using identical exact-binary inputs, demand timing and finite backup limits; '
        'retain correlated inventory/ports/clocks and reject unresolved event ordering. Extend the SAME chart only with justified guards, '
        'then independently check original-MAT bounds and energy/service consequences. Preserve v57-v65; physical calibration and primary evidence remain OPEN.')
    status=dict(version='0.65',timestamp_utc=stamp,inherits='STATUS_v64.json',result='SCOPED_SIX_MODE_INTERVAL_SERVICE_STATEFLOW_PASS_EXACT_EVENT_REPLACEMENT_OPEN',
        new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        accepted_dispatch_model=prior['accepted_dispatch_model'],accepted_dispatch_version='0.57',accepted_dispatch_sha256=prior['accepted_dispatch_sha256'],
        accepted_sampled_interval_model=model.relative_to(ROOT).as_posix(),conservative_interval_service_acceptance=True,coupled_stateflow_acceptance=False,
        matlab_metadata=report['metadata'],matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        actual_runs=len(report['runs']),protocol_ticks=sum(len(r['input']) if isinstance(r['input'][0],list) else 1 for r in report['runs']),
        service_intervals=qa['service_intervals'],required_mode_coverage=report['mode_coverage'],actual_runtime_fault_rejections=len(report['faults']),
        v30_reference_comparisons=sum(len(r['references_v30']) for r in report['runs']),reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        result_directory=rel,independent_qa=qapath.relative_to(ROOT).as_posix(),derivation='audit/Interval_service_derivation_v65.md',
        scalar_service_interface_blocker='RESOLVED_FOR_CONSERVATIVE_SAMPLED_POLICY',full_primary_signoffs=0,total_sources=31,
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next_actionable_task=next_task)
    text=f'''# Executed six-mode interval-service Stateflow checkpoint v65

UTC {stamp}. New saved `DCHR_Interval_Dispatch_Stateflow_v65.slx` executes
all six modes in the SAME chart, including each retained v64 restart chain and
subsequent direct heat, discharge, bounded boiler, unmet demand, IDLE and charge.
The scalar-service interface blocker is resolved for this conservative sampled
policy: use lower inventory for service and upper inventory for capacity;
retain the entire inventory, cumulative ports and age hulls. No midpoint reset.

MATLAB {status['matlab_passed']} PASS / 0 FAIL; {status['actual_runs']} actual runs /
{status['protocol_ticks']} protocol ticks / {qa['service_intervals']} service intervals;
{len(report['faults'])} specific runtime fault rejections, two valid samples before
delayed rejection; {status['v30_reference_comparisons']} verified-v30 comparisons.
Independent QA {qa['summary']['passed']} PASS / 0 FAIL and
{len(qa['reviewer_selfchecks'])} separate synthetic corruptions detected.
Exact-binary 120/160-digit original-trajectory and whole-inventory-box solutions,
piecewise source-energy integrals, finite water/source capacities, HP latch/dwell,
first law, auxiliary exclusion, service bounds and artifact hashes all checked.
Unit discharge efficiency/zero loss and near-cutoff no-credit fixtures execute.

Immutable reopened original MAT/binary exports, numeric CSV, MATLAB/Python logs,
receipts and source snapshots: `{rel}`.
All v57-v64 models/status/stageboards and earlier MATLAB sources are unchanged.
Legacy dispatch acceptance remains v57. V65 is a scoped additional sampled model;
general repeated exact-event coupling remains OPEN. No new primary-source or
physical-validation claims.

Development scaffold recovery is recorded in
`results/v65_scaffold_recovery_20261011T211923092Z`.
Original builder was restored from the earlier saved snapshot; unused draft
generator stopped before changing the existing kernel. Startup/configuration,
absolute-horizon subtraction, coverage fixtures and stale reviewer-manifest
failures remain in the timestamped development results. Final execution uses
the saved model bound to a fresh sealed source manifest.

Limitations:
'''+'\n'.join('- '+x for x in limits)+f'\n\nNext actionable task: {next_task}\n'
    for name in ['STATUS_v65.json','STATUS_stateflow_v65.json']:
        p=ROOT/name;assert not p.exists();p.write_text(json.dumps(status,indent=2)+'\n')
    for name in ['MASTER_STAGEBOARD_v65.md','MASTER_STAGEBOARD_stateflow_v65.md','audit/Interval_service_results_v65.md']:
        p=ROOT/name;assert not p.exists();p.write_text(text)
    progress=f'''\n\n## {stamp} — v65 executed six-mode conservative interval service

Read latest STATUS/stageboards, Stateflow acceptance, research frontier, progress
and v64/v57/v52/v30 code before changes. Found and completed the unfinished v65
scaffold. All work stayed in this project; no Jarvice, settings, scheduler,
agent runner, secrets, unrelated files or external publication touched.

Implemented and executed retained restart + actual six-mode service in one saved
Stateflow chart. Repaired heterogeneous JSON harness, workspace final-value
configuration, cumulative-clock certification, data shadowing and representable
service subtraction. Exact etaD=1 discharge loss is zero. Independent QA derives
whole-inventory-box/ original-trajectory ODE solutions and piecewise source
integrals separately using Fraction/120/160-digit arithmetic. Correlated
inventory, ports, age and initial provenance persist; no scalar midpoint service.

PASS/FAIL: MATLAB {status['matlab_passed']}/0, independent {qa['summary']['passed']}/0;
{status['actual_runs']} runs/{status['protocol_ticks']} ticks, all six modes;
{len(report['faults'])} faults and two valid delayed-prefix samples;
{status['v30_reference_comparisons']} v30 comparisons; {len(qa['reviewer_selfchecks'])} separate mutations detected.
Timestamped logs, receipts, reopened MAT/binary/numeric exports and sealed sources:
`{rel}`. Previous source/model/status/stageboard preservation hashes pass.

Files: matlab/simulink/build_interval_dispatch_v65.m,
interval_service_core_v65.m, interval_dispatch_kernel_v65.m,
DCHR_Interval_Dispatch_Stateflow_v65.slx; matlab/run_interval_dispatch_v65.m;
audit/assemble/prepare/run/verify/finalize_interval_dispatch_v65;
Interval_service_derivation/results_v65.md; STATUS/stageboards_v65.
Shared progress and acceptance are append-only. Development drafts and failures
retained with clear recovery note; reviewer correctly rejected its stale manifest.

Scope: conservative sampled policy accepted, general repeated exact-event
replacement OPEN; legacy acceptance remains v57. Same-agent algorithmic QA,
normal-mode chart, conditional arithmetic and engineering water assumptions.
No new primary text, calibration, article replication or measured validation.

Next actionable task: {next_task}
Stop after this coherent executable deliverable and handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a') as f:f.write(f'\n\n## Six-mode conservative interval-service Stateflow — {stamp} / v65\n\n'+text.split('\n\n',1)[1])
    (folder/'release_v65.json').write_text(json.dumps(dict(timestamp_utc=stamp,status_sha256=sha(ROOT/'STATUS_v65.json'),model_sha256=sha(model),qa_sha256=sha(qapath)),indent=2)+'\n')
    print(json.dumps({k:status[k] for k in ['result','matlab_passed','independent_passed','actual_runs','service_intervals','result_directory']},indent=2))
if __name__=='__main__':main()
