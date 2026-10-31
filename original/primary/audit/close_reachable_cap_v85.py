"""Publish workspace checkpoint only after executed model and independent QA pass."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal as D
import json,sys,hashlib
from reachable_cap_v85 import ROOT,MODEL,LEDGERS,sha,dump,rows
def main(folder):
    report=json.loads((folder/'report.json').read_text());qp=sorted(folder.glob('independent_QA_v85_*.json'))[-1];qa=json.loads(qp.read_text())
    assert report['summary']['failed']==qa['summary']['failed']==0
    assert all(c['passed'] for c in qa['checks']+qa['reviewer_selfchecks'])
    assert report['saved_model_version']=='0.85' and report['mode_coverage']==list(range(6))
    assert sha(ROOT/MODEL)==qa['model_sha256']
    good=next(json.loads(p.read_text(encoding='utf-8-sig')) for p in folder.glob('execution_*.json') if json.loads(p.read_text(encoding='utf-8-sig'))['exit_code']==0)
    assert f'PASS={report["summary"]["passed"]} FAIL=0 COMPLETE_RUNS={len(report["runs"])} FAULTS=7' in Path(good['log_path']).read_text()
    # No input, production source, baseline or evidence mutation since QA.
    for file in ['source_hashes.json','preservation.json']:
        for e in json.loads((folder/file).read_text()):assert sha(ROOT/e['path'])==e['sha256'],e['path']
    now=datetime.now(timezone.utc).isoformat();rel=folder.relative_to(ROOT).as_posix()
    intervals=sum(len(rows(r['trace'])) for r in report['runs'])
    segments=sum(int(row[12]) for r in report['runs'] for row in rows(r['trace']))
    events=sum(int(row[13]) for r in report['runs'] for row in rows(r['trace']))
    refs=sum(bool(rows(r['reference_trace'])) if r['reference_trace'] else False for r in report['runs'])
    next_task='Compare declared-horizon cap dependence against the v84 nonlinear comparator at H=1/2/4 hours and held-input partitions on identical histories, then derive a versioned interval-renewal contract before changing the immutable effective-policy kernel. Seek primary equipment supplement/calibration through a new accessible route. Preserve v80-v85 and all failed attempts.'
    limits=[
        'One certified constant cap over the declared horizon, not a maximal nonlinear instantaneous electrical limiter. Ignoring passive loss in the reachability bound is conservative; larger horizons can recover global-cap behavior.',
        'Compressor rating, approaches, cooling-factor and storage parameters remain synthetic. No new primary text, equipment calibration, article replication, measured physical validation, annual or generated-code acceptance; full signoffs remain 0/31.',
        'Auxiliary electricity is separate and total external electricity may exceed the compressor ceiling.',
        'Raw 27-operand policy and declared horizon are immutable. Thermal schema 75/reporter 76 authenticate effective policy; separate 29-operand certificate and independent QA bind raw policy, cap and reachable inventory.',
        'Same-agent algorithmic independence: exact Fraction and 120/160-digit closed exp/log equations call no production MATLAB solver. MATLAB reopens MAT for binary export; no independent personnel or independent MAT parser.',
        'Inherited finite-span, physical-clock, segment-count and unresolved-event domains remain. Analytic event segments execute within macro protocol ticks, not solver-clock events.',
        'Restricted startup failure, first successful 122-assertion candidate with stale inherited release label, and corrected 124-assertion/24930-pass candidate with one missing-cutoff-coverage QA failure are retained. Final expanded suite adds a focused cutoff witness; saved production model remains v85 and execution harness v85r2.'
    ]
    text=f'# Certified reachable-temperature Stateflow acceptance v85\n\nUTC {now}.\n\n'
    text+=f'New saved `{MODEL}` actually executes {len(report["runs"])} schedules / {intervals} held intervals / {segments} positive segments / {events} interior events, with all six modes. MATLAB {report["summary"]["passed"]} PASS / 0 FAIL; independent QA {qa["summary"]["passed"]} PASS / 0 FAIL; {len(qa["reviewer_selfchecks"])} separate reviewer corruptions detected. Seven actual chart refusals include exhausted/mutated horizon and uncertified ON dwell. {refs} fresh saved-v80 comparisons and clean saved-v85 reopening are bitwise equal. Every schedule also executes preserved v83r2 on identical inputs.\n\n'
    text+='A declared-horizon inventory upper bound replaces the global maximum-temperature electrical cap. It safely raises available heat for cold schedules while retaining the verified held-power loss/event kernel. Positive-loss charging crosses the hot-water floor; binding stop and repeated stop/cutoff/restart histories execute and pass independent closed-equation and pointwise electrical-power QA.\n\n'
    text+='| Case | v83r2 HP heat (MWh) | v85 HP heat (MWh) | Extra recovered source (MWh) | Extra compressor work (MWh) | Extra delivered service (MWh) | Extra final TES (MWh) |\n|---|---:|---:|---:|---:|---:|---:|\n'
    cmp=json.loads((folder/'comparisons_v85.json').read_text())
    for c in cmp:
        if c['id'] not in ['service_E3.0_a1.0','service_E8.5_a1.0','charge_E4.95_a1.0','loss_charge_E4.95_a1.0']:continue
        n={k:D(v) for k,v in c['new_totals'].items()};g={k:D(v) for k,v in c['global_totals'].items()}
        text+=f'| {c["id"]} | {g["hp_heat"]:.10g} | {n["hp_heat"]:.10g} | {n["recovered_source"]-g["recovered_source"]:.10g} | {n["compressor_work"]-g["compressor_work"]:.10g} | {n["delivered_service"]-g["delivered_service"]:.10g} | {n["final_inventory"]-g["final_inventory"]:.10g} |\n'
    text+='\nGains use additional compressor work. Charging gains are inventory, not delivered district heat. Comparisons use closed equations reconstructed from original-MAT binary exports, never reporting-hull midpoints.\n\n'
    text+=f'Model SHA256 `{qa["model_sha256"]}`. Timestamped execution/QA logs, original/reopened MAT, binary traces/certificates, source/preservation seals, predeclared cases and comparison evidence: `{rel}`. Derivation: `audit/Reachable_cap_derivation_v85.md`.\n\nLimitations:\n\n'+'\n'.join('- '+x for x in limits)+'\n\nNext actionable task: '+next_task+'\n'
    status=dict(version='0.85',timestamp_utc=now,inherits='STATUS_v84.json',result='CERTIFIED_DECLARED_HORIZON_CAP_SAVED_STATEFLOW_ACCEPTED_CALIBRATION_OPEN',new_model=True,
        saved_model=MODEL,saved_model_version='0.85',harness_version='0.85r2',model_sha256=qa['model_sha256'],model_executed_this_run=True,trace_schema=75,reporting_api_version='0.76',
        matlab_passed=report['summary']['passed'],matlab_failed=0,independent_passed=qa['summary']['passed'],independent_failed=0,complete_saved_model_runs=len(report['runs']),held_intervals=intervals,
        positive_segments=segments,interior_events=events,required_actual_final_mode_coverage=report['mode_coverage'],actual_fault_rejections=7,bitwise_v80_comparisons=refs,
        reviewer_selfchecks=len(qa['reviewer_selfchecks']),matlab_metadata=report['metadata'],result_directory=rel,independent_qa=qp.relative_to(ROOT).as_posix(),
        derivation='audit/Reachable_cap_derivation_v85.md',results='audit/Reachable_cap_results_v85.md',primary_article_replication=False,independent_physical_validation='NOT_TESTED',full_primary_signoffs=0,total_sources=31,
        limitations=limits,next_actionable_task=next_task)
    for name in ['STATUS_v85.json','STATUS_stateflow_v85.json']:dump(ROOT/name,status)
    for name in ['MASTER_STAGEBOARD_v85.md','MASTER_STAGEBOARD_stateflow_v85.md','audit/Reachable_cap_results_v85.md']:
        with (ROOT/name).open('x',encoding='utf-8') as f:f.write(text)
    entry='\n\n## '+now+' - v85 certified reachable-temperature Stateflow\n\nRead current STATUS/stageboards, acceptance, frontier and relevant code before edits. Work stayed inside this project. Added versioned cap, builder/SLX, execution and QA harnesses, derivation/results, status/stageboard twins. All prior models, MATLAB and checkpoints are hash-preserved; shared ledgers append-only.\n\n'+text+'\nStop after this coherent executed deliverable and handoff.\n'
    for name in LEDGERS:
        with (ROOT/name).open('a',encoding='utf-8') as f:f.write(entry)
    files=[p for p in folder.rglob('*') if p.is_file() and not any(x in p.parts for x in ['cache','codegen'])]
    files += [ROOT/MODEL,ROOT/'audit/close_reachable_cap_v85.py']+[ROOT/n for n in ['STATUS_v85.json','STATUS_stateflow_v85.json','MASTER_STAGEBOARD_v85.md','MASTER_STAGEBOARD_stateflow_v85.md','audit/Reachable_cap_results_v85.md']]
    dump(folder/'closure_seal.json',[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha(p)) for p in files])
    print(json.dumps({k:status[k] for k in ['result','matlab_passed','independent_passed','held_intervals','positive_segments','interior_events']}))
if __name__=='__main__':main((ROOT/sys.argv[1]).resolve())
