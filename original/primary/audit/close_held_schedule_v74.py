"""Close the executed adapter checkpoint, append ledgers, seal final evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(v):return [v] if isinstance(v[0],(int,float)) else v
def new(p,txt):
    assert not p.exists(),p;p.write_text(txt,encoding='utf-8')
def main():
    folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
    report=json.loads((folder/'report.json').read_text());qpath=sorted(folder.glob('independent_QA_v74_*.json'))[-1];qa=json.loads(qpath.read_text())
    assert report['summary']['failed']==0 and qa['summary']['failed']==0 and all(v['passed'] for v in qa['reviewer_selfchecks'])
    assert all(sha(ROOT/r['path'])==r['sha256'] for r in json.loads((folder/'preservation.json').read_text()))
    assert all(r['model'] in ['v57','v66'] for r in report['references'])
    stamp=datetime.now(timezone.utc).isoformat();relative=folder.relative_to(ROOT).as_posix()
    models={v:'matlab/simulink/'+n+'.slx' for v,n in [('v73r2','DCHR_Earliest_Dispatch_Stateflow_v73r2'),('v66','DCHR_Interval_Dispatch_Stateflow_v66'),('v57','DCHR_Dispatch_Stateflow_v57')]}
    assert sha(ROOT/models['v73r2'])==json.loads((ROOT/'STATUS_v73.json').read_text())['model_sha256']
    counts=dict(probe_scenarios=len(report['probes']),complete_accepted_schedules=sum(v['accepted'] for v in report['probes']),
        accepted_runs_including_valid_prefixes=len(report['runs']),completed_held_intervals=sum(len(rows(v['trace'])) for v in report['runs']),
        positive_event_segments=int(sum(sum(row[12] for row in rows(v['trace'])) for v in report['runs'])),
        interior_events=int(sum(sum(row[13] for row in rows(v['trace'])) for v in report['runs'])),
        actual_runtime_rejections=sum(not v['accepted'] for v in report['probes']),actual_baseline_comparisons=len(report['references']))
    limitations=[
        'Synthetic 48-hour operating motifs and short controls only, not an annual weather/demand representation or measured validation. No new primary source signoff; 0/31 remain.',
        'Actual unchanged saved v73r2 executes normal-mode analytic event segments inside protocol calls, not solver-clock thermal event firing. No new SLX or generated-code acceptance.',
        'Binary held durations are authoritative; cumulative labels follow canonical binary64 cumsum and must lie in saved physical-clock hulls. General span/clock/order/dwell/segment refusals remain; no hidden retry or subdivision.',
        'v66 sampled policy and v57 fixed maximum-tank condenser/fixed return boundary are materially different. Seasonal delivered service and final inventories differ; no cost/efficiency ranking. v57 cannot represent independent enable commands or variable timesteps in this adapter.',
        'Same-agent algorithmic independence using exact-binary Fraction and 120/160-digit closed exp/log equations. MAT reopening/export is performed by MATLAB, not an independent HDF5 reader or independent personnel.',
        'Finite normal engineering arithmetic only; arbitrary-scale, subnormal and overflow acceptance remain untested. Integrated electricity/service is a boundary diagnostic, not calibrated total primary-energy efficiency.'
    ]
    next_task='Resume primary equipment-map evidence and boundary audit using audit/HP_upstream_boundary_results_v44.md: obtain and verify source20 upstream [62] primary text and performance-correlation supplement (DOI 10.1016/j.tsep.2025.103513), distinguish actual coefficients/domains from metadata, and document any access blocker. Trace refrigerant versus water axes, compressor/auxiliary power and admissible source/hot flow ranges before designing a separate calibrated backend. Preserve accepted v57/v66/v73r2 and v74 schedule evidence; do not interpret the synthetic comparison as calibrated or annual performance.'
    status=dict(version='0.74',timestamp_utc=stamp,inherits='STATUS_v73.json',result='BOUNDED_HELD_SCHEDULE_ADAPTER_ACCEPTED_QA_PASS',
        new_model=False,saved_model=models['v73r2'],saved_model_version='0.73r2',model_executed_this_run=True,
        corrected_model_accepted=False,inherited_model_acceptance_preserved=True,model_sha256=sha(ROOT/models['v73r2']),
        baseline_model_hashes={v:sha(ROOT/p) for v,p in models.items()},
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),required_actual_final_mode_coverage=report['mode_coverage'],**counts,
        matlab_metadata=report['metadata'],result_directory=relative,independent_qa=qpath.relative_to(ROOT).as_posix(),
        derivation='audit/Held_schedule_derivation_v74.md',results='audit/Held_schedule_results_v74.md',
        source_code=['matlab/+dchr/adapt_held_schedule_v74.m','matlab/+dchr/report_held_schedule_v74.m','matlab/run_held_schedule_v74.m'],
        primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        comparison_scope='12 saved-v66 schedules; 2 saved-v57 schedules, including equal delivered-service control',
        development_failures_preserved=['results/held_schedule_v74_20261012T075130_241955Z','results/held_schedule_v74_20261012T075425_611845Z',relative+'/'+sorted(folder.glob('independent_QA_v74_*.json'))[0].name],
        limitations=limitations,next_actionable_task=next_task)
    for name in ['STATUS_v74.json','STATUS_stateflow_v74.json']:new(ROOT/name,json.dumps(status,indent=2)+'\n')
    board=f'''# Executed held-boundary adapter checkpoint v74

UTC {stamp}. Unchanged saved v73r2 actually executes six final modes,
48-hour synthetic motifs at dt=.25/.5/1, variable holds and enable changes.
MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
seven reviewer corruptions detected. {counts['completed_held_intervals']} accepted/prefix intervals,
{counts['positive_event_segments']} positive segments, {counts['interior_events']} interior events,
six actual expected refusals and fourteen actual saved-model comparisons.
No new SLX: accepted v57/v66/v73r2 and all prior artifacts remain unchanged.
Evidence `{relative}`; audit/Held_schedule_results_v74.md.
Implementation QA only; annual/calibration/primary replication/measured validation
remain OPEN, full primary signoffs 0/31.

Next actionable task: {next_task}
'''
    for name in ['MASTER_STAGEBOARD_v74.md','MASTER_STAGEBOARD_stateflow_v74.md']:new(ROOT/name,board)
    agg={(a['id'],a['model']):a for a in qa['aggregates']}
    def fmt(id,model,key):return f"{float(agg[id,model][key]):.9f}"
    result=f'''# Executed held-boundary schedule and reporting v74

UTC {stamp}. The preserved actual `DCHR_Earliest_Dispatch_Stateflow_v73r2.slx`
was simulated, with saved v66 and v57 comparisons. No SLX was created or resaved.
New MATLAB APIs encode authoritative held durations, rounded cumulative labels,
immutable policy and persistent state; reporting retains energy/clock/inventory
hulls, refuses incomplete traces and excludes unmet heat from delivery.

MATLAB **{status['matlab_passed']} PASS / 0 FAIL**; independent original-MAT
closed-equation/report QA **{status['independent_passed']} PASS / 0 FAIL**.
Seven deliberate reviewer corruptions are detected, counted separately.
18 probes, 12 complete accepted schedules and two separately labelled valid
prefixes; {counts['completed_held_intervals']} held intervals / {counts['positive_event_segments']} positive segments /
{counts['interior_events']} interior events. All six final chart states execute. Six actual refusals
cover collision, root boundary, segment budget, early ON disable, span and clock.
Twelve actual v66 comparisons and two actual v57 comparisons completed.

The three 48-hour partitions share identical regime boundaries. Independently
integrated v73r2 energy and final-inventory totals agree within the declared
1e-85 closed-arithmetic comparison budget. This does not assert equal binary
uncertainty hulls or timestep invariance for the sampled v66 policy.

The dt=.5 synthetic schedule demands 63.5 MWh:

| Actual saved model | Delivered MWh | Unmet MWh | External electricity MWh | Final TES MWh |
|---|---:|---:|---:|---:|
| v73r2 earliest segments | {fmt('seasonal_0p5','v73r2','delivered_service')} | {fmt('seasonal_0p5','v73r2','unmet_demand')} | {fmt('seasonal_0p5','v73r2','external_electricity')} | {fmt('seasonal_0p5','v73r2','final_inventory')} |
| v66 sampled | {fmt('seasonal_0p5','v66','delivered_service')} | {fmt('seasonal_0p5','v66','unmet_demand')} | {fmt('seasonal_0p5','v66','external_electricity')} | {fmt('seasonal_0p5','v66','final_inventory')} |
| v57 fixed boundary | {fmt('seasonal_0p5','v57','delivered_service')} | {fmt('seasonal_0p5','v57','unmet_demand')} | {fmt('seasonal_0p5','v57','external_electricity')} | {fmt('seasonal_0p5','v57','final_inventory')} |

These are rounded diagnostics from independently checked synthetic trajectories.
Original MAT-derived reports retain the actual enclosures. Delivered service
and final inventories differ, so this table supports no cost/efficiency ranking.
The v57 boundary fixes condenser support at tank maximum and hot return at
ambient; it lacks the later thermal-stop policy. It is not a pure controller
comparison or calibrated plant result.

The separate charge/discharge-disabled control delivers exactly 5 MWh at
the independent comparison resolution, with no unmet energy in all three
models. External electricity is {fmt('equal_service_HP','v73r2','external_electricity')},
{fmt('equal_service_HP','v66','external_electricity')} and
{fmt('equal_service_HP','v57','external_electricity')} MWh respectively. Differences
still include the fixed-versus-dynamic v57 temperature boundary. v73r2/v66
allocate tiny binary rounding margins to backup; no assertion of exactly zero
backup is made. Final inventories accompany the machine-readable comparison.

Evidence `{relative}` contains timestamped batch/exit logs, original SimulationOutputs,
reopened report MAT, row-major binary64 exports, closed-equation numeric CSV,
initial and final reviewer snapshots, and prior preservation hashes. The actual
Stateflow license test returns 1 and sfroot observes the six-state chart;
`ver('stateflow')` returns empty and no installed-version inference is made.

Development failures are preserved. Restricted MATLAB startup failed before
execution; the first legacy adapter packed initial age into the low-order
clock residual and rejected both schedules. That was a harness defect, repaired
to [latch,age,0,0], not a demonstrated v57 model defect. An onCleanup capture
warning was also repaired. The first reviewer found two JSON column-vector
shape mismatches; row/column-aware binary binding repaired them without changing
model results or relaxing numeric acceptance. Legacy undefined COP diagnostics
remain NaN in binary and null in JSON; finite earliest traces forbid NaN.

Limitations:

'''+''.join('- '+v+'\n' for v in limitations)+f'\nNext actionable task: {next_task}\nStop after this coherent executed deliverable and clear handoff.\n'
    new(ROOT/'audit/Held_schedule_results_v74.md',result)
    ledgers=['automation/engineering_progress.md','automation/STATEFLOW_ACCEPTANCE.md','audit/research_frontier_2026_10_08.md'];prefixes=[]
    for name in ledgers:
        path=ROOT/name;before=path.read_bytes();prefixes.append(dict(path=name,bytes=len(before),sha256=hashlib.sha256(before).hexdigest()))
        if name=='automation/engineering_progress.md':
            entry=f'''\n\n## {stamp} — v74 executed held-boundary schedule/reporting adapter

Read latest STATUS/MASTER_STAGEBOARD, Stateflow acceptance, research frontier,
progress and relevant v73r2/v66/v57 code before changes. All work stayed in this
project; no Jarvice, unrelated files, settings, tasks, runner, secrets or external
publication touched. Added persistent held-input adapter, enclosure reporting,
actual saved-model harness and independent exact-binary closed-equation QA.

PASS/FAIL: MATLAB {status['matlab_passed']}/0; independent {status['independent_passed']}/0;
seven reviewer corruptions detected; six actual expected runtime refusals.
18 probes; {counts['completed_held_intervals']} accepted/prefix intervals, {counts['positive_event_segments']} positive segments,
{counts['interior_events']} interior events; six final modes and fourteen actual baseline comparisons.
48-hour partition totals agree; unequal-service seasonal comparisons earn no
efficiency ranking. The 5 MWh control provides equal-service boundary comparison.

Files added: matlab/+dchr/adapt_held_schedule_v74.m,
report_held_schedule_v74.m; matlab/run_held_schedule_v74.m; audit prepare/batch/
verify/reviewer-seal/close/release tools; Held_schedule_derivation/results_v74.md;
STATUS/stageboard twins v74. Accepted SLX and prior MATLAB code unchanged.
Shared ledgers appended byte-preservingly. Evidence `{relative}` includes
timestamped logs, original/reopened MAT, binary/CSV, snapshots and hashes.
Restricted startup, incorrect legacy timer packing/cleanup and reviewer JSON
column-shape failures remain retained; none is counted as acceptance.

Limitations: synthetic bounded schedules, finite macro event arithmetic,
same-agent algorithmic QA/MAT reopening; no annual, calibration, primary
replication, measured validation, independent personnel or generated-code claim.
Full primary signoffs remain 0/31.

Next actionable task: {next_task}
Stop after this coherent executed deliverable and clear handoff.
'''
        else:
            entry=f'\n\n## Held-boundary adapter acceptance — {stamp} / checkpoint v74\n\n'+board.split('\n\n',1)[1]
        with path.open('ab') as f:f.write(entry.encode('utf-8'))
    new(folder/'ledger_prefix_seals_v74.json',json.dumps(prefixes,indent=2)+'\n')
    final_sources=[]
    for base in ['matlab','audit']:
        for src in (ROOT/base).rglob('*v74*'):
            if not src.is_file() or '__pycache__' in src.parts:continue
            rel=src.relative_to(ROOT).as_posix();dst=folder/'final_source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);final_sources.append(dict(path=rel,sha256=sha(src)))
    new(folder/'final_source_hashes_v74.json',json.dumps(final_sources,indent=2)+'\n')
    evidence=[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in folder.rglob('*') if p.is_file() and not any(x in p.relative_to(folder).parts for x in ['cache','codegen'])]
    new(folder/'evidence_hashes_v74.json',json.dumps(evidence,indent=2)+'\n')
    release=dict(timestamp_utc=stamp,status_paths=['STATUS_v74.json','STATUS_stateflow_v74.json'],status_sha256=sha(ROOT/'STATUS_v74.json'),stageboard_sha256=sha(ROOT/'MASTER_STAGEBOARD_v74.md'),results_sha256=sha(ROOT/'audit/Held_schedule_results_v74.md'),
        evidence_manifest_sha256=sha(folder/'evidence_hashes_v74.json'),source_manifest_sha256=sha(folder/'final_source_hashes_v74.json'),ledger_prefix_manifest_sha256=sha(folder/'ledger_prefix_seals_v74.json'))
    new(folder/'release_seal_v74.json',json.dumps(release,indent=2)+'\n')
    log=dict(version='0.74',timestamp_utc=stamp,matlab=report['summary'],independent=qa['summary'],counts=counts,checkpoint='STATUS_v74.json');new(folder/'checkpoint_close_v74.log',json.dumps(log,indent=2)+'\n');print(json.dumps(log))
if __name__=='__main__':main()
