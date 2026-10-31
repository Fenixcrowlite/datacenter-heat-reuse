"""Seal executed scoped v73r2 acceptance and byte-preserving handoff."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v):return [v] if isinstance(v[0],(int,float)) else v

def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    assert not (ROOT/'STATUS_v73.json').exists() and not (folder/'closure.json').exists()
    rel=folder.relative_to(ROOT).as_posix();report=json.loads((folder/'report.json').read_text())
    qapath=sorted(folder.glob('independent_QA_v73_*.json'))[-1];qa=json.loads(qapath.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(v['passed'] for v in qa['reviewer_selfchecks'])
    for manifest in ['preservation.json','source_hashes.json','reviewer_sources.json']:
        for r in json.loads((folder/manifest).read_text()):assert sha(ROOT/r['path'])==r['sha256'],r['path']
    ticks=segments=events=references=0;finalmodes=set();symbolic=0
    for r in report['runs']:
        tr=rows(r['trace']);ticks+=len(tr);segments+=sum(int(v[12]) for v in tr);events+=sum(int(v[13]) for v in tr)
        finalmodes.update(int(v[0]) for v in tr);references+=len(r['reference_v30']);symbolic+=sum(v[71]==1 for v in tr)
    assert finalmodes==set(range(6));assert symbolic>0
    model=ROOT/'matlab/simulink/DCHR_Earliest_Dispatch_Stateflow_v73r2.slx';assert sha(model)==qa['model_sha256']
    rejected=[p for p in report['probes'] if not p['accepted']]
    now=datetime.now(timezone.utc).isoformat()
    nexttask='Develop an additive held-boundary input/reporting adapter for the saved v73r2 earliest-event model. Begin with a bounded representative seasonal schedule and source/demand/enable changes, preserve held physical timestamps and uncertainty hulls, explicitly surface collision/span/segment/clock refusals, and independently audit service/source/work/TES/backup/unmet aggregation from original MAT. Compare identical schedules with verified v57/v66 and equal delivered-service reporting before any full annual claim. Primary calibration, article replication and measured validation remain OPEN.'
    limits=[
        'Scoped synthetic normal-mode implementation acceptance only; analytic event segments execute inside macro Stateflow protocol calls, not at solver-clock thermal events. No generated-code acceptance.',
        'Public lambda*heldDt<=1 and sixteen-segment limits remain. Generic unresolved boundary/root/dwell/collision decisions still reject. Symbolic passive contact applies only to retained STOP, B=0, lambda>0 and the declared log1p domain.',
        'Compensated ON-age certificate is optional and invalidated by uncertain event segments. Source limiting is conservative with eight ulps of allocation room. Arbitrary-scale, subnormal, overflow and arbitrary-policy acceptance are untested.',
        'Same-agent algorithmic independence using exact binary Fraction and 120/160-digit closed exp/log/source equations, not independent personnel. Original MAT reopening/export uses MATLAB; no independent HDF5 reader.',
        'Original v72 numerical witnesses repaired in the executed scope. This does not establish equipment calibration, measured performance, primary article replication or a full annual earliest-event simulation. Full primary signoffs remain 0/31.'
    ]
    status=dict(version='0.73',model_revision='r2',timestamp_utc=now,inherits='STATUS_v72.json',result='SCOPED_NUMERICAL_REPAIRS_AND_SYMBOLIC_PASSIVE_CONTACT_ACCEPTED_QA_PASS',
        new_model=True,saved_model=model.relative_to(ROOT).as_posix(),saved_model_version='0.73r2',model_sha256=sha(model),model_executed_this_run=True,corrected_model_accepted=True,
        accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',accepted_scoped_earliest_event_model=model.relative_to(ROOT).as_posix(),
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,actual_probe_scenarios=len(report['probes']),
        accepted_probe_scenarios=len(report['probes'])-len(rejected),accepted_runs_including_valid_prefixes=len(report['runs']),completed_held_intervals=ticks,positive_event_segments=segments,interior_events=events,
        required_actual_final_mode_coverage=sorted(finalmodes),actual_runtime_rejections=len(rejected),v30_reference_comparisons=references,reviewer_selfchecks=len(qa['reviewer_selfchecks']),symbolic_passive_contact_macro_calls=symbolic,
        repaired_prior_defect_classes=['PASSIVE_INTERVAL_WRAPPING','INCLUSIVE_ON_DWELL_EQUALITY','SOURCE_LIMIT_PROOF_DEPENDENCY','CORRELATED_WORK_NONNEGATIVITY'],findings=qa['findings'],
        matlab_metadata=report['metadata'],result_directory=rel,independent_qa=qapath.relative_to(ROOT).as_posix(),derivation='audit/Earliest_dispatch_derivation_v73.md',results='audit/Earliest_dispatch_results_v73.md',
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,limitations=limits,next_actionable_task=nexttask)
    result=f'''# Executed numerical-admissibility repair v73r2

UTC {now}. Saved `{status['saved_model']}` was built and actually simulated.
All six final chart modes execute. The original v72 passive, inclusive ON-dwell,
source-limiter and correlated-work witnesses pass in this tested scope.

MATLAB **{status['matlab_passed']} PASS / 0 FAIL**; independent original-MAT
closed-form QA **{status['independent_passed']} PASS / 0 FAIL**;
{len(qa['reviewer_selfchecks'])} separately counted reviewer corruptions detected.
{len(report['probes'])} probes, {len(report['runs'])} saved accepted/prefix runs,
{ticks} completed held intervals, {segments} positive segments,
{events} interior events, {references} exact-singleton v30 comparisons.
{len(rejected)} actual runtime refusals are the expected domain/early-disable/
collision/boundary/resource controls, rather than acceptance failures.

The positive passive product and monotone affine corners repair the 91/23-hour
wrapping witnesses. Full 256-hour lambda=.2/h, 80-hour lambda=1/h and 256-hour
lambda=.01/h controls execute. The 208-hour repeated schedule executes.
Exact .25h and compensated .5h ON-dwell equality accept; true early disable,
including a displayed-but-inexact 1h binary sum, rejects. Source-limited,
rounded water/source tie, below/above tie and finite-water controls pass.
The 2^-42 K band executes with positive independently checked compressor work.
Matched dt=.25/.5/1 schedules retain independently equal physical trajectories.

The first saved v73 model is preserved. Its initial suite yielded 2759 passing
checks and one acceptance failure: after repairing positive work, the narrow
band next refused an unresolved passive root boundary. Additive v73r2 retains
the exact STOP-to-RESTART manifold and cancels the common heat capacity in
the log1p root equation. It records {symbolic} macro calls using that symbolic
certificate. No root midpoint, capacity relaxation or energy tolerance was used.

Evidence `{rel}` contains timestamped MATLAB logs/exit receipts, diagnostics,
original/reopened MAT, little-endian binary exports, numeric closed trajectories,
source/model snapshots and prior preservation hashes. Independent numeric CSV:
`{qa['numeric_csv']}`. Derivation: `audit/Earliest_dispatch_derivation_v73.md`.
All fixture values are synthetic model units, not measured or paper data.

Development evidence is retained in the earlier v73 folders, including the
pre-existing startup/JSON-shape failures, this session's restricted MATLAB
startup refusal and first generated-v73 failed acceptance suite. An unexecuted
alternative scaffold refused to overwrite the existing v73 builder and was
archived under `results/v73_alternative_draft_*`; it is not production evidence.
No failed run is counted as acceptance.

Limitations:

'''+''.join('- '+v+'\n' for v in limits)+f'\nNext actionable task: {nexttask}\nStop after this coherent executed deliverable and handoff.\n'
    (ROOT/status['results']).write_text(result)
    for name in ['STATUS_v73.json','STATUS_stateflow_v73.json']:(ROOT/name).write_text(json.dumps(status,indent=2)+'\n')
    stage=f'''# Scoped saved-v73r2 numerical repair acceptance

UTC {now}. Actual saved v73r2 executes all six modes and original v72 numerical
witnesses. MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
{len(qa['reviewer_selfchecks'])} reviewer mutations; {len(rejected)} expected runtime refusals.
{ticks} held intervals / {segments} positive segments / {events} interior events.
First generated v73 and all v57-v72 baselines/evidence remain preserved.
Authoritative evidence `{rel}` and audit/Earliest_dispatch_results_v73.md.
Scoped macro analytic implementation only; annual/equipment calibration/
article replication/measured validation remain OPEN; primary signoffs 0/31.

Next actionable task: {nexttask}
'''
    for name in ['MASTER_STAGEBOARD_v73.md','MASTER_STAGEBOARD_stateflow_v73.md']:(ROOT/name).write_text(stage)
    progress=f'''

## {now} — v73r2 executed numerical-admissibility repairs

Read STATUS/stageboards, Stateflow acceptance, frontier, progress and
v71/v72 code before changes. Discovered and completed the pre-existing
unfinished v73 builder/kernel/flow/harness draft. All work stayed in this
project; no Jarvice, unrelated files, user settings, tasks, runner, secrets
or external publication touched.

Built and simulated additive v73, retained its one failed narrow-band
acceptance, then built additive v73r2 with symbolic passive-contact and exact
residual-cancellation identities. The four original numerical refusal classes
are repaired in the tested scope. Actual six modes, long passive/repeated
service, source/water ties, tiny band, compensated inclusive equality and true
early/collision/resource controls execute. Independent Fraction/120/160-digit
closed-form QA checks every saved accepted/prefix trajectory and all energies;
no production polynomial, bisection or function is called by the reviewer.

PASS/FAIL: final MATLAB {status['matlab_passed']}/0, independent {status['independent_passed']}/0;
{len(qa['reviewer_selfchecks'])} reviewer corruptions detected; {len(report['probes'])} probes,
{ticks} held intervals, {segments} positive segments, {events} events,
{len(rejected)} expected runtime refusals, {references} v30 comparisons.
Evidence `{rel}` has timestamped logs/receipts, original/reopened MAT/binary/CSV,
saved model/source seals and unchanged prior preservation hashes. Initial
restricted startup and v73 failure logs remain retained.

Files changed/added: completed matlab/run_earliest_admissibility_v73.m;
added matlab/simulink/earliest_dispatch_kernel_v73r2.m,
passive_contact_root_v73r2.m, build_earliest_dispatch_v73r2.m,
actual DCHR_Earliest_Dispatch_Stateflow_v73.slx and v73r2.slx;
matlab/run_earliest_admissibility_v73r2.m; audit r2 prepare/runner,
independent closed-form/reviewer/scaffolds/closure/release scripts and
Earliest_dispatch_derivation/results_v73.md; STATUS/stageboard twins v73.
Shared ledgers appended byte-preservingly only. Unexecuted alternative drafts
were archived after the scaffold refused to overwrite the existing builder.

Limitations: synthetic conditional normal-mode macro analytic implementation;
finite span/segment/log-series domains; optional compensated age proof;
same-agent algorithmic QA, MATLAB MAT reopening. Annual adapter, calibration,
article replication, measured validation and independent personnel QA remain
OPEN. Full primary signoffs remain 0/31.

Next actionable task: {nexttask}
Stop after this coherent executed deliverable and clear handoff.
'''
    acceptance=f'''

## Numerical-admissibility repair acceptance — {now} / saved v73r2

Actual additive saved v73r2 executes all six chart modes and repairs original
v72 passive/dwell/source/work witnesses in tested scope. MATLAB
{status['matlab_passed']}/0, independent {status['independent_passed']}/0;
{ticks} held intervals/{segments} segments/{events} interior events;
{len(rejected)} expected runtime refusals and {len(qa['reviewer_selfchecks'])} reviewer mutations.
Symbolic passive contact, compensated inclusive age and limiter/work proofs
verified. First v73 failed narrow-band model and v57-v72 preserved.
STATUS/stageboards v73 and audit/Earliest_dispatch_results_v73.md authoritative.
Scoped macro analytic implementation only; no annual/calibration/primary
replication/measured validation acceptance. Next: held-boundary adapter.
'''
    frontier=f'\n\n## {now} — v73r2 numerical repair handoff\n\nActual model and original-MAT closed-form QA repair the scoped v72 witnesses. No new primary text/signoff or physical calibration.\n\nNext actionable task: {nexttask}\n'
    for name,text in [('automation/engineering_progress.md',progress),('automation/STATEFLOW_ACCEPTANCE.md',acceptance),('audit/research_frontier_2026_10_08.md',frontier)]:
        with (ROOT/name).open('ab') as f:f.write(text.encode('utf-8'))
    closefiles=[Path(__file__),ROOT/'audit/verify_earliest_release_v73.py',ROOT/status['derivation']];closeseals=[]
    for p in closefiles:
        relative=p.relative_to(ROOT);dst=folder/'closure_source_snapshot'/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
        closeseals.append(dict(path=relative.as_posix(),sha256=sha(p)))
    (folder/'closure_source_hashes.json').write_text(json.dumps(closeseals,indent=2)+'\n')
    evidence=[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in folder.rglob('*') if p.is_file() and not any(v in ['cache','codegen'] for v in p.relative_to(folder).parts)]
    checkpoint=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in [ROOT/'STATUS_v73.json',ROOT/'STATUS_stateflow_v73.json',ROOT/'MASTER_STAGEBOARD_v73.md',ROOT/'MASTER_STAGEBOARD_stateflow_v73.md',ROOT/status['results'],model]]
    (folder/'closure.json').write_text(json.dumps(dict(timestamp_utc=now,result=status['result'],evidence_hashes=evidence,checkpoint_hashes=checkpoint),indent=2)+'\n')
    print(json.dumps(dict(result=status['result'],evidence=rel,MATLAB=report['summary'],independent=qa['summary'],ticks=ticks,segments=segments,events=events,rejections=len(rejected))))

if __name__=='__main__':main()
