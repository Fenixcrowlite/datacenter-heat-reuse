"""Close only scoped executable candidate-interface acceptance after both gates."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, shutil, sys
ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve();assert folder.is_relative_to(ROOT/'results')
qpath=max(folder.glob('independent_QA_v70_*.json'));q=json.loads(qpath.read_text());r=json.loads((folder/'report.json').read_text())
assert r['summary']['failed']==q['summary']['failed']==0
assert all(x['passed'] for x in q['reviewer_selfchecks'])
assert r['mode_coverage']==list(range(6)) and len(r['faults'])==8
assert all(x['identifier'] and x['expected_guard'] in x['message'] for x in r['faults'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['preservation.json','source_hashes.json']:
    for x in json.loads((folder/name).read_text()):assert sha(ROOT/x['path'])==x['sha256']
receipts=[json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json')]
assert any(x['exit_code']==0 and x['evidence_class']=='OBSERVED_LOCAL_MATLAB_BATCH' for x in receipts)
rows=lambda v:[v] if isinstance(v[0],(int,float)) else v
ticks=sum(len(rows(x['input'])) for x in r['runs']);refs=sum(len(x['references_v30']) for x in r['runs'])
rel=folder.relative_to(ROOT).as_posix();now=datetime.now(timezone.utc).isoformat()
model=ROOT/'matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx'
assert sha(model)==q['model_sha256']
modelcopy=folder/'generated_model'/model.name;modelcopy.parent.mkdir()
shutil.copy2(model,modelcopy);assert sha(modelcopy)==sha(model)
next_task=('Implement one certified repeated earliest-event cycle in an additive SAME six-mode Stateflow chart using v70 enabled candidates. '
    'Carry threshold identity, root-time hull and correlated inventory/source/work/loss/service/clock offsets and OFF age across each segment; never substitute a root midpoint. '
    'Recompute forcing and candidates after cutoff/stop/restart and held input boundaries. A restart readiness prediction after cutoff is invalid under the old forcing. '
    'Retain strict collision rejection and dwell proofs; compare original-MAT event service/source/work enclosures with an independent exact-binary closed-form event trajectory. '
    'Regress inactive-contact/delayed/strict, forced discharge restart, pair ordering controls, future charge sink, repeated dt=0.25/0.5/1 and lambda*duration=1. '
    'Preserve v57-v70. Primary calibration, article replication and measured validation remain OPEN.')
limitations=[
    'New saved v70 executes prospective mode-conditioned candidate records in the same chart. Sampled service/inventory schema remains 66. Candidates do not split intervals or switch at roots; general repeated earliest-event dispatch remains OPEN.',
    'Candidate powers precede sampled full-horizon withholding and cannot be delivered over an unsplit interval. The consumer must recompute after any earlier event; forcing beyond cutoff is hypothetical.',
    'Conditional normal-mode outward arithmetic and conservative eligibility hulls; generated code not tested.',
    'Independent QA uses same-agent algorithmically separate Fraction/120/160-digit exp/log/corner and first-law calculations, not independent personnel or measured validation.',
    'Original MAT reopened and binary-exported by MATLAB; no independent HDF5 parser. Stateflow license and actual chart execution observed; empty version metadata retained.',
    'Synthetic engineering equipment/thresholds; no new primary text, calibration, article replication or physical validation. Full source signoffs remain 0/31.',
    'Development startup, harness matrix assertion, JSON fault decoding, sampled cutoff-domain edge and ordering-fixture efficiency omission retained. Initial v70 model preserved; accepted v70r2 also rejects enabled derivative ambiguity. Final sealed execution passes.'
]
csvpath=folder/'candidate_records_v70.csv'
with csvpath.open('x',newline='') as f:
    w=csv.writer(f);w.writerow(['id','tick','event','enabled','status','root_lo_h','root_hi_h','ready_lo_h','ready_hi_h','boundary_order','B_lo_MW','B_hi_MW','pair_order','HP_MW','direct_MW','charge_MW','discharge_MW'])
    for run in r['runs']:
        for tick,row in enumerate(rows(run['trace'])):
            if rows(run['input'])[tick][0]==0:continue
            z=row[205:]
            for j,name in enumerate(['stop','cutoff','restart']):
                v=z[15*j:15*j+15]
                w.writerow([run['id'],tick,name,z[51+j],v[0],v[1],v[2],v[9],v[10],v[11],*z[45+2*j:47+2*j],z[66],*z[54:58]])
status=dict(version='0.70',timestamp_utc=now,inherits='STATUS_v69.json',result='MODE_CONDITIONED_EVENT_CANDIDATE_INTERFACE_ACCEPTED_QA_PASS',new_model=True,
    model_revision='v70r2',
    saved_model='matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx',model_sha256=q['model_sha256'],model_executed_this_run=True,
    accepted_dispatch_model='matlab/simulink/DCHR_Dispatch_Stateflow_v57.slx',accepted_sampled_interval_model='matlab/simulink/DCHR_Interval_Dispatch_Stateflow_v66.slx',
    accepted_event_candidate_model='matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx',embedded_dispatch_schema=66,event_interface_schema=70,
    coupled_stateflow_acceptance=False,general_repeated_earliest_event_stateflow='OPEN',
    v69_defects_repaired_in_tested_scope=['Disabled cutoff no longer rejects strict HP-only contact or delayed prefix.','OFF/dwell-blocked HP has no charging stop candidate.','OFF restart uses the enabled TES-discharge forcing, including positive loss.'],
    matlab_passed=r['summary']['passed'],matlab_failed=0,independent_passed=q['summary']['passed'],independent_failed=0,
    actual_runs=len(r['runs']),protocol_ticks=ticks,required_mode_coverage=r['mode_coverage'],actual_runtime_rejections=len(r['faults']),
    v30_reference_comparisons=refs,reviewer_selfchecks=len(q['reviewer_selfchecks']),matlab_metadata=r['metadata'],result_directory=rel,
    independent_qa=qpath.relative_to(ROOT).as_posix(),candidate_csv=csvpath.relative_to(ROOT).as_posix(),derivation='audit/Event_candidates_derivation_v70.md',results='audit/Event_candidates_results_v70.md',
    primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,limitations=limitations,next_actionable_task=next_task)
summary=f'''# Executed mode-conditioned event candidate interface v70

UTC {now}. New saved model: `matlab/simulink/DCHR_Event_Candidates_Stateflow_v70r2.slx`.
Actual normal-mode simulations execute all six states and candidate records.
Sampled service remains schema 66; earliest-event switching is not accepted.

MATLAB **{r['summary']['passed']} PASS / 0 FAIL**; independent QA
**{q['summary']['passed']} PASS / 0 FAIL**; {len(r['runs'])} runs / {ticks} protocol ticks;
{refs} v30 reference comparisons, {len(r['faults'])} actual runtime rejections and
{len(q['reviewer_selfchecks'])} detected reviewer corruptions.

The v69 inactive HP-only cutoff contact and delayed strict witnesses now pass.
OFF/dwell-blocked charging has no stop root. Zero/positive-loss TES discharge
uses negative forcing in the restart certificate. Genuine active stop/cutoff
boundary collisions and overlapping cutoff/restart readiness still reject.
Separated cutoff-first/restart-first and above-stop future charge sink controls
execute. Repeated dt=0.25/0.5/1 and v68 span boundary regressions pass.

Evidence: `{rel}`. Timestamped MATLAB log/exit receipt, sealed source/model
snapshots, original/reopened MAT and little-endian binary exports, plant CSV,
`candidate_records_v70.csv`, closed-form root-box/source/work/service QA and
baseline preservation hashes retained. No earlier model/checkpoint overwritten.

Development failures retained: 02:36:04 sandbox startup plus harness matrix
scalar-reduction failure; 02:37:45 JSON fault-decoding failure; 02:39:20 sampled
zero-loss cutoff-domain rejection; 02:41:13 MATLAB 1133/3 and independent
47208/4 due ordering fixtures omitting etaD and the cutoff-domain fixture,
including failed receipts. Preflight-only specification folders also retained.
All are under `results/event_candidates_v70_*`; none was counted as acceptance.
The initial v70 SLX is preserved. Additive v70r2 retains unresolved derivative
records and rejects their strict consumption; a near-equilibrium witness passes.
Finalization uses the completed sealed execution, not a compile-only prototype.

Limitations:

'''+ '\n'.join('- '+v for v in limitations)+f'\n\nNext actionable task: {next_task}\n'
outputs={name:json.dumps(status,indent=2)+'\n' for name in ['STATUS_v70.json','STATUS_stateflow_v70.json']}
outputs.update({name:summary for name in ['MASTER_STAGEBOARD_v70.md','MASTER_STAGEBOARD_stateflow_v70.md','audit/Event_candidates_results_v70.md']})
assert all(not (ROOT/name).exists() for name in outputs)
for name,value in outputs.items():
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:f.write(value)
progress=f'''

## {now} — v70 executed mode-conditioned event candidate repair

Read latest STATUS/stageboards, Stateflow acceptance, frontier, progress and
v68/v69/v66 code before edits. Work stayed in this project; no Jarvice,
unrelated files, settings, tasks, runner, secrets or publication touched.

Added versioned v70 builder/kernel/candidate function and actual saved six-mode
model. Repaired the three v69 interface witnesses and added enabled-pair
ordering, collision rejection and above-stop future charge sink controls.
Retained incoming E/OFF-age hulls, ports, forcing, thresholds, boundary and
latch provenance; no midpoint consumed. Sampled plant remains schema 66.

PASS/FAIL: MATLAB {r['summary']['passed']}/0; independent {q['summary']['passed']}/0;
{len(r['runs'])} runs/{ticks} ticks/all six modes; {len(r['faults'])} runtime rejections,
{refs} v30 comparisons, {len(q['reviewer_selfchecks'])} reviewer corruptions detected.
Evidence `{rel}`: timestamped logs/receipts, original/reopened MAT, binary/CSV,
sealed sources/model and unchanged prior preservation hashes. Failed development
startup and harness checks remain in their timestamped folders.

Files: matlab/simulink/build_event_candidates_v70.m, interval_dispatch_kernel_v70.m,
event_candidates_v70.m, DCHR_Event_Candidates_Stateflow_v70r2.slx;
matlab/run_event_candidates_v70.m; audit/prepare/run/verify/finalize event
candidates v70 and derivation/results; STATUS/stageboards v70.
Shared progress, acceptance and frontier appended only.

Limitations: executable candidate-interface acceptance only; repeated earliest
segments, calibrated physics, primary article replication and independent
personnel/measured QA OPEN. Closed-form Fraction/Decimal algorithms are separate
from production Taylor/bisection; MAT reopened/exported by MATLAB, not an
independent HDF5 parser. Full primary signoffs remain 0/31.

Next actionable task: {next_task}
Stop after this coherent executable repair and clear handoff.
'''
with (ROOT/'automation/engineering_progress.md').open('a',encoding='utf-8') as f:f.write(progress)
with (ROOT/'automation/STATEFLOW_ACCEPTANCE.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## Mode-conditioned candidate-interface acceptance — {now} / v70\n\nNew saved v70 chart executed: MATLAB {r["summary"]["passed"]}/0, independent {q["summary"]["passed"]}/0; {len(r["runs"])} runs/{ticks} ticks/all six modes; {len(r["faults"])} runtime rejections and {len(q["reviewer_selfchecks"])} reviewer corruptions detected. v69 inactive cutoff/stop and discharge-forced restart witnesses repaired in tested scope; genuine collision rejection preserved. Candidate interface accepted only; sampled schema 66 unchanged and earliest switching OPEN. STATUS/stageboards v70 and Event_candidates_results_v70.md authoritative. Calibration/primary replication/physical validation OPEN.\n')
with (ROOT/'audit/research_frontier_2026_10_08.md').open('a',encoding='utf-8') as f:
    f.write(f'\n\n## {now} — v70 executed event candidate repair\n\nMode-conditioned candidate records and closed-form QA repair v69 interface witnesses; no new primary-source signoff or earliest-switching claim.\n\nNext actionable task: {next_task}\n')
seal=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in [qpath,folder/'report.json',csvpath,model,modelcopy,ROOT/'audit/finalize_event_candidates_v70.py']+[ROOT/name for name in outputs]]
with (folder/'checkpoint_artifact_hashes_v70.json').open('x') as f:json.dump(seal,f,indent=2);f.write('\n')
print(json.dumps(dict(status='STATUS_v70.json',evidence=rel,matlab=r['summary'],independent=q['summary'],next_task=next_task)))
