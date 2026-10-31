"""Publish the local checkpoint only after executed and independent gates pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
qa_path=sorted(folder.glob('independent_QA_v86_*.json'))[-1]
qa=json.loads(qa_path.read_text());report=json.loads((folder/'report.json').read_text())
assert qa['summary']['failed']==report['summary']['failed']==0
assert all(a['passed'] for a in qa['reviewer_selfchecks'])
timestamp=datetime.now(timezone.utc).isoformat()
relative=folder.relative_to(ROOT).as_posix()
runs=report['runs'];intervals=sum(len(r['trace']) if isinstance(r['trace'][0],list) else 1 for r in runs)
traces=[row for r in runs for row in (r['trace'] if isinstance(r['trace'][0],list) else [r['trace']])]
segments=sum(int(row[12]) for row in traces);events=sum(int(row[13]) for row in traces)
limitations=[
    'No new SLX or renewal implementation: actual saved model remains 0.85, checkpoint/harness is 0.86.',
    'Nominal H=1 uses actual certificate horizon 1+2^-40 h. Exact H=1 endpoint outcome is retained separately; no elapsed history or production tolerance changed.',
    'The nonlinear comparator is hypothetical, zero-loss, HP initially ON and nonbinding except for compressor rating, with no switching. Positive-loss/event controls execute the actual saved model separately.',
    'Additional heat may use more compressor work; charging inventory is not delivered heat or equal-electricity savings.',
    'Same-agent algorithmic independence: exact-binary Fraction/120-160 digit closed equations and separate RK4 call no production MATLAB solver. MATLAB reopens MAT; no independent personnel or MAT parser claim.',
    'Synthetic rating, refrigerant proxy, approaches, efficiencies and fixtures are engineering assumptions. No new primary text/signoff, equipment calibration, article replication, measured physical validation, annual or generated-code acceptance. Full signoffs 0/31.',
    'Inherited span, clock uncertainty, segment-count and event-collision refusal domains remain. Protocol ticks are not solver-clock event times. Auxiliary electricity is outside compressor ceiling.',
    'Restricted MATLAB startup failed before model loading; the authorized unrestricted local batch and all retained logs provide the execution evidence.'
]
next_task=('Implement additive interval-renewable electrical cap in the SAME six-mode saved Stateflow chart using audit/Horizon_renewal_derivation_v86.md. '
    'Preserve raw policy, retained inventory hull, physical clock, latch, ON/OFF age and correlated event/energy memory; certify expiry, generation and provenance in a versioned schema/reporter. '
    'Regress v86 histories/partitions and positive-loss, floor, stop/cutoff/restart/dwell, zero/nonbinding and corruption/refusal controls with independent original-MAT closed equations. '
    'Do not reset the simulation or use the start-temperature cap alone. Preserve v80-v86. Primary equipment supplement/calibration remains open.')
status=dict(version='0.86',timestamp_utc=timestamp,inherits='STATUS_v85.json',
    result='SAVED_V85_HORIZON_PARTITION_SENSITIVITY_ACCEPTED_RENEWAL_NOT_IMPLEMENTED_CALIBRATION_OPEN',
    new_model=False,saved_model='matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v85.slx',saved_model_version='0.85',
    harness_version='0.86',model_sha256=qa['model_sha256'],model_executed_this_run=True,
    matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
    complete_saved_model_runs=len(runs),held_intervals=intervals,positive_segments=segments,interior_events=events,
    required_actual_final_mode_coverage=report['mode_coverage'],actual_fault_rejections=len(report['faults']),
    nonlinear_comparisons=len(qa['comparisons']),partition_comparisons=len(qa['partition_results']),
    exact_one_hour_horizon_accepted=qa['exact_horizon_probe_accepted'],reviewer_selfchecks=len(qa['reviewer_selfchecks']),
    matlab_metadata=report['metadata'],result_directory=relative,independent_qa=qa_path.relative_to(ROOT).as_posix(),
    derivation='audit/Horizon_renewal_derivation_v86.md',results='audit/Horizon_sensitivity_results_v86.md',
    primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
    limitations=limitations,next_actionable_task=next_task)
def write_new(p,text):
    with p.open('x',encoding='utf-8') as f:f.write(text)
for name in ['STATUS_v86.json','STATUS_stateflow_v86.json']:write_new(ROOT/name,json.dumps(status,indent=2)+'\n')
by={c['id']:c for c in qa['comparisons']}
selected=['service_E3.0_a1.0','charge_E4.95_a1.0','charge_E8.5_a1.0']
table=['| History | Nominal H (h) | Cap (MW) | Actual HP heat (MWh) | Hypothetical dynamic HP heat (MWh) | Gap (MWh) |',
       '|---|---:|---:|---:|---:|---:|']
for history in selected:
    for H in [1,2,4]:
        c=by[f'{history}_H{H}_dt0.25']
        table.append(f"| {history} | {H} | {c['cap_MW']:.10g} | {float(c['actual']['hp_heat']):.10g} | {float(c['hypothetical_dynamic']['hp_heat']):.10g} | {float(c['dynamic_heat_gap_MWh']):.10g} |")
partition_max=max(float(c['max_closed_difference']) for c in qa['partition_results'])
accepted=qa['exact_horizon_probe_accepted']
text=f'''# Saved-v85 horizon and partition sensitivity v86

UTC {timestamp}.

The preserved actual saved v85 Stateflow model executes {len(runs)} schedules / {intervals} held intervals / {segments} positive segments / {events} interior events, with all six required modes. MATLAB {report['summary']['passed']} PASS / 0 FAIL; independent equation/artifact QA {qa['summary']['passed']} PASS / 0 FAIL; three separate reviewer corruptions detected. Seven actual chart refusals and fresh saved-v80/global-v83r2 comparisons execute; clean saved-v85 reopening is bitwise equal. No new SLX is created.

Twelve identical one-hour v84 histories execute at nominal H=1/2/4. Larger declared horizon never increases the effective cap or reconstructed HP heat. Twelve paired partition comparisons (0.125/0.5 versus 0.25 h) preserve the cap exactly and match closed trajectories to the predeclared 1e-90 budget; maximum observed difference {partition_max:.3g} MWh-equivalent across reconstructed fields. Original report hulls overlap. The hypothetical nonlinear comparator is independently reconstructed at 120/160 digits and checked against floor-aware RK4; it is not an implemented renewable controller.

{chr(10).join(table)}

Nominal H=1 uses actual H=1+2^-40 h, a predeclared certificate margin (~3.27 nanoseconds); all simulated histories remain exactly one hour. The separately executed exact H=1 endpoint probe was {'ACCEPTED' if accepted else 'REFUSED by the saved declared-horizon upper-clock guard'}. Its original MAT and actual diagnostic are retained. This outcome is an implementation-domain observation, not a changed production guard.

The exact-rational charging witness proves that an electrical cap taken only at the initial temperature can exceed its compressor rating at the charged endpoint. The proposed renewal contract therefore certifies a reachable inventory upper bound over each renewal window and preserves clock, inventory hull, latch, dwell and correlated event/energy memory. Current v85 raw/effective policy immutability does not implement that contract; restarting the model is not renewal.

Evidence `{relative}` contains timestamped MATLAB/Simulink and independent QA logs, execution receipts, original/reopened MAT, binary exports, predeclared specification, source snapshots and preservation hashes, numeric trajectory CSV and 48 comparisons. Model SHA256 `{qa['model_sha256']}`. Derivation: `audit/Horizon_renewal_derivation_v86.md`.

Files added: `matlab/run_horizon_sensitivity_v86.m`, `audit/run_horizon_sensitivity_v86.ps1`, `audit/scaffold_horizon_v86.py`, `audit/horizon_sensitivity_v86.py`, `audit/close_horizon_v86.py`, `audit/Horizon_renewal_derivation_v86.md`, `audit/Horizon_sensitivity_results_v86.md`, and v86 STATUS/stageboard twins. Shared engineering progress, acceptance and research-frontier ledgers are appended only. Prior MATLAB, SLX and checkpoints are hash-preserved.

Limitations:

{chr(10).join('- '+v for v in limitations)}

Next actionable task: {next_task}

Stop after this coherent executed deliverable and handoff.
'''
for name in ['MASTER_STAGEBOARD_v86.md','MASTER_STAGEBOARD_stateflow_v86.md','audit/Horizon_sensitivity_results_v86.md']:write_new(ROOT/name,text)
for name in ['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md']:
    with (ROOT/name).open('ab') as f:f.write(('\n\n## '+timestamp+' — checkpoint v86\n\n'+text).encode('utf-8'))
handoff=[]
for manifest in ['preservation.json','source_hashes.json']:
    for e in json.loads((folder/manifest).read_text()):
        ok=hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()==e['sha256']
        if manifest=='source_hashes.json':ok=ok and hashlib.sha256((folder/'source_snapshot'/e['path']).read_bytes()).hexdigest()==e['sha256']
        handoff.append(dict(name=e['path'],passed=ok))
for e in json.loads((folder/'ledger_prefixes.json').read_text()):
    handoff.append(dict(name=e['path']+'_prefix',passed=hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256']))
handoff.append(dict(name='status_twins_equal',passed=(ROOT/'STATUS_v86.json').read_bytes()==(ROOT/'STATUS_stateflow_v86.json').read_bytes()))
handoff.append(dict(name='stageboard_twins_equal',passed=(ROOT/'MASTER_STAGEBOARD_v86.md').read_bytes()==(ROOT/'MASTER_STAGEBOARD_stateflow_v86.md').read_bytes()))
artifacts=[]
for name in ['STATUS_v86.json','STATUS_stateflow_v86.json','MASTER_STAGEBOARD_v86.md','MASTER_STAGEBOARD_stateflow_v86.md',
             'audit/Horizon_sensitivity_results_v86.md','audit/Horizon_renewal_derivation_v86.md','audit/close_horizon_v86.py']:
    p=ROOT/name;dest=folder/'closure_snapshot'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    artifacts.append(dict(path=name,sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
write_new(folder/'closure_artifacts.json',json.dumps(artifacts,indent=2)+'\n')
summary=dict(passed=sum(x['passed'] for x in handoff),failed=sum(not x['passed'] for x in handoff))
write_new(folder/('final_handoff_v86_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')+'.json'),json.dumps(dict(summary=summary,checks=handoff),indent=2)+'\n')
print(json.dumps(dict(status=status['result'],matlab=report['summary'],independent=qa['summary'],handoff=summary)))
assert summary['failed']==0
