"""Publish a workspace-only checkpoint after executed and independent gates pass."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, shutil, sys

ROOT=Path(__file__).resolve().parents[1]
folder=(ROOT/sys.argv[1]).resolve()
assert folder.is_relative_to(ROOT/'results')
report=json.loads((folder/'report.json').read_text())
qa_path=sorted(folder.glob('independent_QA_v84_*.json'))[-1]
qa=json.loads(qa_path.read_text())
assert report['summary']['failed']==qa['summary']['failed']==0
assert all(c['passed'] for c in qa['reviewer_selfchecks'])
assert any(json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0 for p in folder.glob('execution_*.json'))
for name in ['STATUS_v84.json','STATUS_stateflow_v84.json','MASTER_STAGEBOARD_v84.md','MASTER_STAGEBOARD_stateflow_v84.md','audit/Electrical_conservatism_results_v84.md']:
    assert not (ROOT/name).exists(),name

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
    with p.open('x',encoding='utf-8') as f:
        if isinstance(v,str):f.write(v)
        else:json.dump(v,f,indent=2);f.write('\n')
def rows(v):return [v] if isinstance(v[0],(int,float)) else v
def short(s):return f'{float(s):.10g}'

stamp=datetime.now(timezone.utc).isoformat()
model='matlab/simulink/DCHR_Electrical_Dispatch_Stateflow_v83r2.slx'
assert sha(ROOT/model)==qa['model_sha256']=='6c3923c30e7058ec07e8d6f1667a5b9aae4db012775cba52bb0fb8d9cd98e1dd'
counts=dict(schedules=len(report['runs']),held_intervals=sum(len(rows(r['trace'])) for r in report['runs']),
    positive_segments=int(sum(row[12] for r in report['runs'] for row in rows(r['trace']))),
    interior_events=int(sum(row[13] for r in report['runs'] for row in rows(r['trace']))))
next_task=('Derive and independently verify a temperature-conditioned ON charging backend with positive passive loss, '
    'hot-water floor crossing and TES stop events before integration into an additive six-mode Stateflow model. '
    'The affine held-power kernel cannot accept a start-temperature electrical cap safely while charging. '
    'Choose a certified whole-segment constant cap or a certified nonlinear flow/event solver explicitly, '
    'bind raw and effective policies with versioned trace/report provenance, and regress v84 histories plus '
    'zero/nonbinding ratings and stop/restart/dwell/refusal controls. Preserve v80-v84. '
    'Keep primary equipment supplement acquisition/calibration open; synthetic Pmax is not a commercial rating.')
limits=[
    'Checkpoint 0.84 is a fresh saved-v83r2 experiment and independent hypothetical comparator; no new SLX or dynamic-cap Stateflow implementation is accepted.',
    'Twelve comparison histories are zero-loss, HP initially ON, service-only or charge-only, with disabled boiler/TES discharge and no stop/restart on the dynamic paths. Six modes and an interior event control execute separately.',
    'Dynamic heat/source gains use increased compressor work. Service-only gains are delivered service; charging gains are stored inventory, never delivered district heat or equal-electricity savings.',
    'Reduced constant cooling-factor/refrigerant proxy equations, approach values, storage efficiencies and 0.05 MW compressor ratings are synthetic engineering assumptions. No new primary text/signoff or commercial supplement was acquired; full signoffs remain 0/31.',
    'Same-agent algorithmic independence: Fraction/binary inputs and 120/160-digit closed equations call no production MATLAB solver; a separate RK4 integrates the comparator ODE. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser claim.',
    'Independent comparator budgets are 1e-100 precision agreement, 1e-110 primitive residual and 1e-10 MWh RK4 endpoint agreement, not relaxed production guards or measured accuracy.',
    'No positive-loss dynamic comparator, mixed service/charge optimization, source-map calibration, annual performance, article replication, measured physical validation or generated-code acceptance.',
    'Inherited saved-model span, clock, segment-count and event-collision domains remain. Its protocol ticks are not solver-clock event times.',
    'Initial restricted MATLAB startup failed. Two complete candidates each passed MATLAB 79/79 and 11008 independent checks but failed the interior-event coverage gate at 0.2/0.5 MW. Both attempts and original snapshots are preserved; only the corrected 1000 MW nonbinding event-fixture batch and QA count as checkpoint acceptance.'
]
body=f'''# Saved-Stateflow electrical conservatism experiment v84

UTC {stamp}.

Preserved saved v83r2 actually executes {counts['schedules']} complete schedules / {counts['held_intervals']} held intervals / {counts['positive_segments']} positive segments / {counts['interior_events']} interior events, with all six required modes. MATLAB {report['summary']['passed']} PASS / 0 FAIL; independent equation/artifact QA {qa['summary']['passed']} PASS / 0 FAIL; {len(qa['reviewer_selfchecks'])} separate reviewer corruptions detected. One fresh nonbinding saved-v80 reference comparison and clean saved-v83r2 reopening are bitwise equal.

The global maximum-temperature electrical cap is safe but leaves useful capacity unused on every one of twelve tested service/charging histories. A new independently derived temperature-conditioned comparator quantifies the gap on identical raw policies, initial conditions and four 0.25-hour inputs. It is a hypothetical reduced-model calculation, not a saved Stateflow dynamic controller. No hull midpoint is used: actual totals are reconstructed from original-MAT binary exports and checked against reporting hulls.

| Case | Global HP heat (MWh) | Conditioned HP heat (MWh) | Additional recovered source (MWh) | Additional delivered service (MWh) | Additional final TES (MWh) | Heat increase (%) |
|---|---:|---:|---:|---:|---:|---:|
'''
for c in qa['comparisons']:
    a,d,g=c['actual_global'],c['hypothetical_conditioned'],c['foregone']
    body+=f"| {c['id']} | {short(a['hp_heat'])} | {short(d['hp_heat'])} | {short(g['recovered_source'])} | {short(g['delivered_service'])} | {short(g['final_inventory'])} | {short(c['heat_increase_percent'])} |\n"
body+='''
For service-only cold E=3 MWh and approaches 1/1 K, delivered service rises from 0.2216761364 to 0.4475657895 MWh in one hour. The extra heat is supported by both more recovered source and more compressor work. At hot E=8.5 MWh the gap is smaller. Charging near the hot-water floor at E=4.95 MWh crosses that floor on both compared paths; the nonlinear comparator uses a separated logarithmic solution and explicit crossing time, independently checked by RK4 at 1024/2048 steps. The dynamic endpoint stays strictly below the stop threshold in every comparator case.

'''
body+=f"Model `{model}`, SHA256 `{qa['model_sha256']}`. No production model or prior checkpoint changed. Evidence `{folder.relative_to(ROOT).as_posix()}` contains timestamped MATLAB/Simulink and Python logs, execution receipt, 19 individual original MAT files and a reopened aggregate MAT, binary exports, comparison/trajectory CSV, predeclared specification, source snapshots and preservation hashes. Derivation: `audit/Electrical_conservatism_derivation_v84.md`. Prior failed scope attempts: `results/electrical_conservatism_v84_20261013T105044_893030Z` and `results/electrical_conservatism_v84_20261013T105247_497281Z`.\n\nLimitations:\n\n"
body+=''.join('- '+v+'\n' for v in limits)
body+='\nNext actionable task: '+next_task+'\n\nStop after this coherent executed deliverable and clear handoff.\n'

status=dict(version='0.84',timestamp_utc=stamp,inherits='STATUS_v83.json',
    result='SAVED_V83R2_CONSERVATISM_QUANTIFIED_DYNAMIC_STATEFLOW_BACKEND_OPEN',new_model=False,
    saved_model=model,saved_model_version='0.83r2',model_sha256=qa['model_sha256'],model_executed_this_run=True,
    trace_schema=75,reporting_api_version='0.76',matlab_passed=report['summary']['passed'],matlab_failed=0,
    independent_passed=qa['summary']['passed'],independent_failed=0,complete_saved_model_runs=counts['schedules'],
    held_intervals=counts['held_intervals'],positive_segments=counts['positive_segments'],interior_events=counts['interior_events'],
    required_actual_final_mode_coverage=report['mode_coverage'],bitwise_v80_comparisons=1,reviewer_selfchecks=len(qa['reviewer_selfchecks']),
    matlab_metadata=report['metadata'],comparisons=len(qa['comparisons']),hypothetical_dynamic_backend_implemented_in_stateflow=False,
    result_directory=folder.relative_to(ROOT).as_posix(),independent_qa=qa_path.relative_to(ROOT).as_posix(),
    derivation='audit/Electrical_conservatism_derivation_v84.md',results='audit/Electrical_conservatism_results_v84.md',
    primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
    limitations=limits,next_actionable_task=next_task)
for name in ['STATUS_v84.json','STATUS_stateflow_v84.json']:write(ROOT/name,status)
for name in ['MASTER_STAGEBOARD_v84.md','MASTER_STAGEBOARD_stateflow_v84.md','audit/Electrical_conservatism_results_v84.md']:write(ROOT/name,body)
write(folder/'prior_attempts.json',dict(directories=['results/electrical_conservatism_v84_20261013T105044_893030Z','results/electrical_conservatism_v84_20261013T105247_497281Z'],
    retained_failure='INTERIOR_EVENT_COVERAGE_NOT_EXERCISED_BY_0.2_OR_0.5_MW_CONTROL',
    corrected_fixture='Existing 1000 MW nonbinding cycle control with 11 historical events; twelve comparator cases and thresholds unchanged.',
    reviewer_refinement='Source-feasibility witness now uses exact max(floor,initial-lift) instead of an unnecessarily stronger below-floor bound.'))
added=['audit/scaffold_electrical_conservatism_v84.py','audit/electrical_conservatism_v84.py','audit/run_electrical_conservatism_v84.ps1','audit/close_electrical_conservatism_v84.py','audit/Electrical_conservatism_derivation_v84.md','matlab/run_electrical_conservatism_v84.m']
for rel in added:
    dest=folder/'closure_source_snapshot'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,dest)
write(folder/'closure_source_hashes.json',[dict(path=p,sha256=sha(ROOT/p)) for p in added])
progress=f'\n\n## {stamp} - v84 actual Stateflow conservatism experiment\n\nRead current STATUS/stageboards v83, acceptance, frontier, progress and current builder/kernel/adapter/QA before edits. Work remained in this project.\n\nFiles added: '+', '.join(added)+', report and STATUS/stageboard twins. Prior MATLAB/SLX/checkpoints hash-preserved; shared ledgers appended.\n\n'+body
for name,text in [('automation/engineering_progress.md',progress),('automation/STATEFLOW_ACCEPTANCE.md','\n\n## Saved-v83r2 conservatism checkpoint v84\n\n'+body),('audit/research_frontier_2026_10_08.md','\n\n## v84 electrical conservatism evidence and handoff\n\n'+body)]:
    with (ROOT/name).open('a',encoding='utf-8') as f:f.write(text)

checks=[]
def check(name,ok):checks.append(dict(name=name,passed=bool(ok)))
for e in json.loads((folder/'preservation.json').read_text()):check(e['path'],sha(ROOT/e['path'])==e['sha256'])
for e in json.loads((folder/'source_hashes.json').read_text()):check('source_'+e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'source_snapshot'/e['path'])==e['sha256'])
for e in json.loads((folder/'closure_source_hashes.json').read_text()):check('closure_'+e['path'],sha(ROOT/e['path'])==e['sha256'] and sha(folder/'closure_source_snapshot'/e['path'])==e['sha256'])
for e in json.loads((folder/'ledger_prefixes.json').read_text()):check('prefix_'+e['path'],hashlib.sha256((ROOT/e['path']).read_bytes()[:e['size']]).hexdigest()==e['sha256'])
check('status_twins',(ROOT/'STATUS_v84.json').read_bytes()==(ROOT/'STATUS_stateflow_v84.json').read_bytes())
check('stageboard_twins',(ROOT/'MASTER_STAGEBOARD_v84.md').read_bytes()==(ROOT/'MASTER_STAGEBOARD_stateflow_v84.md').read_bytes())
check('model_preserved',sha(ROOT/model)==qa['model_sha256'])
verification=dict(timestamp_utc=datetime.now(timezone.utc).isoformat(),checks=checks,
    summary=dict(passed=sum(c['passed'] for c in checks),failed=sum(not c['passed'] for c in checks)))
write(folder/'final_handoff_verification.json',verification)
assert verification['summary']['failed']==0
files=[p for p in folder.rglob('*') if p.is_file() and not any(x in ['cache','codegen'] for x in p.relative_to(folder).parts)]
write(folder/'artifact_manifest.json',[dict(path=p.relative_to(folder).as_posix(),sha256=sha(p)) for p in files])
print(json.dumps(dict(checkpoint='0.84',counts=counts,matlab=report['summary'],independent=qa['summary'],handoff=verification['summary'])))
