"""Publish scoped local checkpoint only after executed MATLAB and independent QA."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
qpath=max(folder.glob('independent_QA_v68r2_*.json'),key=lambda p:p.name)
q=json.loads(qpath.read_text());r=json.loads((folder/'report.json').read_text())
assert q['summary']['failed']==r['summary']['failed']==0
assert all(v['passed'] for v in q['reviewer_selfchecks'])
assert r['mode_coverage']==list(range(6))
receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
assert any(v['exit_code']==0 for v in receipts)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['preservation.json','source_hashes.json','reviewer_hashes_v68r2.json']:
    for v in json.loads((folder/name).read_text()):assert sha(ROOT/v['path'])==v['sha256']
now=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
mdl=ROOT/'matlab/simulink/DCHR_Span_Repair_Stateflow_v68.slx'
rows=lambda v:[v] if v and isinstance(v[0],(float,int)) else v
ticks=sum(len(rows(v['input'])) for v in r['runs'])
refs=sum(len(v['references_v30']) for v in r['runs'])
actual=[v for v in r['legacy_defects'] if v['model']!='host_v67']
legacy_rejections=sum(bool(v['identifier']) for v in actual)
assert legacy_rejections==2 and len(actual)==3
limitations=[
    'Numerical-span repair and executed root observer only; roots do not control service or reset inventory. Earliest-event integration remains OPEN.',
    'Public root-domain predicate is the unchanged represented lambda*horizon<=1. The private outward evaluation span must be <=2; its remainder is widened with a proved bound.',
    'More conservative tail padding can widen enclosures and classify additional near-contacts as unresolved; no tolerance selects an event side.',
    'Plant schema remains 66 with unchanged conservative sampled allocation and finite-water/port/clock guards. Thermal thresholds and approach parameters remain engineering assumptions.',
    'Normal-mode Stateflow execution and conditional binary64 interval arithmetic; generated-code/subnormal rounding and calibrated hardware behavior are not accepted.',
    'Same-agent independent rational/160-digit closed exp/log QA and reviewer mutations; not independent personnel or measured validation.',
    'No new primary source text, equipment calibration, article replication or measured physical validation; full source signoffs remain 0/31.',
    'Development and first final batches failed due to harness expectations/case lookup. Original logs, MAT reports and reviewer failures remain preserved. Corrected QA/proof revision has a separate source seal.'
]
next_task=('Implement a correlated event-segment record for one repeated earliest-event cycle in an additive SAME six-mode chart. '
           'Use the repaired v68 certifier and retain threshold identity, root-time hull, inventory, source/work/loss/service offsets '
           'and OFF age across the split without midpoint substitution. Certify dwell and strict ordering against held boundaries; '
           'reject unresolved collisions. Compare original-MAT service and source/work enclosures with an independent event trajectory, '
           'including the v66 stop witness, repeated dt=0.25/0.5/1 schedules and the exact lambda*duration=1 boundary. '
           'Preserve v57-v68. Primary calibration and measured validation remain OPEN.')
status=dict(version='0.68',timestamp_utc=now,inherits='STATUS_v67.json',
    result='EXECUTED_NUMERICAL_SPAN_REPAIR_PASS_EARLIEST_SWITCHING_OPEN',new_model=True,
    saved_model=mdl.relative_to(ROOT).as_posix(),model_sha256=sha(mdl),model_executed_this_run=True,
    accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',
    accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',
    accepted_root_observer_model=mdl.relative_to(ROOT).as_posix(),embedded_dispatch_schema=66,
    numerical_span_repair_acceptance=True,event_root_observer_acceptance=True,coupled_stateflow_acceptance=False,
    general_repeated_earliest_event_stateflow='OPEN',matlab_passed=r['summary']['passed'],matlab_failed=0,
    independent_passed=q['summary']['passed'],independent_failed=0,actual_runs=len(r['runs']),protocol_ticks=ticks,
    required_mode_coverage=r['mode_coverage'],actual_runtime_fault_rejections=len(r['faults']),v30_reference_comparisons=refs,
    active_compiled_certificates=q['active_certificates'],root_probes=q['root_probes'],
    legacy_actual_rejections=legacy_rejections,legacy_actual_near_boundary_controls=1,
    legacy_valid_prefix_ticks=2,root_status_counts=q['root_status_counts'],ordering_counts=q['ordering_counts'],
    reviewer_selfchecks=len(q['reviewer_selfchecks']),matlab_metadata=r['metadata'],result_directory=rel,
    independent_qa=qpath.relative_to(ROOT).as_posix(),derivation='audit/Span_padding_derivation_v68r2.md',
    results='audit/Span_padding_results_v68.md',primary_article_replication=False,
    independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
    limitations=limitations,next_actionable_task=next_task)

def new(path,text):
    with path.open('x',encoding='utf-8',newline='\n') as f:f.write(text)

summary=f'''# Executed Stateflow numerical-span repair v68

UTC {now}. Actual new saved `DCHR_Span_Repair_Stateflow_v68.slx`
executes all six modes and the repaired event-root observer in one chart.
It remains a sampled service controller; earliest-event switching is OPEN.

MATLAB **{r['summary']['passed']} PASS / 0 FAIL**;
independent QA **{q['summary']['passed']} PASS / 0 FAIL**;
{len(r['runs'])} runs / {ticks} protocol ticks; {len(r['faults'])} actual runtime
fault rejections; {refs} executed v30 reference comparisons;
{q['active_certificates']} compiled observations / {q['root_probes']} host root probes.
All six deliberate reviewer corruptions were detected.

The saved v67r2 model rejects exact-binary lambda=1/8, duration=8
at the private outward-span guard despite the nominal product being exactly 1.
A delayed actual witness completes two valid ticks before the same rejection.
The host root function reproduces that rejection; adjacent values below 8 are
passing controls. The new saved model executes all four new boundary/delayed
witnesses, preserving inventory, port and physical-clock enclosures.

Repair: use a private outward evaluation domain |x|<=2 and a common proved
degree-24 Taylor remainder 8*2^25/26! for phi1 and phi2. The public root
predicate stays unchanged. The dispatch kernel differs only in its function
name, private-span guard and remainder. No argument clipping or event midpoint
is introduced. Independent integral-form proof and exact rational polynomial
checks cover the complete claimed private domain; exp/log corner QA reviews
actual original-MAT root/energy/source/work/clock traces.

Evidence: `{rel}`. Timestamped MATLAB log and observed exit 0,
original/reopened MAT, binary exports, numeric CSV, immutable QA JSON,
execution source snapshot, corrected reviewer/proof snapshot and preservation
hashes all pass. Stateflow license observation and actual chart execution are
recorded; an empty ver('stateflow') response is not presented as a version.

Retained development:
- `results/span_repair_v68_20261011T215413_685622Z`: sandbox startup failure;
  MATLAB 1432/3 due to wrong near-boundary expectations and appended fault base.
- `results/span_repair_v68_final_20261011T215609_349756Z`: MATLAB 1434/1 due to
  wrong delayed-prefix comparison; independent 36981/2 correctly rejects the
  failed assertion and nonzero batch receipt, with all six mutations detected.
- The first sealed proof/reviewer draft is preserved. Revised proof uses the
  valid conservative geometric e-tail ratio 1/5, and QA matches actual chart
  stack reporting and already-reached delayed-restart classification.
- No saved v68 model or production kernel changed after the first build.

Limitations:

'''+ '\n'.join('- '+v for v in limitations)+f'\n\nNext actionable task: {next_task}\n'
for name in ['STATUS_v68.json','STATUS_stateflow_v68.json']:
    new(ROOT/name,json.dumps(status,indent=2)+'\n')
for name in ['MASTER_STAGEBOARD_v68.md','MASTER_STAGEBOARD_stateflow_v68.md','audit/Span_padding_results_v68.md']:
    new(ROOT/name,summary)
progress=f'''

## {now} — v68 executed outward-span defect repair

Read latest STATUS/stageboards, Stateflow acceptance, frontier, progress and
v67/v66/v65 code first. Confined work to this project; no Jarvice, unrelated
files, settings, tasks, runner, secrets or external publication touched.

Reproduced valid exact lambda*duration=1 rejection in preserved saved v67r2
and host root function, including a delayed two-tick valid prefix. Implemented
additive v68 builder/kernel/certifier/observer and actual saved six-mode model.
Proved private |x|<=2 Taylor tail 8*2^25/26! for both storage phi functions;
unchanged sampled policy and public root predicate. Independent QA uses exact
rational polynomial coefficients and 160-digit closed exp/log/corner checks.

PASS/FAIL: MATLAB {r['summary']['passed']}/0; independent {q['summary']['passed']}/0;
{len(r['runs'])} runs/{ticks} ticks/all six modes; {len(r['faults'])} runtime faults;
{refs} v30 comparisons; {q['root_probes']} probes; six reviewer mutations detected.
Timestamped logs, original/reopened MAT, binary/CSV traces, source/reviewer seals,
receipt/exit 0 and unchanged baseline hashes: `{rel}`.

Files: matlab/simulink/build_span_repair_v68.m, interval_dispatch_kernel_v68.m,
certify_event_root_v68.m, event_observer_v68.m, DCHR_Span_Repair_Stateflow_v68.slx;
matlab/run_span_repair_v68.m; audit/prepare/repair/run/seal/verify/finalize span
repair scripts, corrected derivation v68r2 and results v68; STATUS/stageboards.
Shared progress and acceptance appended only.

Development failures and recovery notes preserved in two earlier evidence
folders. Harness expectation/base/prefix bugs repaired; sealed proof/reviewer
revision corrected separately. No production/model rewrite after initial build.
No new primary text, calibration, article replication or measured validation.

Remaining limitations: numerical repair/root-observer acceptance only;
earliest-event integration OPEN; conditional normal-mode arithmetic and
same-agent algorithmic QA. Full source signoffs remain 0/31.

Next actionable task: {next_task}
Stop after this coherent executed repair and handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Numerical-span repair acceptance — {now} / v68\n\n'
            f'Actual new saved v68 six-mode model: MATLAB {r["summary"]["passed"]}/0, '
            f'independent {q["summary"]["passed"]}/0; {len(r["runs"])} runs/{ticks} ticks, '
            f'{len(r["faults"])} runtime faults, {refs} references and six reviewer corruptions detected. '
            'Exact lambda*duration=1 legacy rejection reproduced and repaired with a proved widened '
            'private Taylor-domain bound. STATUS/stageboards v68 and corrected derivation v68r2 '
            'are authoritative. Root observer/sampled policy only; earliest-event switching, '
            'primary calibration and physical validation remain OPEN. Baselines preserved.\n')
print(json.dumps(dict(status=status['result'],matlab=r['summary'],independent=q['summary'],runs=len(r['runs']),ticks=ticks),indent=2))
