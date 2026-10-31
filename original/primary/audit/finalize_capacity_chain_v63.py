from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qa_path=sorted(folder.glob('independent_QA_v63_*.json'))[-1];qa=json.loads(qa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0 and all(s['passed'] for s in qa['reviewer_selfchecks'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];assert any(r['exit_code']==0 for r in receipts)
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    model=ROOT/'matlab/simulink/DCHR_Capacity_Chain_Stateflow_v63.slx';assert sha(model)==qa['model_sha256']
    inherited=json.loads((ROOT/'STATUS_stateflow_v62.json').read_text());assert sha(ROOT/inherited['accepted_dispatch_model'])==inherited['accepted_dispatch_sha256']
    stamp=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix();n=report['summary']['passed'];q=qa['summary']['passed']
    next_task=('Integrate the v63 symbolic capacity safety-OFF record and conservative OFF-age enclosure into an additive six-mode dispatch model. '
               'Implement thermal restart/cutoff hysteresis and actual uncertainty-aware OFF-to-ON event chains without resetting inventory/ports at a scalar root. '
               'Preserve v57 finite-water guards and v52 endpoint protocol. Reject unsupported limiters/regimes; execute six required modes, delayed faults, '
               'verified-reference comparisons and independent original-MAT equation/port/clock QA. Preserve v52-v63; do not repeat unchanged annual matrices. '
               'Equipment calibration and measured physical validation remain OPEN.')
    limits=[
        'Scoped constant-request branch/capacity safety-OFF/passive component; accepted full six-mode dispatch remains v57. No full coupled replacement accepted.',
        'Dwell readiness is three-way enclosure certification only. Every restart command rejects; thermal cutoff/restart hysteresis and actual OFF-to-ON integration OPEN.',
        'Protocol solver ticks are separate from physical event-time enclosures. No physical solver-clock event firing or general event chains accepted.',
        'Exact branch/capacity operands and correlations are retained; equivalent limiter ties rely on host exact-rational certificate. No scalar event reset/service credit.',
        'Conditional outward binary64, |lambda*span|<=1, strictly increasing request-limited charge, scalar exact initial inventory, 128 source rectangles.',
        'Stateflow license, one saved actual chart and normal-mode execution observed; ver(Stateflow) remains empty. No standalone generated-code acceptance.',
        'Same-agent independent Fraction and 120/160-digit analytic QA, not independent personnel. Synthetic fixtures only; primary calibration/article replication/physical validation OPEN.',
        'Development sandbox startup failure and two fault-expectation failures retained. First development SLX archived; final evidence uses sealed source and saved-model hashes.',
        'Delayed faults execute in saved chart; timing evidence includes separate four-tick valid-prefix replay, not partial outputs from the failing simulation.'
    ]
    status=dict(version='0.63',timestamp_utc=stamp,inherits='STATUS_stateflow_v62.json',result='SCOPED_CAPACITY_SAFETY_OFF_PASSIVE_DWELL_COMPONENT_PASS_FULL_COUPLED_DISPATCH_OPEN',
        new_model=True,model_version='0.63_CAPACITY_CHAIN_COMPONENT',saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        accepted_dispatch_model=inherited['accepted_dispatch_model'],accepted_dispatch_version='0.57',accepted_dispatch_sha256=inherited['accepted_dispatch_sha256'],
        coupled_stateflow_acceptance=False,capacity_chain_component_acceptance='SCOPED_PASS',actual_restart_acceptance=False,matlab_metadata=report['metadata'],
        matlab_passed=n,matlab_failed=0,actual_runs=len(report['runs']),protocol_ticks=qa['protocol_ticks'],actual_runtime_fault_rejections=len(report['faults']),
        v30_reference_comparisons=sum(len(r['references_v30']) for r in report['runs']),independent_passed=q,independent_failed=0,reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        nonrepresentable_branch_runs=qa['nonrepresentable_branch_runs'],nonrepresentable_capacity_runs=qa['nonrepresentable_capacity_runs'],
        six_mode_evidence_this_run='INHERITED_V57_V61_NOT_REEXECUTED_UNCHANGED',full_primary_signoffs=0,total_sources=31,primary_article_replication=False,
        independent_physical_validation='NOT_TESTED',result_directory=relative,independent_qa=qa_path.relative_to(ROOT).as_posix(),derivation='audit/Capacity_chain_derivation_v63.md',
        next_actionable_task=next_task,limitations=limits)
    text=f'''# Compiled correlated capacity-chain checkpoint v63

UTC {stamp}. Actual saved new component: **0.63**; accepted six-mode dispatch **0.57**.
Full continuously coupled six-mode acceptance remains OPEN.

Fourteen saved-chart runs / {qa['protocol_ticks']} protocol ticks execute FLOOR,
branch CONTACT, TANK, CAPACITY CONTACT and PASSIVE COOLING. Capacity safety OFF
retains the exact capacity expression and root enclosure. Post-OFF charge/source/
compressor/auxiliary energies freeze; passive standing loss and correlated OFF-age
bounds advance. OFF-dwell outcomes too early / unresolved / certified ready all
execute. No midpoint, scalar event reset or restart authorization.

MATLAB {n} PASS / 0 FAIL; fourteen specific actual runtime fault rejections;
56 accepted-v30 scalar energy comparisons. Independent reopened-MAT/binary/Fraction/
120-/160-digit QA {q} PASS / 0 FAIL; eight separate synthetic mutations detected.
Zero/positive loss, unit charging efficiency, zero auxiliary electricity and
nonrepresentable branch/capacity expressions tested. Four-tick valid prefix replay
is separate from delayed failing simulations. Saved embedded kernel bound to source.

Evidence: `{relative}`. Derivation: `audit/Capacity_chain_derivation_v63.md`.
Development evidence remains in `results/capacity_chain_v63_20261011T163955_649834Z`
and `results/capacity_chain_v63_20261011T164215_633744Z`. First SLX archived;
prior baseline source/model/status/stageboard hashes preserved. No annual reruns.

Scope: normal-mode compiled component, constant REQUEST branch, conditional outward
binary64/span domain, host exact-tie trust boundary and protocol-clock phases.
All restart requests reject. Thermal restart/cutoff, other limiters, arbitrary
interval initial inventory and full six-mode integration remain OPEN. Stateflow
license/chart observed; version listing empty. Same-agent algorithmic review,
no independent personnel, new primary text, article replication, equipment
calibration or measured validation; full source signoffs remain 0/31.

Next actionable task: {next_task}
'''
    outputs=['STATUS_v63.json','STATUS_stateflow_v63.json','MASTER_STAGEBOARD_v63.md','MASTER_STAGEBOARD_stateflow_v63.md','audit/Capacity_chain_results_v63.md']
    for name in outputs:
        p=ROOT/name;assert not p.exists();p.write_text(json.dumps(status,indent=2)+'\n' if name.endswith('.json') else text)
    progress=f'''

## {stamp} — v63 actual capacity safety-OFF / passive / OFF-dwell component

Read latest STATUS/stageboards, acceptance, frontier, progress, v62/v57/v52 chart
code and v30 reference before changes. Work confined to this project; no Jarvice,
unrelated files, settings, scheduler, runner, secrets or publication touched.

Added versioned builder/kernel and generated DCHR_Capacity_Chain_Stateflow_v63.slx.
Derived capacity root and exact-expression handoff, froze active energy at safety
OFF, integrated passive loss and bounded elapsed OFF age. Implemented conservative
three-way dwell readiness; unsupported restarts reject. Fixed exact singleton
subtraction for unit efficiency; zero-loss passive identity preserved.

Tests: MATLAB {n}/0; 14 actual runs/{qa['protocol_ticks']} protocol ticks; 14 actual
fault rejections; 56 v30 reference comparisons; independent actual {q}/0 and eight
separate synthetic reviewer self-checks. Original reopened MAT/binary exports,
numeric CSV, timestamped MATLAB/reviewer logs, receipts and sealed snapshots:
`{relative}`. Prior source/model/status/stageboard hashes match.

Preserved development failures: sandbox startup; 157/2 first batch had two wrong
fault-message expectations (runtime guards rejected correctly). Repaired precise
fault expectations and bracket fixture; added unit-efficiency/zero-aux cases.
Second development batch 183/0 and independent 6382/0 retained. Final fresh batch
adds representative verified-v30 comparisons; saved v63 model is executed afresh.

Files added: matlab/simulink/build_charge_memory_v63.m, charge_memory_kernel_v63.m,
DCHR_Capacity_Chain_Stateflow_v63.slx; matlab/run_capacity_chain_v63.m;
audit/create/prepare/run/verify/finalize_capacity_chain_v63, derivation/results;
STATUS_v63/stateflow_v63 and MASTER_STAGEBOARD_v63/stateflow_v63. Shared ledgers append-only.

Limitations: component acceptance only; dispatch stays v57. No actual restart,
thermal cutoff/hysteresis or full six-mode coupled acceptance. Protocol time vs
physical root, conditional arithmetic, exact-host tie trust, same-agent review
and scalar-reference limitations explicit. Primary calibration/physical validation
OPEN; no research claims fabricated. See status for all bounds.

Next actionable task: {next_task}
Stop after this coherent component deliverable and handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    acceptance=f'''

## Scoped correlated capacity safety-OFF / passive / dwell — {stamp} / v63

Actual new saved capacity-chain component executes 14 runs/{qa['protocol_ticks']} protocol ticks;
MATLAB {n}/0, fourteen runtime fault rejections, 56 v30 comparisons, independent
{q}/0 and eight separate reviewer mutations. Symbolic capacity/root provenance,
frozen post-OFF active energies, passive first law and three-way OFF-dwell bounds
verified. All restart commands reject; thermal cutoff/restart/full six-mode
integration OPEN. Accepted full dispatch remains v57. STATUS_stateflow_v63 and
audit/Capacity_chain_results_v63.md authoritative. No calibrated physical acceptance.
'''
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:f.write(acceptance)
    artifact=folder/'closure_artifacts';artifact.mkdir()
    for p in [model,ROOT/'audit/Capacity_chain_derivation_v63.md',Path(__file__)]+[ROOT/p for p in outputs]:shutil.copy2(p,artifact/p.name)
    closure=dict(timestamp_utc=stamp,result=status['result'],qa_sha256=sha(qa_path),previous_hashes_verified=True,
        artifacts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in artifact.iterdir()])
    (folder/'closure.json').write_text(json.dumps(closure,indent=2)+'\n');print(json.dumps(dict(result=status['result'],matlab=n,independent=q,evidence=relative),indent=2))
if __name__=='__main__':main()
