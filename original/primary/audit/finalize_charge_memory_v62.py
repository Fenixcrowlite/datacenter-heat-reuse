from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qa_path=sorted(folder.glob('independent_QA_v62_*.json'))[-1]
    qa=json.loads(qa_path.read_text());assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(s['passed'] for s in qa['reviewer_selfchecks'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];assert any(r['exit_code']==0 for r in receipts)
    for record in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/record['path'])==record['sha256']
    for record in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/record['path'])==record['sha256']==sha(folder/'source_snapshot'/record['path'])
    model=ROOT/'matlab/simulink/DCHR_Charge_Memory_Stateflow_v62.slx';assert sha(model)==qa['model_sha256']
    artifact_folder=folder/'closure_artifacts';artifact_folder.mkdir()
    for path in [model,ROOT/'audit/Charge_memory_derivation_v62.md',Path(__file__)]:shutil.copy2(path,artifact_folder/path.name)
    artifact_manifest=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in artifact_folder.iterdir()]
    (folder/'closure_artifacts.json').write_text(json.dumps(artifact_manifest,indent=2)+'\n')
    stamp=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix()
    inherited=json.loads((ROOT/'STATUS_stateflow_v61.json').read_text())
    next_task=('Integrate v62 fixed-size trajectory/provenance and enclosure memory into a new additive six-mode dispatch model. '
        'Begin with capacity/cutoff event chains and uncertainty-aware HP dwell; reject unsupported regimes. '
        'Preserve v57 compiled finite-water guards and v52 endpoint protocol. Execute all six required cases, actual delayed '
        'faults, verified-reference comparisons and independent original-MAT/equation/port/clock QA. Preserve v52-v62; '
        'do not rerun unchanged annual matrices. Equipment calibration and measured physical validation remain OPEN.')
    limitations=[
        'Scoped constant-request increasing FLOOR-to-TANK charge-memory SLX; not the six-mode dispatch replacement. Accepted full dispatch remains 0.57.',
        'Solver ticks are protocol phases; physical event time is an enclosure. No solver-clock event firing or general event chain accepted.',
        'Exact manifold retained by original operands/expression schema; exact equivalent limiter set is host rational adapter certified. Compiled interval consistency is not an independent exact tie proof.',
        'Only scalar exact initial inventory and preserved ON latch supported. HP switching, uncertainty-aware dwell integration, other limiters and capacity termination remain OPEN.',
        'Conditional outward binary64 arithmetic, |lambda*t|<=1, strictly increasing capacity-domain trajectory, 128 source rectangles. Enclosures are not independent combinations or scalar service credit.',
        'Stateflow license, one actual chart and executed simulations observed; ver(Stateflow) listing remains empty. Normal-mode compiled chart, not standalone generated-code validation.',
        'Same-agent independent Fraction and 120/160-digit analytic QA; six synthetic reviewer mutations separate. No primary calibration, measured physical validation or article replication.',
        'Development sandbox startup, cache-directory and snapshot mismatch failures plus shadow warnings retained. Fresh final source-sealed run has no warnings and zero failures.'
    ]
    status=dict(version='0.62',timestamp_utc=stamp,inherits='STATUS_stateflow_v61.json',
        result='SCOPED_COMPILED_CORRELATED_CHARGE_MEMORY_PASS_SIX_MODE_COUPLED_INTEGRATION_OPEN',
        new_model=True,model_version='0.62_CHARGE_MEMORY_COMPONENT',saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),
        accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',accepted_dispatch_version='0.57',
        accepted_dispatch_sha256=inherited['model_sha256'],model_executed_this_run=True,coupled_stateflow_acceptance=False,
        compiled_correlated_charge_memory_acceptance='SCOPED_PASS',matlab_metadata=report['metadata'],
        matlab_passed=report['summary']['passed'],matlab_failed=0,actual_runs=len(report['runs']),protocol_ticks=qa['protocol_ticks'],
        actual_runtime_fault_rejections=len(report['faults']),nonrepresentable_manifold_runs=qa['nonrepresentable_runs'],
        independent_passed=qa['summary']['passed'],independent_failed=0,reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        six_mode_evidence_this_run='INHERITED_V57_V61_NOT_REEXECUTED_UNCHANGED',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        result_directory=relative,independent_qa=qa_path.relative_to(ROOT).as_posix(),derivation='audit/Charge_memory_derivation_v62.md',
        defect_status='COMPILED_CONSTANT_REQUEST_MEMORY_HANDOFF_RESOLVED_IN_SCOPED_FIXTURES_GENERAL_SIX_MODE_INTEGRATION_OPEN',
        next_actionable_task=next_task,limitations=limitations)
    for name in ['STATUS_v62.json','STATUS_stateflow_v62.json']:
        path=ROOT/name;assert not path.exists();path.write_text(json.dumps(status,indent=2)+'\n')
    text=f'''# Compiled correlated charge-memory checkpoint v62

UTC {stamp}. Actual new saved charge-memory component: **0.62**.
Accepted six-mode dispatch remains **0.57**. Continuously coupled six-mode
dispatch acceptance remains OPEN.

Compiled FLOOR / CORRELATED_CONTACT / TANK charge phases execute 24 runs / 120
protocol ticks, with three post-event continuations per run. Original manifold
operands, event bracket, exact host-certified equivalent mask and HP age are
retained without scalar event reset. Tank-linked inlet/source/water-port bounds
are computed within the actual saved chart. The original nonrepresentable
90071992547409925/18014398509481984 MWh fixture is included.

MATLAB 204 PASS / 0 FAIL; twelve actual saved-chart runtime fault rejections.
Independent original-MAT/binary/Fraction/120-/160-digit QA {qa['summary']['passed']}
PASS / 0 FAIL; six separate synthetic reviewer mutations detected. One chart
and Stateflow license observed; version listing remains empty. Final batch has
no shadow warnings. Prior model/source/data/status hashes preserved.

Evidence: `{relative}`. Derivation: `audit/Charge_memory_derivation_v62.md`.
Failed development evidence and the first development SLX remain in
`results/charge_memory_v62_20261011T163005_410247Z`.

Scope: constant-request upward branch, scalar exact initial inventory and
preserved ON latch. The host exact rational adapter certifies equivalent ties;
runtime interval overlap is not exact tie proof. Solver ticks are protocol phases,
not physical event times. General events/limiters, capacity termination,
uncertainty-aware dwell and full six-mode integration remain OPEN. No new primary
text, article replication, equipment calibration or measured physical validation;
inherited full signoffs 0/31. No unchanged annual or baseline matrix reruns.

Next actionable task: {next_task}
'''
    for name in ['MASTER_STAGEBOARD_v62.md','MASTER_STAGEBOARD_stateflow_v62.md','audit/Charge_memory_results_v62.md']:
        path=ROOT/name;assert not path.exists();path.write_text(text)
    progress=f'''

## {stamp} — v62 actual compiled correlated charge-memory execution

Read latest STATUS/stageboard, Stateflow acceptance, research frontier,
engineering progress, v61 exact-record equations/host code and v57/v60 builders
before changes. Work remained in this project; no Jarvice/unrelated files,
settings, scheduled tasks, runner or publication touched.

Added versioned builder and generated DCHR_Charge_Memory_Stateflow_v62.slx,
embedded fixed-size compiled trajectory/provenance/port/HP-age memory, actual
runtime harness and independent Fraction/120-/160-digit reviewer. Continuous
tank-linked source/water ports are integrated across the uncertain branch
window. Exact manifold operands retained; no scalar inventory snap, timer reset
or scalar service authorization. Three post-event horizons execute per run.

Pass/fail: MATLAB 204 PASS/0 FAIL, 24 actual runs/120 protocol ticks;
12 actual chart runtime rejections; independent {qa['summary']['passed']} PASS/0 FAIL,
six separate synthetic reviewer self-checks. Reopened original MAT, binary
exports, numerical CSV, timestamped MATLAB logs/receipts and sealed sources in
`{relative}`. Model and derivation closure snapshots saved. Previous hashes match.

Development evidence retained in results/charge_memory_v62_20261011T163005_410247Z:
sandbox startup failure, missing cache directory, shadow warnings and reviewer
snapshot mismatch. Corrected cache setup and chart names, archived development
SLX, then ran a fresh source-sealed batch and reviewer. No final warnings/failures.

Files: matlab/simulink/build_charge_memory_v62.m, charge_memory_kernel_v62.m,
DCHR_Charge_Memory_Stateflow_v62.slx; matlab/run_charge_memory_v62.m;
audit/prepare/run/verify/finalize_charge_memory_v62, Charge_memory_derivation/results;
STATUS_v62/stateflow_v62 and MASTER_STAGEBOARD_v62/stateflow_v62. Shared progress
and acceptance appended only; existing baseline models preserved.

Limitations: scoped charge-memory component, NOT full six-mode coupled plant.
Accepted dispatch remains v57. Host exact rational adapter is the tie-certificate
trust boundary; normal-mode compiled chart, conditional binary64/span domain,
protocol-clock phases and bounded port hulls explicit. Other limiters/event
chains/initial interval inventory/HP switch/dwell/capacity termination OPEN.
No equipment calibration or measured physical validation; no new primary text.

Next actionable task: {next_task}
Stop after this coherent compiled-memory deliverable and clear handoff.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    acceptance=f'''

