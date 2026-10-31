"""Write an honest local blocker checkpoint after saved-model execution and QA."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
qpath=max(folder.glob('independent_QA_v69_*.json'))
q=json.loads(qpath.read_text());r=json.loads((folder/'report.json').read_text())
assert r['summary']['failed']==q['summary']['failed']==0
assert all(v['passed'] for v in q['reviewer_selfchecks'])
assert r['mode_coverage']==list(range(6)) and len(r['faults'])==3
assert all(v['identifier'] and v['expected_guard'] in v['message'] for v in r['faults'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['preservation.json','source_hashes.json']:
    for v in json.loads((folder/name).read_text()):assert sha(ROOT/v['path'])==v['sha256']
receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
assert any(v['exit_code']==0 and v['evidence_class']=='OBSERVED_LOCAL_MATLAB_BATCH' for v in receipts)
rows=lambda v:[v] if isinstance(v[0],(int,float)) else v
ticks=sum(len(rows(v['input'])) for v in r['runs']);refs=sum(len(v['references_v30']) for v in r['runs'])
rel=folder.relative_to(ROOT).as_posix();now=datetime.now(timezone.utc).isoformat()
next_task=('Implement additive v70 mode-conditioned event candidates in the SAME six-mode chart before correlated earliest-event segments. '
    'Retain inventory/OFF-age hulls and held boundary; derive candidate ports from eligible HP/TES allocation, evaluate OFF restart with discharge forcing, '
    'stop only for enabled charge and cutoff only for enabled discharge. Retain threshold/root/forcing provenance and reject unresolved ordering only among enabled candidates. '
    'Execute v69 inactive-contact/delayed/strict controls, blocked-stop and zero/positive-loss forced-restart witnesses; keep genuine collision rejection. '
    'Then integrate one certified repeated earliest cycle with correlated source/work/loss/service/clock offsets, regress v66 repeated dt=0.25/0.5/1 and v68 span boundary. '
    'Preserve v57-v69; calibration and measured validation remain OPEN.')
limitations=[
    'No new SLX or corrected-controller acceptance. Saved v68 observer executed; sampled service policy stays schema 66. General earliest-event integration OPEN.',
    'Observer roots remain valid for their hypothetical held paths. The confirmed defects concern event applicability and missing forced restart when these records are consumed as a dispatch-event interface.',
    'Independent QA is same-agent algorithmic independence using exact binary Fraction and 120/160-digit closed exp/log, not independent personnel or measured validation.',
    'Original MAT reopened and binary-exported by MATLAB; no independent HDF5 parser. Normal-mode conditional interval arithmetic only; generated code not validated.',
    'Synthetic engineering equipment and threshold assumptions; no new primary text, calibration, article replication or physical validation. Source signoffs remain 0/31.',
    'Startup, cell-decoding and fixture/reviewer expectation failures preserved in two development folders; all final checks pass on a separately sealed execution.'
]
status=dict(version='0.69',timestamp_utc=now,inherits='STATUS_v68.json',
    result='SAVED_V68_EVENT_APPLICABILITY_BLOCKER_CONFIRMED_QA_PASS',new_model=False,
    saved_model='matlab/simulink/DCHR_Span_Repair_Stateflow_v68.slx',model_sha256=q['model_sha256'],model_executed_this_run=True,
    accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',
    accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',
    accepted_root_observer_model='matlab/simulink/DCHR_Span_Repair_Stateflow_v68.slx',
    embedded_dispatch_schema=66,coupled_stateflow_acceptance=False,general_repeated_earliest_event_stateflow='OPEN',
    blocking_defects=['Hypothetical cutoff contact can reject strict HP-only service with zero actual discharge.',
        'Stop certificate can be nonactionable while HP is OFF and OFF dwell blocks restart.',
        'Passive-only restart candidate misses eligible restart during actual TES discharge.'],
    matlab_passed=r['summary']['passed'],matlab_failed=0,independent_passed=q['summary']['passed'],independent_failed=0,
    actual_runs=len(r['runs']),protocol_ticks=ticks,required_mode_coverage=r['mode_coverage'],
    actual_runtime_rejections=3,false_inactive_cutoff_rejections=2,genuine_boundary_rejection_controls=1,
    delayed_valid_prefix_ticks=2,forced_restart_probes=len(r['root_probes']),v30_reference_comparisons=refs,
    reviewer_selfchecks=len(q['reviewer_selfchecks']),matlab_metadata=r['metadata'],result_directory=rel,
    independent_qa=qpath.relative_to(ROOT).as_posix(),derivation='audit/Event_applicability_derivation_v69.md',
    results='audit/Event_applicability_results_v69.md',primary_article_replication=False,
    independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
    limitations=limitations,next_actionable_task=next_task)
summary=f'''# Saved-v68 event applicability blocker v69

UTC {now}. Preserved actual saved v68 six-mode chart executed afresh.
No new SLX or repaired event controller is claimed. The numerical root certificates
are valid for hypothetical paths; they are not yet a mode-conditioned event list.

MATLAB **{r['summary']['passed']} PASS / 0 FAIL**; independent QA
**{q['summary']['passed']} PASS / 0 FAIL**; {len(r['runs'])} runs / {ticks} protocol ticks,
all six modes, {refs} v30 comparisons, two forced-restart probes and six detected
reviewer corruptions. Three actual runtime rejections include two inactive-cutoff
false-rejection witnesses (one with a two-tick valid prefix) and one genuine
stop-boundary collision control. Strict separated HP-only controls pass.

Confirmed integration blockers:

- HP-only demand is delivered directly with zero TES discharge. The observer's
  hypothetical full-discharge near-contact still rejects strict event ordering.
  Actual zero-loss storage inventory stays constant above cutoff.
- The HP is OFF with OFF dwell not satisfied; actual charging is zero. The
  observer nevertheless certifies a strictly interior hypothetical thermal stop.
- Actual OFF-state discharge crosses the thermal restart threshold and satisfies
  dwell within the held interval. The passive-only observer reports no restart.
  Independent exp/log roots and executed host probes confirm both zero-loss and
  positive-loss fixtures. This does not imply a defect in the intentional sampled
  policy; it blocks using its observer as an earliest-event dispatch interface.

Evidence: `{rel}`. Original/reopened MAT, little-endian binary exports,
numeric CSV, MATLAB log/exit receipt, sealed execution/reviewer sources and prior
preservation hashes pass. Empty `ver('stateflow')` is retained as metadata;
actual chart execution and license observation provide availability evidence.

Development retained:

- `results/event_applicability_v69_20261012T022419_517279Z`: sandbox MATLAB
  startup filesystem failure, then cell/struct decoding failure before simulation.
- `results/event_applicability_v69_20261012T022529_327801Z`: MATLAB 136/6 and
  independent 1901/15. Saturated outward water limit left tiny TES discharge,
  invalidating the initial HP-only fixture; increased water-capacity headroom
  isolates actual zero-discharge behavior. Lossy passive restart has a no-crossing
  record, not an empty record; reviewer expectation corrected. Failed logs,
  assertions and QA are preserved. Saved v68 was never modified.

Limitations:

'''+ '\n'.join('- '+v for v in limitations)+f'\n\nNext actionable task: {next_task}\n'
outputs={name:json.dumps(status,indent=2)+'\n' for name in ['STATUS_v69.json','STATUS_stateflow_v69.json']}
outputs.update({name:summary for name in ['MASTER_STAGEBOARD_v69.md','MASTER_STAGEBOARD_stateflow_v69.md','audit/Event_applicability_results_v69.md']})
assert all(not (ROOT/name).exists() for name in outputs)
for name,value in outputs.items():
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(value)
progress=f'''

## {now} — v69 saved-model event applicability blocker

Read latest STATUS/stageboards, acceptance, frontier, progress and v68/v66 code.
Finished the existing draft v69 audit within this project; no Jarvice, unrelated
files, settings, scheduler, runner, secrets or external publication touched.

Executed preserved saved v68 in all six modes. Confirmed three integration
blockers: inactive hypothetical cutoff strict rejection; nonactionable stop
while HP OFF/dwell blocked; passive-only restart misses forced-discharge roots.
No new SLX or corrected earliest-event implementation accepted. Independent QA
checks actual original-MAT binary exports with Fraction/Decimal exp/log and
analytic source/work/first-law equations, plus six reviewer mutations.

PASS/FAIL: MATLAB {r['summary']['passed']}/0; independent {q['summary']['passed']}/0;
{len(r['runs'])} runs/{ticks} ticks/all modes; three runtime rejections, {refs} v30 references;
two forced-root probes, delayed two-tick prefix. Evidence `{rel}` contains
timestamped logs/receipts, original/reopened MAT, binary/CSV, source seals and
unchanged preservation hashes. Initial failures and corrected fixture/reviewer
expectations are documented in Event_applicability_results_v69.md and retained.

Files added/completed: matlab/run_event_applicability_v69.m;
audit/prepare_event_applicability_v69.py, run_event_applicability_v69.ps1,
verify_event_applicability_v69.py, finalize_event_applicability_v69.py,
Event_applicability_derivation/results_v69.md; STATUS/stageboards_v69.
Shared acceptance/frontier/progress appended only. Limitations: hypothetical
observer remains accepted only in prior scoped sense; general earliest dispatch,
primary calibration, physical validation and independent personnel QA OPEN.

Next actionable task: {next_task}
Stop after this coherent executed defect checkpoint and clear handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Event applicability blocker checkpoint — {now} / v69\n\nSaved v68 executed afresh, no new SLX. MATLAB {r["summary"]["passed"]}/0 and independent {q["summary"]["passed"]}/0, all six modes, three actual rejections and six reviewer mutations. Hypothetical cutoff/stop applicability and passive-only restart forcing are confirmed integration blockers. Prior observer and sampled acceptance remain scoped; no corrected earliest-event acceptance. STATUS/stageboards v69 and audit/Event_applicability_results_v69.md authoritative. Next: additive mode-conditioned candidates before correlated event segments. Calibration and physical validation OPEN.\n')
with (ROOT/'audit/research_frontier_2026_10_08.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## {now} — v69 event interface blocker\n\nSaved-v68 actual execution/independent QA confirms observer roots require mode/forcing applicability before earliest-event integration. No primary-source signoff added.\n\nNext actionable task: {next_task}\n')
seal=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in [qpath,folder/'report.json',ROOT/'audit/finalize_event_applicability_v69.py']+[ROOT/name for name in outputs]]
with (folder/'checkpoint_artifact_hashes_v69.json').open('x') as f:json.dump(seal,f,indent=2);f.write('\n')
print(json.dumps(dict(status='STATUS_v69.json',evidence=rel,matlab=r['summary'],independent=q['summary'],next_task=next_task)))
