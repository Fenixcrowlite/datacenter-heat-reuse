"""Release scoped executed observer evidence; do not accept event switching."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
qpath=max(folder.glob('independent_QA_v67_*.json'),key=lambda p:p.name)
q=json.loads(qpath.read_text());r=json.loads((folder/'report.json').read_text())
assert q['summary']['failed']==r['summary']['failed']==0
assert all(v['passed'] for v in q['reviewer_selfchecks'])
receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
assert any(v['exit_code']==0 for v in receipts)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['preservation.json','source_hashes.json']:
    for v in json.loads((folder/name).read_text()):assert sha(ROOT/v['path'])==v['sha256']
certifier=(ROOT/'matlab/simulink/certify_event_root_v67.m').read_text()
observer=(ROOT/'matlab/simulink/event_observer_v67.m').read_text()
assert observer.endswith(certifier),'Embedded/host root certifiers differ'
now=datetime.now(timezone.utc).isoformat();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
rel=folder.relative_to(ROOT).as_posix();mdl=ROOT/'matlab/simulink/DCHR_Event_Brackets_Stateflow_v67r2.slx'
ticks=sum(len(v['input']) if isinstance(v['input'][0],list) else 1 for v in r['runs'])
refs=sum(len(v['references_v30']) for v in r['runs'])
limitations=[
    'Executed root observer only. Sampled plant schema 66 and policy remain embedded unchanged; roots do not control service or reset inventory.',
    'Coupled repeated earliest-event switching OPEN: brackets alone cannot provide scalar service authority. Symbolic threshold, event-time, inventory, port and OFF-age dependencies must persist across both segments.',
    'Strict unresolved-order guards are demonstrated in near-boundary and delayed fixtures. Inactive or no-crossing lanes do not establish general event-policy acceptance.',
    'Root solver requires a certified strict derivative sign and lambda*horizon<=1. Unsupported monotonicity rejects; no standalone generated-code/subnormal rounding guarantee accepted.',
    'Candidate lanes are alternative potential full held-power paths, not simultaneous executed ports or an optimized control policy. Earliest-event source/compressor comparison remains open.',
    'Exact root at held boundary is a standalone function probe; actual compiled near-boundary candidate uses conservative water-limited forcing and has a small binary gap. No exact compiled tie is fabricated.',
    'Same-agent independent Fraction/160-digit all-corner closed exp/log QA; not independent personnel or measured physical validation.',
    'Inherited v66 finite-water/correlated prefix/endpoint/policy limits remain. Fixed thermal approaches and cooling-factor boundary are engineering assumptions.',
    'No new primary article text, calibrated equipment, article replication or physical validation. Full source signoffs remain 0/31.',
    'Development model v67 preserved separately. First batch 1368 pass / 3 wrong expected-mode labels fail; initial sandbox startup and shadow warnings retained. Revised saved model is v67r2.'
]
nexttask='Integrate one certified repeated earliest-event cycle into an additive SAME six-mode chart using the v67 strict root witnesses. Carry threshold identity plus correlated root-time, inventory, source/work/loss/service offsets and OFF-age across event segments; never substitute a midpoint. Certify OFF dwell and ordering against held demand/source boundaries; reject unresolved collisions. Compare actual original-MAT service and source/work enclosures with an independent event trajectory. Preserve v57-v67r2, and regress the near-boundary/delayed witnesses plus dt=0.25/0.5/1 repeated schedules. Primary calibration and measured validation remain OPEN.'
status=dict(version='0.67',timestamp_utc=now,inherits='STATUS_v66.json',
    result='EXECUTED_SIX_MODE_ROOT_OBSERVER_PASS_EARLIEST_SWITCHING_OPEN',new_model=True,
    saved_model=mdl.relative_to(ROOT).as_posix(),model_sha256=sha(mdl),model_executed_this_run=True,
    accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',
    accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',
    accepted_root_observer_model=mdl.relative_to(ROOT).as_posix(),embedded_dispatch_schema=66,
    event_root_observer_acceptance=True,coupled_stateflow_acceptance=False,general_repeated_earliest_event_stateflow='OPEN',
    matlab_passed=r['summary']['passed'],matlab_failed=0,independent_passed=q['summary']['passed'],independent_failed=0,
    actual_runs=len(r['runs']),protocol_ticks=ticks,required_mode_coverage=r['mode_coverage'],
    actual_runtime_fault_rejections=len(r['faults']),v30_reference_comparisons=refs,
    active_compiled_certificates=q['active_certificates'],root_probes=q['root_probes'],
    root_status_counts=q['root_status_counts'],ordering_counts=q['ordering_counts'],reviewer_selfchecks=len(q['reviewer_selfchecks']),
    matlab_metadata=r['metadata'],result_directory=rel,independent_qa=qpath.relative_to(ROOT).as_posix(),
    derivation='audit/Event_bracket_derivation_v67.md',results='audit/Event_bracket_results_v67.md',
    primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
    limitations=limitations,next_actionable_task=nexttask)
def new(path,value):
    with path.open('x',encoding='utf-8') as f:f.write(value)
for name in ['STATUS_v67.json','STATUS_stateflow_v67.json']:new(ROOT/name,json.dumps(status,indent=2)+'\n')
summary=f"""# Executed held-trajectory event bracket observer v67

