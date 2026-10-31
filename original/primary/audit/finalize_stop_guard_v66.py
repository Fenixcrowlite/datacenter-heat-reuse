"""Close only a fully executed, independently reviewed local checkpoint."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qp=sorted(folder.glob('independent_QA_v66_*.json'))[-1];qa=json.loads(qp.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert report['mode_coverage']==list(range(6)) and all(x['passed'] for x in qa['reviewer_selfchecks'])
    assert len(report['runs'])==16 and len(report['faults'])==10
    for r in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/r['path'])==r['sha256']
    for r in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/r['path'])==r['sha256']==sha(folder/'source_snapshot'/r['path'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
    assert any(x['exit_code']==0 and x['evidence_class']=='OBSERVED_LOCAL_MATLAB_BATCH' for x in receipts)
    model=ROOT/'matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx';assert sha(model)==qa['model_sha256']
    prior=json.loads((ROOT/'STATUS_v65.json').read_text());stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    comparisons=json.loads((folder/'earliest_comparisons_v66.json').read_text())
    limits=[
        'Conservative sampled stop guard and repeated sampled cycles only; general repeated exact-event Stateflow remains OPEN. Legacy v57 and sampled v65 acceptance preserved.',
        'Withholding an entire uncertified charge interval can shut down early and lose delivered service. Timestep service is not monotonic in these fixtures.',
        'Earliest comparator is separate 120/160-digit engineering mathematics with explicit root ordering threshold; no certified compiled earliest-event switching or source/compressor comparison claimed.',
        'Inherited correlated v64 prefix, exact host equivalent-limiter certificate, 128-rectangle source/work enclosures and |lambda*dt|<=1 domain remain.',
        'Fixed refrigerant/water approaches, common tank return and cooling factor are engineering assumptions; equipment calibration, article replication and measured physical validation are untested.',
        'Same-agent independent algorithms, not independent personnel. Original MAT reopened/exported by MATLAB; standalone generated code and Python HDF5 parsing not accepted.',
        'Sandbox startup, initial MATLAB JSON vector setup and reviewer indentation/stale-manifest failures preserved in the earlier development evidence folder.'
    ]
    nxt=('Derive certified local thermal-stop/cutoff/restart root brackets for repeated v66 trajectories and integrate one repeated earliest-event cycle into an additive SAME six-mode chart. '
        'Carry original inventory/ports/age/clock correlation, certify OFF dwell and ordering against held demand/source boundaries, reject unresolved ordering, and compare original-MAT service and source/work enclosures to the independent v66 event reference. '
        'Use the v66 stop witness and repeated dt=0.25/0.5/1 schedules as regression fixtures; preserve v57-v66. Primary calibration and measured validation remain OPEN.')
    status=dict(version='0.66',timestamp_utc=stamp,inherits='STATUS_v65.json',result='SCOPED_SAMPLED_STOP_GUARD_AND_REPEATED_CYCLES_PASS_EARLIEST_STATEFLOW_OPEN',
        new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        accepted_dispatch_model=prior['accepted_dispatch_model'],accepted_dispatch_sha256=prior['accepted_dispatch_sha256'],accepted_dispatch_version='0.57',
        accepted_sampled_interval_model=model.relative_to(ROOT).as_posix(),conservative_interval_service_acceptance=True,coupled_stateflow_acceptance=False,
        matlab_metadata=report['metadata'],matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        actual_runs=len(report['runs']),protocol_ticks=sum(len(x['input']) if isinstance(x['input'][0],list) else 1 for x in report['runs']),service_intervals=qa['service_intervals'],
        required_mode_coverage=report['mode_coverage'],actual_runtime_fault_rejections=len(report['faults']),v30_reference_comparisons=sum(len(x['references_v30']) for x in report['runs']),
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),result_directory=rel,independent_qa=qp.relative_to(ROOT).as_posix(),derivation='audit/Sampled_stop_derivation_v66.md',
        saved_v65_stop_overshoot_MWh=report['baseline_witness']['trace'][36:38],stop_inventory_MWh=9.6,
        repeated_schedule_h=52,repeated_cycles_per_resolution=4,repeated_dt_h=[.25,.5,1],general_repeated_earliest_event_stateflow='OPEN',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',limitations=limits,next_actionable_task=nxt)
    rows=[]
    for x in comparisons:
        s=x['sampled_enclosures'];e=x['earliest']['ports'];gap=D(e['delivered'])-D.from_float(s['delivered'][1])
        rows.append(f"| {x['dt']:g} | {s['delivered'][0]:.9f}–{s['delivered'][1]:.9f} | {s['unmet'][0]:.9f}–{s['unmet'][1]:.9f} | {gap:.9f} |")
    text=f'''# Executed sampled stop and repeated-cycle Stateflow checkpoint v66

UTC {stamp}. New saved `DCHR_Interval_Dispatch_Stateflow_v66.slx` adds an
entire-interval thermal stop guard and actually executes four repeated charge,
cutoff and restart cycles at each of three binary timesteps. The original v65
stop witness reaches 9.70199459269636 MWh above the 9.6 MWh stop while remaining
below 10 MWh capacity. Same-input v66 withholds charge and remains below stop.
This strengthens the sampled contract; previous capacity-safety acceptance is
preserved. No earliest-event Stateflow replacement is accepted.

MATLAB {status['matlab_passed']} PASS / 0 FAIL; independent {qa['summary']['passed']}
PASS / 0 FAIL; {status['actual_runs']} actual runs / {status['protocol_ticks']}
protocol ticks / {qa['service_intervals']} service intervals, all six modes,
10 actual runtime fault rejections, {status['v30_reference_comparisons']} v30
comparisons, eight separate reviewer corruptions detected. Each repeated run
observes four shutdowns and three restarts after the initial ON state. Retained
inventory, cumulative ports, age and physical-clock bounds survive every step.

Independent earliest comparator uses the SAME binary equipment and 52-hour
demand/source schedule with 2 MW boiler limit. Across all resolutions it delivers
26.933679986 MWh and leaves 21.066320014 MWh unmet; boiler energy is 16 MWh.
Numerical event roots and all ports agree at 120/160 digits. Actual sampled
service losses below are engineering policy consequences, not measured results.

| dt (h) | Sampled delivered (MWh enclosure) | Sampled unmet (MWh enclosure) | Earliest minus sampled upper service (MWh) |
| --- | --- | --- | --- |
{chr(10).join(rows)}

The differences are NOT monotonic with timestep: the v65 half-capacity charge
budget and v66 whole-interval withholding change the sampled decisions. No
convergence, optimization or physical-equivalence conclusion follows.

Evidence: `{rel}`: actual MATLAB logs/exit receipt, original reopened MAT,
binary exports, numeric CSV, independent QA and event comparison JSON, sealed
sources and preservation hashes. Earlier startup/setup/reviewer failures remain
in `results/stop_guard_v66_20261011T213334_742656Z`; the reviewer correctly rejected
that folder's stale source manifest after its indentation repair. Fresh final
execution uses the already saved model and corrected sealed reviewer.

Limitations:
{chr(10).join('- '+x for x in limits)}

Next actionable task: {nxt}
'''
    for name in ['STATUS_v66.json','STATUS_stateflow_v66.json']:
        p=ROOT/name;assert not p.exists();p.write_text(json.dumps(status,indent=2)+'\n')
    for name in ['MASTER_STAGEBOARD_v66.md','MASTER_STAGEBOARD_stateflow_v66.md','audit/Sampled_stop_results_v66.md']:
        p=ROOT/name;assert not p.exists();p.write_text(text)
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## {stamp} — v66 executed sampled thermal stop / repeated cycles\n\nRead STATUS/stageboards, acceptance, frontier and v65/v64 code first. Work stayed in this project; no Jarvice, unrelated files, user settings, tasks, runner, secrets or external publication touched. Added versioned v66 builder/kernel/core/model and MATLAB harness; independently reviewed original-MAT exports and derived repeated earliest-event service comparator. Saved-v65 stop overshoot reproduced; strengthened v66 sampled stop guard passes.\n\nPASS/FAIL: MATLAB {status["matlab_passed"]}/0; independent {qa["summary"]["passed"]}/0; eight reviewer corruptions detected. {status["actual_runs"]} runs/{status["protocol_ticks"]} ticks/{qa["service_intervals"]} service intervals; all six modes, ten runtime faults; three resolutions × four cycles. Logs and evidence: `{rel}`. Initial startup/setup and reviewer indentation/stale-manifest failures retained in the development folder. Final saved-model batch and fresh sealed review pass; prior preservation hashes unchanged.\n\nFiles: matlab/simulink/*v66.m and DCHR_Interval_Dispatch_Stateflow_v66.slx; matlab/run_interval_dispatch_v66.m; audit/prepare_stop_guard, prepare_reviewer, earliest_service_reference, verify_interval_dispatch, seal_stop_guard, finalize_stop_guard, run_interval_dispatch and Sampled_stop_derivation/results_v66; STATUS/stageboards_v66.\n\nLimitations: whole-sample early OFF reduces delivered service by 0.756498743–1.126472212 MWh against the separate earliest comparator in the synthetic 52-hour fixtures; timestep differences are nonmonotonic. General earliest-event Stateflow, hardware calibration, primary replication and measured validation remain OPEN. Same-agent algorithmic QA only.\n\nNext actionable task: {nxt}\nStop after this coherent executed deliverable and handoff.\n')
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Sampled thermal stop / repeated-cycle acceptance — {stamp} / v66\n\nNew saved v66 actually executes all six modes and three four-cycle schedules. MATLAB {status["matlab_passed"]}/0, independent {qa["summary"]["passed"]}/0, ten runtime rejections, eight reviewer mutations. Saved-v65 stop overshoot reproduced; conservative entire-interval v66 stop guard accepted. General repeated earliest-event Stateflow remains OPEN; separate high-precision event comparator is not that implementation. Prior models preserved. STATUS_stateflow_v66 and audit/Sampled_stop_results_v66.md are authoritative. No calibration/article replication/measured validation.\n')
    print(json.dumps(dict(status='CHECKPOINT_V66_CLOSED',matlab=report['summary'],independent=qa['summary'],folder=rel),indent=2))

if __name__=='__main__':main()