## Scoped compiled correlated charge-memory checkpoint — {stamp} / v62

Actual new saved charge-memory component v62 executes 24 runs/120 protocol ticks
with FLOOR/CONTACT/TANK and persistent three-horizon continuation. MATLAB204/0,
12 actual runtime rejections, independent{qa['summary']['passed']}/0 and six separate
reviewer mutations. Exact expression operands/event bracket/port/HP-age bounds
are retained without scalar reset; tank-linked inlet/source/water-port integration
executes inside the compiled chart. Accepted six-mode dispatch stays v57;
coupled six-mode acceptance OPEN. Host exact tie-certificate boundary, protocol
clock, conditional arithmetic and general event/dwell/capacity limits explicit.
STATUS_stateflow_v62 and audit/Charge_memory_results_v62.md are authoritative.
No equipment calibration, article replication or measured validation claimed.
'''
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:f.write(acceptance)
    closure=dict(timestamp_utc=stamp,result=status['result'],model_sha256=status['model_sha256'],
        independent_qa=qa_path.name,qa_sha256=sha(qa_path),files=[dict(path=p,sha256=sha(ROOT/p)) for p in
        ['STATUS_v62.json','STATUS_stateflow_v62.json','MASTER_STAGEBOARD_v62.md','MASTER_STAGEBOARD_stateflow_v62.md','audit/Charge_memory_results_v62.md']],
        previous_hashes_verified=True,compiled_model_bound_to_kernel=True)
    (folder/'checkpoint_closure.json').write_text(json.dumps(closure,indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],MATLAB=report['summary'],independent_QA=qa['summary'],handoff='MASTER_STAGEBOARD_stateflow_v62.md'),indent=2))
if __name__=='__main__':main()