UTC {now}. Saved `DCHR_Event_Brackets_Stateflow_v67r2.slx` executes the inherited
sampled dispatch and new root observer in one actual six-mode Stateflow chart.
All six states run. Plant memory schema remains 66; the observer appends root
and forcing certificates. Root observations do not switch the plant at events.

MATLAB **{r['summary']['passed']} PASS / 0 FAIL**; independent **{q['summary']['passed']}
PASS / 0 FAIL**. {len(r['runs'])} actual runs / {ticks} protocol ticks;
{len(r['faults'])} actual runtime rejections; {refs} executed v30 comparisons;
{q['active_certificates']} active compiled root observations; {q['root_probes']}
separate function probes; six reviewer corruptions detected.

Root observation counts: strict interior 61, no crossing in horizon 436,
unresolved near-boundary 2, already reached 46. Readiness ordering counts:
strictly before 106, no event 436, unresolved 2, strictly after 1.
These are observations along sampled trajectories, not event-policy transitions.

The original v66 stop witness has a certified potential stop bracket of roughly
0.124300824 hours. This quantifies the event that sampled whole-interval
withholding loses. Three repeated dt=0.25/0.5/1 schedules retain the full incoming
inventory box, cumulative ports, OFF/ON ages and physical clocks. Their existing
sampled service policy is independently checked again in the new chart.

Actual near-boundary and delayed strict probes reject `v67 unresolved event
ordering`. The delayed probe retains two identical valid samples before the
rejection. Independent closed-form exp/log QA checks every E/B/threshold corner,
strict endpoint witnesses, readiness and exact threshold expressions. Eleven
function probes additionally include broad incoming boxes, nonzero loss,
passive restart, exact boundary equality and OFF dwell ending before/at/after
the held boundary. The embedded certifier equals the host-probed source.

Evidence: `{rel}`. Original MAT reopened/exported by MATLAB, binary and numeric
traces, observed batch receipt/exit 0, timestamped MATLAB log, immutable QA JSON,
sealed sources and unchanged baseline hashes. Development evidence stays in
`results/event_brackets_v67_20261011T214411_093986Z`, including the original saved
v67 model and source snapshot. Corrected final saved model is revision v67r2.

Concrete integration blocker: v66 allocation consumes one held scalar duration;
a certified root is an interval correlated with threshold identity and every
energy/age offset. Passing a midpoint or independently resetting inventory would
erase this relationship. The observer resolves root existence/order for tested
paths, while correlated post-event service integration remains the next task.
No earliest-event switching acceptance is claimed.

Limitations:

"""+'\n'.join('- '+v for v in limitations)+f'\n\nNext actionable task: {nexttask}\n'
new(ROOT/'audit/Event_bracket_results_v67.md',summary)
for name in ['MASTER_STAGEBOARD_v67.md','MASTER_STAGEBOARD_stateflow_v67.md']:new(ROOT/name,summary)
progress=f"""

## {now} — v67 executed root certificates in the same six-mode chart

