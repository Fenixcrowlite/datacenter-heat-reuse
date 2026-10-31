from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    folder=(ROOT/sys.argv[1]).resolve();reg=(ROOT/sys.argv[2]).resolve()
    assert folder.is_relative_to(ROOT/'results') and reg.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qa_path=sorted(folder.glob('independent_QA_v64_*.json'))[-1];qa=json.loads(qa_path.read_text())
    regreport=json.loads((reg/'report.json').read_text());regqa_path=sorted(reg.glob('independent_QA_v57_*.json'))[-1];regqa=json.loads(regqa_path.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==regreport['summary']['failed']==regqa['summary']['failed']==0
    assert all(x['passed'] for x in qa['reviewer_selfchecks']+regqa['reviewer_selfchecks'])
    for rec in json.loads((folder/'preservation.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']
    for rec in json.loads((folder/'source_hashes.json').read_text()):assert sha(ROOT/rec['path'])==rec['sha256']==sha(folder/'source_snapshot'/rec['path'])
    receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')];assert any(r['exit_code']==0 for r in receipts)
    model=ROOT/'matlab/simulink/DCHR_Restart_Chain_Stateflow_v64.slx';assert sha(model)==qa['model_sha256']
    prior=json.loads((ROOT/'STATUS_stateflow_v63.json').read_text());assert sha(ROOT/prior['accepted_dispatch_model'])==prior['accepted_dispatch_sha256']==regqa['model_sha256']
    # The v57 reviewer ran against its complete sealed manifest before v64
    # harness fixture repair. Recheck every actual v57 dependency now; unrelated
    # v64 scaffold edits cannot change the immutable saved v57 execution.
    for rec in json.loads((reg/'source_hashes.json').read_text()):
        assert sha(reg/'source_snapshot'/rec['path'])==rec['sha256']
        if 'v64' not in Path(rec['path']).name:assert sha(ROOT/rec['path'])==rec['sha256']
    stamp=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix();regrel=reg.relative_to(ROOT).as_posix()
    next_task=('Integrate v64 retained restart trajectory and port/clock memory into an additive six-mode dispatch model. '
        'Resolve the specific interface blocker: v52/v57 allocation requires one scalar canonical inventory; v64 carries a correlated inventory hull and has no scalar service authority. '
        'Derive conservative demand/discharge/backup allocation and interval-capacity termination without midpoint resets; preserve finite-water guards and explicit endpoint protocol. '
        'Execute six modes in that SAME new coupled model, delayed faults and independent original-MAT equation/port/clock QA. '
        'Preserve v52-v64; equipment calibration and measured physical validation remain OPEN.')
    limits=['Scoped normal-mode restart component; full six-mode coupled replacement OPEN; accepted dispatch remains v57.',
        'Restart occurs at a certified sampled physical horizon, not an earliest-event thermal root or solver-clock physical event.',
        'One capacity OFF and one restart; resumed tank branch and constant request only. Further capacity/branch crossings reject.',
        'Inventory and cumulative port/loss hulls preserve the exact original trajectory but cannot authorize scalar delivered service.',
        'Inherited host exact equivalent-limiter certificate trust boundary; outward binary64 arithmetic and |lambda*span|<=1.',
        'Positive passive-loss restart fixtures only; zero loss cannot cool below a strict lower restart threshold.',
        'Stateflow license and actual saved chart observed; ver(stateflow) empty; no standalone generated-code acceptance.',
        'Same-agent independent Fraction/120-/160-digit algorithms; synthetic fixtures only, no independent personnel, article replication, calibration or measured validation.',
        'Inherited v57 shadow warnings retained; historical v57 report new_model flag is not evidence of a new v57 model in this run.',
        'Sandbox startup, builder loop failure and one fault-fixture expectation failure retained; repaired fixture did not require a model/kernel change.']
    status=dict(version='0.64',timestamp_utc=stamp,inherits='STATUS_stateflow_v63.json',
        result='SCOPED_ACTUAL_INTERVAL_RESTART_PASS_FULL_COUPLED_DISPATCH_BLOCKED_BY_SCALAR_SERVICE_INTERFACE',
        new_model=True,saved_model=model.relative_to(ROOT).as_posix(),model_sha256=sha(model),model_executed_this_run=True,
        accepted_dispatch_model=prior['accepted_dispatch_model'],accepted_dispatch_version='0.57',accepted_dispatch_sha256=prior['accepted_dispatch_sha256'],
        coupled_stateflow_acceptance=False,actual_restart_component_acceptance='SCOPED_PASS',matlab_metadata=report['metadata'],
        matlab_passed=report['summary']['passed'],matlab_failed=0,actual_runs=qa['runs'],protocol_ticks=qa['protocol_ticks'],
        actual_runtime_fault_rejections=len(report['faults']),v30_reference_comparisons=sum(len(x['references_v30']) for x in report['runs']),
        independent_passed=qa['summary']['passed'],independent_failed=0,reviewer_selfchecks=len(qa['reviewer_selfchecks']),
        six_mode_regression=dict(saved_model_version='0.57',new_model_this_run=False,evidence=regrel,
            matlab_summary=regreport['summary'],independent_summary=regqa['summary'],counts=regqa['counts'],
            runtime_fault_rejections=len(regreport['faults']),references=len(regreport['references']),qa=regqa_path.relative_to(ROOT).as_posix()),
        result_directory=rel,independent_qa=qa_path.relative_to(ROOT).as_posix(),derivation='audit/Restart_chain_derivation_v64.md',
        full_primary_signoffs=0,total_sources=31,primary_article_replication=False,independent_physical_validation='NOT_TESTED',
        next_actionable_task=next_task,limitations=limits)
    text=f'''# Executed retained interval restart checkpoint v64

UTC {stamp}. New saved component v64; accepted six-mode dispatch remains v57.
The v64 chart executes capacity safety OFF, passive cooling, certified thermal
and OFF-dwell restart, then three resumed charging horizons. No scalar event
root/inventory reset: retained inventory bounds and cumulative port offsets
continue through the restart. Restart ON age begins at the known sampled horizon.

MATLAB {status['matlab_passed']} PASS / 0 FAIL; {qa['runs']} actual runs /
{qa['protocol_ticks']} protocol ticks; fourteen specific runtime rejections;
{status['v30_reference_comparisons']} v30 scalar storage comparisons.
Independent exact-binary/Fraction/120-/160-digit QA {qa['summary']['passed']} PASS /
0 FAIL; eight separate synthetic reviewer mutations detected. Original reopened
MAT, row-major binary exports, numeric CSV, batch logs/receipts and sealed sources:
`{rel}`. Saved embedded kernel is bound to source; prior hashes verified.

Separate preserved-v57 regression `{regrel}` executes all six required modes,
{regqa['counts']['intervals']} intervals; MATLAB {regreport['summary']['passed']}/0,
independent {regqa['summary']['passed']}/0, twelve actual runtime faults,
including a two-sample delayed valid prefix, and six verified-v30 comparisons.
This is regression of v57, not six-mode acceptance of v64. Existing name-shadow
warnings and the historical report flag are disclosed; saved v57 hash unchanged.

Specific coupled-model blocker: the v52/v57 allocation API consumes a scalar
canonical inventory and performs bounded endpoint normalization. v64 retains
an interval inventory with original trajectory provenance and no scalar service
authorization. Selecting a midpoint would lose that guarantee. Conservative
served-demand/discharge/backup allocation and further capacity termination must
be implemented before the restart component can become a six-mode replacement.

Development startup, builder loop and fault-fixture failures are preserved in
`results/restart_chain_v64_20261011T165015_277711Z` and
`results/restart_chain_v64_20261011T165141_875940Z`. The last failure was the
test horizon preceding the deliberately colder passive horizon; corrected the
test sequence, not the physical kernel. Independent equations already passed.

Limitations:
'''+''.join(f'- {x}\n' for x in limits)+f'\nNext actionable task: {next_task}\n'
    outputs=['STATUS_v64.json','STATUS_stateflow_v64.json','MASTER_STAGEBOARD_v64.md','MASTER_STAGEBOARD_stateflow_v64.md','audit/Restart_chain_results_v64.md']
    for name in outputs:
        p=ROOT/name;assert not p.exists();p.write_text(json.dumps(status,indent=2)+'\n' if name.endswith('.json') else text)
    progress=f'''

## {stamp} — v64 actual certified interval restart and six-mode regression

Read STATUS/stageboards, Stateflow acceptance, frontier, progress and v63/v57/v52
code before changes. All work confined to this project; no Jarvice, settings,
scheduler, runner, unrelated files, secrets or external publication touched.

Added versioned builder/kernel and DCHR_Restart_Chain_Stateflow_v64.slx.
Derived conservative thermal and OFF-age guards; executed actual OFF-to-ON
transition and resumed tank-linked source/water integration from the full
retained inventory hull. Cumulative heat/source/compressor/auxiliary/loss offsets
persist; no scalar capacity root or restart-inventory reset. Independent QA
evaluates the exact correlated original trajectory, not an interval midpoint.

PASS/FAIL: v64 MATLAB {status['matlab_passed']}/0, {qa['runs']} runs/
{qa['protocol_ticks']} ticks, fourteen actual faults, 28 v30 references,
independent {qa['summary']['passed']}/0 and eight separate reviewer mutations.
Saved v57 afresh: six modes/{regqa['counts']['intervals']} intervals,
MATLAB {regreport['summary']['passed']}/0, independent {regqa['summary']['passed']}/0,
twelve runtime faults, two-sample delayed prefix and six v30 references.
Timestamped logs, reopened original MAT/binary/numeric traces, sealed sources and
receipts: `{rel}` and `{regrel}`. Prior baseline hashes unchanged.

Development sandbox startup and builder loop failure retained; repaired builder.
First actual suite 161/1: one colder restart fixture had reversed later horizons,
so a horizon guard fired before its intended floor guard. Corrected fixture,
fresh sealed batch against the same saved model. Development independent analytic
checks passed; failure classification/receipt checks correctly failed. Inherited
v57 name-shadow warnings retained. No unchanged annual matrices executed.

Files added: matlab/simulink/build_restart_chain_v64.m, restart_chain_kernel_v64.m,
DCHR_Restart_Chain_Stateflow_v64.slx; matlab/run_restart_chain_v64.m;
audit/create/prepare/run/verify/finalize_restart_chain_v64 and derivation/results;
STATUS_v64/stateflow_v64, MASTER_STAGEBOARD_v64/stateflow_v64, immutable evidence.
Shared progress/acceptance appended only.

Full coupled dispatch remains blocked by the concrete scalar-service API mismatch,
not accepted by combining evidence from separate models. Sampled restart policy,
one cycle/constant request/tank branch/span limits, same-agent algorithmic QA,
open primary calibration and physical validation remain explicit. No new primary
article text verified; full source signoffs remain 0/31.

Next actionable task: {next_task}
Stop after this coherent executable deliverable and documented integration blocker.
'''
    with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
    with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
        f.write(f'\n\n## Scoped actual retained restart component — {stamp} / v64\n\n'
            f'Saved new v64 chart executes {qa["runs"]} runs/{qa["protocol_ticks"]} ticks; MATLAB '
            f'{status["matlab_passed"]}/0, fourteen actual faults, 28 v30 references, independent '
            f'{qa["summary"]["passed"]}/0 and eight reviewer mutations. Thermal/OFF dwell guards, '
            'actual restart latch, retained inventory/ports and resumed continuous tank-linked '
            'equations verified. Separate saved-v57 six-mode/fault/reference regression passes. '
            'Full coupled six-mode acceptance OPEN: scalar allocation/service interface must '
            'be replaced. STATUS_stateflow_v64 and audit/Restart_chain_results_v64.md authoritative. '
            'No physical validation or article replication.\n')
    closure=folder/'closure_artifacts';closure.mkdir()
    for p in [model,ROOT/'audit/Restart_chain_derivation_v64.md']+[ROOT/n for n in outputs]:shutil.copy2(p,closure/p.name)
    (folder/'closure.json').write_text(json.dumps(dict(timestamp_utc=stamp,result=status['result'],
        qa_sha256=sha(qa_path),regression_qa_sha256=sha(regqa_path),previous_hashes_verified=True,
        artifacts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in closure.iterdir()]),indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],evidence=rel),indent=2))
if __name__=='__main__':main()