Read latest STATUS/stageboards, Stateflow acceptance, research frontier,
engineering progress and v66/v65/v64 code first. Work confined to this project;
no Jarvice, unrelated files, settings, scheduler, runner, secrets or publication.

Implemented versioned outward held-trajectory root certifier and observer in
the SAME actual six-mode sampled chart. Strict before/after witnesses retain
incoming inventory/forcing/threshold hulls; OFF dwell uses retained age bounds.
Unresolved near-boundary ordering rejects rather than choosing by tolerance.
Embedded v66 dispatch remains unchanged; root observations do not switch events.

PASS/FAIL: MATLAB {r['summary']['passed']}/0; independent {q['summary']['passed']}/0;
{len(r['runs'])} runs/{ticks} ticks/all six modes, {len(r['faults'])} actual faults,
{refs} v30 references; {q['active_certificates']} compiled observations and
{q['root_probes']} function probes; six reviewer corruptions detected. Evidence:
`{rel}` (MAT/reopen/binary/CSV/log/exit receipt/sealed sources). Baseline hashes pass.

Preserved development: sandbox MATLAB initialization failure; initial 1368/3
batch with three wrong expected-mode labels (safe capacity-limited charge still
occurred); core-name shadow warning. Repaired expectations, renamed observer
argument and appended candidate forcing provenance for independent corner QA.
Original development v67 model preserved; accepted observer revision is v67r2.

Files added: matlab/simulink/certify_event_root_v67.m, event_observer_v67.m,
build_event_brackets_v67.m, DCHR_Event_Brackets_Stateflow_v67[r2].slx;
matlab/run_event_brackets_v67.m; audit/prepare/create/repair/run/seal/verify/
finalize_event_brackets_v67 and derivation/results; STATUS/stageboards_v67.
Shared ledgers append-only.

Scope: root-observer acceptance only; actual repeated earliest-event integration
OPEN. Concrete interface blocker: root-time interval is correlated with symbolic
threshold, port offsets and OFF-age; existing scalar-duration allocation cannot
consume it without a new correlated segment protocol. Conditional arithmetic,
strict-monotonic/span guards and same-agent algorithmic independence explicit.
No new primary text/calibration/replication/measured validation.

Next actionable task: {nexttask}
Stop after this coherent executed observer deliverable and clear handoff.
"""
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Executed root-observer checkpoint — {now} / v67\n\nActual saved v67r2 runs all six modes with {r["summary"]["passed"]}/0 MATLAB and {q["summary"]["passed"]}/0 independent checks; {len(r["faults"])} actual rejections, {q["active_certificates"]} compiled root observations, eleven function probes and six reviewer mutations. Retained-root/threshold/dwell/order certificates pass; sampled plant schema stays 66. This accepts the observer only. General correlated earliest-event control remains OPEN; no physical validation or article replication. STATUS_stateflow_v67 and audit/Event_bracket_results_v67.md authoritative; v57/v66 acceptance preserved.\n')
with (ROOT/'audit/research_frontier_2026_10_08.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## {now} — v67 event-certification handoff\n\nExecuted same-chart root observer; MATLAB {r["summary"]["passed"]}/0, independent {q["summary"]["passed"]}/0. New root existence/order and OFF-dwell certificates pass for tested paths; actual earliest switching remains open. No new primary-source signoff.\n\nNext actionable task: {nexttask}\n')
new(folder/f'QA_receipt_{stamp}.log',f'Observed immutable QA file: {qpath.name}\nSHA256: {sha(qpath)}\nPASS={q["summary"]["passed"]} FAIL=0 MUTATIONS_DETECTED=6\nEmbedded and standalone certifier source equality: PASS\nBaseline and sealed source hashes at finalization: PASS\n')
new(folder/'release_receipt_v67.json',json.dumps(dict(timestamp_utc=now,status='STATUS_v67.json',status_sha256=sha(ROOT/'STATUS_v67.json'),
    model_sha256=sha(mdl),qa_sha256=sha(qpath),embedded_host_certifier_equal=True),indent=2)+'\n')
print(json.dumps(dict(result=status['result'],matlab=status['matlab_passed'],independent=status['independent_passed'],status='STATUS_v67.json'),indent=2))
